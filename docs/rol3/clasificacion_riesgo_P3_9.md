# P3.9 - Clasificacion de riesgo y prioridades de revision

> **Guia de lectura (version actual):** las secciones iniciales
> describen resultados historicos exploratorios. Para la entrega
> definitiva, utilizar la seccion «Actualizacion del modelo
> definitivo yield-v1» y sus archivos `*_yield_v1`.


## Objetivo

Integrar las predicciones de rendimiento, las alertas de
detección OOD y los intervalos exploratorios de incertidumbre
en un único archivo para las 59 parcelas de Cebada360.

Establecer prioridades de revisión utilizando el nivel
relativo de rendimiento y las alertas OOD, manteniendo
los intervalos como información complementaria.

## Metodologia

### Clasificacion de rendimiento

Se utilizan los terciles de las predicciones
de las 59 parcelas.

Las categorias son:

- Bajo relativo.
- Intermedio relativo.
- Alto relativo.

Estas categorias son comparativas y no representan
umbrales agronomicos absolutos.

### Prioridades de revision

Las reglas son:

- Rendimiento bajo y alerta OOD:
  Prioridad alta de revision.
- Rendimiento bajo sin alerta OOD:
  Revisar rendimiento estimado.
- Alerta OOD sin rendimiento bajo:
  Revisar caracteristicas inusuales.
- Ninguna de las condiciones anteriores:
  Sin alerta combinada.

### Incertidumbre

Se integran los limites inferior y superior
calculados en P3.6.

El margen exploratorio es aproximadamente
0.8892 t/ha.

Estos intervalos no se utilizan para modificar
las prioridades porque tienen amplitud constante.

## Resultados

Parcelas procesadas: 59.
Columnas integradas: 14.
Valores faltantes: 0.
Identificadores duplicados: 0.

### Rendimiento relativo

- Bajo relativo: 20 parcelas.
- Intermedio relativo: 19 parcelas.
- Alto relativo: 20 parcelas.

### Prioridades de revision

- Prioridad alta de revision: 1 parcela.
- Revisar rendimiento estimado: 19 parcelas.
- Revisar caracteristicas inusuales: 2 parcelas.
- Sin alerta combinada: 37 parcelas.

### Deteccion OOD

- Con alerta OOD: 3 parcelas.
- Sin alerta OOD: 56 parcelas.

## Archivo integrado

El resultado final se encuentra en:

`ml/results/rol3/predicciones_riesgo_integrado_rol3.csv`

El archivo contiene:

- Identificador de parcela.
- Rendimiento predicho.
- Versión del modelo.
- Nivel relativo de rendimiento.
- Prioridad de revisión.
- Puntaje y alerta OOD.
- Interpretación de la alerta.
- Umbral OOD.
- Margen exploratorio de incertidumbre.
- Límites inferior y superior.
- Nivel nominal y método del intervalo.

## Verificaciones

Se comprobo que los archivos de clasificacion
e incertidumbre contienen las mismas 59 parcelas.

No existen identificadores duplicados ni
valores faltantes.

Las predicciones de ambos archivos coinciden
dentro de una tolerancia de 0.0001 t/ha.

## Limitaciones

Las prioridades no representan probabilidades
calibradas de perdida de rendimiento.

Los niveles relativos dependen de las
59 parcelas evaluadas.

Los intervalos son exploratorios y no garantizan
cobertura individual del 90 %.

La seguridad temporal de la matriz maestra
todavia no esta completamente certificada.

## Conclusion

Se completo la integracion de rendimiento,
prioridades de revision, deteccion OOD e
incertidumbre predictiva para 59 parcelas.

El resultado permite identificar parcelas
que requieren atencion adicional, sin
atribuir probabilidades de riesgo no validadas.

## Actualizacion del modelo definitivo yield-v1

### Integracion de resultados

Se integraron las 59 predicciones oficiales del modelo
yield-v1 con los resultados actualizados de:

