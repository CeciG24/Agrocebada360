# P4.7 — Serialización y schema del modelo

Perfil interno implementado: **bundle 1.0.0**, compatible con System Contract
**0.3.0**. La API pública conserva **0.1.0**. No se cambian endpoints ni se
activa el servicio real. Este perfil concreta decisiones de integración; no
agrega requisitos atribuidos a FIRA ni confirma los pendientes oficiales de §20.

## Entrega congelada

```text
<carpeta_de_entrega>/
  <nombre_declarado_por_ML>.joblib
  feature_schema.json
  model_manifest.json
```

El joblib contiene el predictor y el preprocesamiento aprendido. Se copian los
archivos originales de ML byte a byte, sin envolver, reentrenar, reserializar ni
inyectar metadata al predictor. El manifiesto vincula versiones y hashes.

El perfil de entrega exige en `feature_schema.json`:

- `contract_version`, `model_version`, `feature_schema_version`, `data_version`.
- Target interno documentado, unidad `t/ha`, ciclo `2025-04/2025-10`, corte
  operativo no posterior a `2025-10-31` y `training_id_source`.
- Features únicas y ordenadas, sin ID/target, y `n_features` coherente.
- Política de faltantes confirmada; `documented` requiere descripción técnica.
- `model_file` y SHA256 del archivo ya declarados por ML.
- Entorno de exportación: Python y versiones de paquetes, incluyendo joblib.

Se preservan los campos adicionales de ML, incluidos comentarios sobre alias y
nombres oficiales pendientes. Si aparecen `verified` y `fast_mode`, deben ser
respectivamente `true` y `false`. Esos flags no prueban por sí solos temporalidad
ni procedencia. Un alias interno no se convierte en confirmación oficial.

Los schemas Draft 2020-12 están en `docs/schemas/`: `model-artifact.schema.json`,
`model-bundle.schema.json`, `feature-provenance.schema.json`. El validador Python
`ml/artifact_contract.py` añade comprobaciones entre campos, fechas y hashes,
sin agregar dependencias al runtime de inferencia.

## Manifiesto 1.0.0

Claves obligatorias: `bundle_format_version: "1.0.0"`, `serialization: "joblib"`,
las cuatro versiones copiadas del schema, `model_file`, `feature_schema_file`,
`model_sha256` y `feature_schema_sha256`. Los hashes se calculan sobre los bytes
exactos; no se deducen versiones del nombre del archivo.

Se rechazan nombres con rutas relativas/absolutas o ADS de Windows, enlaces que
resuelvan fuera del paquete, claves JSON duplicadas y NaN/Infinity. Los hashes
vinculan archivos, no autentican a su autor: conservar el origen/commit de una
entrega de confianza. Joblib puede ejecutar código al deserializar.

## Empaquetar e inspeccionar

Desde la raíz, con los originales recibidos de ML:

```powershell
.\.venv\Scripts\python.exe -m ml.model_bundle pack --model <modelo.joblib> --schema <feature_schema.json> --out <nueva_carpeta>
.\.venv\Scripts\python.exe -m ml.model_bundle inspect --bundle <carpeta>
```

`pack` verifica el hash que declaró ML; no lo corrige. No sobrescribe carpetas
existentes y escribe el manifiesto al final. Una copia interrumpida puede dejar
archivos parciales, pero no un paquete válido sin su manifiesto completo; usar
una carpeta nueva. `inspect` comprueba integridad, schema y versiones **sin
deserializar**. Un rechazo termina con código 1.

`ARTIFACTS_VERIFIED` no significa API real lista: `data_provenance_checked` sigue
en `false`. El informe compara entorno declarado e instalado, no instala nada
ni oculta diferencias. El entorno de ML puede incluir paquetes que el modelo
elegido no necesita; su ausencia se informa sin deducir dependencias por nombre
del algoritmo. La reproducción necesita un entorno compatible y evidencia.

## Uso con 4.6

