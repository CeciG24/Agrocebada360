# P3.7 - Explicabilidad SHAP global y por parcela

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
