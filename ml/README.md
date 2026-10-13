# Cebada360 · Módulo de ML (Rol 2)

> **Reto Agrocebada 2026** — Predicción de rendimiento de cebada (t/ha) a partir de imágenes satelitales, datos climáticos y topografía, sobre 138 parcelas de entrenamiento y 59 de evaluación.

---

## Descripción general

Este repositorio implementa el **pipeline de Machine Learning** dentro del ecosistema Cebada360. Su objetivo es comparar sistemáticamente combinaciones de familias de features (satélite Sentinel-2, Landsat, Planet, fenología, clima, topografía) con diferentes modelos de regresión, afinando los finalistas con CV anidada, construyendo un ensemble y evaluando qué tan pronto en el ciclo puede anticiparse el rendimiento final, siguiendo en todo momento un protocolo de validación cruzada repetida con verificación estadística pareada.

---

## Instalación y uso rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Auditar el dataset contra el contrato (corte temporal, IDs)
python audit_data.py        # → results/data_audit.json (exit 1 si viola el corte)

# 2b. Apuntar al dataset (o usar la variable de entorno) || Modificar config.py
$env:CEBADA_DATA="D:\ruta\a\DATASET_RETO_AGRO_2026_LIMPIO"

# 3. Correr todos los experimentos
python run_experiments.py --repeats 10
#   → results/leaderboard.csv   (tabla comparativa de todos los experimentos x modelos)
#   → results/oof/*.csv         (predicciones fuera de fold para Rol 3)

# 4. Generar tabla de experimentos (P2.4)
python make_tabla_experimentos.py
#   → results/tabla_experimentos.csv

# 5. Afinar los mejores modelos con CV anidada (P2.5)
python tune.py
#   → results/tuning/<exp>__<modelo>.json
#   → results/tuning_summary.csv

# 6. Evaluar ensemble final (P2.7)
python run_ensemble.py --repeats 10 --params tuned
#   → results/ensemble/ensemble_config.json
#   → results/ensemble/ensemble_compare.csv
#   → results/ensemble/ensemble_oof.csv

# 7. Predicción temprana por corte (P2.6)
python run_early.py --repeats 10
#   → results/early/early_leaderboard.csv
#   → results/early/early_summary.json
#   → results/early/early_curve.png

