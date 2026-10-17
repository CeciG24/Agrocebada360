# P3.2 — Política temporal contra la fuga de información

> **Guia de lectura (version actual):** las secciones 8 y 9 documentan el estado historico anterior a la seleccion del modelo definitivo. La auditoria de las 30 variables de `yield-v1` y sus resultados actualizados se presentan en la seccion 10. La auditoria no certifica la disponibilidad operativa de todas las fuentes al corte temporal.


## 1. Objetivo

Establecer y verificar una política de prevención de fuga temporal de información (*temporal data leakage*) para los modelos de predicción de rendimiento de cebada del proyecto Cebada360.

La finalidad es impedir que los modelos utilicen observaciones o características que no estarían disponibles en el momento de realizar la predicción.

## 2. Fecha de corte

La fecha máxima permitida para el escenario de predicción al cierre del ciclo es el **31 de octubre de 2025**, inclusive.

Las observaciones posteriores al `2025-10-31` no pueden utilizarse para construir características predictoras bajo esta política.

Para los experimentos de predicción temprana se aplican cortes adicionales:

- Junio de 2025.
- Julio de 2025.
- Agosto de 2025.
- Septiembre de 2025.
- Octubre de 2025.

Cada matriz temporal debe utilizar únicamente información disponible hasta el cierre del mes correspondiente.

## 3. Alcance

La política comprende las siguientes fuentes y variables:

- Series temporales climáticas.
- Series temporales de Sentinel-2.
- Series temporales de Landsat.
- Series temporales de Planet.
- Características derivadas de las series temporales.
- Características fenológicas: picos, fechas de pico, áreas bajo la curva, tasas de crecimiento y decaimiento.
- Variables agregadas anuales o multianuales que puedan incorporar observaciones posteriores al corte.

Las variables topográficas y geográficas tampoco se consideran automáticamente seguras: deben verificarse su procedencia y disponibilidad.

## 4. Auditoría inicial de las fuentes originales

Se inspeccionaron las series temporales originales para identificar observaciones posteriores al 31 de octubre de 2025.

| Fuente | Registros posteriores al corte |
|---|---:|
| `climate_timeseries.csv` | 394 |
| `sentinel2_timeseries.csv` | 3,091 |
| `landsat_timeseries.csv` | 1,914 |
| `planet_timeseries.csv` | 7,932 |

**Hallazgo:** las cuatro fuentes originales contienen observaciones posteriores a la fecha máxima permitida.

Por tanto, no deben utilizarse directamente para generar características sujetas al corte sin aplicar previamente los filtros temporales correspondientes.

También se revisaron inicialmente los siguientes archivos:

| Archivo | Registros posteriores al corte |
|---|---:|
| `climate_corte_octubre.csv` | 0 |
| `climate_corte_septiembre.csv` | 0 |
| `sentinel2_corte_octubre.csv` | 0 |
| `sentinel2_corte_septiembre.csv` | 0 |

Las fechas de pico de Sentinel-2 y Planet registradas en `features_master.csv` tampoco superaron el 31 de octubre de 2025.

Sin embargo, esta última comprobación no demuestra que todas las características agregadas de la matriz maestra respeten la política temporal.

## 5. Reglas de prevención

1. Convertir las fechas de observación a un formato válido y verificable.
2. Excluir cualquier observación posterior al corte temporal aplicable.
3. Recalcular las características climáticas y satelitales a partir de registros permitidos.
4. Verificar los periodos de las variables anuales y multianuales.
5. Recalcular las características fenológicas usando exclusivamente observaciones disponibles hasta el corte.
6. Excluir las variables cuyo periodo de cálculo o disponibilidad no pueda verificarse.
7. Aplicar las mismas reglas temporales a entrenamiento y predicción.
8. Conservar intactos los archivos originales y generar versiones filtradas por separado.
9. Repetir la validación del modelo cuando se modifiquen las características utilizadas.
10. Registrar los archivos, fechas, transformaciones y resultados de cada verificación.

## 6. Implementación de los cortes temporales

