# Cebada360 · Módulo de ML (Rol 2)

> **Reto Agrocebada 2026** — Predicción de rendimiento de cebada (t/ha) a partir de imágenes satelitales, datos climáticos y topografía, sobre 138 parcelas de entrenamiento y 59 de evaluación.

---

## Descripción general

Este repositorio implementa el **pipeline de Machine Learning** dentro del ecosistema Cebada360. Su objetivo es comparar sistemáticamente combinaciones de familias de features (satélite Sentinel-2, Landsat, Planet, fenología, clima, topografía) con diferentes modelos de regresión, siguiendo un protocolo de validación cruzada repetida con verificación estadística pareada.

---

## Instalación y uso rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Auditar el dataset contra el contrato (corte temporal, IDs)
python audit_data.py        # → results/data_audit.json (exit 1 si viola el corte)

# 2b. Apuntar al dataset (o usar la variable de entorno) || Modificar config.py
$env:CEBADA_DATA="/ruta/a/DATASET_RETO_AGRO_2026_LIMPIO"
|
# 3. Correr todos los experimentos
python run_experiments.py --repeats 10
#   → results/leaderboard.csv   (tabla comparativa de todos los experimentos x modelos)
#   → results/oof/*.csv         (predicciones fuera de fold para Rol 3)

# 4. Generar predicciones de evaluación con baseline v0 (contrato para Rol 4/5)
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

---

## Estructura del proyecto

```
cebada360_ml/
│
├── src/                        # Librería principal del módulo ML
│   ├── __init__.py
│   ├── config.py               # Protocolo central: rutas, semilla, folds, métrica
│   ├── data.py                 # Carga de datos + definición de familias de features + experimentos E0-E5
│   ├── models.py               # Zoo de modelos (Ridge, RF, GBR, CatBoost, XGBoost, LightGBM...)
│   └── cv.py                   # Validación cruzada repetida, CV espacial y diferencia pareada
│
├── run_experiments.py          # Script principal: corre E0-E5 x modelos → leaderboard + OOF
├── make_baseline_predictions.py# Contrato Rol 4/5: genera predictions_raw.csv y guarda modelo
│
├── data/
│   └── DATASET_RETO_AGRO_2026_LIMPIO/  # Dataset de Rol 1 (no se modifica)
│       ├── features/           # features_master.csv (todas las familias fusionadas)
│       ├── targets/            # rendimiento.csv (variable objetivo: rendimiento_t_ha)
│       ├── clima/              # Series climáticas (precipitación, tmin, tmax, amplitud)
│       ├── sensores/           # Datos satelitales crudos (Sentinel-2, Landsat, Planet)
│       ├── topografia/         # Variables topográficas (area_ha, elevation_mean, slope_mean)
│       ├── normalizado/        # Versiones normalizadas de features
│       ├── prediccion_temprana/# Features para predicción anticipada
│       └── parcel_master.csv   # Maestro de parcelas con metadatos y split ENTRENAMIENTO/PREDICCION
│
├── notebooks/
│   └── 01_baselines.ipynb      # Exploración inicial y validación de baselines
│
├── models/
│   ├── yield_model_v0.joblib   # Solo el modelo (contrato §5)
│   └── feature_schema.json     # Features en orden contractual, unidad, versión, data_cutoff
├── audit_data.py               # Auditoría del dataset vs system-contract.md
├── tests/test_contract.py      # Tests de contrato (pytest)
│
├── results/
│   ├── leaderboard.csv         # Tabla comparativa: RMSE, MAE, R² por experimento x modelo
│   ├── predictions_raw.csv     # Predicciones de las 59 parcelas de evaluación (contrato API)
│   ├── run_log.txt             # Log de ejecución del último run_experiments.py
│   └── oof/                    # Predicciones OOF: {experimento}__{modelo}.csv (para Rol 3)
│
├── catboost_info/              # Logs internos de CatBoost (generado automáticamente)
├── requirements.txt            # Dependencias Python
└── README.md                   # Este archivo
```

---

## Descripción de archivos fuente (`src/`)

### `config.py` — Configuración central del protocolo

Define **todas las constantes compartidas** del protocolo. Es el único lugar donde deben modificarse parámetros globales.

| Variable | Valor | Descripción |
| ---------- | ------- | ------------- |
| `DATA_ROOT` | `data/DATASET_RETO_AGRO_2026_LIMPIO` | Ruta al dataset (override con `$CEBADA_DATA`) |
| `RESULTS` | `results/` | Directorio de salida de métricas y predicciones |
| `ARTIFACTS` | `artifacts/` | Directorio de modelos serializados |
| `SEED` | `42` | Semilla global de aleatoriedad |
| `N_SPLITS` | `5` | Número de folds por repetición de CV |
| `N_REPEATS` | `10` | Repeticiones de CV (usar 3 para pruebas rápidas) |
| `N_SPATIAL_GROUPS` | `6` | Clusters KMeans para CV espacial de diagnóstico |
| `TARGET` | `rendimiento_t_ha` | Variable objetivo |
| `PRIMARY_METRIC` | `rmse` | Métrica principal de comparación |

---

### `data.py` — Carga y definición de features

Responsabilidades:

1. **`load()`**: Carga `features_master.csv` + `rendimiento.csv`, los fusiona, añade dummies de municipio y asigna grupos espaciales (KMeans sobre lat/lon). Separa y retorna `(train, eval)` donde `eval` **nunca tiene target**.

2. **`families(df)`**: Clasifica las columnas numéricas en familias por prefijo/nombre:

