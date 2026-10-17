# P3.10 - Consolidacion de resultados tecnicos

## 1. Objetivo

Consolidar los resultados de validacion, explicabilidad,
incertidumbre, prediccion temprana y ablacion del Rol 3.

Se distinguen los resultados del modelo definitivo
yield-v1 y los experimentos exploratorios del Rol 2.

## 2. Modelo definitivo

- Version: yield-v1.
- Experimento: E4_clima.
- Algoritmo: Ridge.
- Variables: 30 climaticas.
- Parcelas etiquetadas: 138.
- Parcelas de prediccion: 59.
- Dataset: sha256:b045a212af57282a.
- Corte temporal: 2025-10-31.

## 3. Validacion

| Metrica | Resultado |
|---|---:|
| RMSE convencional | 0.514672 |
| MAE convencional | 0.356096 |
| R2 convencional | 0.631662 |
| RMSE espacial | 0.699534 |
| R2 espacial | 0.319617 |

El error espacial es mayor que el convencional.
Esto indica una limitacion de generalizacion geografica.

## 4. Incertidumbre predictiva

Se calcularon intervalos exploratorios para
las 59 parcelas de prediccion.

- Nivel nominal: 90 %.
- Margen: 0.887987 t/ha.
- Amplitud total: 1.775974 t/ha.
- Cobertura descriptiva sobre OOF: 126/138, 91.3 %.

La cobertura descriptiva no constituye una
garantia independiente de cobertura futura.

Fuente:
ml/results/rol3/intervalos_yield_v1/

## 5. Explicabilidad SHAP

Se utilizo SHAP LinearExplainer para explicar
las 59 predicciones del modelo definitivo.

Variables con mayor importancia global media
en valor absoluto:

| Variable | Media absoluta SHAP |
|---|---:|
| precip_mean_mm_2025 | 0.28648 |
| precip_total_mm_2025 | 0.28648 |
| precip_mean_mm_2023 | 0.24461 |
| precip_total_mm_2023 | 0.24461 |
| amplitud_termica_std_c_2023 | 0.14420 |

Las variables de precipitacion total y media
pueden estar altamente correlacionadas.

Los valores SHAP describen el comportamiento
del modelo, no efectos causales.

Fuente:
ml/results/rol3/shap_yield_v1/

## 6. Deteccion de datos fuera de distribucion

Se utilizo IsolationForest sobre las
30 variables climaticas.

- Parcelas de prediccion: 59.
- Alertas OOD: 4.
- Proporcion: 6.78 %.

Parcelas identificadas:

- AGC_029.
- AGC_061.
- AGC_087.
- AGC_120.

Estas alertas indican observaciones inusuales
respecto a los datos de entrenamiento.

No demuestran que las predicciones sean incorrectas.

Fuente:
ml/results/rol3/ood_yield_v1/

## 7. Clasificacion operativa de riesgo

La clasificacion combina rendimiento predicho
y alertas OOD.

- Prioridad alta de revision: 4 parcelas.
- Revision por rendimiento relativo bajo: 17.
- Sin alerta combinada: 38.

Los niveles son relativos al conjunto evaluado.
No representan probabilidades de perdida agricola.

Fuente:
ml/results/rol3/riesgo_yield_v1/

## 8. Prediccion temprana

Se incorporan los resultados exploratorios
early-v2 del Rol 2.

| Corte | Ridge | ExtraTrees | CatBoost |
|---|---:|---:|---:|
| Junio | 0.574562 | 0.537184 | 0.549248 |
| Julio | 0.560584 | 0.527159 | 0.540942 |
| Agosto | 0.568167 | 0.529109 | 0.539487 |
| Septiembre | 0.574621 | 0.531353 | 0.556567 |
| Octubre | 0.563297 | 0.535483 | 0.553765 |

Los valores representan RMSE convencional en t/ha.

Los experimentos utilizan 27 variables y
no corresponden al modelo congelado yield-v1.

Los tres algoritmos superaron al baseline
Dummy desde junio, pero no al baseline
Ridge por municipio.

Fuentes:
ml/results/early/early_leaderboard.csv
ml/results/early/early_summary.json

## 9. Ablacion de variables

Se conserva el experimento exploratorio
E5_fusion Ridge con 207 variables.

| Configuracion | RMSE espacial |
|---|---:|
| Fusion completa | 0.692060 |
| Sin clima | 0.815060 |
| Sin Sentinel-2 | 0.758621 |
| Sin Landsat | 0.678701 |

La eliminacion del clima produjo el mayor
incremento de error espacial.

Estos resultados historicos de E5_fusion no constituyen
una ablacion directa de yield-v1. La ablacion directa
de yield-v1 se presenta en la actualizacion al final.

Fuente:
ml/results/rol3/ablacion_espacial_P3_5.csv

## 10. Auditoria temporal

Las 30 variables climaticas de yield-v1
se reprodujeron utilizando registros
hasta el 31 de octubre de 2025.

- Comparaciones: 5910.
- Coincidencias: 5910.
- Diferencias: 0.

La auditoria no demuestra por si sola
la disponibilidad operativa de cada registro
en la fecha de corte.

## 11. Limitaciones generales

- El rendimiento espacial es inferior al convencional.
- Los intervalos son exploratorios.
- SHAP no demuestra causalidad.
- Las alertas OOD no equivalen a errores confirmados.
- La prediccion temprana corresponde a early-v2.
- La ablacion original corresponde a E5_fusion.
- No se dispone de rendimiento real para las
  59 parcelas reservadas para prediccion.

## 12. Conclusion

El Rol 3 integra validacion espacial,
incertidumbre, explicabilidad y alertas
operativas para el modelo yield-v1.

Los experimentos complementarios permiten
contextualizar el desempeno del modelo,
sin confundirlos con sus metricas oficiales.

La validacion final de consistencia se realizo en P3.12:
43 verificaciones aprobadas y cero errores.

## Actualizacion: ablacion climatica del modelo yield-v1

Se evaluaron seis configuraciones del experimento E4_clima
Ridge mediante el protocolo oficial de validacion.

| Variante | Variables | RMSE | RMSE espacial |
|---|---:|---:|---:|
| Completo | 30 | 0.514672 | 0.699534 |
| Sin precipitacion | 20 | 0.522794 | 0.745227 |
| Sin temperaturas | 20 | 0.521024 | 0.646792 |
| Sin amplitud termica | 20 | 0.518974 | 0.730090 |
| Sin variables anuales de 2025 | 18 | 0.520768 | 0.748133 |
| Sin agregados multianuales | 24 | 0.514632 | 0.697256 |

La eliminacion de temperaturas redujo el RMSE espacial
en 0.052742 t/ha, aunque empeoro el RMSE convencional.

La eliminacion de agregados multianuales produjo
diferencias muy pequenas.

La variante sin variables anuales especificas de 2025
conserva agregados multianuales que incluyen dicho a?o.

Estos resultados son diagnosticos y no justifican
modificar automaticamente el modelo congelado.

Fuente:
ml/results/rol3/ablacion_yield_v1/ablacion_climatica_yield_v1.csv

Script:
ml/rol3/ablacion_climatica_yield_v1.py