Se trabajó con cinco cortes mensuales de 2025: junio, julio, agosto, septiembre y octubre.

Para cada corte se verificaron archivos filtrados de dos fuentes:

- Clima.
- Sentinel-2.

En total se analizaron **10 archivos de origen**: cinco climáticos y cinco satelitales.

### 6.1 Verificación de fechas

Los resultados de las comprobaciones fueron:

- Registros posteriores al corte correspondiente: **0**.
- Fechas no interpretables: **0**.
- Archivos que respetan el límite temporal de su mes: **10 de 10**.

Esto confirma que los archivos temporales revisados cumplen sus respectivos límites de fecha.

### 6.2 Verificación de variables derivadas

Se recalcularon y comprobaron 24 variables temporales por cada corte, utilizando los archivos filtrados.

| Corte temporal | Variables verificadas | Resultado |
|---|---:|---|
| Junio de 2025 | 24 | Correctas |
| Julio de 2025 | 24 | Correctas |
| Agosto de 2025 | 24 | Correctas |
| Septiembre de 2025 | 24 | Correctas |
| Octubre de 2025 | 24 | Correctas |
| **Total** | **120** | **120 correctas** |

La tolerancia numérica utilizada fue de `0.0001`.

**Resultado:** las 120 comprobaciones realizadas coincidieron con los valores recalculados a partir de las fuentes temporales filtradas.



### 6.3 Matrices de predicción temprana

Se generaron cinco matrices de características temporales,
almacenadas localmente en:

`prediccion_temprana/matrices/`

Archivos:

- `features_master_corte_junio.csv`
- `features_master_corte_julio.csv`
- `features_master_corte_agosto.csv`
- `features_master_corte_septiembre.csv`
- `features_master_corte_octubre.csv`

Se verificó que cada matriz contiene 197 registros y
33 columnas, coincidiendo con las dimensiones documentadas.

Los archivos se encuentran en el directorio local del
dataset original y todavía no forman parte de la rama
`ml-avanzado`.

Estas matrices constituyen la base para continuar los
experimentos de predicción temprana dentro del alcance
de la auditoría realizada.



## 7. Trazabilidad y límites de la validación

La auditoría permite afirmar que:

- Los 10 archivos temporales revisados respetan sus cortes mensuales.
- No se encontraron fechas no interpretables en esos archivos.
- Las 120 comprobaciones de características derivadas fueron correctas dentro de la tolerancia establecida.
- Se dispone de matrices temporales diferenciadas para los cinco escenarios de predicción temprana.

No obstante, **la auditoría no certifica automáticamente toda la matriz `features_master.csv`**.

Esta matriz contiene características adicionales, incluidas variables anuales o multianuales y otras familias de sensores, que no quedaron completamente verificadas mediante las 120 comprobaciones.

Tampoco se evaluaron mediante esta auditoría otras posibles formas de fuga de información, como:

- Uso indebido de la variable objetivo.
- Preprocesamiento ajustado fuera de los pliegues de validación.
- Separaciones incorrectas entre entrenamiento y evaluación.
- Selección de modelos utilizando información de las parcelas de evaluación.

Estos aspectos deben comprobarse mediante los protocolos correspondientes.

## 8. Estado actual y actividades pendientes

**Estado de P3.2: política documentada y auditoría de matrices temporales completada.**

### Actividades completadas

- Definición del corte máximo del 31 de octubre de 2025.
- Identificación de observaciones posteriores al corte en las fuentes originales.
- Verificación de los archivos temporales de clima y Sentinel-2.
- Revisión de cinco escenarios mensuales.
- Recalculo y comprobación de 120 valores de características derivadas.
- Identificación de las matrices temporales disponibles para experimentos posteriores.

### Actividades pendientes de integración

- Verificar las variables adicionales de `features_master.csv` cuando se pretenda utilizar esa matriz bajo la política temporal.
- Confirmar la procedencia y disponibilidad de las características no cubiertas por la auditoría.
- Comprobar que el modelo seleccionado por el Rol 2 utilice exclusivamente características compatibles con el escenario temporal definido.
- Ejecutar o revisar la validación del modelo definitivo con las características autorizadas.

