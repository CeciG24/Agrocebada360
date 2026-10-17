# P3.4 - Analisis comparativo de sensores y familias de variables

## Objetivo

Comparar el desempeno predictivo de diferentes familias
de variables para estimar el rendimiento de cebada.

## Fuente de resultados

- `ml/results/leaderboard_v2.csv`
- `ml/src/data.py`

Se reutilizaron los experimentos existentes del Rol 2.
No fue necesario volver a entrenar modelos.

## Conjuntos evaluados

- E1_topo: area, elevacion y pendiente (3 variables).
- E2_basico: Sentinel-2, Landsat y fenologia Sentinel-2 (144 variables).
- E3_planet: Planet y fenologia Planet (30 variables).
- E4_clima: precipitacion, temperaturas y amplitud termica (30 variables).
- E5_fusion: topografia, sensores satelitales,
  fenologia y clima (207 variables).

E2_basico no representa exclusivamente Sentinel-2.

## Metodologia

Se compararon ocho algoritmos comunes:

- CatBoost
- ElasticNet
- ExtraTrees
- Gradient Boosting
- LightGBM
- Random Forest
- Ridge
- XGBoost

Se utilizaron RMSE convencional y RMSE espacial.

Las comparaciones entre familias mantienen fijo
el algoritmo, aunque los conjuntos tienen diferentes
cantidades y tipos de variables.

> **Nota de version:** los resultados de `leaderboard_v2.csv`
> son comparaciones exploratorias. Las metricas del modelo
> definitivo `yield-v1` se documentan en la seccion de
> actualizacion correspondiente.

## Resultados

En validacion convencional:

- E4_clima obtuvo el menor RMSE en 7 de 8 algoritmos.
- E5_fusion obtuvo el menor RMSE en 1 de 8 algoritmos.

En validacion espacial:

- E5_fusion obtuvo el menor RMSE en 5 de 8 algoritmos.
- E4_clima obtuvo el menor RMSE en 3 de 8 algoritmos.

### Ejemplo con Ridge

| Conjunto | RMSE convencional | RMSE espacial |
|---|---:|---:|
| E2_basico | 0.6058 | 0.7952 |
| E3_planet | 0.6224 | 0.7248 |
| E4_clima | 0.5152 | 0.6966 |
| E5_fusion | 0.5510 | 0.6921 |

Las unidades de RMSE son t/ha.

## Interpretacion

Las variables climaticas presentan resultados
competitivos en la validacion convencional.

La fusion de fuentes puede mejorar el desempeno
espacial en algunos algoritmos, pero no en todos.

El conjunto Planet por separado no supera al
conjunto clima en los ocho algoritmos comparados.

Estos resultados no permiten atribuir efectos
causales ni demostrar que algun sensor sea innecesario.

## Limitaciones

- E2_basico agrupa Sentinel-2 y Landsat.
- No se aislo el aporte individual de cada sensor.
- No se realizaron pruebas de significancia estadistica.
- Los resultados provienen de la matriz maestra completa,
  cuya seguridad temporal no esta certificada.
- Comparar conjuntos no equivale a una ablacion estricta.

## Conclusion

Se completo una comparacion exploratoria de familias
de variables utilizando ocho algoritmos y validaciones
convencional y espacial.

Las variables climaticas muestran un desempeno
competitivo, mientras que la fusion puede aportar
mejoras en validacion espacial.

Los hallazgos deben interpretarse como exploratorios.

## Actualizacion para el modelo definitivo yield-v1

### Seleccion de variables

El modelo definitivo yield-v1 utiliza el conjunto
E4_clima, compuesto por 30 variables climaticas
de precipitacion, temperaturas y amplitud termica.

El algoritmo utilizado es Ridge.

El modelo se entreno con 138 parcelas etiquetadas.
Las otras 59 parcelas se reservaron para prediccion.

### Resultados de validacion del modelo definitivo

| Metrica | Resultado |
|---|---:|
| RMSE convencional | 0.514672 |
| MAE convencional | 0.356096 |
| R2 convencional | 0.631662 |
| RMSE espacial | 0.699534 |
| R2 espacial | 0.319617 |

Las unidades de RMSE y MAE son t/ha.

Estas metricas corresponden al modelo definitivo
yield-v1 y no deben confundirse con los resultados
exploratorios del leaderboard.

### Relacion con el analisis comparativo

La seleccion de E4_clima es coherente con su buen
desempeno en validacion convencional.

Sin embargo, el modelo definitivo presenta un
error espacial mayor que el convencional.

La comparacion original muestra que algunas
configuraciones de fusion obtuvieron un menor
RMSE espacial que E4_clima.

Por tanto, los resultados no permiten concluir
que utilizar exclusivamente clima sea la mejor
estrategia para generalizar a nuevas regiones.

### Verificacion temporal

La auditoria P3.2 reprodujo las 30 variables
climaticas en las 197 parcelas utilizando
registros hasta el 31 de octubre de 2025.

Se obtuvieron 5910 coincidencias de 5910
comparaciones, con tolerancia absoluta de 0.00001.

Esta verificacion aplica a las variables
climaticas utilizadas por yield-v1.

No certifica temporalmente las variables
satelitales ni todas las variables de fusion.

### Limitaciones

La comparacion entre sensores y familias de
variables sigue siendo exploratoria.

No se aislo experimentalmente el aporte
individual de cada sensor satelital.

Tampoco se realizaron pruebas de significancia
estadistica ni se demostraron relaciones causales.

La auditoria temporal no demuestra por si sola
la disponibilidad operativa de los registros
en la fecha de corte.
