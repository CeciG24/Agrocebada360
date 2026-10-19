# Aportaciones del Equipo — Agrocebada360

Versión: `1.0.0`
Fecha: 2026-10-18

Este documento registra las actividades y aportaciones de cada integrante del equipo,
en cumplimiento con las Bases de Participación del Reto AgroCebada FIRA 2026 (§ Reporte técnico).

---

## Persona 1 — Data / ETL / Geospatial

**Rol:** Preparación de datos, ingeniería de features, validación geoespacial y reproducibilidad del dataset.

| ID | Tarea | Entregable | Período |
|----|-------|-----------|---------|
| P1.1 | Inventario y diccionario del dataset | `data-dictionary.md` con archivos, columnas, fuentes, periodos, granularidad y faltantes | 24 sep 2026 |
| P1.2 | Validar IDs y crear maestro de parcelas | `parcel_master.csv` con 197 parcelas, split train/evaluación, área y ubicación | 24–25 sep 2026 |
| P1.3 | Normalizar fechas y campos temporales | Fechas en formato YYYY-MM-DD + year, month y day_of_year | 24–25 sep 2026 |
| P1.4 | Separar datasets por sensor | Conjuntos separados Sentinel-2, Landsat y Planet | 25–26 sep 2026 |
| P1.5 | Preparar clima por parcela | Precipitación, Tmin, Tmax y agregados por parcela | 25–27 sep 2026 |
| P1.6 | Preparar topografía y geometría | Área, elevación, pendiente, municipio, estado y centroides | 25–27 sep 2026 |
| P1.7 | Agregados satelitales por parcela | mean, median, max, min, std y rango por índice/sensor | 28–30 sep 2026 |
| P1.8 | Features temporales/fenológicas | Picos, fecha de pico, AUC, crecimiento, caída y variabilidad | 29 sep – 1 oct 2026 |
| P1.9 | Features climáticas por ventanas | Precipitación acumulada/ventanas, Tmax/Tmin y amplitud térmica | 29 sep – 1 oct 2026 |
| P1.10 | Construir `features_master.csv` | Una fila por parcela con 30 features reproducibles | 1–2 oct 2026 |
| P1.11 | Crear datasets de predicción temprana | Cortes abril–junio, julio, agosto, septiembre y octubre | 4–6 oct 2026 |
| P1.12 | Generar features por cada corte temporal | Matrices de features equivalentes por mes límite | 5–7 oct 2026 |
| P1.13 | Auditoría final de features y leakage | Checklist sin leakage, mismas columnas train/test y fechas válidas | 10–12 oct 2026 |
| P1.14 | Script reproducible `build_features.py` | Script que reconstruye `features_master.csv` desde datos crudos | 11–13 oct 2026 |
| P1.15 | Validación final de datos y reproducibilidad | Reejecución limpia de preparación y features verificada | 16–17 oct 2026 |

**Artefactos clave producidos:**
- `features_master.csv` — 197 parcelas × 30 features de clima y vegetación
- `parcel_master.csv` — maestro con IDs, split, área, ubicación y geometría
- `scripts/build_integration.py` — reproducibilidad verificada con tolerancia 1e-10
- `docs/data-dictionary-review-2026-10-18.md` — diccionario reconciliado con fuente Persona 1

---

## Persona 2 — Modelado Predictivo

**Rol:** Entrenamiento, comparación y selección del modelo de predicción de rendimiento.

