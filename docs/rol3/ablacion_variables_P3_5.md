# P3.5 - Ablacion de familias de variables

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
