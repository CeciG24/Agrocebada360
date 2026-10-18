# P3.5 - Ablacion de familias de variables

> **Guia de lectura (version actual):** el analisis inicial de `E5_fusion` es historico. La ablacion especifica del modelo definitivo `yield-v1` (`E4_clima` Ridge, 30 variables) se presenta en la seccion «Ablacion adicional del modelo definitivo yield-v1».


## Objetivo

Evaluar el efecto de retirar individualmente familias
de variables del modelo de fusion E5 para identificar
su contribucion predictiva.

## Metodologia

Datos:
- 138 parcelas de entrenamiento.
- 59 parcelas de prediccion, no utilizadas en validacion.

Modelo:
- Ridge, utilizando el pipeline existente en src/models.py.

Validacion:
- GroupKFold de 5 particiones espaciales.
- Grupos definidos en src/data.py.
- Mismas particiones para todos los experimentos.

Referencia:
- E5_fusion con 207 variables.

Se retira una familia a la vez y se compara el RMSE
espacial contra el modelo completo.

## Resultados

| Experimento | Variables | RMSE espacial | Delta RMSE |
|---|---:|---:|---:|
| Sin Landsat | 201 | 0.678701 | -0.013359 |
| Completo E5 | 207 | 0.692060 | 0.000000 |
| Sin topografia | 204 | 0.697789 | +0.005729 |
| Sin Planet | 183 | 0.698012 | +0.005952 |
| Sin fenologia Sentinel-2 | 201 | 0.698019 | +0.005959 |
| Sin fenologia Planet | 201 | 0.714921 | +0.022861 |
| Sin Sentinel-2 | 75 | 0.758621 | +0.066561 |
| Sin clima | 177 | 0.815060 | +0.123000 |

RMSE expresado en t/ha.

Delta RMSE = RMSE sin familia - RMSE completo.

## Interpretacion

La eliminacion de clima produjo el mayor aumento
del error espacial (+0.123000 t/ha).

Retirar Sentinel-2 tambien incremento el error
(+0.066561 t/ha).

La fenologia Planet mostro una contribucion
moderada en este experimento (+0.022861 t/ha).

La eliminacion de Planet, topografia y fenologia
Sentinel-2 produjo cambios pequenos.

Retirar Landsat redujo ligeramente el RMSE
(-0.013359 t/ha), sin demostrar que esta fuente
sea innecesaria en otros modelos o escenarios.

## Limitaciones

- Se utilizo un unico algoritmo: Ridge.
- No se realizaron pruebas de significancia estadistica.
- Los resultados no representan efectos causales.
- Las familias pueden contener informacion redundante.
- Se utilizo la matriz maestra completa, cuya seguridad
  temporal no esta certificada segun P3.2.
- La validacion espacial es exploratoria.

## Archivos

Resultados:
- `ml/results/rol3/ablacion_espacial_P3_5.csv`

Código reutilizado del Rol 2:
- `ml/src/data.py`
- `ml/src/models.py`

Documentación:
- `docs/rol3/ablacion_variables_P3_5.md`

## Conclusion

La ablacion espacial sugiere que las familias de clima
y Sentinel-2 son especialmente relevantes para el
desempeno del modelo Ridge evaluado.

La fusion completa no necesariamente proporciona el
menor error: retirar Landsat produjo una pequena
mejora en este experimento.

Los resultados son exploratorios y deben interpretarse
considerando las limitaciones temporales y espaciales.

## Actualizacion para el modelo definitivo yield-v1

### Relacion con el modelo definitivo

La ablacion original P3.5 corresponde al conjunto
E5_fusion, con 207 variables y algoritmo Ridge.

El modelo definitivo yield-v1 utiliza E4_clima,
con 30 variables climaticas y algoritmo Ridge.

Por tanto, los resultados de la ablacion original
no representan una ablacion directa de yield-v1.

### Resultados relevantes de la ablacion original

