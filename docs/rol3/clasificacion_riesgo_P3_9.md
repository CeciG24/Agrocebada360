# P3.9 - Clasificacion de riesgo y prioridades de revision

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
