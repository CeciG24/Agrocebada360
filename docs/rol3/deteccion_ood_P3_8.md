# P3.8 - Deteccion de parcelas fuera de distribucion (OOD)

> **Guia de lectura (version actual):** las secciones iniciales
> describen resultados historicos exploratorios. Para la entrega
> definitiva, utilizar la seccion «Actualizacion del modelo
> definitivo yield-v1» y sus archivos `*_yield_v1`.


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

## Actualizacion del modelo definitivo yield-v1

### Modelo y datos

- Modelo definitivo: yield-v1.
- Experimento: E4_clima.
- Variables climaticas: 30.
- Parcelas de entrenamiento: 138.
- Parcelas de evaluacion: 59.
- Version de datos: sha256:b045a212af57282a.

Los resultados anteriores de baseline_v0 se conservan
como analisis exploratorios historicos.

### Metodologia

Se utilizo Isolation Forest con:

- n_estimators: 300.
- contamination: auto.
- random_state: 42.

Las 30 variables climaticas fueron imputadas y
estandarizadas utilizando el preprocesamiento
del modelo definitivo yield-v1.

El detector se ajusto exclusivamente con las
138 parcelas de entrenamiento.

El umbral se calculo como el percentil 5 de los
puntajes score_samples obtenidos en entrenamiento.

Una parcela recibe alerta cuando su puntaje
es estrictamente menor que el umbral.

### Resultados generales

| Metrica | Resultado |
|---|---:|
| Parcelas de entrenamiento | 138 |
| Parcelas evaluadas | 59 |
| Umbral OOD | -0.63192776 |
| Parcelas con alerta | 4 |
| Parcelas sin alerta | 55 |
| Porcentaje con alerta | 6.78 % |

### Parcelas identificadas

| Parcela | Prediccion (t/ha) | Puntaje OOD |
|---|---:|---:|
| AGC_061 | 3.067883 | -0.697110 |
| AGC_029 | 3.038316 | -0.668064 |
| AGC_087 | 2.734081 | -0.664180 |
| AGC_120 | 2.734081 | -0.664180 |

AGC_061 presenta el puntaje mas bajo y,
por tanto, la mayor anomalia segun el detector.

### Diagnostico de caracteristicas extremas

Se examinaron las variables con mayor valor
absoluto estandarizado para cada parcela.

**AGC_029**

- precip_mean_mm_2022: z=+3.9085.
- precip_total_mm_2022: z=+3.9085.
- precip_total_mm_2023: z=+3.6242.
- precip_mean_mm_2023: z=+3.6242.
- precip_mean_mm_2022_2025: z=+3.2548.

**AGC_061**

- precip_mean_mm_2022: z=+4.2833.
- precip_total_mm_2022: z=+4.2833.
- precip_total_mm_2023: z=+3.7882.
- precip_mean_mm_2023: z=+3.7882.
- precip_total_mm_2022_2025: z=+3.6674.

**AGC_087**

- tmin_mean_c_2025: z=-1.8242.
- tmin_mean_c_2024: z=-1.6901.
- tmin_mean_c_2022_2025: z=-1.6860.
- tmin_mean_c_2023: z=-1.6484.
- tmin_mean_c_2022: z=-1.6311.

**AGC_120**

- tmin_mean_c_2025: z=-1.8242.
- tmin_mean_c_2024: z=-1.6901.
- tmin_mean_c_2022_2025: z=-1.6860.
- tmin_mean_c_2023: z=-1.6484.
- tmin_mean_c_2022: z=-1.6311.

AGC_087 y AGC_120 coinciden en las cinco
variables examinadas y en su puntaje OOD.
Esto no demuestra identidad de sus 30 variables.

Los valores z describen desviaciones respecto
al entrenamiento; no constituyen atribuciones
exactas del algoritmo Isolation Forest.

### Comparacion con baseline_v0

El modelo exploratorio baseline_v0 identifico
tres parcelas: AGC_029, AGC_142 y AGC_154.

El detector basado en yield-v1 identifica cuatro:
AGC_029, AGC_061, AGC_087 y AGC_120.

AGC_029 es la unica parcela presente en
ambos conjuntos de alertas.

Las diferencias se relacionan con el cambio
de representacion: 207 variables del modelo
exploratorio frente a 30 variables climaticas.

### Archivos generados

Script:
- `ml/rol3/detectar_ood_yield_v1.py`

Resultados:
- `ml/results/rol3/ood_yield_v1/predicciones_ood_yield_v1.csv`
- `ml/results/rol3/ood_yield_v1/metadata_ood_yield_v1.json`

### Limitaciones

1. El percentil 5 es un umbral operativo y no
   garantiza una tasa de alertas futura del 5 %.
2. Una alerta OOD no demuestra que la prediccion
   de rendimiento sea incorrecta.
3. El diagnostico por valores z no explica
   directamente las decisiones de Isolation Forest.
4. El detector utiliza solamente variables climaticas.
5. La procedencia temporal de las variables
   requiere la verificacion descrita en P3.2.
6. No se ha evaluado la estabilidad de las
   alertas frente a otros umbrales o semillas.

### Conclusion actualizada

P3.8 dispone de un detector OOD para las
59 predicciones del modelo definitivo yield-v1.

Se identificaron cuatro parcelas con caracteristicas
climaticas inusuales respecto al entrenamiento.

Las alertas pueden utilizarse como indicadores
operativos de revision, sin interpretarlas
como errores predictivos confirmados.
