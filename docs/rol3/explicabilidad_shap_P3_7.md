# P3.7 - Explicabilidad SHAP global y por parcela

> **Guia de lectura (version actual):** las secciones iniciales
> describen resultados historicos exploratorios. Para la entrega
> definitiva, utilizar la seccion «Actualizacion del modelo
> definitivo yield-v1» y sus archivos `*_yield_v1`.


## Objetivo

Explicar las predicciones de rendimiento de Cebada360
mediante SHAP, tanto a nivel global como individual.

## Modelos analizados

1. baseline_v0: E5_fusion + Ridge, 207 variables.
2. X0_municipio + Ridge, 9 variables.

Ambos modelos explican 59 parcelas de prediccion.

## Explicabilidad global

### baseline_v0

Principales variables segun importancia SHAP media absoluta:

| Variable | Importancia SHAP |
|---|---:|
| sentinel2_ndvi_growth_rate | 0.03261 |
| sentinel2_lai_median | 0.03108 |
| sentinel2_savi_median | 0.03088 |
| precip_total_mm_2025 | 0.03012 |
| precip_mean_mm_2025 | 0.03012 |

Las variables mas importantes incluyen indices de
vegetacion, precipitacion y temperatura.

### X0_municipio

Principales variables:

| Variable | Importancia SHAP |
|---|---:|
| mun_Chignahuapan | 0.32325 |
| mun_Calpulalpan | 0.28972 |
| mun_Singuilucan | 0.15383 |
| mun_Almoloya | 0.08967 |
| mun_Cuautepec de Hinojosa | 0.07570 |

Estas importancias representan magnitudes promedio
de contribucion, no efectos causales.

## Explicabilidad individual: AGC_003

### baseline_v0

- Valor base: 3.9735 t/ha.
- Suma SHAP: -0.1834 t/ha.
- Prediccion: 3.7901 t/ha.

Principales contribuciones positivas:

- sentinel2_lai_median: +0.11630.
- sentinel2_savi_median: +0.11296.
- sentinel2_evi_median: +0.09598.

Principales contribuciones negativas:

- planet_ndvi_mean: -0.16736.
- planet_msavi_median: -0.12150.
- planet_lai_mean: -0.11244.

### X0_municipio

- Valor base: 3.9554 t/ha.
- Suma SHAP: -0.8694 t/ha.
- Prediccion: 3.0860 t/ha.

Contribuciones destacadas:

- mun_Calpulalpan: +0.17917.
- mun_Singuilucan: -0.65674.
- mun_Chignahuapan: -0.33245.

Las contribuciones de variables binarias dependen
de su presencia o ausencia y de la referencia SHAP.

## Verificacion de coherencia

- Parcelas explicadas por modelo: 59.
- Identificadores duplicados: 0.
- Valores faltantes: 0.
- Diferencia maxima baseline_v0: 0.00004926 t/ha.
- Diferencia maxima X0_municipio: 0 t/ha.

La pequena diferencia de baseline_v0 es compatible
con el redondeo de las predicciones almacenadas.

## Archivos de resultados

### Modelo baseline_v0

- `ml/results/rol3/shap_importancia_baseline_v0.csv`
- `ml/results/rol3/shap_valores_baseline_v0.csv`
- `ml/results/rol3/shap_resumen_baseline_v0.png`

### Modelo X0_municipio + Ridge

- `ml/results/rol3/shap_importancia_x0_municipio_ridge.csv`
- `ml/results/rol3/shap_valores_x0_municipio_ridge.csv`
- `ml/results/rol3/shap_resumen_x0_municipio_ridge.png`

### Scripts utilizados

- `ml/rol3/analizar_shap.py`
- `ml/rol3/analizar_shap_x0.py`

## Reproducibilidad

Los análisis SHAP se realizaron utilizando modelos Ridge
y sus respectivos conjuntos de variables.

El modelo baseline_v0 utiliza el artefacto local
`ml/artifacts/baseline_v0.joblib`.

Los modelos serializados no se incluyen en esta rama.
Para reproducir las explicaciones desde cero es necesario
disponer de los modelos correspondientes o reconstruirlos
mediante el flujo de entrenamiento.

Los archivos CSV y las gráficas incluidos permiten
consultar las explicaciones previamente generadas.

Las explicaciones deberán actualizarse cuando el Rol 2
confirme el modelo definitivo.

## Limitaciones

SHAP explica las predicciones del modelo y no
establece relaciones causales.

Los resultados globales corresponden a las
59 parcelas evaluadas, no necesariamente a toda
la poblacion de parcelas.

Los modelos utilizan datos cuya seguridad temporal
no ha sido certificada completamente.

Por ello, los resultados son exploratorios.

## Conclusion

Se generaron y verificaron explicaciones SHAP
globales e individuales para dos modelos de referencia
de Cebada360: baseline_v0 y X0_municipio + Ridge.

