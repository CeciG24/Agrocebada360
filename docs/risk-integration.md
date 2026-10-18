# P4.14 — Integración de prioridades de revisión

`GET /risk/{id}` implementa el contrato público existente `0.1.0`. Utiliza los resultados de P3.9 correspondientes a `yield-v1`; no clasifica ni recalcula umbrales durante las consultas. El modelo, las predicciones, SHAP y los intervalos de `/predict` no se modifican.

## Metodología y alcance

La metodología interna `review-priority-adapter-v1` adapta las prioridades ya publicadas por Persona 3. El mapeo al vocabulario de la API se definió en P4.14 con la autorización del equipo; no se atribuye como una metodología oficial de FIRA ni una aprobación adicional de Persona 3.

| Condición documentada en P3.9 | Prioridad de origen | API `level` | Etiqueta de interfaz |
|---|---|---|---|
| Rendimiento bajo relativo y alerta OOD | Prioridad alta de revision | `high` | Prioridad alta |
| Rendimiento bajo relativo, sin alerta OOD | Revisar rendimiento estimado | `medium` | Revisión media |
| OOD sin rendimiento bajo relativo | Revisar caracteristicas inusuales | `medium` | Revisión media |
| Ninguna de las condiciones anteriores | Sin alerta combinada | `low` | Sin alerta combinada |

El rendimiento bajo relativo usa `predicción <= primer tercil`; el nivel intermedio incluye valores hasta el segundo tercil. Los terciles se calculan sobre las predicciones del conjunto evaluado, con interpolación lineal de pandas, conservando empates. Los resultados actuales son `3.210176393119016` y `4.365824382475769` t/ha. La alerta OOD publicada es `score_samples < -0.6319277612298091`; el umbral proviene del percentil 5 de entrenamiento del detector IsolationForest de P3.8. La integración comprueba estas reglas sobre los resultados existentes; no vuelve a ajustar el detector ni acredita una calibración de probabilidades.

**Es una prioridad operativa relativa, no una probabilidad de pérdida, riesgo crediticio ni recomendación agronómica validada.** Una alerta OOD no confirma un error predictivo. `low` significa “sin alerta combinada” bajo estas reglas, no ausencia de riesgo. Los intervalos exploratorios de P3.6 no intervienen en la clasificación. Los umbrales no deben recalcularse al filtrar parcelas o navegar por el mapa.

Hay 59 evaluaciones: **4 high, 17 medium y 38 low**. Las cuatro de prioridad alta son `AGC_029`, `AGC_061`, `AGC_087` y `AGC_120`. Para las 138 parcelas de entrenamiento no se inventa una evaluación: se conserva la ausencia esperada.

## Trazabilidad y validaciones

Fuentes originales, conservadas sin modificaciones:

- `ml/results/rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv`
- `ml/results/rol3/riesgo_yield_v1/metadata_riesgo_yield_v1.json`
- `ml/results/rol3/ood_yield_v1/predicciones_ood_yield_v1.csv`
- `ml/results/rol3/ood_yield_v1/metadata_ood_yield_v1.json`

`ml/risk_adapter.py` verifica cobertura exacta de IDs respecto a las predicciones del modelo cargado, duplicados, versiones, valores finitos, booleanos explícitos, coincidencia de scores/alertas con la fuente OOD, terciles, prioridades y conteos. La correspondencia numérica usa tolerancia absoluta `1e-8`, sin tolerancia relativa. La metadata OOD vincula modelo y dataset mediante hash y versión.

El empaquetado genera dos archivos opcionales dentro de la entrega:

- `risks.json`: respuestas públicas precalculadas, incluida la descripción con sus limitaciones.
- `risk_method.json`: versión interna, mapeo, umbrales, predicciones de referencia, modelo/hash/data_version y SHA256 de las cuatro fuentes.

Ambos se sellan en `integration_manifest.json`. La API valida sus hashes, modelo, dataset, cobertura, contexto, descripciones/niveles y predicciones de referencia contra el predictor congelado al iniciar. Publica la caché únicamente si todas las filas pasan. Las consultas de riesgo no leen archivos ni ejecutan inferencia o entrenamiento.

## Estados HTTP

| Caso | Respuesta |
|---|---|
| Evaluación disponible y compatible | 200, `available`, nivel/metodología/modelo/descripción presentes, `reason=null` |
| Parcela conocida sin evaluación; entrega antigua sin módulo | 200, `unavailable`, `RISK_NOT_READY`, cuatro campos de contexto null |
| Modo mock de la API | Ausencia explícita con `meta.mode=mock`; no reutiliza evaluaciones reales |
| ID desconocido | 404 `PARCEL_NOT_FOUND` |
| ID vacío/no válido | 422 `VALIDATION_ERROR` |
| Catálogo no disponible | 503 `DATA_UNAVAILABLE` |
| Modelo no disponible o módulo declarado incompleto/alterado/incompatible | 503 `RISK_UNAVAILABLE` |

Un fallo exclusivo del módulo de riesgo no deshabilita predicción ni explicación. Health mantiene los indicadores existentes de datos/modelo; no certifica todos los módulos opcionales. Cambiar la entrega requiere reiniciar la API.

## Regenerar y probar

Desde la raíz, usando una carpeta de salida nueva:

```powershell
.\.venv\Scripts\python.exe -m ml.integration --data-root data/integrated/verified-2026-10-17/data --out data/integrated/p414-2026-10-18/delivery
.\.venv\Scripts\python.exe scripts/verify_integrated_delivery.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/p414-2026-10-18/delivery --report data/integrated/p414-2026-10-18/integration-check.json
.\.venv\Scripts\python.exe scripts/verify_real_api.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/p414-2026-10-18/delivery --report data/integrated/p414-2026-10-18/http-check.json
$env:CEBADA_MODE = "real"
$env:CEBADA_DATA = (Resolve-Path data/integrated/verified-2026-10-17/data).Path
$env:CEBADA_DELIVERY = (Resolve-Path data/integrated/p414-2026-10-18/delivery).Path
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

`prepare_delivery` también integra riesgo cuando se utiliza desde `scripts/build_integration.py`. Se conservan entregas antiguas sin estos archivos como compatibles; para habilitar P4.14 hay que generar una nueva entrega. No se sobrescribe la entrega anterior. La clasificación de los resultados nuevos que no cumplan las verificaciones falla; no se degrada silenciosamente a `low` ni se reemplaza por mock.

En el frontend real, probar `/parcela/AGC_029?demo=0` (alta), `AGC_003` (media), `AGC_011` (sin alerta) y `AGC_001` (no disponible). Las descripciones y versión se conservan desde la respuesta de la API. El mapa mantiene neutras las parcelas sin evaluación consultada; la ruta de catálogo no publica evaluaciones masivas ni añade campos.

Evidencia de aceptación: [HTTP](risk-api-acceptance-2026-10-18.json), [adaptadores](risk-integration-acceptance-2026-10-18.json) y [navegador](risk-browser-acceptance-2026-10-18.json).