| ID | Tarea | Entregable | Período |
|----|-------|-----------|---------|
| P2.1 | Preparar notebook de baselines | Notebook reproducible con Dummy, lineales y árboles | 24–26 sep 2026 |
| P2.2 | Definir métricas y protocolo de comparación | RMSE principal + MAE y R²; tabla estándar de resultados | 24–25 sep 2026 |
| P2.3 | Entrenar baselines reales | Resultados de Dummy, Ridge, RF, ExtraTrees, CatBoost, XGBoost/LightGBM | 2–3 oct 2026 |
| P2.4 | Comparar familias de features E0–E5 | Tabla de experimentos: topografía, básico, Planet, combinaciones y clima | 2–4 oct 2026 |
| P2.5 | Tuning de los 2–3 mejores modelos | Hiperparámetros y CV de finalistas | 3–5 oct 2026 |
| P2.6 | Entrenar modelos de predicción temprana | RMSE por corte junio–octubre | 6–8 oct 2026 |
| P2.7 | Evaluar ensemble final | Weighted ensemble de modelos finalistas y comparación CV | 6–9 oct 2026 |
| P2.8 | Seleccionar modelo definitivo | Modelo, hiperparámetros, RMSE, MAE y R² documentados | 10–12 oct 2026 |
| P2.9 | Reentrenar modelo final con las 138 parcelas | Artefacto final entrenado sobre conjunto de entrenamiento completo | 12–13 oct 2026 |
| P2.10 | Generar predicciones de las 59 parcelas | `predictions_raw.csv` con rendimiento en t/ha y 4 decimales | 13–14 oct 2026 |
| P2.11 | Validación final de modelo y predicciones | Chequeo final de modelo, métricas y 59 predicciones | 16–17 oct 2026 |

**Artefactos clave producidos:**
- `ml/models/yield_model_v1.joblib` — modelo Ridge congelado, entrenado en 138 parcelas
- `predictions_raw.csv` — 59 predicciones en t/ha, rango [1.9, 6.5], media ≈ 3.9
- Tabla de experimentos E0–E5 documentada en notebooks

---

## Persona 3 — ML Avanzado / Validación / Explicabilidad

**Rol:** Validación espacial, incertidumbre predictiva, explicabilidad SHAP, detección OOD y clasificación de riesgo.

| ID | Tarea | Entregable | Período |
|----|-------|-----------|---------|
| P3.1 | Diseñar validación convencional y espacial | Esquema K-Fold/Repeated K-Fold + GroupKFold espacial | 24–27 sep 2026 |
| P3.2 | Definir política temporal anti-leakage | Documento: no usar observaciones posteriores a octubre 2025 | 24–25 sep 2026 |
| P3.3 | Ejecutar validación espacial | Resultados GroupKFold por municipio/grupos espaciales | 3–5 oct 2026 |
| P3.4 | Comparar aporte de sensores | Análisis de aporte Sentinel, Landsat y Planet | 3–5 oct 2026 |
| P3.5 | Ablation study por grupos de variables | Modelo completo vs. −clima, −Planet, −topografía, −estrés | 4–6 oct 2026 |
| P3.6 | Implementar incertidumbre predictiva | Intervalos calibrados (conformal prediction) | 5–8 oct 2026 |
| P3.7 | Generar SHAP global y por parcela | Importancia global + explicación individual para 59 parcelas | 6–9 oct 2026 |
| P3.8 | Detección fuera de distribución | Score OOD con Isolation Forest | 7–9 oct 2026 |
| P3.9 | Definir riesgo productivo | Reglas documentadas usando incertidumbre + estrés + OOD → niveles high/medium/low | 8–10 oct 2026 |
| P3.10 | Consolidar resultados técnicos | Resumen de importancia, intervalos, CV espacial, early prediction y ablation | 10–14 oct 2026 |
| P3.11 | Gráficas científicas finales | Predicted vs Real, residuos, importancia y RMSE temporal | 11–14 oct 2026 |
| P3.12 | Validación final de intervalos, SHAP y gráficas | Resultados finales consistentes con modelo congelado | 16–17 oct 2026 |

**Artefactos clave producidos:**
- `docs/rol3/` — 12 documentos técnicos (protocolo, ablation, SHAP, OOD, riesgo, gráficas, consolidación)
- SHAP precalculados para 59 parcelas; verificación: |sum(SHAP) − predicción| < 1e-8
- Clasificación de riesgo: 4 high, 17 medium, 38 low (sobre 59 parcelas evaluadas)
- Score OOD (Isolation Forest) cacheado por parcela
- `docs/rol3/incertidumbre_predictiva_P3_6.md` — intervalos exploratorios documentados

