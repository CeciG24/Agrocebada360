# P3.1 - Diseño de validación convencional y espacial

## Objetivo

Definir un protocolo reproducible para evaluar la capacidad
predictiva de los modelos de rendimiento de cebada y analizar
su generalización a regiones geográficas no vistas.

## Datos

- Parcelas de entrenamiento: 138.
- Parcelas de predicción: 59.
- Variable objetivo: rendimiento_t_ha.
- Identificador: parcel_id.
- Semilla aleatoria: 42.

Las parcelas de predicción no tienen rendimiento observado
y no se utilizan para calcular las métricas de validación.

## Validación convencional

Método: KFold con aleatorización.

Configuración:
- 5 folds.
- 10 repeticiones.
- Semillas: 42 a 51.
- Predicciones fuera de fold (OOF).

En cada repetición, cada parcela de entrenamiento recibe
una predicción generada por un modelo que no fue entrenado
con su rendimiento observado.

## Validación espacial

Método: GroupKFold.

Los grupos se generan mediante KMeans utilizando:
- centroid_lat
- centroid_lon

Configuración:
- 6 grupos espaciales.
- 5 folds de validación.
- Semilla KMeans: 42.
- n_init: 10.

Distribución de parcelas por grupo:
- Grupo 0: 41.
- Grupo 1: 22.
- Grupo 2: 17.
- Grupo 3: 11.
- Grupo 4: 13.
- Grupo 5: 34.

## Resultados de verificación

Fold 1: 97 entrenamiento, 41 validación, grupo 0.
Fold 2: 104 entrenamiento, 34 validación, grupo 5.
Fold 3: 116 entrenamiento, 22 validación, grupo 1.
Fold 4: 121 entrenamiento, 17 validación, grupo 2.
Fold 5: 114 entrenamiento, 24 validación, grupos 3 y 4.

Resultados:
- Grupos compartidos entre entrenamiento y validación: 0.
- Parcelas compartidas entre entrenamiento y validación: 0.
- Parcelas validadas: 138.
- Parcelas únicas validadas: 138.
- Cada parcela fue validada exactamente una vez.

## Métricas

Métrica principal:
- RMSE: raíz del error cuadrático medio.

Métricas complementarias:
- MAE: error absoluto medio.
- R2: coeficiente de determinación.

Se compararán los resultados convencionales y espaciales
para identificar posibles pérdidas de generalización.

## Consideraciones metodológicas

Los grupos espaciales se construyen sobre las coordenadas
de las 197 parcelas, incluyendo las de predicción, sin
utilizar sus rendimientos observados.

KMeans sobre latitud y longitud es una aproximación a
la agrupación espacial, no una división geográfica exacta.

La separación entre grupos se verificó correctamente,
pero esto no demuestra por sí solo ausencia de todas las
formas de fuga de información.

La validación de las variables respecto al corte temporal
se documenta por separado en P3.2.

Los experimentos basados en features_master.csv requieren
revisión de sus variables temporales antes de considerarse
libres de fuga temporal.


## Archivos relacionados

Implementación del Rol 2:

- `ml/src/config.py`
- `ml/src/data.py`
- `ml/src/cv.py`
- `ml/run_experiments.py`

Documentación del Rol 3:

- `docs/rol3/politica_temporal_anti_leakage.md`
- `docs/rol3/resultados_validacion_espacial_P3_3.md`


## Estado

P3.1 completado: protocolo identificado, revisado y
separación espacial verificada.

La ejecución y comparación de métricas espaciales
corresponde a P3.3.

> **Nota de version:** el protocolo general anterior se
> conserva como antecedente. La configuracion y los resultados
> oficiales de `yield-v1` se detallan a continuacion.

## Actualizacion del modelo definitivo yield-v1

### Configuracion

- Version del modelo: yield-v1.
- Experimento: E4_clima.
- Algoritmo: Ridge.
- Variables climaticas: 30.
- Parcelas de entrenamiento: 138.
- Parcelas de evaluacion: 59.
- Version de datos: sha256:b045a212af57282a.

Se conserva el protocolo convencional de cinco folds
y diez repeticiones, con semillas de 42 a 51.

La validacion espacial utiliza GroupKFold sobre
seis grupos geograficos construidos mediante KMeans.

### Resultados del modelo definitivo

| Metrica | Convencional | Espacial |
|---|---:|---:|
| RMSE (t/ha) | 0.514672 | 0.699534 |
| R2 | 0.631662 | 0.319617 |

El RMSE espacial es aproximadamente 35.92 %
superior al RMSE convencional.

Esta diferencia sugiere una perdida de capacidad
de generalizacion bajo la particion espacial.

El RMSE convencional corresponde al promedio
de las diez repeticiones de validacion cruzada.

### Interpretacion y limitaciones

La validacion espacial evalua la transferencia
entre los grupos definidos por KMeans, pero no
garantiza generalizacion a cualquier nueva region.

Los resultados no certifican ausencia de fuga
temporal. La auditoria correspondiente se
documenta en P3.2.

La seleccion del modelo a partir de experimentos
de validacion puede introducir optimismo en las
metricas reportadas.

Las 59 parcelas sin rendimiento observado no
se utilizaron para calcular estas metricas.

### Referencias internas

- `ml/results/final_model_config.json`
- `docs/rol3/resultados_validacion_espacial_P3_3.md`
- `docs/rol3/politica_temporal_anti_leakage.md`