```python
from ml.inference import InferencePipeline

pipeline = InferencePipeline.from_bundle(
    bundle_path="data/model-bundles/<entrega>",
    features_path="data/processed/features_master.csv",
    provenance_path="data/processed/feature_provenance.json",
    catalog_ids=verified_catalog_ids,
)
pipeline.load_model()
prediction = pipeline.predict(requested_id)
```

`from_bundle` verifica artefactos; `load_model` vuelve a comprobar los vínculos,
exige procedencia de Data y comprueba nombres/dimensiones aprendidos. La carga
sigue siendo atómica e idempotente; predict no entrena ni inventa imputaciones.

También se acepta directamente el formato actual de ML: `model_sha256` en el
schema, sin exigir metadata duplicada dentro del predictor. El paquete añade
el hash del JSON exacto. Un manifiesto proporcionado siempre debe ser válido.
Se conserva el soporte previo de metadata embebida y manifiestos legacy; no se
migran automáticamente schemas 0.1.0 ni se fabrican campos oficiales.

## Procedencia de Data

El CSV y su procedencia permanecen separados del modelo. Data debe proporcionar
`data_version`, SHA256 del CSV y metadata por cada feature seleccionada: fuente,
sensor/dataset, ventana, transformación, faltantes, uso histórico, tipo de
información y fecha máxima; el histórico requiere su significado. Ver
`docs/inference-pipeline.md`. Todo se comprueba antes de deserializar.

El manifiesto de rutas de `prepare_data.py` y el sello parcial `data_audit.json`
no sustituyen esa procedencia. No se generan fechas o fuentes a partir de los
nombres de columnas para conseguir que el modelo cargue.

## Evidencia inicial — 16 de octubre

Se empaquetaron los originales de `origin/ml`, commit
`2c7402650db6c830a7ba7e783836821a7353d719`, en la carpeta local ignorada
`data/model-bundles/yield-v1-p47/`. Sus blobs coinciden con esa referencia.
Modelo `yield-v1`, schema `features-v1`, **30 features**,
`data_version = sha256:b045a212af57282a` y modelo SHA256
`f624c2324e418b642a41c98bed53977fa4eb9fa3e210c0341d239592b4bc33d6`.

Se conservaron ambos archivos originales. El reporte declara Python exportador
3.13.9 frente a 3.12.14 local y los paquetes del entorno de ML ausentes localmente.
Intentar usar el manifiesto de rutas de Data como procedencia sigue fallando,
con **cero deserializaciones**. La evidencia completa está en
`docs/model-bundle-acceptance-2026-10-16.json`.

Después de verificar los hashes, se cargó explícitamente el joblib de confianza
fuera de la API y se reprodujeron sus 59 predicciones, con diferencia máxima
`8.88e-16`. Esto comprueba que el paquete conserva el predictor; no equivale a
aceptación del flujo completo de `InferencePipeline` con procedencia real.
La suite completa de API/inferencia/paquetes terminó con **139 pruebas aprobadas**.

`tests/test_model_bundle.py` prueba inferencia real con un pipeline sklearn
**sintético**, bytes, hashes, nombres, versiones, entorno y ausencia de
procedencia. No convierte ese fixture en aceptación del dataset real.

**Estado:** definición y herramientas P4.7 implementadas y compatibles con los
artefactos actuales de ML. El perfil queda documentado para acuerdo del equipo;
no se afirma aprobación de otros integrantes. Aceptar datos reales y activar
`/predict` quedan pendientes de Data y de 4.8.

## Integración comprobada — 17 de octubre

El perfil climático P1.9 ya dispone de un adaptador que verifica sus 30 features
en todos los IDs, genera procedencia respaldada por fuentes y carga el paquete
mediante `InferencePipeline`. Se reconstruyó el dataset desde los archivos
originales y se documentó la compatibilidad numérica/bytes antes de reutilizar el
modelo. La aceptación real de 59 predicciones y explicaciones está en
`integration-acceptance-2026-10-17.json`; instrucciones completas en
[integration-data-ml.md](integration-data-ml.md). Activar el servicio HTTP sigue
siendo P4.8; los resultados previos se conservan como evidencia histórica.