- P3.6: intervalos exploratorios de incertidumbre.
- P3.8: deteccion OOD mediante Isolation Forest.

La integracion contiene 59 parcelas y 14 columnas,
sin duplicados ni valores faltantes.

Se verifico la coincidencia de los identificadores
y las predicciones entre los tres archivos de origen.

### Clasificacion relativa de rendimiento

Se conservaron las reglas originales basadas en
terciles de las 59 predicciones.

| Indicador | Valor |
|---|---:|
| Primer tercil | 3.210176 t/ha |
| Segundo tercil | 4.365824 t/ha |
| Bajo relativo | 21 parcelas |
| Intermedio relativo | 26 parcelas |
| Alto relativo | 12 parcelas |

Las cantidades no son iguales debido a la presencia
de valores de prediccion repetidos en los limites
de los terciles.

Estas categorias son relativas al conjunto evaluado
y no representan umbrales agronomicos absolutos.

### Prioridades de revision

Se mantuvieron las reglas originales de prioridad:

1. Rendimiento bajo y alerta OOD:
   prioridad alta de revision.
2. Rendimiento bajo sin alerta OOD:
   revisar rendimiento estimado.
3. Alerta OOD sin rendimiento bajo:
   revisar caracteristicas inusuales.
4. Ninguna condicion anterior:
   sin alerta combinada.

| Prioridad | Parcelas |
|---|---:|
| Prioridad alta de revision | 4 |
| Revisar rendimiento estimado | 17 |
| Revisar caracteristicas inusuales | 0 |
| Sin alerta combinada | 38 |
| Total | 59 |

### Parcelas con prioridad alta

| Parcela | Prediccion (t/ha) | Puntaje OOD |
|---|---:|---:|
| AGC_029 | 3.038316 | -0.668064 |
| AGC_061 | 3.067883 | -0.697110 |
| AGC_087 | 2.734081 | -0.664180 |
| AGC_120 | 2.734081 | -0.664180 |

Las cuatro parcelas con alerta OOD presentan
rendimiento bajo relativo y reciben prioridad alta.

No se identificaron parcelas OOD fuera del grupo
de rendimiento bajo relativo.

### Incertidumbre predictiva

Se integraron los intervalos exploratorios de P3.6:

- Nivel nominal: 90 %.
- Margen uniforme: 0.887987 t/ha.
- Ancho uniforme: 1.775974 t/ha.

Los intervalos son informacion complementaria.
No modifican las prioridades porque su amplitud
es constante para las 59 parcelas.

La cobertura descriptiva OOF no representa
una garantia de cobertura individual.

### Archivos generados

Script:
- `ml/rol3/clasificar_riesgo_yield_v1.py`

Resultados:
- `ml/results/rol3/riesgo_yield_v1/predicciones_riesgo_yield_v1.csv`
- `ml/results/rol3/riesgo_yield_v1/metadata_riesgo_yield_v1.json`

### Limitaciones

1. Los terciles dependen de las 59 parcelas evaluadas.
2. Las prioridades no representan probabilidades
   calibradas de perdida de rendimiento.
3. Las alertas OOD no confirman errores predictivos.
4. Los intervalos de P3.6 son exploratorios.
5. La auditoria P3.2 reprodujo las 30 variables climaticas
   de yield-v1, pero no certifica su disponibilidad operativa
   en la fecha de corte ni otras fuentes.
6. Las prioridades son criterios operativos de revision,
   no recomendaciones agronomicas validadas.

### Conclusion actualizada

P3.9 integra las predicciones, la incertidumbre
exploratoria y las alertas OOD del modelo yield-v1.

Se identificaron cuatro parcelas con prioridad alta,
17 para revision de rendimiento y 38 sin alerta combinada.

El archivo integrado permite priorizar revisiones
sin atribuir probabilidades de riesgo no validadas.