| Configuracion E5_fusion | RMSE espacial (t/ha) | Cambio frente a E5 |
|---|---:|---:|
| Fusion completa | 0.692060 | 0.000000 |
| Sin clima | 0.815060 | +0.123000 |
| Sin Sentinel-2 | 0.758621 | +0.066561 |
| Sin Landsat | 0.678701 | -0.013359 |

La retirada de las variables climaticas produjo
el mayor incremento de RMSE espacial entre las
familias evaluadas.

Esto respalda su utilidad dentro del experimento
de fusion, pero no demuestra que sean suficientes
para obtener la mejor generalizacion espacial.

### Comparacion con yield-v1

| Modelo o experimento | Variables | RMSE espacial (t/ha) |
|---|---:|---:|
| E5_fusion Ridge exploratorio | 207 | 0.692060 |
| E5_fusion sin clima | 177 | 0.815060 |
| yield-v1 E4_clima Ridge definitivo | 30 | 0.699534 |

Las metricas de yield-v1 corresponden al modelo
definitivo. Las otras dos corresponden a los
experimentos exploratorios de ablacion.

La tabla ofrece contexto comparativo, pero
no constituye una prueba controlada de ablacion
del modelo definitivo.

### Verificacion temporal

Las 30 variables climaticas de yield-v1 fueron
reproducidas a partir de registros anteriores
o iguales al 31 de octubre de 2025.

La auditoria P3.2 obtuvo 5910 coincidencias
en 5910 comparaciones.

Esta verificacion no certifica temporalmente
las otras 177 variables del conjunto E5_fusion.

### Estado de la ablacion especifica

La ablacion directa de las 30 variables de yield-v1 ya fue
ejecutada. Sus seis configuraciones, metricas y archivos
reproducibles se presentan en la seccion final de este documento.

### Conclusion

La ablacion exploratoria E5_fusion identifica
a las variables climaticas como una familia
importante para el rendimiento predictivo.

El resultado es coherente con la seleccion de
E4_clima para yield-v1, pero no demuestra que
el modelo definitivo sea optimo ni que otras
familias de variables sean innecesarias.

## Ablacion adicional del modelo definitivo yield-v1

Se realizo una ablacion controlada sobre las 30 variables
del experimento E4_clima Ridge seleccionado como yield-v1.

Se reutilizaron las funciones oficiales repeated_cv y
spatial_cv, con 5 folds, 10 repeticiones y grupos espaciales.
Cada variante se entreno independientemente durante la
validacion. El modelo congelado no fue modificado.

| Variante | Variables | RMSE | RMSE espacial | Delta espacial |
|---|---:|---:|---:|---:|
| Completo_30 | 30 | 0.514672 | 0.699534 | +0.000000 |
| Sin_precipitacion | 20 | 0.522794 | 0.745227 | +0.045693 |
| Sin_temperaturas | 20 | 0.521024 | 0.646792 | -0.052742 |
| Sin_amplitud_termica | 20 | 0.518974 | 0.730090 | +0.030555 |
| Sin_2025 | 18 | 0.520768 | 0.748133 | +0.048599 |
| Sin_multianual_2022_2025 | 24 | 0.514632 | 0.697256 | -0.002279 |

### Interpretacion

- El modelo completo reproduce RMSE 0.514672 y
  RMSE espacial 0.699534.
- Retirar precipitacion o amplitud termica empeora
  ambos indicadores.
- Retirar temperaturas empeora el RMSE convencional
  pero mejora el espacial hasta 0.646792.
- Retirar agregados multianuales produce diferencias
  minimas, sin evidencia suficiente de una mejora robusta.
- La variante Sin_2025 conserva agregados multianuales
  que contienen informacion de 2025.

Estas comparaciones son diagnosticas. No demuestran
causalidad ni justifican cambiar automaticamente
el modelo oficial.

### Reproducibilidad

Script: ml/rol3/ablacion_climatica_yield_v1.py

Resultados:
ml/results/rol3/ablacion_yield_v1/ablacion_climatica_yield_v1.csv
