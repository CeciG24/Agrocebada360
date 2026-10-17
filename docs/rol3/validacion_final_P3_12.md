# P3.12 - Validacion final de resultados

## Objetivo

Verificar la consistencia de los intervalos,
explicaciones SHAP, alertas y graficas
asociadas al modelo congelado yield-v1.

## 1. Resultado automatico

- Estado: APROBADO.
- Verificaciones ejecutadas: 43.
- Verificaciones correctas: 43.
- Errores detectados: 0.
- Parcelas de prediccion: 59.
- Variables del modelo: 30.

## 2. Identidad del modelo

Se verifico la existencia y el SHA-256
del archivo yield_model_v1.joblib.

La configuracion oficial identifica:

- Modelo: yield-v1.
- Experimento: E4_clima.
- Algoritmo: Ridge.
- Variables climaticas: 30.

## 3. Consistencia de predicciones

Los archivos de intervalos, OOD y riesgo
contienen las mismas 59 parcelas que
predictions_raw.csv.

Las predicciones coinciden numericamente
con las oficiales dentro de la tolerancia
de la validacion.

## 4. Intervalos predictivos

Se comprobaron:

- Limites inferiores.
- Limites superiores.
- Margen exploratorio.
- Nivel nominal del 90 %.

La consistencia aritmetica no demuestra
cobertura independiente ni garantiza
el comportamiento sobre datos futuros.

## 5. Explicabilidad SHAP

Se comprobaron:

- 59 registros.
- 30 contribuciones por parcela.
- Aditividad de las contribuciones.
- Reconstruccion de predicciones oficiales.
- Correspondencia de variables de importancia.

SHAP explica el comportamiento predictivo
del modelo y no establece causalidad.

## 6. OOD y riesgo

Se verifico la coherencia entre:

- Alertas OOD.
- Puntuaciones OOD.
- Umbrales OOD.
- Intervalos incorporados al reporte de riesgo.

Las alertas indican prioridad de revision,
no errores confirmados ni probabilidades
de perdida agricola.

## 7. Graficas cientificas

Se verifico la existencia de:

1. Predicho frente a real.
2. Residuos.
3. Importancia SHAP.
4. RMSE temporal early-v2.

La comprobacion automatica verifica
existencia y tamaño minimo de los archivos.

No certifica por si sola la interpretacion
visual ni todos los elementos de las figuras.

Las graficas OOF corresponden al experimento
E4_clima Ridge.

La curva temporal corresponde a early-v2,
un experimento independiente del modelo
congelado yield-v1.

## 8. Trazabilidad

Script de validacion:

ml/rol3/validar_resultados_P3_12.py

Reporte JSON:

ml/results/rol3/validacion_final_yield_v1/reporte_validacion_P3_12.json

Configuracion oficial:

ml/results/final_model_config.json

Predicciones oficiales:

ml/results/predictions_raw.csv

## 9. Limitaciones

- No existe rendimiento observado para
  las 59 parcelas de prediccion.
- Los intervalos son exploratorios.
- El modelo presenta deterioro en
  validacion espacial.
- La prediccion temprana no representa
  una evaluacion temporal de yield-v1.
- La ablacion historica corresponde a E5_fusion;
  tambien se ejecuto una ablacion directa de las
  30 variables de yield-v1 (P3.5).
- La inspeccion visual de las cuatro graficas se
  realizo posteriormente a la validacion automatica;
  no sustituye la verificacion cientifica de sus datos.

## Conclusion

Las 43 verificaciones automaticas
se completaron correctamente.

Los resultados derivados del Rol 3
son consistentes con las predicciones
oficiales y la identidad del modelo
congelado yield-v1, dentro del alcance
de las comprobaciones realizadas.
