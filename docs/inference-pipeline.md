# Pipeline de inferencia — tarea 4.6

Implementación en `ml/inference.py`, alineada al System Contract **0.3.0**
proporcionado por el equipo. No activa el modo real de la API ni cambia los
artefactos de Persona 2. El contrato público de API conserva su versión 0.1.0;
es independiente de la versión del contrato interno.

## Entradas y schema

- Modelo joblib congelado de confianza, con el preprocesamiento aprendido.
  Se acepta el objeto predictor directamente, como lo exporta ahora ML, o un
  diccionario `model`, `features`, `version`, `metadata`.
- JSON con los campos de §7.2: `model_version`, `target_name`, `prediction_unit`,
  `features`, `target_cycle`, `prediction_information_cutoff`,
  `training_id_source`, `missing_value_policy`.
- Versiones de §12 en el schema: `contract_version` (0.3.0),
  `feature_schema_version`, `data_version`, además de `model_version`.
- CSV con `parcel_id` y las features requeridas. Su orden físico puede variar.
  Se ignoran columnas adicionales. El target no puede figurar en `features`.
- IDs string del catálogo oficial, validados por el adaptador de Data. Se
  preservan exactamente, incluidos ceros iniciales. No hay cantidades fijas
  de parcelas; una parcela del catálogo sin features produce un error de
  predicción, no un ID inexistente.
- Procedencia técnica de las features entregada por Data/ETL.

Los placeholders, valores `PENDIENTE` y campos ausentes en los campos operativos
obligatorios impiden la carga; se conservan las notas sobre confirmaciones
oficiales pendientes sin convertirlas en requisitos ya confirmados.
No se migran automáticamente `unit` o `data_cutoff`: ML debe confirmar y publicar
el schema actualizado. Unidad: `t/ha`; ciclo: `2025-04/2025-10`.

## Vínculo verificable del modelo

No basta con el nombre del archivo para validar la versión. Esta implementación
admite tres mecanismos internos, alternativos:

1. Metadata dentro del artefacto: `cebada_metadata_` en un predictor directo,
   o `metadata` en un diccionario. Contiene `contract_version`, `model_version`,
   `feature_schema_version`, `data_version` y `features` ordenadas, que deben
   coincidir con el schema.
2. Un manifest de ML externo para el predictor sin metadata. Contiene las
   mismas cuatro versiones, `model_sha256` y `feature_schema_sha256`.
   Los hashes se calculan sobre los archivos congelados y se verifican antes
   de deserializar. Se entrega mediante `model_manifest_path`.

3. La entrega actual de ML con `model_sha256` en el schema. Se verifica ese
   hash antes de deserializar, además de `model_file` cuando está declarado y
   nombres/dimensiones aprendidos. No se exige envolver el predictor ni añadir
   metadata duplicada. Un manifest proporcionado también debe ser válido.

P4.7 define un paquete con los archivos originales y un manifiesto versionado
que añade el hash del JSON exacto del schema. Se puede crear/inspeccionar sin
deserializar mediante `python -m ml.model_bundle`; ver `docs/model-bundle.md`
y `InferencePipeline.from_bundle(...)`.

Estos nombres/hashes son un **formato interno de esta implementación**, no
campos exigidos por FIRA. Quien congela la entrega puede usar el empaquetador
de P4.7 sobre un par modelo/schema que ML ya vinculó. El empaquetador no
deduce versiones ni corrige discrepancias; no acredita procedencia de Data.

Se comprueban `n_features_in_` y `feature_names_in_` cuando existen. Los modelos
que seleccionan por nombre reciben un DataFrame ordenado; los demás, una matriz
numérica. No se modifica ni se ajusta nuevamente el preprocesamiento.

## Procedencia y temporalidad

`2025-10-31` es el cierre operativo interno del mes, no una fecha diaria atribuida
a FIRA. Se permiten features anteriores a 2025; no se interpretan como cebada.

El archivo de procedencia soportado concreta §5.3. Este ejemplo es sintético:

