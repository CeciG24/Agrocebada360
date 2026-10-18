# Integración de Data, ML y ML avanzado en dev

Las ramas `origin/ml-avanzado` y `origin/feature/preparacion-datos` están fusionadas en
`dev`. P4.7 se guardó por separado en `a797904`; las fusiones son `b695967` y `6a5023f`.
El modelo congelado y su schema se conservan sin reentrenar ni reserializar.

Aceptación del 17 de octubre: reconstrucción completa P1.15 aprobada, 29 tablas
CSV equivalentes, 197 geometrías y 59 predicciones/explicaciones verificadas.
La suite terminó con 172 tests Python y 15 tests frontend aprobados; lint y build
del frontend pasaron. El comando completo desde ambos ZIP pasó en
`data/integrated/verified-2026-10-17/`. El resumen versionable está en
`integration-acceptance-2026-10-17.json`; datos, modelos empaquetados y logs locales
permanecen bajo `data/`, fuera de Git. En Windows fue necesario ejecutar fuera
del sandbox para acceder al temporal del sistema y para los tests del cliente API.

## Construcción reproducible

Requiere los dos ZIP entregados por el equipo, fuera de Git, y un entorno compatible
con el modelo. Instalar en la `.venv` del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-inference.txt -r scripts_limpieza/requirements.txt -r api/requirements.txt
.\.venv\Scripts\python.exe scripts/build_integration.py --raw-zip DataSet.zip --clean-reference DATASET_RETO_AGRO_2026_LIMPIO_2.zip --out data/integrated/run-001
```

La salida debe ser nueva. El comando se detiene al primer fallo, conserva logs y no
sobrescribe una entrega previa. Extrae los cuatro ZIP internos con sus rutas reales,
ejecuta P1.1–P1.16 mediante P1.15, adapta ambos layouts, comprueba equivalencia,
audita las 30 features requeridas en todas las parcelas y genera el paquete.
No convierte esta ejecución en un entrenamiento ni una evaluación oficial.

Estructura de salida:

```text
run-001/
  raw/                 # fuentes extraídas, raw_manifest.json y salida de Data
  reference/           # layout del ZIP limpio usado por ML
  candidate/           # layout reconstruido desde el ZIP original
  data/                # CSV compatibles y geometrías; data_compatibility.json
  audit/               # auditoría temporal con fuentes vinculadas por SHA256
  delivery/
    model/             # joblib y schema originales + model_manifest.json P4.7
    feature_provenance.json
    catalog.json
    explanations.json
    intervals.json
    integration_manifest.json
  acceptance.json
  *.log
```

## Compatibilidad de datos y procedencia

La reconstrucción observada produce diferencias de coma flotante de hasta
`4.55e-13` respecto al ZIP limpio, incluyendo `1.42e-14` en las features del modelo.
Los bytes de CSV son diferentes y por tanto también lo es su hash de conjunto.

`ml.align_data` comprueba las 29 tablas CSV completas: mismas filas, columnas,
IDs y texto, con tolerancias numéricas `atol=rtol=1e-10`. Solo después copia los
bytes originales de los tres archivos que definen la versión publicada por ML
(`features_master`, target y catálogo) al layout reconstruido. Los demás archivos,
incluidas las geometrías validadas, provienen de la reconstrucción. Registra los
hashes de candidato/referencia, tolerancias y los archivos preservados en
`data_compatibility.json`; también actualiza los hashes del manifiesto de layout.
Si cambia un valor fuera de tolerancia o un ID, falla y no publica una salida.
No se asigna la versión anterior a bytes nuevos ni se modifica el schema para
ocultar una diferencia: se conservan explícitamente los bytes ya congelados.

`ml.data_handoff` implementa únicamente las transformaciones climáticas de P1.9:
seis estadísticas por año 2022–2025 y ventana conjunta, sin enero–marzo de 2025.
Recalcula todas las features declaradas en el schema para todos los IDs y las
compara con el CSV. Rechaza transformaciones desconocidas y no inventa su procedencia.
El histórico se declara como contexto ambiental, sin asumir cultivo de cebada.
La fecha máxima registrada es fecha de observación de la serie mensual; no es
una certificación de fecha de publicación del raster.

La evidencia vincula CSV y fuentes climáticas/topográficas, target, catálogo,
geometrías y compatibilidad mediante SHA256. El adaptador verifica estos hashes
antes de cargar el modelo. La auditoría de ML ya no se conforma con la antigua
muestra de 40 parcelas y precipitación: exige verificar todas las features del
modelo y todas las parcelas. Los sellos antiguos sin esa evidencia dejan de ser
válidos para nuevas exportaciones; hay que reauditar, sin alterar modelos congelados.
`CEBADA_RESULTS` permite mantener la auditoría nueva en una carpeta aislada.

## Adaptadores disponibles

```python
from ml.integration import IntegratedArtifacts

