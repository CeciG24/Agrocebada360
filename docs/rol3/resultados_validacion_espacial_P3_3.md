# P3.3 - Resultados de validacion espacial

## Objetivo

Evaluar la generalizacion de los modelos de rendimiento
de cebada hacia grupos geograficos no vistos.

## Metodologia

- Dataset: 138 parcelas de entrenamiento.
- Agrupacion: KMeans sobre latitud y longitud.
- Grupos espaciales: 6.
- Validacion: GroupKFold de 5 particiones.
- Metrica principal: RMSE.
- Metricas complementarias: MAE y R2.
- Semilla: 42.

La separacion espacial fue verificada en P3.1:
ninguna parcela ni grupo espacial se comparte entre
entrenamiento y validacion dentro del mismo fold.


> **Nota de version:** los resultados de `leaderboard_v2.csv`
> son comparaciones exploratorias. Las metricas del modelo
> definitivo `yield-v1` se documentan en la seccion de
> actualizacion correspondiente.

## Experimentos evaluados

Se analizaron 73 combinaciones de configuraciones
experimentales y algoritmos, distribuidas entre
10 familias de experimentos y 9 algoritmos.

La siguiente tabla presenta una selección de
resultados representativos: el modelo con menor
RMSE espacial reportado para cada experimento.

Los resultados completos se encuentran en
`ml/results/leaderboard_v2.csv`.


| Experimento | Modelo | RMSE espacial | R2 espacial |
|---|---|---:|---:|
| X1_geo | LightGBM | 0.6413 | 0.4283 |
| X0_municipio | Ridge | 0.6422 | 0.4265 |
| E5_fusion | Ridge | 0.6921 | 0.3341 |
| X2_fusion_mas_geo | Ridge | 0.6939 | 0.3305 |
| E4_clima | Ridge | 0.6966 | 0.3253 |
| X3_muni_mas_sat | ElasticNet | 0.7023 | 0.3142 |
| E3_planet | Ridge | 0.7248 | 0.2696 |
| E2_basico | Ridge | 0.7952 | 0.1208 |
| E1_topo | LightGBM | 0.9466 | -0.2458 |
| E0_baseline | Dummy Median | 1.2104 | -1.0370 |

## Hallazgos

1. El mejor resultado espacial fue X1_geo con LightGBM,
   con RMSE de 0.6413 t/ha y R2 de 0.4283.

2. Para X1_geo con LightGBM, el RMSE convencional
   fue de 0.5122 t/ha y el RMSE espacial fue de
   0.6413 t/ha. Esto representa un incremento
   aproximado del 25.19 % en el error bajo
   validación espacial, lo que sugiere una
   menor capacidad de generalización hacia
   grupos geográficos no vistos.

3. Los experimentos basados en ubicacion geografica
   muestran resultados competitivos.

4. La fusion de variables no supera necesariamente
   a los modelos geograficos bajo este protocolo.

5. Todos los mejores modelos por experimento superan
   el RMSE espacial del baseline.

## Limitaciones

Los resultados proceden de features_master.csv.

La matriz maestra no fue certificada completamente
contra fuga temporal en P3.2.

Por ello, las metricas espaciales presentadas son
resultados exploratorios y no deben interpretarse
como validacion final libre de fuga temporal.

Los resultados tampoco demuestran que las coordenadas
sean causalmente responsables del rendimiento.


## Archivos relacionados

Implementación del Rol 2:

- `ml/src/cv.py`
- `ml/src/data.py`
- `ml/src/config.py`
- `ml/run_experiments.py`

Resultados:

- `ml/results/leaderboard_v2.csv`

Documentación del Rol 3:

- `docs/rol3/protocolo_validacion_P3_1.md`
- `docs/rol3/politica_temporal_anti_leakage.md`


## Estado

P3.3: validacion espacial ejecutada y resultados
exploratorios documentados.

## Evaluacion del modelo definitivo yield-v1

### Identificacion del modelo

- Version del modelo: yield-v1.
- Experimento seleccionado: E4_clima.
- Algoritmo: RidgeCV dentro de un Pipeline.
- Variables utilizadas: 30 variables climaticas.
- Parcelas etiquetadas: 138.
- Version de datos: sha256:b045a212af57282a.
- Fuente: ml/results/final_model_config.json.

### Resultados de validacion

| Metrica | Validacion convencional | Validacion espacial |
|---|---:|---:|
| RMSE (t/ha) | 0.5147 | 0.6995 |
| R2 | 0.6317 | 0.3196 |
| MAE (t/ha) | 0.3561 | No reportado |

El RMSE espacial es aproximadamente 35.92 % mayor que el
RMSE convencional. Esto indica una disminucion del desempeno
predictivo cuando la evaluacion separa grupos geograficos.

### Comparacion con el modelo basado en municipio

| Modelo | RMSE convencional | RMSE espacial |
|---|---:|---:|
| X0_municipio / Ridge | 0.5076 | 0.6422 |
| E4_clima / Ridge (yield-v1) | 0.5147 | 0.6995 |

El modelo basado en municipio obtuvo menor error en ambas
evaluaciones. Por tanto, los resultados disponibles no permiten
afirmar que yield-v1 supera a todas las alternativas evaluadas.

### Procedencia y limitaciones

Las metricas de esta seccion proceden de la configuracion final
del Rol 2 y no representan una nueva ejecucion independiente
del protocolo espacial por parte del Rol 3.

La validacion espacial utiliza grupos geograficos y constituye
un diagnostico de generalizacion, no una reproduccion del
muestreo oficial de evaluacion.

La seleccion del modelo se realizo utilizando resultados de
validacion sobre los mismos datos empleados para comparar
candidatos, por lo que puede existir optimismo de seleccion.

La verificacion de las 59 predicciones de evaluacion confirmo
coincidencia numerica con los resultados publicados por el Rol 2,
con una diferencia maxima de aproximadamente 4.44e-16 t/ha.
Esta comprobacion demuestra reproducibilidad de predicciones,
pero no constituye una validacion espacial independiente.

Los resultados deben interpretarse considerando las limitaciones
de procedencia temporal de las variables climaticas documentadas
en P3.2.

### Estado actualizado

P3.3: resultados exploratorios conservados y metricas espaciales
del modelo definitivo yield-v1 incorporadas y documentadas.