---

## Persona 4 — Cecilia — Backend & ML Engineering

**Rol:** Arquitectura del repositorio, API FastAPI, pipeline de inferencia, integración con ML, testing, despliegue y entrega.

| ID | Tarea | Entregable | Período |
|----|-------|-----------|---------|
| P4.1 | Crear estructura del repositorio | Repo con `api/`, `ml/`, `frontend/`, `data/`, `notebooks/`, `tests/`, `docs/`, `scripts/` | 24 sep 2026 |
| P4.2 | Diseñar contrato de API | Especificación de endpoints: `/parcels`, `/parcel/{id}`, `/predict/{id}`, `/explain/{id}`, `/regions` | 24–25 sep 2026 |
| P4.3 | Crear respuestas MOCK | JSON mock con predicción, intervalo, riesgo, confianza y metadata | 25 sep 2026 |
| P4.4 | Crear FastAPI base | API funcional con `/health`, `/parcels`, `/parcel/{id}`, `/predict/{id}` en modo mock | 25–27 sep 2026 |
| P4.5 | Configurar flujo GitHub y ramas | main/develop + ramas feature y reglas básicas de PR | 24–25 sep 2026 |
| P4.6 | Crear pipeline de inferencia | `load_model()`, `preprocess()`, `predict()` reproducibles | 2–4 oct 2026 |
| P4.7 | Definir serialización y schema del modelo | `model.joblib` + `feature_schema.json` | 2–3 oct 2026 |
| P4.8 | Conectar `/predict` con modelo real | Endpoint real de inferencia por ID de parcela | 4–5 oct 2026 |
| P4.9 | Endpoint de metadata de parcela | `/parcel/{id}` con municipio, estado, área, elevación, pendiente y coordenadas | 28 sep – 1 oct 2026 |
| P4.10 | Preparar servicios de integración frontend | `getParcels()`, `getParcel()`, `getPrediction()` y manejo de errores | 28 sep – 2 oct 2026 |
| P4.11 | Integrar intervalos predictivos en API | `prediction + lower + upper` en respuesta API | 8–10 oct 2026 |
| P4.12 | Crear endpoint de explicabilidad SHAP | `/explain/{id}` con factores e impacto | 9–11 oct 2026 |
| P4.13 | Diccionario de nombres amigables | `technical_name → friendly_name` para UI (30 features) | 8–10 oct 2026 |
| P4.14 | Integrar riesgo productivo | `/risk/{id}` con nivel y componentes | 10–11 oct 2026 |
| P4.15 | Crear endpoint regional | `/regions/{region}` con rendimiento y riesgo agregados | 9–11 oct 2026 |
| P4.16 | Automatizar CSV oficial de FIRA | `generate_submission.py` → `nombre_del_equipo_prediccion.csv` | 13–15 oct 2026 |
| P4.17 | Validador automático del submission | Chequeo de 59 IDs únicos, sin NaN/inf y columnas correctas | 13–15 oct 2026 |
| P4.18 | Desplegar backend | API pública estable en Render/Railway/Azure | 11–14 oct 2026 |
| P4.19 | Integrar y desplegar frontend | Frontend conectado a API y desplegado en Vercel | 12–15 oct 2026 |
| P4.20 | Separar configuración DEV/PROD | Variables `API_URL`, `MODEL_PATH` y `ENVIRONMENT` | 11–13 oct 2026 |
| P4.21 | Tests mínimos de API | Tests de health, parcela válida/inválida, predict, explain, risk y región | 13–15 oct 2026 |
| P4.22 | README técnico del repositorio | Arquitectura, instalación, ejecución, API, modelo y estructura del repo | 13–15 oct 2026 |
| P4.23 | Prueba end-to-end desde cero | Datos → features → modelo → predicciones → API → web → CSV | 16–17 oct 2026 |
| P4.24 | Preparar submission final | CSV final con nombre exacto requerido por FIRA | 17–18 oct 2026 |
| P4.25 | Crear backup de entrega | Modelo, CSV, notebooks, repo, reporte y presentación respaldados | 18 oct 2026 |
| P4.26 | Crear release GitHub v1.0-agrocebada | Release congelado de la versión entregada | 18–19 oct 2026 |

