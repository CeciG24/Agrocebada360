# Cebada360 · Módulo de ML (Rol 2)

> **Reto Agrocebada 2026** — Predicción de rendimiento de cebada (**t/ha**) por parcela a partir de satélite (Sentinel-2, Landsat, Planet), clima y topografía.
> Alineado con `system-contract.md` **v0.3.0**, `audit-2026-10-14.md` y `backlog-review-2026-10-14.md`.

Las cantidades del split actual (138 etiquetadas / 59 de evaluación) son **observaciones**, no constantes contractuales: el código valida contra
`split/official_ids_v1.json` (lista versionada con hash), que debe contrastarse con la lista oficial de FIRA cuando se publique (contrato §20).

---

## 1. Instalación

```bash
cd ml
pip install -r requirements.txt
```

## 2. Datos

El dataset de Data se localiza con `CEBADA_DATA`, o en `<repo>/data/DATASET_RETO_AGRO_2026_LIMPIO/` o `ml/data/...`.
Si el ZIP trae otro layout (p. ej. `prediccion_temprana/features/` en vez de `matrices/`), conviértelo con el adaptador reproducible:

```bash
python prepare_data.py --src ruta/al/DATASET.zip --out data/DATASET_RETO_AGRO_2026_LIMPIO   # escribe data_manifest.json con sha256 por archivo
```

PowerShell: `$env:CEBADA_DATA="D:\ruta\DATASET_RETO_AGRO_2026_LIMPIO"` · bash: `export CEBADA_DATA=/ruta/...`

## 3. Orden de ejecución (backlog P2.x)

```bash
# --- Preparación (una vez por versión del dataset) ---
python make_official_ids.py        # split/official_ids_v1.json (no sobrescribe sin --force)
python audit_data.py               # results/data_audit.json   (exit 1 si hay datos posteriores al corte)
python stamp_audit.py              # sella la auditoría con el hash del dataset (sin sello válido NO se exporta nada)

# --- P2.3 / P2.4  baselines y familias de features ---
python run_experiments.py --repeats 10      # results/leaderboard.csv (+ _meta.json, oof/)  ; columna `tipo`: oficial | baseline | diagnostico
python make_tabla_experimentos.py           # results/tabla_experimentos.csv

# --- P2.5  tuning con CV anidada ---
python tune.py                              # results/tuning/*.json, results/tuning_summary.csv

# --- P2.6  predicción temprana (curva diagnóstica, no un modelo por corte) ---
python run_early.py --repeats 10            # results/early/*

# --- P2.7  ensemble (decisión imparcial: parámetros por defecto) ---
python run_ensemble.py --repeats 10         # results/ensemble/*   (descartar el ensemble es un resultado válido)

# --- P2.8  selección del modelo definitivo ---
python select_model.py                      # results/final_model_config.json

# --- P2.9  reentrenar con TODAS las parcelas etiquetadas oficiales ---
python train_final_model.py                 # models/yield_model_v1.joblib + models/feature_schema.json

# --- P2.10 predicciones de las parcelas de evaluación ---
python generate_predictions.py              # results/predictions_raw.csv (precisión completa) + predictions_4dp.csv + predictions_meta.json

# --- P2.11 validación final (exit 1 si algo falla) ---
python validate_final.py                    # results/final_validation.json

# --- Baseline de integración para Rol 4/5 (yield-v0) ---
python make_baseline_predictions.py         # models/baseline_v0/*, results/baseline_v0/predictions_raw.csv

# --- Tests ---
python -m pytest tests -q
```

Pruebas rápidas: `--repeats 2 --fast` (menos repeticiones/árboles). Un modelo entrenado con `--fast` **no** pasa `validate_final.py`.

## 4. Qué cambió con v0.3.0 (resumen)

