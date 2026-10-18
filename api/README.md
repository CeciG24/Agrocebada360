# API Cebada360 — P4.8/P4.9

La API conserva el contrato público 0.1.0 y sus cuatro rutas: `/health`, `/parcels`,
`/parcel/{id}` y `/predict/{id}`. El modo por defecto es `mock`; configurar `real`
requiere rutas explícitas a datos y entrega integrada. Un fallo real nunca activa mocks.

Desde la raíz del repositorio, con una entrega creada mediante
[`scripts/build_integration.py`](../scripts/build_integration.py):

```powershell
.\.venv\Scripts\python.exe -m pip install -r api/requirements.txt -r ml/requirements-inference.txt
$env:CEBADA_MODE = "real"
$env:CEBADA_DATA = (Resolve-Path data/integrated/verified-2026-10-17/data).Path
$env:CEBADA_DELIVERY = (Resolve-Path data/integrated/verified-2026-10-17/delivery).Path
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

Las rutas relativas se resuelven desde el directorio de ejecución; usar absolutas
en despliegue. `api/.env.example` documenta las variables, pero no se carga de forma
automática. `CEBADA_MODE=real` sin ambas rutas o con un modo desconocido detiene la
configuración. Para volver a datos sintéticos, usar `CEBADA_MODE=mock` y reiniciar.

El servicio valida hashes, procedencia, versiones y correspondencia de IDs al
iniciar. Carga una vez el joblib y su preprocesamiento congelado. Las consultas
no entrenan, reabren CSV ni recargan artefactos; un cambio de entrega requiere reiniciar.
`/predict/{id}` conserva el float finito sin redondear y declara `unit=t/ha`, la
versión del modelo y `meta.mode=real`. Los cuatro campos de intervalo permanecen
null: activar intervalos es una integración posterior y opcional.

El catálogo usa exclusivamente `id`, `region` y geometría verificadas. No expone
productores, target, features, superficies ni otros atributos internos.
`/parcels?include_geometry=true` entrega el mapa completo en una petición.
Sin ese parámetro no incluye la clave geometry. Una geometría ausente de origen
puede ser null; un catálogo inválido o inaccesible produce un error operativo.
Las regiones permanecen null hasta contar con su fuente autorizada. Un filtro
sin coincidencias devuelve `items=[]`, `total=0`, como establece el listado.

Estados operativos:

| Estado | Health | Catálogo | Predicción |
|---|---|---|---|
| Real listo | 200, data_ready=true, model_loaded=true | 200 | 200 |
| Modelo incompatible/ausente | 503, data_ready=true, model_loaded=false | 200 | 503 MODEL_UNAVAILABLE |
| Fuente/catálogo inválido | 503, data_ready=false, model_loaded=false | 503 DATA_UNAVAILABLE | 503 DATA_UNAVAILABLE |
| ID desconocido con catálogo listo | — | 404 PARCEL_NOT_FOUND | 404 PARCEL_NOT_FOUND |
| ID conocido sin features/salida utilizable | — | 200 | 503 PREDICTION_UNAVAILABLE |

Health mock sigue declarando `model_loaded=false` y puede estar `ok` porque no
requiere un modelo. Los detalles de excepciones se registran en el servidor;
la respuesta pública mantiene códigos y mensajes seguros del contrato.
Una fuente corrupta de geometrías detectada al cargar no se oculta devolviendo null.

Verificación de la entrega real, sin depender de un servidor ya levantado:

```powershell
.\.venv\Scripts\python.exe scripts/verify_real_api.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/verified-2026-10-17/delivery --report data/integrated/verified-2026-10-17/api-acceptance.json
```

El test recorre catálogo y detalles, compara las 59 predicciones con ML, comprueba
errores HTTP, una única deserialización y prohíbe entrenamiento durante consultas.
La suite `tests/test_real_api.py` cubre además fallos de modelo, integridad,
procedencia, configuración y falta de features sin fallback.
La aceptación del 17 de octubre pasó con 197 parcelas/geometrías y 59 predicciones,
error máximo `1.78e-15` y una única deserialización. La suite conjunta terminó con
179 pruebas aprobadas. El reporte es `docs/api-real-acceptance-2026-10-17.json`.
El frontend puede usar estas cuatro rutas con el modo demo local desactivado;
explicabilidad, riesgo y agregados regionales aún requieren sus integraciones HTTP.