artifacts = IntegratedArtifacts("data/integrated/run-001/data",
                                "data/integrated/run-001/delivery")
prediction = artifacts.predict("<ID del catálogo>")
explanation = artifacts.explain("<ID del catálogo>")
risk = artifacts.risk("<ID del catálogo>")
```

La instancia carga una vez el pipeline P4.6/P4.7, verifica versiones y no entrena.
Los payloads siguen `docs/api-contract.md`: metadatos reales, t/ha y precisión sin
redondear. Los nombres amigables usan el nombre técnico mientras no exista un
diccionario aprobado. Las contribuciones se ordenan por impacto absoluto y
reconstruyen la salida con tolerancia `1e-8` t/ha. SHAP se sirve solo para los 59
IDs con artefacto; en otros IDs conocidos devuelve `EXPLANATION_NOT_READY`.

Las 197 geometrías son válidas y están en EPSG:4326, con coordenadas 2D
`[longitude, latitude]`; se preserva el CRS de origen en metadata. El catálogo no
expone los demás atributos del shapefile. Si no se entrega geometría, admite null.
La región permanece null: no se inventa equivalencia con municipio.

Los intervalos permanecen desactivados por defecto. Se pueden solicitar con
`predict(id, exploratory_intervals=True)` para los IDs cubiertos; el método se
identifica expresamente como exploratorio y no garantiza cobertura.
Riesgo permanece `unavailable / RISK_NOT_READY`: falta que ML avanzado apruebe el
mapeo `low/medium/high`, sus descripciones y la versión del método. El manifiesto
registra los hashes de sus archivos para poder continuar sin reinterpretarlos.
Los identificadores `linear-shap-adapter-v1` y `mean-oof-residual-adapter-v1`
versionan este perfil interno de adaptación; no se atribuyen al productor.

La API mantiene mock por defecto y ya permite conectar este paquete mediante
`CEBADA_MODE=real`, `CEBADA_DATA` y `CEBADA_DELIVERY` (P4.8/P4.9). Ver
[api/README.md](../api/README.md) para iniciar el servicio y comprobar su health.
Las rutas de predicción/catálogo conservan el contrato; P4.12 añade la ruta ya
definida `/explain/{id}` con sus ausencias y errores explícitos. Las pruebas de artefactos de esta sección son
distintas de la aceptación HTTP registrada en `api-real-acceptance-2026-10-17.json`.

## Verificación

```powershell
.\.venv\Scripts\python.exe scripts/verify_integrated_delivery.py --data-root data/integrated/run-001/data --delivery data/integrated/run-001/delivery --report data/integrated/run-001/recheck.json
$env:CEBADA_DATA = (Resolve-Path data/integrated/run-001/data).Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
.\.venv\Scripts\python.exe -m pytest tests ml/tests -q --basetemp=data/integrated/run-001/pytest
```

La aceptación contrasta las 59 predicciones contra los archivos publicados,
reconstrucción SHAP, intervalos, errores por IDs inexistentes, ausencias y catálogo
geográfico. Los tests negativos incluyen contaminación por temperatura futura,
cambio de fuentes sin cambiar `data_version`, desalineación de modelo/SHAP,
alteración numérica durante normalización y rutas de ZIP que intentan salir de su destino.
El entorno geoespacial probado se registra en `integration-environment-2026-10-17.json`.
Para regenerar SHAP y figuras originales instalar además `ml/requirements-advanced.txt`;
los adaptadores no dependen de ejecutar SHAP en cada consulta.

Siguen pendientes las confirmaciones oficiales de IDs y formato final de entrega;
se conserva el estado provisional de las listas, sin convertirlo en aprobación de FIRA.