Estas actividades no invalidan las verificaciones completadas, pero impiden declarar que cualquier modelo entrenado con la matriz maestra original está automáticamente libre de fuga temporal.

## 9. Conclusión

Se estableció una política temporal para prevenir el uso de información posterior al momento de predicción en el proyecto Cebada360.

La auditoría inicial identificó observaciones posteriores al 31 de octubre de 2025 en las cuatro series temporales originales: clima, Sentinel-2, Landsat y Planet.

Posteriormente, se verificaron diez archivos temporales de clima y Sentinel-2 correspondientes a cinco cortes mensuales. No se detectaron registros posteriores a sus respectivas fechas límite ni fechas no interpretables.

Asimismo, se comprobaron **120 de 120 valores de características derivadas**, con una tolerancia numérica de `0.0001`.

Por tanto, **la auditoría de las matrices temporales revisadas se considera completada satisfactoriamente dentro de su alcance**.

Sin embargo, la matriz maestra original y el futuro modelo definitivo requieren comprobaciones adicionales antes de afirmar que cumplen integralmente la política anti-leakage.

Los resultados de P3.2 constituyen una base técnica para que el Rol 2 seleccione y valide un modelo compatible con las restricciones temporales del proyecto.

## Estado actualizado de P3.2

Las actividades pendientes mencionadas en las secciones 8 y 9
corresponden a la fase anterior a la seleccion de yield-v1.
La auditoria posterior del modelo definitivo, documentada
a continuacion, verifico las 30 variables climaticas utilizadas
por yield-v1 (5910/5910 coincidencias). No certifica las
otras familias de features_master.csv ni la disponibilidad
operativa de cada fuente al corte temporal.

## 10. Auditoria temporal del modelo definitivo yield-v1

### Modelo y datos

- Modelo: yield-v1.
- Experimento: E4_clima.
- Algoritmo: Ridge.
- Variables climaticas utilizadas: 30.
- Parcelas verificadas: 197.
- Corte temporal: 2025-10-31.

### Procedimiento

Se recalcularon las 30 variables climaticas a partir
de climate_timeseries.csv, utilizando exclusivamente
registros con fecha igual o anterior al corte.

Se utilizaron las siguientes ventanas:

- 2022: enero a diciembre.
- 2023: enero a diciembre.
- 2024: enero a diciembre.
- 2025: abril a octubre.
- 2022-2025: combinacion de los periodos anteriores.

La amplitud termica se calculo como tmax_c - tmin_c.
La desviacion estandar se calculo con ddof=1.

Los valores recalculados se compararon contra
climate_features.csv y features_master.csv.

### Resultados

| Comprobacion | Resultado |
|---|---:|
| Parcelas verificadas | 197 |
| Variables climaticas | 30 |
| Comparaciones por variable | 197 |
| Comparaciones totales | 5910 |
| Coincidencias | 5910 |
| Diferencias | 0 |
| Tolerancia absoluta | 0.00001 |
| Coincidencias entre climate_features y features_master | 5910/5910 |

Las 30 variables se reprodujeron correctamente
utilizando los periodos temporales permitidos.

La serie climatica original contiene 394 registros
posteriores al corte. Sin embargo, las variables
auditadas se reprodujeron sin utilizar esos registros.

### Interpretacion

No se encontro evidencia de fuga temporal en los
valores de las 30 variables climaticas utilizadas
por yield-v1, dentro del alcance de esta auditoria.

La comprobacion no demuestra por si sola la
disponibilidad operativa de cada registro en la
fecha de corte, ni descarta otras formas de fuga
de informacion.

La conclusion aplica al modelo yield-v1 y a
las variables verificadas. No certifica las
otras familias de variables de features_master.csv.

### Fuentes verificadas

- clima/climate_timeseries.csv
- clima/climate_features.csv
- features/features_master.csv
- ml/models/feature_schema.json
- ml/audit_data.py
