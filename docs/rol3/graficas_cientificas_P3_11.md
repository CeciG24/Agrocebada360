# P3.11 - Graficas cientificas finales

## Objetivo

Presentar visualmente los resultados de validacion,
explicabilidad y prediccion temprana asociados
al proyecto Agrocebada360.

Las graficas distinguen los resultados del
experimento E4_clima Ridge, el modelo congelado
yield-v1 y los experimentos early-v2.

## 1. Predicho frente a real

Archivo:
ml/results/rol3/graficas_yield_v1/01_predicho_vs_real.png

Fuente:
ml/results/oof/E4_clima__ridge.csv

Se comparan los rendimientos reales y las
predicciones fuera de muestra (OOF) de 138 parcelas.

- RMSE OOF agregado: 0.512451 t/ha.
- MAE OOF agregado: 0.353605 t/ha.

Estas metricas se calculan sobre las predicciones
OOF agregadas y no sustituyen las metricas
oficiales de validacion repetida.

## 2. Analisis de residuos

Archivo:
ml/results/rol3/graficas_yield_v1/02_residuos.png

Fuente:
ml/results/oof/E4_clima__ridge.csv

Los residuos se calculan como:

Residuo = rendimiento real - prediccion OOF.

La linea horizontal representa el error cero.

La grafica permite examinar visualmente
posibles patrones de error, sesgo y dispersion.

No constituye por si sola una prueba formal
de normalidad u homocedasticidad.

## 3. Importancia SHAP

Archivo:
ml/results/rol3/graficas_yield_v1/03_importancia_shap.png

Fuente:
ml/results/rol3/shap_yield_v1/shap_importancia_yield_v1.csv

Se representan las 12 variables con mayor
importancia SHAP media absoluta del modelo
congelado yield-v1.

La importancia expresa contribuciones al
comportamiento predictivo del modelo.

No debe interpretarse como causalidad.

## 4. RMSE temporal

Archivo:
ml/results/rol3/graficas_yield_v1/04_rmse_temporal_early_v2.png

Fuente:
ml/results/early/early_leaderboard.csv

Se representa el RMSE convencional de
Ridge, ExtraTrees y CatBoost en cinco cortes:

- Junio de 2025.
- Julio de 2025.
- Agosto de 2025.
- Septiembre de 2025.
- Octubre de 2025.

Los experimentos early-v2 utilizan
27 variables y no corresponden a
reevaluaciones temporales de yield-v1.

El menor RMSE convencional de los tres
algoritmos se obtuvo con ExtraTrees
en julio: 0.527159 t/ha.

El baseline Ridge por municipio obtuvo
RMSE 0.507552 t/ha y supero a los
tres algoritmos en estos experimentos.

## 5. Reproducibilidad

Script:
ml/rol3/generar_graficas_P3_11.py

Comando:

python ml/rol3/generar_graficas_P3_11.py

Directorio de salida:

ml/results/rol3/graficas_yield_v1/

El script utiliza resultados existentes.
No reentrena ni modifica el modelo congelado.

## 6. Limitaciones

- Las graficas OOF no muestran el rendimiento
  real de las 59 parcelas de prediccion.
- La importancia SHAP puede verse afectada
  por correlaciones entre variables.
- El RMSE temporal corresponde a early-v2,
  no al modelo definitivo yield-v1.
- La validacion final de consistencia
  se realizara en P3.12.

## Conclusion

Las cuatro graficas permiten comunicar
los resultados de evaluacion, errores,
explicabilidad y prediccion temprana,
manteniendo la trazabilidad de sus fuentes.
