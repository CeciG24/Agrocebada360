# P3.8 - Deteccion de parcelas fuera de distribucion (OOD)

## Objetivo

Identificar parcelas cuyas caracteristicas sean inusuales
respecto a las parcelas utilizadas para entrenar Cebada360.

## Metodologia

Se utiliza Isolation Forest con los siguientes parametros:

- n_estimators: 300.
- contamination: auto.
- random_state: 42.

El detector se ajusta exclusivamente con las
138 parcelas de entrenamiento.

Se utilizan las 207 variables del modelo baseline_v0,
aplicando su imputacion y estandarizacion.

Se calcula un puntaje mediante score_samples.
Los puntajes mas bajos representan mayor anomalia.

El umbral se define como el percentil 5 de los
puntajes obtenidos en entrenamiento.

Una parcela recibe alerta cuando:

score_ood < umbral_ood

### Reproducibilidad

El cálculo original utiliza el artefacto local
`ml/artifacts/baseline_v0.joblib`, generado por
el flujo de experimentación del Rol 2.

El artefacto serializado no se incluye en esta
rama. Por tanto, la reproducción completa del
detector requiere generar o disponer previamente
de dicho modelo.

Los resultados CSV publicados permiten consultar
las alertas obtenidas, pero no sustituyen la
reproducción independiente del entrenamiento.

## Resultados generales

- Parcelas de entrenamiento: 138.
- Parcelas evaluadas: 59.
- Parcelas con alerta OOD: 3.
- Parcelas sin alerta OOD: 56.
- Porcentaje con alerta: 5.08 %.
- Umbral OOD: -0.53632357.
- Identificadores duplicados: 0.
- Puntajes faltantes: 0.
- Consistencia de alertas con el umbral: correcta.

## Parcelas identificadas

| Parcela | Prediccion t/ha | Puntaje OOD |
|---|---:|---:|
| AGC_142 | 4.352 | -0.579405 |
| AGC_154 | 4.727 | -0.555398 |
| AGC_029 | 2.813 | -0.537467 |

## Diagnostico de caracteristicas

### AGC_142

Presenta valores fuera del rango observado en
entrenamiento en las cinco variables examinadas:

- sentinel2_ndti_min.
- sentinel2_sti_min.
- sentinel2_ndvi_peak.
- sentinel2_ndvi_max.
- sentinel2_ndsvi_max.

Ejemplo:

sentinel2_ndvi_peak = 0.48.
Minimo de entrenamiento = 0.54.

Es la parcela con menor puntaje OOD.

### AGC_154

La variable sentinel2_enddi_range presenta
un valor de 0.501, superior al maximo de
entrenamiento de 0.497.

Otras cuatro caracteristicas examinadas son
extremas respecto al 90 % central:

- sentinel2_ndti_min.
- sentinel2_sti_min.
- sentinel2_nddi_range.
- sentinel2_ndsvi_range.

### AGC_029

Presenta valores elevados de precipitacion
respecto al 90 % central de entrenamiento
en los años 2022 y 2023.

La variable planet_ndvi_decay_rate tiene
un valor de -0.0075065, inferior al minimo
de entrenamiento de -0.0070256.

## Interpretacion

Las tres parcelas presentan caracteristicas
inusuales respecto a los datos de entrenamiento.

Las alertas indican que conviene revisar
la confiabilidad de sus predicciones.

No significan necesariamente que las
predicciones sean incorrectas.

El analisis de variables extremas es
descriptivo y no demuestra causalidad
ni atribucion exacta de Isolation Forest.

## Archivos relacionados

Scripts del Rol 3:
- `ml/rol3/recalcular_ood_rol3.py`
- `ml/rol3/analizar_ood.py`
- `ml/rol3/revisar_ood.py`

Resultados:
- `ml/results/rol3/predicciones_con_alertas_ood.csv`

Documentación:
- `docs/rol3/deteccion_ood_P3_8.md`

## Limitaciones

El percentil 5 es un umbral operativo y no
garantiza una tasa de alertas del 5 % en
parcelas futuras.

La verificacion realizada confirma la
consistencia del archivo existente,
pero no reproduce independientemente
el ajuste completo del detector.

El analisis utiliza la matriz maestra,
cuya seguridad temporal no ha sido
certificada completamente.

Los resultados se consideran exploratorios.

## Conclusion

Se dispone de un procedimiento de deteccion
OOD basado en Isolation Forest.

Se identificaron tres parcelas con alerta
entre las 59 parcelas de prediccion.

Las alertas fueron verificadas y se
documentaron caracteristicas inusuales
para cada una de las tres parcelas.