| Tema | Ahora |
| --- | --- |
| Schema | `feature_schema.json` 0.3.0: `target_name`, `prediction_unit`, `target_cycle`, `prediction_information_cutoff`, `training_id_source`, `data_version`, `model_sha256`, `missing_value_policy`, entorno |
| Modelo ↔ schema | sha256 del joblib, nº y **orden** de features (el modelo se entrena con DataFrame; sklearn valida nombres) |
| Auditoría | `stamp_audit.py` ata el resultado al hash del dataset; exportar exige auditoría válida **para ese dataset** (`--allow-unverified` solo para pruebas; queda `verified=false`) |
| IDs | listas oficiales versionadas, no 138/59 |
| Ensemble | ponderación con stacking **anidado** (sin fuga entre niveles); `--params tuned` se marca `evaluation_independent=false` |
| Experimentos | `tipo`: E1–E5 **oficial**; X* **diagnóstico** (municipio/ubicación); el modelo oficial solo sale de E1–E5 |
| Predicciones | `predictions_raw.csv` a precisión completa; `predictions_4dp.csv` a 4 decimales; columnas/nombre del CSV oficial **pendientes** (§20) |
| Predicción temprana | curva diagnóstica; no es un endpoint de modelos por corte |

### Faltantes (§5.3)
`features_master.csv` tiene **2 NaN** en `planet_ndvi_decay_rate` (parcelas de evaluación sin días posteriores al pico). Se imputan con la **mediana del train** dentro del `Pipeline`
(política `documented` en el schema); no se rellenan aguas arriba.

### Política temporal (§2)
Ciclo abril–octubre 2025; `prediction_information_cutoff = 2025-10-31` es una **convención técnica** (FIRA confirma el mes). Hay features con histórico 2022–2024 usado como **contexto ambiental**,
no como historial de cebada. El rendimiento de otras parcelas/años, fecha de siembra, dosis, variedad, siniestros 2025 e historial de cultivo no se usan (§5.6).

## 5. Hallazgos a tener presentes (con el dataset auditado)
- El baseline de **solo municipio** (Ridge) tiene RMSE comparable o mejor que el mejor modelo con satélite; `select_model.py` lo reporta (`municipality_baseline_gap`). Si el municipio puede entrar al modelo oficial es una **decisión del equipo/FIRA**: el contrato no lo prohíbe, pero el schema actual rechaza `mun_*`.
- La curva de predicción temprana es casi plana (junio → octubre).
- El ensemble suele descartarse (residuos muy correlacionados).
- La CV espacial (KMeans sobre centroides) es **diagnóstico**; no reproduce el muestreo oficial.

## 6. Estructura

```
ml/
├── src/
│   ├── config.py        # constantes, versiones (contract 0.3.0, yield-v1), rutas, STRICT_CUTOFF
│   ├── provenance.py    # sha256 del dataset (data_version), estado de la auditoría, run_meta()
│   ├── split.py         # listas oficiales de IDs (build/load/diff)
│   ├── contract.py      # validaciones §5, schema 0.3.0, save/load verificados, predict_frame, validate_predictions
│   ├── data.py          # carga + familias + EXPERIMENTS (E0–E5 y X*)
│   ├── models.py        # zoo de modelos (no modificar sin avisar: el equipo ajustó parámetros)
│   ├── cv.py            # CV repetida, CV espacial, métricas
│   ├── tuning.py        # espacios de búsqueda y CV anidada
│   ├── ensemble.py      # OOF compartidos, stacking anidado, decisión keep/discard
│   ├── early.py         # cortes tempranos
│   └── final.py         # construir el modelo desde final_model_config.json
├── audit_data.py        # auditoría de ventana temporal (versión del equipo)
├── stamp_audit.py       # sella la auditoría con el hash del dataset
├── prepare_data.py      # adaptador de layout del ZIP de Data
├── make_official_ids.py # split/official_ids_v1.json
├── run_experiments.py · make_tabla_experimentos.py · tune.py · run_early.py · run_ensemble.py
├── select_model.py · train_final_model.py · generate_predictions.py · validate_final.py   # P2.8–P2.11
├── make_baseline_predictions.py   # yield-v0 (integración)
├── split/official_ids_v1.json
├── models/ (yield_model_v1.joblib, feature_schema.json, baseline_v0/)
├── results/
└── tests/
notebooks/01_baselines.ipynb       # P2.1 (usa ml/src; CEBADA_REPS, CEBADA_FAST)
```

## 7. Pendientes oficiales (contrato §20) — marcados como placeholders
Nombre oficial de ID y target, columnas/orden/nombre/canal del archivo de envío, región, CRS. Este módulo entrega `predictions_raw.csv` (insumo) y deja el formato oficial al exportador (Rol 4, P4.16).