| Familia | Descripción |
| --------- | ------------- |
| `topo` | Topografía: `area_ha`, `elevation_mean`, `slope_mean` |
| `geo` | Coordenadas del centroide (proxy de ubicación; uso diagnóstico) |
| `s2` | Bandas/índices Sentinel-2 (sin fenología) |
| `landsat` | Bandas/índices Landsat |
| `planet` | Bandas/índices Planet (sin fenología) |
| `feno_s2` | Features fenológicas de Sentinel-2 (`_peak`, `_auc`, `_growth_rate`...) |
| `feno_planet` | Features fenológicas de Planet |
| `clima` | Variables climáticas (`precip`, `tmin`, `tmax`, `amplitud`) |
| `muni` | Dummies de municipio (one-hot encoding) |

1. **`EXPERIMENTS`**: Diccionario que mapea cada experimento a la lista de familias que lo compone:

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

1. **`columns_for(exp, fam)`**: Retorna la lista de columnas correspondientes a un experimento dado.

---

### `models.py` — Zoo de modelos

Define la función `zoo(fast=False)` que devuelve un diccionario `{nombre: callable_que_crea_modelo}`. Todos los modelos incluyen la imputación y el escalado **dentro del `Pipeline`** para garantizar que se ajustan por fold (sin data leakage).

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

Los modelos de boosting de terceros se importan con `try/except`, por lo que son opcionales.

---

### `cv.py` — Protocolo de validación

| Función | Descripción |
| --------- | ------------- |
| `metrics(y, p)` | Calcula RMSE, MAE y R² |
| `repeated_cv(...)` | CV aleatoria repetida (`KFold` × `N_REPEATS`). Retorna métricas por repetición, OOF promedio y OOF por repetición |
| `spatial_cv(...)` | CV por grupos espaciales (`GroupKFold`). Diagnóstico de generalización geográfica; suele ser más pesimista |
| `paired_diff(oofs_a, oofs_b, y)` | Diferencia pareada de RMSE por repetición. Un modelo solo "gana" si `mean(diff) < 0` de forma consistente, no por un fold afortunado |

---

## Flujo de datos y relación entre archivos

```
DATASET_RETO_AGRO_2026_LIMPIO/
  features/features_master.csv  ──┐
  targets/rendimiento.csv       ──┤  src/data.py::load()
                                  │       │
                                  ▼       ▼
                            (tr, ev)  ←  split ENTRENAMIENTO / PREDICCION
                                  │
              src/data.py::families() + EXPERIMENTS
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              src/models.py   src/cv.py    src/config.py
                    │             │
                    └──────┬──────┘
                           ▼
                   run_experiments.py
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
      results/          results/    results/
      leaderboard.csv   oof/*.csv   run_log.txt

                   make_baseline_predictions.py
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      results/predictions_raw.csv   artifacts/baseline_v0.joblib
      (contrato Rol 4/5 API)        (modelo serializado + features + versión)
```

---

## Reglas del protocolo (no negociables)

1. **Todo preprocesamiento va dentro del `Pipeline`** (imputación, escalado): se ajusta por fold, nunca sobre el conjunto completo.
2. **Las 59 parcelas de evaluación jamás participan en tuning** ni en la selección del modelo ganador.
3. **Un experimento solo "gana" si mejora el RMSE de forma estadísticamente consistente** en las repeticiones (prueba pareada), no por un fold afortunado.
4. **Contrato de salida** — `predictions_raw.csv` debe tener exactamente: `parcel_id`, `rendimiento_pred_t_ha`, `model_version` con 59 filas únicas y sin valores nulos.
5. **`E0_baseline` solo corre con `dummy_median`**; el resto de los experimentos lo excluyen automáticamente.
6. **`X0_municipio`** es el **piso real**: cualquier modelo que no lo supere no justifica el uso de datos satelitales.

---

## Alineación con `system-contract.md` (v0.1.0)

- `parcel_id` siempre `string`; IDs validados entre `parcel_master`, `features_master`, `rendimiento` y topografía (§3.2).
- Faltantes: `features_master.csv` no trae NaN; el Pipeline imputa con mediana del train solo si aparecieran (§3.3).
- Schema oficial solo con columnas originales de `features_master`; `mun_*`, `grupo_espacial` y `geo` son diagnóstico y se rechazan (§1.3, §5).
- Predicciones se generan recargando `models/` y validando orden/faltantes/finitud (§5.2, §6, §13).
- **Corte temporal (§1.7): hoy NO se cumple.** Ver `results/data_audit.json`: los agregados de `features_master` usan series completas 2022–2025 (incluye nov–dic 2025). `data_cutoff_verified=false` queda registrado en el schema. `CEBADA_STRICT_CUTOFF=1` bloquea la generación de artefactos mientras no se corrija.
- Pendientes de confirmación oficial (§17): nombre de columna ID, unidad, formato del CSV de FIRA.

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

| Archivo | Descripción |
| --------- | ------------- |
| `results/leaderboard.csv` | Tabla con `exp`, `model`, `n_feat`, `rmse`, `rmse_sd`, `mae`, `r2`, `rmse_spatial`, `r2_spatial`, `repeats`, `secs` |
| `results/oof/{exp}__{model}.csv` | Columnas: `parcel_id`, `y` (real), `oof` (predicción promedio OOF) |
| `results/predictions_raw.csv` | Predicciones de las 59 parcelas de evaluación — contrato para la API |
| `models/yield_model_v0.joblib` | Modelo serializado (sin metadatos); cargar con `src.contract.load_artifacts()` |
| `models/feature_schema.json` | Schema contractual: `features` (orden), `unit`, `model_version`, `data_cutoff`, `data_cutoff_verified` |
| `results/data_audit.json` | Resultado de `audit_data.py` |