**Artefactos clave producidos:**
- `api/` — FastAPI con 7 endpoints, mock y modo real, hash-verificado
- `ml/inference.py` — pipeline de inferencia sin entrenamiento en runtime
- `ml/integration.py` — integración data-ML verificada 2026-10-17
- `tests/` — 249+ tests Python (unit + integración), todos aprobados
- `docs/api-contract.md` — contrato público v0.1.0
- `docs/system-contract.md` — contrato interno v0.3.0
- `docs/model-bundle.md`, `docs/inference-pipeline.md` — documentación ML
- Acceptance evidence: 8 archivos JSON con verificación de integración

---

## Persona 5 — UX / Visualización / Storytelling

**Rol:** Diseño de interfaz, visualizaciones interactivas, storytelling de la demo y presentación final.

| ID | Tarea | Entregable | Período |
|----|-------|-----------|---------|
| P5.1 | Wireframes de las 3 vistas principales | Wireframes de dashboard, parcela y región | 24–27 sep 2026 |
| P5.2 | Construir layout y componentes base | Navbar, tarjetas, filtros y selector de parcela usando MOCKs | 28 sep – 3 oct 2026 |
| P5.3 | Dashboard general con MOCKs | KPIs generales y distribución visual inicial | 1–4 oct 2026 |
| P5.4 | Vista detallada de parcela | Rendimiento, intervalo, confianza, riesgo y factores | 8–12 oct 2026 |
| P5.5 | Mapa interactivo de parcelas | Mapa coloreable por rendimiento/riesgo con 197 geometrías | 8–13 oct 2026 |
| P5.6 | Visualización simplificada de SHAP | Factores positivos/negativos en lenguaje claro (30 nombres amigables) | 10–13 oct 2026 |
| P5.7 | Pulido visual y estados de UI | Responsive, loading, errores y empty states | 13–15 oct 2026 |
| P5.8 | Definir storytelling de la demo | Flujo: mapa → parcela → predicción → explicación → riesgo → utilidad FIRA | 13–15 oct 2026 |
| P5.9 | Preparar video/demo final | Grabación, screenshots y recorrido estable (≤ 5 min) | 16–18 oct 2026 |
| P5.10 | Preparar presentación final | Deck con problema, método, resultados, producto e impacto FIRA | 16–18 oct 2026 |

**Artefactos clave producidos:**
- `frontend/` — React + Vite, 4 rutas, mapa interactivo, responsive (390px–1920px)
- Dashboard: conteo de parcelas, regiones y geometrías
- Vista de parcela: predicción, top-3 SHAP, nivel de riesgo
- Vista regional: filtro por estado, tabla resumen, gráfica
- Tests frontend: 15+ tests aprobados; verificación browser desktop + mobile
- Presentación final y video demo ≤ 5 min

---

## Equipo — Entrega Final

| Tarea | Entregable | Fecha límite |
|-------|-----------|-------------|
| Revisión final y envío | Proyecto registrado en plataforma FIRA, CSV enviado a `innovacion@fira.gob.mx` y todos los anexos verificados | 19 oct 2026, 23:59 hrs |

---

## Resumen por componente del sistema

| Componente | Responsable principal |
|------------|----------------------|
| Dataset y features (30 variables) | Persona 1 |
| Modelo predictivo (Ridge, yield-v1) | Persona 2 |
| Validación espacial, SHAP, OOD, riesgo | Persona 3 |
| API, pipeline de inferencia, tests, despliegue | Persona 4 — Cecilia |
| Frontend, mapa, visualizaciones, demo, presentación | Persona 5 |
