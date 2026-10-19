# Cebada360 — Reto AgroCebada FIRA 2026

Prototipo para explorar parcelas, estimar rendimiento de grano en t/ha y consultar factores explicativos, prioridades de revisión y resúmenes regionales. Conserva el diseño oscuro y distingue explícitamente los modos real y demo.

## Ejecutar con datos reales

Desde la raíz, con Python 3.12.7 y Node disponibles:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements.txt -r ml/requirements-inference.txt -r ml/requirements-advanced.txt
$env:CEBADA_MODE = "real"
$env:CEBADA_DATA = (Resolve-Path data/deploy/data).Path
$env:CEBADA_DELIVERY = (Resolve-Path data/deploy/delivery).Path
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Abrir `http://127.0.0.1:5173/?demo=0`. Vite dirige las consultas a `http://127.0.0.1:8000`; `VITE_API_TARGET` permite cambiar ese destino local. Para demo visual usar `?demo=1`. La API arranca en mock si no se define `CEBADA_MODE`; para usar sus ejemplos sintéticos basta ejecutar uvicorn sin las variables de modo real. No existe sustitución silenciosa por datos mock cuando falla la API real.

## Qué contiene esta versión

- 197 parcelas con geometrías verificadas en EPSG:4326; 138 etiquetadas y 59 de evaluación en el split actual.
- Modelo congelado `yield-v1`: pipeline Ridge con 30 variables climáticas seleccionadas de una matriz de 215 columnas. No entrena durante peticiones.
- Predicciones, SHAP y prioridades de revisión para las 59 parcelas de evaluación. Las 138 de entrenamiento no tienen SHAP ni prioridades precalculadas.
- Cuatro regiones definidas internamente a partir de municipios. Sus medias son parciales, no ponderadas, sobre las 59 predicciones de evaluación; se muestra cobertura.
- Vista Modelo con métricas de validación interna y 138 pares OOF versionados. Verifica compatibilidad contra una predicción de referencia de la API. La API no expone un endpoint de métricas ni acredita el hash del modelo al navegador.

RMSE interno: 0.5147 t/ha; MAE: 0.3561 t/ha; R²: 0.6317. RMSE espacial: 0.6995 t/ha. Son resultados de validación interna, no desempeño oficial sobre el conjunto sin etiquetas. No se afirma superioridad sobre todos los baselines.

## Contratos y límites

Las siete rutas públicas son `/health`, `/parcels`, `/parcel/{id}`, `/predict/{id}`, `/explain/{id}`, `/risk/{id}` y `/regions/{region}`. Se mantienen API `0.1.0` y [System Contract](docs/system-contract.md) `0.3.0`; detalles en [API Contract](docs/api-contract.md).

El ciclo es abril–octubre de 2025; el día 31 representa el cierre técnico del mes. Los datos de 2022–2024 describen contexto ambiental, sin afirmar historial de cebada. SHAP explica asociaciones del modelo y no causalidad. Los intervalos exploratorios no tienen cobertura independiente validada y permanecen desactivados en la API. El riesgo representa prioridad relativa de revisión, no probabilidad de pérdida ni riesgo crediticio. Persona 3 validó el mapeo de niveles según confirmación del equipo comunicada en este chat; ver [riesgo](docs/risk-integration.md).

## Validar la entrega incluida

```powershell
.\.venv\Scripts\python.exe scripts/verify_integrated_delivery.py --data-root data/deploy/data --delivery data/deploy/delivery --report data/deploy/acceptance.json
.\.venv\Scripts\python.exe scripts/verify_real_api.py --data-root data/deploy/data --delivery data/deploy/delivery --report docs/deploy-api-acceptance-2026-10-19.json
.\.venv\Scripts\python.exe scripts/generate_submission.py --validate-only submissions/la_amariza_prediccion.csv
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:CEBADA_DATA = (Resolve-Path data/deploy/data).Path
.\.venv\Scripts\python.exe -m pytest tests ml/tests -q
cd frontend
npm test
npm run lint
npm run build
```

## Despliegue

Frontend público: [agrocebada360.vercel.app](https://agrocebada360.vercel.app/). API: [agrocebada-api.onrender.com](https://agrocebada-api.onrender.com). Vercel usa raíz `frontend`, build `npm run build`, salida `dist` y la reescritura SPA de `frontend/vercel.json` (o `vercel.json` si la raíz del proyecto es el repositorio). Configurar `VITE_API_URL` con el origen HTTPS de la API antes de construir. El proxy de Vite solo opera en desarrollo/preview local.

Render usa `render.yaml`, Python fijado y los artefactos versionados en `data/deploy`; configurar `CEBADA_ALLOWED_ORIGINS=https://agrocebada360.vercel.app` y reiniciar tras cambiar artefactos. No es necesario un disco persistente ni ejecutar `setup_render_disk.sh` para esta configuración. Ese script corresponde a una alternativa anterior. Conservar las reglas de `.gitattributes`: los hashes requieren preservar los bytes de los artefactos.

El push a `main` requiere comprobar después el resultado de los proveedores; por sí solo no demuestra que ambos despliegues hayan terminado. Ver [lista de cierre](docs/release-readiness.md).

## Entrega y trazabilidad

[Generación y validación del CSV](docs/fira-submission-instructions.md), [aportaciones con evidencia](docs/TEAM-CONTRIBUTIONS.md), [diccionario de datos](docs/data-dictionary-review-2026-10-18.md), [ficha Modelo](docs/model-view.md) y [definición regional](docs/regional-integration.md).

El CSV versionado contiene 59 IDs y predicciones finitas con cuatro decimales; su validación técnica no sustituye la confirmación del listado oficial de FIRA ni prueba que se haya enviado. Reporte, video, divulgación del uso de IA y envío final deben cerrarse por el equipo con las fuentes oficiales disponibles.