```json
{
  "data_version": "synthetic-data-v1",
  "features_file_sha256": "<SHA256 del CSV entregado>",
  "features": {
    "synthetic_feature": {
      "source": "Fuente documentada por ETL",
      "sensor_or_dataset": "Dataset documentado",
      "temporal_window": "2022-01/2024-12",
      "transformation": "Media de observaciones válidas",
      "missing_value_policy": "Imputación dentro del modelo congelado",
      "uses_historical_information": true,
      "historical_context": "Contexto ambiental; cultivo histórico no identificado",
      "information_kind": "temporal",
      "max_information_date": "2024-12-31"
    }
  }
}
```

Todas las features seleccionadas requieren metadata. `information_kind` es
`temporal` o `static`. Para temporal la fecha máxima es obligatoria y no puede
exceder el cutoff. Para estática puede ser null; fuente/ventana siguen siendo
obligatorias. El uso histórico requiere su significado en `historical_context`.

El hash vincula la evidencia al CSV exacto. No demuestra cómo se construyeron los
agregados: fuentes, periodos y semántica requieren auditoría y código de Data.
El reporte parcial actual `ml/results/data_audit.json` no sustituye la procedencia
por feature. No se fabrican fechas ni metadata usando solo nombres de columnas.

## Faltantes y salida

Se procesan las features numéricas usadas actualmente por ML. Textos no numéricos
e infinitos impiden la predicción; no se inventan codificaciones de categorías.

- `reject` rechaza vacíos y NaN.
- Otras políticas documentadas pasan los vacíos como NaN al predictor congelado;
  el modelo aplica su propio tratamiento o falla explícitamente.
- `documented` se acepta con `missing_value_policy_detail` técnico; no se exige
  que ML use un nombre de política inventado por Backend.

`predict()` devuelve un float finito **sin redondearlo**. Los cuatro decimales del
contrato corresponden al archivo oficial que genere el exportador/validador de
submission. Agregar ceros a una salida ya redondeada no recupera precisión.

## Uso

Instalar `ml/requirements-inference.txt` en un entorno compatible con las
versiones usadas para exportar. Modelos de terceros requieren sus bibliotecas.
Solo se cargan joblib de confianza: su deserialización puede ejecutar código.

```python
from ml.inference import InferencePipeline

# Entregas reales de Data/ML; los IDs ya están validados.
pipeline = InferencePipeline(
    model_path="ml/models/yield_model_v1.joblib",
    schema_path="ml/models/feature_schema.json",
    features_path="data/processed/features_master.csv",
    provenance_path="data/processed/feature_provenance.json",
    catalog_ids=verified_official_catalog_ids,
    model_manifest_path="ml/models/model_manifest.json",
)
pipeline.load_model()  # Al iniciar; llamadas repetidas reutilizan la carga.
prediction = pipeline.predict(requested_parcel_id)
unit = pipeline.unit
model_version = pipeline.model_version
```

La carga es atómica; un fallo deja la instancia sin modelo. Para cambiar de
artefactos se crea otra instancia. `predict()` llama a `preprocess()`; ninguna
entrena ni imputa fuera del modelo. Nunca se sustituyen errores por mocks.

## Errores y validación

| Error | Causa |
|---|---|
| `FeatureSchemaMismatch` | Schema, IDs, versiones, features o evidencia incompatibles |
| `ModelNotLoaded` | Modelo sin cargar o imposible de leer/deserializar |
| `ParcelNotFound` | ID string válido ausente del catálogo |
| `PredictionUnavailable` | Parcela sin features utilizables o salida inválida |

La traducción HTTP queda para integrar el servicio real; la API usa `MockService`.

```powershell
.\.venv\Scripts\python.exe -m pip install -r ml/requirements-inference.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

Las pruebas cubren carga única, ID opaco, columnas extra, orden, versiones,
modelo directo/empaquetado, manifest, cambios de archivos, procedencia,
histórico/estático, faltantes, salida finita y preprocesamiento por nombre.
Usan fixtures sintéticos; no aprueban el dataset/modelo reales pendientes.
