# Evidencia real en la página Modelo

La vista `/modelo?demo=0` usa una ficha de validación versionada, generada desde los resultados de ML auditados: `frontend/src/data/model/model-evidence.json`. La fuente de las métricas es el reporte de desarrollo, no un endpoint de métricas inexistente. No se cambian endpoints, schemas HTTP ni lógica del backend.

La ficha se inyecta al repositorio del frontend desde `data/index.js`. Antes de mostrarla, `getMetricasModelo()` consulta únicamente `/predict/{id}` para una parcela de referencia ya incluida en la ficha. Comprueba versión del modelo, unidad, ciclo, corte, versión del contrato y valor predicho, con tolerancia absoluta `1e-8`. Si no coincide, muestra un error y oculta las métricas. La API mock no recibe las métricas reales; el modo demo conserva su repositorio sintético.

Esta comprobación de compatibilidad **no certifica el SHA256 del modelo servido**, porque el contrato público no expone ese hash. La ficha sí registra el hash del modelo documentado y los hashes de sus fuentes. Un cambio de modelo o evidencia exige regenerarla y volver a validar el paquete.

## Contenido

- Ridge `yield-v1`, 30 variables climáticas, 138 parcelas etiquetadas y 59 de evaluación.
- RMSE 0.5146722580 t/ha, MAE 0.3560961583 t/ha, R² 0.6316622492: medias de validación aleatoria por repetición.
- RMSE espacial 0.6995342421 t/ha y R² espacial 0.3196173031: diagnóstico GroupKFold de cinco folds sobre seis grupos KMeans de centroides.
- Gráfica con 138 pares observados/OOF y tabla desplegable accesible. El CSV OOF contiene el promedio de las predicciones fuera de fold entre diez repeticiones. No son predicciones ajustadas sobre el entrenamiento ni resultados del conjunto oculto. Las tarjetas no se recalculan desde esos promedios, porque su agregación estadística es diferente.
- Seis variables destacadas por media del impacto absoluto SHAP, más el listado de las 30 variables con sus nombres técnicos, unidades de entrada, definiciones y ventanas. Las importancias se calculan sobre las 59 parcelas de evaluación; no son efectos causales y pueden repartirse entre variables correlacionadas.
- Fuente climática, contexto histórico ambiental y limitaciones de generalización. El modelo final no utiliza satélites ni topografía como entradas, aunque se hayan explorado durante el desarrollo.

## Regenerar

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe scripts/build_model_evidence.py --data-root data/integrated/verified-2026-10-17/data
```

El generador no deserializa ni entrena modelos. Verifica el hash del joblib y schema, la selección E4_clima/Ridge, el dataset y las etiquetas, la consistencia de métricas con el leaderboard y el protocolo, los IDs OOF frente a la partición etiquetada y sus targets conocidos. También verifica la identidad de modelo/datos de SHAP, su reconstrucción de las predicciones publicadas y las importancias contra la media absoluta de las contribuciones originales. Rechaza valores no finitos o fuentes incompatibles. Los metadatos históricos de ML que no están en UTF-8 se leen explícitamente como CP1252; sus bytes originales no se modifican.

La página distingue validación interna del resultado oficial de evaluación, muestra la limitación espacial y conserva el modo demo identificado. Las tablas desplegables permiten consultar los puntos y variables con teclado; se verificó una vista móvil de 390 px sin overflow.

## Verificación

- 25 pruebas de frontend: regresión de API y rechazo de modelo, predicción, unidad, ID o contexto incompatibles; ausencia de métricas reales en API mock.
- 4 pruebas de la ficha: regeneración exacta, rechazo de target OOF alterado, ID de evaluación introducido en OOF y SHAP de otro modelo.
- Lint y compilación de producción.
- Chrome con API real: métricas, 138 puntos, 30 variables, tablas desplegables, escritorio/móvil, rechazo simulado de otro modelo y separación de demo.

La evidencia está en [model-view-acceptance-2026-10-18.json](model-view-acceptance-2026-10-18.json). Los hashes de fuentes están en la propia ficha. Se conserva el contrato HTTP 0.1.0.