Las explicaciones reconstruyen las predicciones
almacenadas dentro de las tolerancias verificadas
y permiten identificar las contribuciones de las
variables en cada modelo.

Estos resultados son exploratorios y deberán
actualizarse si el Rol 2 selecciona un modelo
definitivo diferente.

## Actualizacion del modelo definitivo yield-v1

### Modelo y datos

- Modelo definitivo: yield-v1.
- Experimento: E4_clima.
- Algoritmo: Pipeline SimpleImputer + StandardScaler + RidgeCV.
- Variables explicadas: 30 variables climaticas.
- Parcelas de entrenamiento utilizadas como referencia: 138.
- Parcelas explicadas: 59.
- Version de datos: sha256:b045a212af57282a.
- Unidad de prediccion y contribuciones SHAP: t/ha.

Los modelos baseline_v0 y X0_municipio documentados anteriormente
se conservan como referencias exploratorias. Sus explicaciones
no corresponden al modelo definitivo.

### Metodologia

Se utilizo shap.LinearExplainer sobre el estimador RidgeCV,
aplicando previamente la imputacion y el escalado del Pipeline.

El conjunto de referencia corresponde a las 138 parcelas de
entrenamiento transformadas. Se configuro un masker Independent
con max_samples=138 para evitar el submuestreo predeterminado.

Las contribuciones se calcularon para las 59 parcelas de
evaluacion, respetando el orden de las 30 variables del modelo.

### Importancia global

La importancia corresponde al promedio del valor absoluto
de las contribuciones SHAP sobre las 59 parcelas evaluadas.

| Variable | Importancia SHAP media (t/ha) |
|---|---:|
| precip_mean_mm_2025 | 0.28648 |
| precip_total_mm_2025 | 0.28648 |
| precip_mean_mm_2023 | 0.24461 |
| precip_total_mm_2023 | 0.24461 |
| amplitud_termica_std_c_2023 | 0.14420 |

Las variables de precipitacion de 2025 y 2023 presentan
las mayores contribuciones promedio en este conjunto.

Las importancias de precipitacion total y media de un
mismo periodo coinciden. Esto requiere precaucion al
interpretar variables correlacionadas o redundantes:
sus atribuciones individuales no prueban efectos
independientes.

### Explicacion individual: AGC_003

- Prediccion yield-v1: 3.210176 t/ha.
- Valor base SHAP: 3.955362 t/ha.
- Suma de contribuciones SHAP: -0.745186 t/ha.
- Prediccion reconstruida: 3.210176 t/ha.

Principales contribuciones positivas:

| Variable | SHAP (t/ha) |
|---|---:|
| precip_mean_mm_2023 | +0.474869 |
| precip_total_mm_2023 | +0.474869 |
| amplitud_termica_std_c_2023 | +0.239413 |
| precip_total_mm_2024 | +0.134576 |
| precip_mean_mm_2024 | +0.134576 |

Principales contribuciones negativas:

| Variable | SHAP (t/ha) |
|---|---:|
| precip_mean_mm_2025 | -0.919352 |
| precip_total_mm_2025 | -0.919352 |
| precip_total_mm_2022_2025 | -0.135415 |
| precip_mean_mm_2022_2025 | -0.135415 |
| precip_mean_mm_2022 | -0.127795 |

La suma de todas las contribuciones, no solo las
mostradas en las tablas, reconstruye la prediccion.

### Verificacion de aditividad

Se verifico para las 59 parcelas:

prediccion = valor_base_SHAP + suma_de_contribuciones_SHAP

El error maximo absoluto fue 8.881784197001252e-16 t/ha,
inferior a la tolerancia establecida de 1e-8 t/ha.

Esta prueba confirma coherencia numerica de las explicaciones,
pero no valida por si sola la precision predictiva del modelo.

### Archivos reproducibles

Script:
- `ml/rol3/analizar_shap_yield_v1.py`

Resultados:
- `ml/results/rol3/shap_yield_v1/shap_importancia_yield_v1.csv`
- `ml/results/rol3/shap_yield_v1/shap_valores_yield_v1.csv`
- `ml/results/rol3/shap_yield_v1/shap_metadata_yield_v1.json`
- `ml/results/rol3/shap_yield_v1/shap_resumen_yield_v1.png`

El script comprueba la version de datos y la coincidencia
del orden de las variables con el modelo serializado.

### Limitaciones y conclusion actualizada

Las explicaciones SHAP describen el comportamiento predictivo
del modelo y no demuestran causalidad.

El uso de variables climaticas correlacionadas puede afectar
la atribucion individual de importancia. Las conclusiones
globales corresponden a las 59 parcelas explicadas.

La interpretacion debe considerar las limitaciones de
procedencia temporal de las variables de 2025 descritas
en P3.2 y las limitaciones de validacion espacial de P3.3.

P3.7 cuenta ahora con explicaciones globales e individuales
del modelo definitivo yield-v1. Los resultados anteriores
permanecen documentados como analisis exploratorios.
