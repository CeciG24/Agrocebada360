# P4.15 — Resúmenes regionales

Se adoptó `state-regions-v1` por decisión explícita del equipo el 18-10-2026. La [investigación](regionalization-research-2026-10-18.md) documenta las referencias estatales; el catálogo ejecutable compartido por backend y frontend es `api/app/catalogs/regions.json`. Cada entrada conserva clave, nombre legible, estado, municipios presentes, referencia y URL de la fuente. Es una agrupación de Cebada360 basada en fuentes estatales, no una regionalización definida por FIRA. No son regiones agroclimáticas homogéneas ni unidades equivalentes entre estados.

| Clave | Región | Parcelas del dataset | Predicciones de evaluación | Media (t/ha, solo presentación) |
|---|---|---:|---:|---:|
| `hgo-apan` | Apan · Hidalgo | 19 | 4 | 4.3446 |
| `hgo-tulancingo` | Tulancingo · Hidalgo | 32 | 11 | 3.5764 |
| `pue-chignahuapan` | Chignahuapan · Puebla | 100 | 29 | 4.4511 |
| `tlx-poniente-calpulalpan` | Poniente–Calpulalpan · Tlaxcala | 46 | 15 | 2.9516 |

## Población y cálculo

La asignación se hace por coincidencia exacta de **estado y municipio** en el maestro validado. Cubre las 197 parcelas sin solapamientos ni cambios en sus identificadores o geometrías. Un municipio desconocido, una asignación ambigua o una partición no reconocida impide construir la entrega; no se adivinan correspondencias. No se realizó una certificación independiente de los límites municipales por intersección geoespacial.

La media usa exclusivamente las **59 predicciones publicadas para las parcelas de evaluación**, contrastadas contra el predictor congelado. No incluye los targets observados ni predicciones sobre las 138 parcelas de entrenamiento. El endpoint individual sigue pudiendo inferir parcelas etiquetadas; eso no las incorpora automáticamente al agregado de evaluación. `parcel_count` cuenta todas las parcelas del dataset en esa región y `predicted_count` cuenta las predicciones incluidas en su media.

Cada predicción tiene el mismo peso: no se pondera por superficie ni se promedian medias municipales. El backend conserva precisión completa; los cuatro decimales de la tabla y UI son formato de presentación. No se mezclan modelos, unidades, ciclos u orígenes. No se calcula producción total ni distribución regional de riesgo, porque no forman parte del schema público. Las prioridades P4.14 siguen disponibles por parcela.

**Estos resúmenes describen las parcelas del dataset, no todos los productores de las regiones.** La cobertura es parcial y las parcelas no constituyen una muestra probabilística acreditada. Apan tiene solo cuatro predicciones y la interfaz muestra un aviso de muestra pequeña; no se le atribuye significancia estadística.

## Artefactos y carga

`ml/region_adapter.py` genera `regions.json` dentro de la entrega integrada. Incluye:

- versión y contenido de la política regional y SHA256 del archivo fuente;
- SHA256 del maestro de parcelas y asignación por ID;
- modelo/hash/data_version y contexto contractual;
- predicciones de evaluación, cuya cobertura debe coincidir exactamente con `dataset_split=PREDICCION`.

El SHA256 del artefacto figura en `integration_manifest.json`. El catálogo empaquetado publica solo la clave de región ya prevista por el contrato. La API valida el artefacto contra la política y el maestro antes de publicar las asignaciones; después verifica sus predicciones contra el modelo cargado y genera los resúmenes en memoria. Las peticiones regionales no leen CSV/JSON, recalculan inferencia ni entrenan.

La política es un archivo versionado del repositorio: conservar sus bytes con la entrega o regenerar el paquete mediante el mismo checkout al desplegar. Si cambia su contenido/hash, no reutilizar silenciosamente un paquete anterior.

## API pública 0.1.0

`GET /regions/{region}` implementa la ruta ya definida, con exactamente `region`, `parcel_count`, `predicted_count`, `mean_prediction`, `unit`, `model_version` y `meta`. `GET /parcels` y `GET /parcel/{id}` usan las mismas claves. El filtro `/parcels?region=...` conserva su comportamiento contractual; un filtro sin coincidencias devuelve una lista vacía.

| Situación | Resultado |
|---|---|
| Región del dataset con predicciones verificadas | 200, media y cobertura |
| Región del dataset sin predicciones de evaluación | 200, `predicted_count=0`, media/unidad/modelo null |
| Región desconocida con fuente regional válida | 404 `REGION_NOT_FOUND` |
| Clave inválida | 422 `VALIDATION_ERROR` |
| Entrega antigua sin fuente; archivo regional ausente/alterado; asignaciones incompatibles | 503 `REGION_DATA_UNAVAILABLE` |
| Fuente válida, pero modelo no disponible o predicciones incompatibles | 503 `REGION_SUMMARY_UNAVAILABLE` |
| Catálogo general no disponible | 503 `DATA_UNAVAILABLE` |

Si falla exclusivamente la fuente regional, las asignaciones se ocultan como null y se conservan catálogo/predicción cuando sus fuentes son válidas. Si falla exclusivamente el resumen, se conservan las asignaciones validadas. No se activa mock por un fallo real. Las entregas antiguas siguen compatibles, con ausencia regional explícita. En modo mock de API se agrupan exclusivamente sus predicciones sintéticas y se declara `meta.mode=mock` / `unit=mock_unit`.

## Regeneración y ejecución

Desde la raíz, elegir una carpeta de entrega que todavía no exista:

```powershell
.\.venv\Scripts\python.exe -m ml.integration --data-root data/integrated/verified-2026-10-17/data --out data/integrated/p415-2026-10-18/delivery
.\.venv\Scripts\python.exe scripts/verify_integrated_delivery.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/p415-2026-10-18/delivery --report data/integrated/p415-2026-10-18/verify-adapters.json
.\.venv\Scripts\python.exe scripts/verify_real_api.py --data-root data/integrated/verified-2026-10-17/data --delivery data/integrated/p415-2026-10-18/delivery --report data/integrated/p415-2026-10-18/verify-http.json
$env:CEBADA_MODE = "real"
$env:CEBADA_DATA = (Resolve-Path data/integrated/verified-2026-10-17/data).Path
$env:CEBADA_DELIVERY = (Resolve-Path data/integrated/p415-2026-10-18/delivery).Path
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

La preparación completa mediante `scripts/build_integration.py` también incorpora este módulo al llamar al empaquetador. No se sobrescriben entregas existentes ni se modifica el modelo congelado.

Frontend: `http://127.0.0.1:5173/regional?demo=0`. Ofrece filtro por estado, selector regional, gráfica con resultados compatibles, tabla, cobertura, fuente estatal y aviso para muestras menores de cinco predicciones. La política compartida aporta las etiquetas sin añadir campos al contrato público; una clave no reconocida conserva su identificador. Los estados pendientes de riesgo y producción regional se mantienen explícitos.

Evidencias: [HTTP y regresión de P4.8–P4.15](regions-api-acceptance-2026-10-18.json), [adaptadores](regions-integration-acceptance-2026-10-18.json) y [navegador](regions-browser-acceptance-2026-10-18.json).
