# API Cebada360 — P4.8/P4.9/P4.12/P4.14

La API conserva el contrato público 0.1.0 e implementa `/health`, `/parcels`,
`/parcel/{id}`, `/predict/{id}`, `/explain/{id}` y `/risk/{id}`. El modo por defecto es `mock`; configurar `real`
requiere rutas explícitas a datos y entrega integrada. Un fallo real nunca activa mocks.

Desde la raíz del repositorio, con una entrega creada mediante
[`scripts/build_integration.py`](../scripts/build_integration.py):

```powershell
.\.venv\Scripts\python.exe -m pip install -r api/requirements.txt -r ml/requirements-inference.txt
$env:CEBADA_MODE = "real"
$env:CEBADA_DATA = (Resolve-Path data/integrated/verified-2026-10-17/data).Path
$env:CEBADA_DELIVERY = (Resolve-Path data/integrated/p414-2026-10-18/delivery).Path
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
.\.venv\Scripts\python.exe scripts/verify_real_api.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/p414-2026-10-18/delivery --report data/integrated/p414-2026-10-18/api-acceptance.json
```

El test recorre catálogo y detalles, compara las 59 predicciones con ML, comprueba
errores HTTP, una única deserialización y prohíbe entrenamiento durante consultas.
La suite `tests/test_real_api.py` cubre además fallos de modelo, integridad,
procedencia, configuración y falta de features sin fallback.
La aceptación del 17 de octubre pasó con 197 parcelas/geometrías y 59 predicciones,
error máximo `1.78e-15` y una única deserialización. La suite conjunta terminó con
191 pruebas aprobadas tras P4.12. El reporte es `docs/api-real-acceptance-2026-10-17.json`.
El frontend puede usar las rutas implementadas con el modo demo local desactivado;
los agregados regionales aún requieren su integración HTTP.

## Explicabilidad P4.12

`GET /explain/{id}` sirve contribuciones verificadas y cacheadas al iniciar:
hash del archivo vinculado a la entrega, modelo, features exactas, escala,
contexto real, signo, orden y reconstrucción con tolerancia absoluta `1e-8`.
La salida reconstruida también se compara con el predictor cargado. El servicio
no ejecuta SHAP ni lee artefactos en cada petición; devuelve todas las contribuciones,
para que la interfaz pueda seleccionar las principales sin perder la identidad SHAP.

Hay 59 explicaciones precalculadas. Para un ID conocido sin explicación, devuelve
200 con `status=unavailable`, `reason=EXPLANATION_NOT_READY`, contexto null y
`features=[]`. ID desconocido: 404. Si un archivo declarado falta, está corrupto
o pertenece a otro modelo, devuelve 503 `EXPLANATION_UNAVAILABLE`, manteniendo
predicción y catálogo disponibles. Health conserva sus indicadores de datos/modelo;
no certifica disponibilidad de todos los módulos opcionales. Mock devuelve
ausencia explícita, sin inventar contribuciones.

Para probar el frontend por proxy, abrir
`http://127.0.0.1:5173/parcela/AGC_003?demo=0`. Esta parcela dispone de explicación;
`AGC_001` permite probar ausencia esperada. Levantar Vite desde `frontend/`:

```powershell
$env:VITE_API_TARGET = "http://127.0.0.1:8000"
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
node scripts/check-api.mjs http://127.0.0.1:5173 AGC_003
```

La comprobación del navegador validó el dashboard, el detalle con 30 contribuciones,
el origen `API · real` y la vista móvil de 390 px sin overflow ni errores JavaScript.
P4.14 añade las prioridades de revisión verificadas cuando la entrega incorpora su módulo.

## Nombres amigables P4.13

El catálogo `api/app/catalogs/feature_labels.json` documenta las 30 variables
climáticas de yield-v1: nombre, definición, unidad de entrada, fórmula y ventana.
Ver [diccionario de variables](../docs/model-feature-dictionary.md).
Las etiquetas se basan en el cálculo P1.9 auditado y se contrastaron con el
diccionario entregado por Persona 1; coinciden en significado, unidades y periodos.
Ver [comparación y complementos](../docs/data-dictionary-review-2026-10-18.md).
La entrega del documento no equivale a aprobación explícita de las etiquetas ni
les atribuye carácter oficial de FIRA.

La API las aplica al cargar SHAP únicamente si coinciden los hashes del modelo y
schema. Cambia solo `friendly_name`, después de verificar contribuciones, escala,
orden y reconstrucción. No modifica los artefactos originales ni añade campos al
contrato. Una variable desconocida, otro modelo/schema o un diccionario ausente
conservan el nombre técnico, sin interrumpir predicción ni explicación.

El frontend muestra los nombres recibidos y mantiene el código técnico en el
título de la etiqueta; la gráfica completa permite desplegarlo con teclado o
toque. Los impactos siguen en t/ha. La unidad mm/°C del diccionario describe la
entrada climática, no la contribución SHAP.

Aceptación P4.13 del 18 de octubre: 201 pruebas Python, 15 de frontend, lint y
build aprobados; 30 nombres comprobados en 59 explicaciones y navegador en
escritorio/móvil. Evidencia en `docs/api-real-acceptance-2026-10-18.json` y
`docs/feature-labels-acceptance-2026-10-18.json`.

## Prioridades de revisión P4.14

`GET /risk/{id}` sirve las evaluaciones P3.9 verificadas para yield-v1:
4 prioridades altas, 17 medias y 38 sin alerta combinada. Utiliza la metodología
interna `review-priority-adapter-v1`. Los niveles no son probabilidades de pérdida
ni riesgo crediticio; `low` se presenta como “Sin alerta combinada”.

La entrega nueva debe generarse antes de usar la ruta `CEBADA_DELIVERY` del ejemplo;
las entregas antiguas siguen funcionando con riesgo `unavailable`. Ver
[método, fuentes, regeneración y estados HTTP](../docs/risk-integration.md).
Los artefactos opcionales `risks.json` y `risk_method.json` se validan y cachean al
iniciar. Ausencia esperada: 200 `RISK_NOT_READY`; corrupción declarada: 503
`RISK_UNAVAILABLE`, sin deshabilitar predicción ni SHAP. Las 138 parcelas de
entrenamiento no reciben evaluaciones inventadas. Mock declara ausencia explícita.

Aceptación: 229 pruebas Python y 16 de frontend aprobadas; lint/build correctos,
59 evaluaciones HTTP contrastadas con Persona 3 y navegador desktop/móvil sin
errores. Evidencia: `docs/risk-api-acceptance-2026-10-18.json`,
`docs/risk-integration-acceptance-2026-10-18.json` y
`docs/risk-browser-acceptance-2026-10-18.json`.