# 8. Generar predicciones de evaluación con baseline v0 (contrato para Rol 4/5)
python make_baseline_predictions.py
#   → results/predictions_raw.csv
#   → models/yield_model_v0.joblib + models/feature_schema.json
```

### Flags útiles de `run_experiments.py`

| Flag | Descripción | Ejemplo |
| ------ | ------------- | --------- |
| `--repeats N` | Número de repeticiones de CV (default: 10) | `--repeats 3` para prueba rápida |
| `--fast` | Reduce árboles a 150 (vs 300) para acelerar | `--fast` |
| `--exps` | Seleccionar experimentos específicos | `--exps E5_fusion E4_clima` |
| `--models` | Seleccionar modelos específicos | `--models ridge catboost` |
| `--tag` | Sufijo para el nombre del leaderboard | `--tag _v2` |

### Flags útiles de `tune.py`

| Flag | Descripción | Ejemplo |
| ------ | ------------- | --------- |
| `--exp` | Experimento sobre el que afinar (default: `E5_fusion`) | `--exp E5_fusion` |
| `--models` | Modelos a afinar (default: top-3 del leaderboard) | `--models extratrees catboost` |
| `--n-iter` | Candidatos por búsqueda aleatoria (default: 15) | `--n-iter 20` |
| `--outer-repeats` | Repeticiones de la CV externa anidada (default: 2) | `--outer-repeats 3` |

### Flags útiles de `run_ensemble.py`

| Flag | Descripción | Ejemplo |
| ------ | ------------- | --------- |
| `--exp` | Experimento base (default: `E5_fusion`) | `--exp E5_fusion` |
| `--models` | Miembros del ensemble | `--models extratrees rf catboost` |
| `--params` | `default` o `tuned` (usa `results/tuning/`) | `--params tuned` |
| `--min-gain` | Mejora mínima de RMSE para conservar ensemble (default: 0.005) | `--min-gain 0.01` |
| `--min-win` | Fracción mínima de repeticiones ganadas (default: 0.8) | `--min-win 0.75` |

### Flags útiles de `run_early.py`

| Flag | Descripción | Ejemplo |
| ------ | ------------- | --------- |
| `--cuts` | Cortes a evaluar (default: junio...octubre) | `--cuts junio agosto octubre` |
| `--models` | Modelos (default: `ridge extratrees catboost`) | `--models ridge catboost` |
| `--params` | `default` o `tuned` | `--params tuned` |
| `--tol` | Tolerancia vs techo octubre (default: 0.05 = 5 %) | `--tol 0.03` |

---

## Estructura del proyecto

```
ml/
|
+-- src/                        # Librería principal del módulo ML
|   +-- config.py               # Protocolo central: rutas, semilla, folds, métrica, versiones
|   +-- data.py                 # Carga de datos + familias de features + EXPERIMENTS (E0-E5, X0-X3)
|   +-- models.py               # Zoo de modelos (Ridge, RF, GBR, CatBoost, XGBoost, LightGBM...)
|   +-- cv.py                   # CV repetida, CV espacial y diferencia pareada
|   +-- contract.py             # Validaciones del system-contract.md: IDs, schema, inferencia
|   +-- tuning.py               # Espacios de búsqueda y utilidades de CV anidada (P2.5)
|   +-- ensemble.py             # Lógica de ensemble: OOF compartidos, pesos simplex, decisión (P2.7)
|   +-- early.py                # Utilidades de predicción temprana por corte (P2.6)
|
+-- run_experiments.py          # E0-E5 x modelos -> results/leaderboard.csv + results/oof/
+-- make_tabla_experimentos.py  # P2.4: tabla resumen por experimento -> results/tabla_experimentos.csv
+-- tune.py                     # P2.5: tuning con CV anidada -> results/tuning/ + tuning_summary.csv
+-- run_ensemble.py             # P2.7: evaluar ensemble final -> results/ensemble/
+-- run_early.py                # P2.6: predicción temprana por corte -> results/early/
+-- make_baseline_predictions.py# Contrato Rol 4/5: predictions_raw.csv + models/
+-- audit_data.py               # Auditoría del dataset vs system-contract.md -> results/data_audit.json
|
+-- data/
|   +-- DATASET_RETO_AGRO_2026_LIMPIO/  # Dataset de Rol 1 (no se modifica)
|       +-- features/           # features_master.csv (todas las familias fusionadas)
|       +-- targets/            # rendimiento.csv (variable objetivo: rendimiento_t_ha)
|       +-- clima/              # Series climáticas (precipitación, tmin, tmax, amplitud)
|       +-- sensores/           # Datos satelitales crudos (Sentinel-2, Landsat, Planet)
|       +-- topografia/         # topography_master.csv (area_ha, elevation_mean, slope_mean)
|       +-- prediccion_temprana/
|       |   +-- matrices/       # features_master_corte_<junio|julio|agosto|septiembre|octubre>.csv (P1.12)
|       +-- parcel_master.csv   # Maestro de parcelas con metadatos y split ENTRENAMIENTO/PREDICCION
|
+-- models/
|   +-- yield_model_v0.joblib   # Modelo serializado (contrato §5); cargar con src.contract.load_artifacts()
|   +-- feature_schema.json     # Schema contractual: features (orden), unit, model_version, data_cutoff
|
+-- results/
|   +-- leaderboard.csv         # RMSE, MAE, R2, RMSE espacial por experimento x modelo
|   +-- tabla_experimentos.csv  # P2.4: mejor modelo por experimento (una fila por experimento)
|   +-- tuning_summary.csv      # P2.5: comparativa defaults vs afinado para los finalistas
|   +-- predictions_raw.csv     # Predicciones de las 59 parcelas de evaluación (contrato API)
|   +-- data_audit.json         # Resultado de audit_data.py
|   +-- run_log.txt             # Log del último run_experiments.py
|   +-- oof/                    # Predicciones OOF: {exp}__{modelo}.csv
|   +-- tuning/                 # JSON por modelo afinado: {exp}__{modelo}.json
|   +-- ensemble/               # ensemble_config.json, ensemble_compare.csv, ensemble_oof.csv
|   +-- early/                  # early_leaderboard.csv, early_summary.json, early_curve.png, oof/
|
+-- tests/
|   +-- test_contract.py        # Tests de contrato (IDs, schema, predicciones)
|   +-- test_early_ensemble.py  # Tests de P2.6 (cortes) y P2.7 (ensemble)
|
+-- requirements.txt            # Dependencias Python
+-- README.md                   # Este archivo
```

---
## Descripción de archivos fuente (`src/`)

### `config.py` — Configuración central del protocolo

Define **todas las constantes compartidas**. Es el único lugar donde deben modificarse parámetros globales.

| Variable | Valor | Descripción |
| ---------- | ------- | ------------- |
| `DATA_ROOT` | auto-detectado | Ruta al dataset (override con `$CEBADA_DATA`) |
| `RESULTS` | `results/` | Directorio de salida de métricas y predicciones |
| `MODELS` | `models/` | Modelos serializados + feature_schema.json (contrato §5) |
| `SEED` | `42` | Semilla global de aleatoriedad |
| `N_SPLITS` | `5` | Número de folds por repetición de CV |
| `N_REPEATS` | `10` | Repeticiones de CV (usar 3 para pruebas rápidas) |
| `N_SPATIAL_GROUPS` | `6` | Clusters KMeans para CV espacial de diagnóstico |
| `TARGET` | `rendimiento_t_ha` | Variable objetivo |
| `UNIT` | `t/ha` | Unidad contractual (§17) |
| `ID` | `parcel_id` | Nombre contractual de la columna ID (§17) |
| `N_TRAIN`, `N_EVAL` | `138`, `59` | Partición oficial del reto |
| `DATA_CUTOFF` | `2025-10-31` | Corte temporal del ciclo (contrato §1.7) |
| `STRICT_CUTOFF` | `false` | Si `CEBADA_STRICT_CUTOFF=1`, bloquea artefactos si el audit falla |
| `MODEL_VERSION` | `yield-v0` | Versión del modelo baseline |
| `PRIMARY_METRIC` | `rmse` | Métrica principal de comparación |

---

### `data.py` — Carga y definición de features

1. **`load()`**: Carga `features_master.csv` + `rendimiento.csv`, los fusiona, añade dummies de municipio y asigna grupos espaciales (KMeans sobre lat/lon). Separa y retorna `(train, eval)` donde `eval` **nunca tiene target**. Llama a `contract.validate_catalog()` antes de cargar.

2. **`families(df)`**: Clasifica las columnas numéricas en familias por prefijo/nombre:

| Familia | Descripción |
| --------- | ------------- |
| `topo` | Topografía: `area_ha`, `elevation_mean`, `slope_mean` |
| `geo` | Coordenadas del centroide (proxy de ubicación; solo diagnóstico) |
| `s2` | Bandas/índices Sentinel-2 (sin fenología) |
| `landsat` | Bandas/índices Landsat |
| `planet` | Bandas/índices Planet (sin fenología) |
| `feno_s2` | Features fenológicas de Sentinel-2 (`_peak`, `_auc`, `_growth_rate`...) |
| `feno_planet` | Features fenológicas de Planet |
| `clima` | Variables climáticas (`precip`, `tmin`, `tmax`, `amplitud`) |
| `muni` | Dummies de municipio (one-hot encoding; solo diagnóstico) |

3. **`EXPERIMENTS`**: Diccionario que mapea cada experimento a la lista de familias que lo compone:

| Experimento | Familias incluidas | Propósito |
| ------------- | -------------------- | ----------- |
| `E0_baseline` | _(ninguna)_ | Dummy median — cota inferior |
| `E1_topo` | `topo` | Solo topografía |
| `E2_basico` | `s2`, `landsat`, `feno_s2` | Satélites ópticos principales |
| `E3_planet` | `planet`, `feno_planet` | Imágenes Planet de alta resolución |
| `E4_clima` | `clima` | Solo variables climáticas |
| `E5_fusion` | `topo` + `s2` + `landsat` + `feno_s2` + `planet` + `feno_planet` + `clima` | Fusión completa (oficial) |
| `X0_municipio` | `muni` | **Piso real**: media por municipio (todo modelo debe superarlo) |
| `X1_geo` | `geo` | Diagnóstico: ¿cuánto aporta la ubicación? |
| `X2_fusion_mas_geo` | `E5_fusion` + `geo` | Diagnóstico: fusión con coordenadas |
| `X3_muni_mas_sat` | `muni` + `topo` + satélites | Diagnóstico: municipio + satélite |

4. **`columns_for(exp, fam)`**: Retorna la lista de columnas correspondientes a un experimento dado.

---

### `models.py` — Zoo de modelos

Define `zoo(fast=False)` que devuelve `{nombre: callable_que_crea_modelo}`. Todos los modelos incluyen imputación y escalado **dentro del `Pipeline`** (sin data leakage).

| Modelo | Tipo | Notas |
| -------- | ------ | ------- |
| `dummy_median` | Baseline | Predice la mediana; solo se usa en E0 |
| `ridge` | Lineal | `RidgeCV` con escalado estándar |
| `elasticnet` | Lineal regularizado | `ElasticNetCV` L1+L2 |
| `rf` | Ensemble (bagging) | `RandomForestRegressor` (300 árboles) |
| `extratrees` | Ensemble (bagging) | `ExtraTreesRegressor` (300 árboles) |
| `gbr` | Boosting (sklearn) | `GradientBoostingRegressor` (200 est.) |
| `catboost` | Boosting | Requiere `catboost` instalado |
| `xgboost` | Boosting | Requiere `xgboost` instalado |
| `lightgbm` | Boosting | Requiere `lightgbm` instalado |

Los modelos de boosting de terceros se importan con `try/except` y son opcionales.

---

### `cv.py` — Protocolo de validación

| Función | Descripción |
| --------- | ------------- |
| `metrics(y, p)` | Calcula RMSE, MAE y R2 |
| `repeated_cv(...)` | CV aleatoria repetida (`KFold` x `N_REPEATS`). Retorna métricas por repetición, OOF promedio y OOF por repetición |
| `spatial_cv(...)` | CV por grupos espaciales (`GroupKFold`). Diagnóstico de generalización geográfica; suele ser más pesimista |
| `paired_diff(oofs_a, oofs_b, y)` | Diferencia pareada de RMSE por repetición. Un modelo solo "gana" si `mean(diff) < 0` de forma consistente |

---

### `contract.py` — Validaciones del system-contract.md

Implementa todas las validaciones contractuales del lado de Modelado. Nunca inventa columnas ni imputa por su cuenta.

| Función / Clase | Descripción |
| ---------------- | ------------- |
| `ContractError`, `FeatureSchemaMismatch`, etc. | Excepciones explícitas (§13) |
| `validate_ids(df)` | `parcel_id` string, sin nulos, sin duplicados (§3.2) |
| `validate_catalog(root)` | IDs coincidentes entre `parcel_master`, `features_master`, `rendimiento` y `topografia` (§15) |
| `validate_features(df, cols)` | Features numéricas, finitas, sin columnas derivadas de Modelado ni fuga de target |
| `build_schema(features, ...)` | Construye el `feature_schema.json` contractual (§5) |
| `save_artifacts(model, schema)` | Serializa modelo + schema en `models/` |
| `load_artifacts(models_dir)` | Carga modelo + schema; falla explícitamente si no existen (§6) |
| `predict_frame(model, schema, df)` | Predice sobre `df` respetando el orden exacto del schema (§6) |
| `validate_predictions(out, ...)` | Verifica 59 filas únicas, sin nulos y con IDs correctos (contrato API) |

---

### `tuning.py` — Espacios de búsqueda y CV anidada (P2.5)

| Elemento | Descripción |
| --------- | ------------- |
| `SPACES` | Rejillas de hiperparámetros para `extratrees`, `rf`, `catboost`, `gbr`, `xgboost`, `lightgbm`, `elasticnet` |
| `build(name, params, fast)` | Construye un modelo del zoo con parámetros opcionales |
| `candidates(name, n_iter)` | Candidato 0 = defaults; el resto de la búsqueda aleatoria |
| `cv_rmse(name, params, X, y, ...)` | RMSE medio sobre repeticiones de KFold |
| `search(name, X, y, n_iter, ...)` | Búsqueda aleatoria ordenada por RMSE |
| `load_best(name, exp)` | Carga los mejores hiperparámetros guardados por `tune.py` |

---

### `ensemble.py` — Ensemble final (P2.7)

| Función | Descripción |
| --------- | ------------- |
| `member_oofs(names, params, X, y, groups, ...)` | OOF de cada miembro con **folds idénticos** (CV aleatoria + espacial) |
| `simplex_weights(P, y)` | Pesos >= 0 que suman 1 y minimizan el error cuadrático OOF |
| `cv_weighted_predictions(P, y, ...)` | Predicción ponderada con ajuste de pesos por fold (nivel 2) |
| `compare(P, Ps, y, names)` | Métricas por repetición: miembros, promedio simple, ponderado y espacial |
| `decide(res, min_gain, min_win, ...)` | Decide si conservar el ensemble: mejora >= `min_gain`, gana en >= `min_win` de repeticiones y no empeora en espacial |
| `build_ensemble(names, weights, ...)` | `VotingRegressor` listo para `.fit()` y serialización con `contract.save_artifacts()` |

---

### `early.py` — Predicción temprana por corte (P2.6)

Responde: ¿qué tan pronto en el ciclo abril-octubre 2025 se puede anticipar el rendimiento final?

| Elemento | Descripción |
| --------- | ------------- |
| `CUTS` | Fechas límite por corte: junio, julio, agosto, septiembre, octubre |
| `load_cut(cut, root)` | Lee la matriz del corte, une el target y devuelve `(train, eval, features)` |
| `load_cuts(cuts, root)` | Carga varios cortes y verifica que describan las mismas parcelas |
| `audit_windows(cuts_data)` | Comprueba coherencia entre cortes (max no baja, min no sube, precipitación acumulada no baja) |
| `baseline_matrices(tr)` | Baselines por corte: mediana y promedio por municipio |
| `spatial_groups()` | Grupos espaciales por parcela, alineados con `run_experiments` |
| `earliest_cut(curve, ok)` | Primer corte donde se cumple el criterio `ok(cut, rmse)` |

---

## Flujo de datos y relación entre archivos

```
DATASET_RETO_AGRO_2026_LIMPIO/
  features/features_master.csv  --+
  targets/rendimiento.csv       --+  src/data.py::load()  <--  src/contract.py::validate_catalog()
  topografia/topography_master  --+       |
                                   (tr, ev)  <--  split ENTRENAMIENTO / PREDICCION
                                          |
              src/data.py::families() + EXPERIMENTS
                                          |
                    +-----------+---------+---------+-----------+
                    v                     v                     v
              src/models.py          src/cv.py            src/config.py
                    |                     |
                    +----------+----------+
                               v
                       run_experiments.py
                               |
              +----------------+-----------------+
              v                v                 v
      results/           results/          results/
      leaderboard.csv    oof/*.csv         run_log.txt
              |
              v
  make_tabla_experimentos.py --> results/tabla_experimentos.csv

  tune.py  (usa leaderboard.csv para elegir finalistas)
              |
      results/tuning/<exp>__<mod>.json + tuning_summary.csv

  run_ensemble.py  (usa tuning/ si --params tuned)
              |
      results/ensemble/{ensemble_config.json, ensemble_compare.csv, ensemble_oof.csv}

  prediccion_temprana/matrices/features_master_corte_<cut>.csv  (entrega Rol 1)
              |
  run_early.py
              |
      results/early/{early_leaderboard.csv, early_summary.json, early_curve.png, oof/}

  make_baseline_predictions.py
              |
      results/predictions_raw.csv  +  models/{yield_model_v0.joblib, feature_schema.json}
```

---

## Reglas del protocolo (no negociables)

1. **Todo preprocesamiento va dentro del `Pipeline`** (imputación, escalado): se ajusta por fold, nunca sobre el conjunto completo.
2. **Las 59 parcelas de evaluación jamás participan en tuning** ni en la selección del modelo ganador.
3. **Un experimento solo "gana" si mejora el RMSE de forma estadísticamente consistente** en las repeticiones (prueba pareada), no por un fold afortunado.
4. **Contrato de salida** — `predictions_raw.csv` debe tener exactamente: `parcel_id`, `rendimiento_pred_t_ha`, `model_version` con 59 filas únicas y sin valores nulos.
5. **`E0_baseline` solo corre con `dummy_median`**; el resto de los experimentos lo excluyen automáticamente.
6. **`X0_municipio`** es el **piso real**: cualquier modelo que no lo supere no justifica el uso de datos satelitales.
7. **El ensemble solo se conserva** si mejora >= 0.005 t/ha en promedio, gana en >= 80 % de las repeticiones y no empeora en CV espacial.
8. **Ningún corte de predicción temprana puede superar `DATA_CUTOFF = 2025-10-31`** (contrato §1.7); esto se verifica en `early.py` con un `assert` al importar.

---

## Alineación con `system-contract.md` (v0.1.0)

- `parcel_id` siempre `string`; IDs validados entre `parcel_master`, `features_master`, `rendimiento` y topografía (§3.2) mediante `contract.validate_catalog()`.
- Faltantes: `features_master.csv` no trae NaN; el Pipeline imputa con mediana del train solo si aparecieran (§3.3).
- Schema oficial solo con columnas originales de `features_master`; `mun_*`, `grupo_espacial` y `geo` son diagnóstico y se rechazan explícitamente en `contract.validate_features()` (§1.3, §5).
- Predicciones se generan recargando `models/` y validando orden/faltantes/finitud mediante `contract.predict_frame()` (§5.2, §6, §13).
- **Corte temporal (§1.7): hoy NO se cumple.** Ver `results/data_audit.json`: los agregados de `features_master` usan series completas 2022-2025 (incluye nov-dic 2025). `data_cutoff_verified=false` queda registrado en el schema. `CEBADA_STRICT_CUTOFF=1` bloquea la generación de artefactos mientras no se corrija.
- Pendientes de confirmación oficial (§17): nombre de columna ID, unidad, formato del CSV de FIRA.

---

## Dependencias

```
numpy          pandas         scikit-learn>=1.3
scipy          joblib
xgboost        lightgbm       catboost        # opcionales (boosting de terceros)
nbformat                                       # para leer notebooks
```

Instalar con:

```bash
pip install -r requirements.txt
```

---

## Salidas generadas

| Archivo | Generado por | Descripción |
| --------- | ------------ | ------------- |
| `results/leaderboard.csv` | `run_experiments.py` | `exp`, `model`, `n_feat`, `rmse`, `rmse_sd`, `mae`, `r2`, `rmse_spatial`, `r2_spatial`, `repeats`, `secs` |
| `results/tabla_experimentos.csv` | `make_tabla_experimentos.py` | Una fila por experimento: mejor modelo, RMSE, métricas y promedio entre modelos |
| `results/oof/{exp}__{model}.csv` | `run_experiments.py` | `parcel_id`, `y` (real), `oof` (predicción promedio OOF) |
| `results/tuning/{exp}__{model}.json` | `tune.py` | `best_params`, RMSE/MAE/R2 anidados vs defaults, top-5 candidatos |
| `results/tuning_summary.csv` | `tune.py` | Comparativa defaults vs afinado para todos los modelos procesados |
| `results/ensemble/ensemble_config.json` | `run_ensemble.py` | Miembros, pesos, decisión keep/discard, métricas CV y espaciales |
| `results/ensemble/ensemble_compare.csv` | `run_ensemble.py` | RMSE por repetición: cada miembro, promedio simple y ponderado |
| `results/ensemble/ensemble_oof.csv` | `run_ensemble.py` | `parcel_id`, `y`, `oof` del ensemble elegido (insumo Rol 3) |
| `results/early/early_leaderboard.csv` | `run_early.py` | RMSE por corte x modelo, `gain_vs_dummy`, `gain_vs_municipio`, `loss_vs_ceiling` |
| `results/early/early_summary.json` | `run_early.py` | Curva RMSE, cortes más tempranos útiles, auditoría de ventanas |
| `results/early/early_curve.png` | `run_early.py` | Gráfica RMSE vs corte (requiere matplotlib) |
| `results/early/oof/{cut}__{model}.csv` | `run_early.py` | OOF por corte y modelo (insumo Rol 3) |
| `results/predictions_raw.csv` | `make_baseline_predictions.py` | Predicciones de las 59 parcelas de evaluación — contrato para la API |
| `results/data_audit.json` | `audit_data.py` | Resultado de la auditoría del dataset |
| `models/yield_model_v0.joblib` | `make_baseline_predictions.py` | Modelo serializado; cargar con `src.contract.load_artifacts()` |
| `models/feature_schema.json` | `make_baseline_predictions.py` | Schema contractual: `features` (orden), `unit`, `model_version`, `data_cutoff` |
