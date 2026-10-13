# P3.6 - Incertidumbre predictiva

## Objetivo

Cuantificar la incertidumbre de las predicciones
de rendimiento de cebada mediante intervalos
exploratorios basados en residuos OOF.

## Modelo utilizado

- Experimento: E5_fusion
- Algoritmo: Ridge
- Version de predicciones: baseline_v0
- Parcelas de entrenamiento: 138
- Parcelas de prediccion: 59

## Metodologia

Se calcularon los residuos absolutos entre los
rendimientos reales y las predicciones OOF.

Se utilizo un cuantil de los residuos con
correccion de muestra finita para calcular
un margen exploratorio al nivel nominal del 90 %.

Los intervalos se construyeron sumando y restando
el mismo margen a cada prediccion.

## Resultados

- Margen exploratorio: 0.889187 t/ha
- Ancho del intervalo: 1.7784 t/ha
- Cobertura descriptiva OOF: 91.30 %
- Parcelas cubiertas OOF: 126 de 138

## Diagnostico adicional

Se dividieron aleatoriamente los 138 residuos OOF:

- Calibracion: 96 residuos
- Prueba: 42 residuos
- Margen calibrado: 0.8892 t/ha
- Cobertura observada: 90.48 %
- Errores cubiertos: 38 de 42

Esta prueba es exploratoria porque la division
se realizo despues de generar las predicciones
OOF mediante validacion cruzada.

No representa una validacion conformal independiente.


La cobertura observada sobre los residuos OOF es
descriptiva y no constituye una garantia de cobertura
para nuevas parcelas.

Aunque se aplico una correccion de muestra finita,
no se han demostrado las condiciones necesarias para
afirmar una garantia conformal de cobertura del 90 %.


## Verificacion de predicciones

El archivo de intervalos contiene:

- 59 parcelas
- 0 valores faltantes
- 0 identificadores duplicados
- Margen uniforme de 0.889187 t/ha

## Limitaciones

1. Los intervalos utilizan un margen constante
   para todas las parcelas.

2. No se ha demostrado cobertura del 90 %
   sobre parcelas nuevas independientes.

3. No se ha validado la cobertura en grupos
   espaciales no vistos.

4. La matriz maestra original no esta
   certificada contra fuga temporal.

5. Los intervalos no deben interpretarse
   como garantias individuales de rendimiento.


## Archivos relacionados

### Scripts

- `ml/rol3/calcular_intervalos_rol3.py` (pendiente de incorporar al repositorio)
- `ml/make_baseline_predictions.py` (Rol 2)

### Resultados

- `ml/results/oof/E5_fusion__ridge.csv`
- `ml/results/predictions_raw.csv`
- `ml/results/rol3/predicciones_intervalos_rol3.csv`

### Documentación

- `docs/rol3/politica_temporal_anti_leakage.md`
- `docs/rol3/resultados_validacion_espacial_P3_3.md`


## Estado

P3.6: intervalos exploratorios implementados,
verificados y documentados.

Pendiente: validacion independiente, espacial
y temporal para su uso como intervalos finales.

## Validacion espacial de intervalos

Se realizo una evaluacion exploratoria mediante
GroupKFold de 5 particiones sobre 138 parcelas.

En cada fold se separaron grupos geograficos
para entrenamiento, calibracion y prueba.

Modelo utilizado: E5_fusion + Ridge.
Nivel nominal: 90 %.

### Resultados

| Fold | Entrenamiento | Calibracion | Prueba | Margen t/ha | Cobertura |
|---|---:|---:|---:|---:|---:|
| 1 | 63 | 34 | 41 | 1.4586 | 97.56 % |
| 2 | 91 | 13 | 34 | 0.7199 | 79.41 % |
| 3 | 82 | 34 | 22 | 1.0271 | 86.36 % |
| 4 | 87 | 34 | 17 | 1.2662 | 70.59 % |
| 5 | 80 | 34 | 24 | 1.2364 | 100.00 % |

### Resumen

- Parcelas evaluadas: 138.
- Parcelas cubiertas: 122.
- Cobertura espacial global: 88.41 %.
- Cobertura nominal: 90 %.
- Diferencia: -1.59 puntos porcentuales.

### Interpretacion

La cobertura global se aproxima al nivel nominal,
pero existe variabilidad importante entre folds.

El Fold 4 obtuvo la cobertura mas baja, 70.59 %.

Los margenes tambien presentan variaciones
considerables entre grupos geograficos.

### Limitaciones

Esta evaluacion no garantiza cobertura del 90 %
en regiones nuevas.

La calibracion utiliza un numero limitado de
grupos espaciales y depende de su seleccion.

Los experimentos utilizan features_master.csv,
cuya seguridad temporal no ha sido certificada.

Los resultados deben considerarse exploratorios
hasta realizar la validacion temporal definitiva.
