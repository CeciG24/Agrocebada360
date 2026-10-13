\# Rol 3 — ML Avanzado, Riesgo y Explicabilidad



\## Proyecto Agrocebada360



Este módulo contiene el trabajo correspondiente al Rol 3 del proyecto Agrocebada360, enfocado en la evaluación avanzada de modelos de aprendizaje automático para estimar el rendimiento de cebada, analizar su incertidumbre, identificar predicciones atípicas y proporcionar herramientas de interpretación y clasificación de riesgo.



El trabajo se desarrolla a partir de los experimentos y resultados del Rol 2, sin modificar su implementación original.


**Rama de trabajo:** `ml-avanzado`

\*\*Estado:\*\* Resultados exploratorios P3.1–P3.9; integración final pendiente.



\## Objetivos



\- Evaluar la capacidad de generalización de los modelos mediante validación cruzada y espacial.

\- Establecer controles para evitar fugas de información temporal.

\- Comparar fuentes de información y grupos de variables predictoras.

\- Analizar la incertidumbre de las predicciones.

\- Interpretar modelos mediante valores SHAP.

\- Detectar observaciones fuera de distribución (OOD).

\- Clasificar parcelas según indicadores relativos de riesgo y prioridad de revisión.



\## Estructura del módulo



Los archivos del Rol 3 se organizan en tres ubicaciones del repositorio:



```text

Agrocebada360/

├── docs/

│   └── rol3/

│       ├── protocolo\_validacion\_P3\_1.md

│       ├── politica\_temporal\_anti\_leakage.md

│       ├── resultados\_validacion\_espacial\_P3\_3.md

│       ├── analisis\_sensores\_P3\_4.md

│       ├── ablacion\_variables\_P3\_5.md

│       ├── incertidumbre\_predictiva\_P3\_6.md

│       ├── explicabilidad\_shap\_P3\_7.md

│       ├── deteccion\_ood\_P3\_8.md

│       └── clasificacion\_riesgo\_P3\_9.md

├── ml/

│   ├── rol3/

│   │   ├── README.md

│   │   ├── analizar\_shap.py

│   │   ├── analizar\_shap\_x0.py

│   │   ├── recalcular\_ood\_rol3.py

│   │   ├── analizar\_ood.py

│   │   ├── revisar\_ood.py

│   │   └── clasificar\_parcelas\_rol3.py

│   └── results/

│       └── rol3/

│           ├── ablacion\_espacial\_P3\_5.csv

│           ├── predicciones\_intervalos\_rol3.csv

│           ├── predicciones\_clasificadas\_rol3.csv

│           ├── predicciones\_riesgo\_integrado\_rol3.csv

│           └── archivos SHAP y gráficas

```



\## Datos y metodología



Los análisis consideran 197 parcelas, de las cuales 138 cuentan con rendimiento observado para entrenamiento y evaluación, mientras que 59 corresponden al conjunto de predicción.



Se utilizaron resultados del Rol 2, incluyendo predicciones fuera de muestra (OOF), comparaciones entre modelos y experimentos con diferentes conjuntos de variables.



Las evaluaciones consideran validación cruzada convencional y validación espacial, reconociendo que ambas responden a preguntas diferentes sobre la generalización del modelo.



La política temporal establece el 31 de octubre de 2025 como fecha límite de información disponible para predicción. La conformidad temporal del modelo definitivo debe verificarse antes de la integración final.



\## Entregables



| Entregable | Descripción | Estado |

|---|---|---|

| P3.1 | Protocolo de validación | Documentado |

| P3.2 | Política temporal y prevención de leakage | Documentado |

| P3.3 | Validación espacial | Análisis exploratorio |

| P3.4 | Comparación de sensores y fuentes de información | Análisis exploratorio |

| P3.5 | Ablación de variables | Análisis exploratorio |

| P3.6 | Incertidumbre predictiva | Análisis provisional |

| P3.7 | Explicabilidad SHAP | Análisis provisional |

| P3.8 | Detección OOD | Análisis provisional |

| P3.9 | Clasificación relativa de riesgo | Análisis provisional |

| P3.10–P3.12 | Integración y cierre de entregables | Pendientes |



\## Resultados principales



\### Validación y selección de variables



Los resultados muestran diferencias entre el desempeño en validación convencional y espacial. Esto evidencia la importancia de evaluar los modelos bajo condiciones que consideren la dependencia geográfica de las parcelas.



Los experimentos de ablación permiten examinar cómo cambia el error al retirar grupos de variables, sin interpretar esas diferencias como efectos causales.



\### Incertidumbre predictiva



Se construyeron intervalos exploratorios alrededor de las predicciones del modelo de referencia.



La cobertura observada no debe interpretarse como una garantía estadística para datos futuros, ya que el procedimiento requiere validación y calibración adicionales.



\### Explicabilidad SHAP



Se generaron análisis de importancia y contribuciones SHAP para modelos Ridge utilizados como referencias exploratorias.



Estas explicaciones corresponden a los modelos específicos analizados; deberán actualizarse si el Rol 2 selecciona un modelo definitivo diferente.



\### Detección de datos fuera de distribución



Se utilizó Isolation Forest para identificar parcelas con características atípicas respecto al conjunto de entrenamiento.



En el análisis exploratorio, 3 de las 59 parcelas de predicción fueron marcadas como OOD.



\### Clasificación de riesgo



Se desarrolló una clasificación relativa de las 59 parcelas a partir de las predicciones y alertas OOD.



Los resultados integrados se encuentran en:



`ml/results/rol3/predicciones\_riesgo\_integrado\_rol3.csv`



Esta clasificación sirve para priorizar la revisión de parcelas. No representa una probabilidad calibrada de pérdida agrícola.



\## Dependencias y reproducción



El módulo depende de los datos y artefactos del flujo de ML del Rol 2. Para consultar las dependencias base, revisar:



`ml/requirements.txt`



Los scripts fueron desarrollados inicialmente en un directorio de experimentación separado. Antes de ejecutarlos directamente desde este repositorio, es necesario revisar sus rutas de entrada y salida, dependencias y referencias a artefactos locales.



Los CSV y las gráficas incluidos permiten consultar los resultados exploratorios sin ejecutar nuevamente todos los experimentos.



No se incluyen datasets privados ni modelos serializados locales.



\## Integración con Rol 2



El trabajo del Rol 3 utiliza como referencia los experimentos del Rol 2, pero mantiene sus propios scripts, documentos y resultados.



Una vez que el Rol 2 confirme el modelo definitivo, será necesario:



1\. Verificar la política temporal y la validación del modelo seleccionado.

2\. Actualizar los análisis de incertidumbre y explicabilidad que dependan de ese modelo.

3\. Revisar las alertas OOD y la clasificación de riesgo integradas.

4\. Completar los entregables P3.10–P3.12.

5\. Validar la consistencia de los archivos finales antes de integrarlos al proyecto.



\## Limitaciones



Los resultados actuales son exploratorios y no constituyen una evaluación final del sistema en producción.



Las métricas observadas, los intervalos, las explicaciones SHAP y las categorías de riesgo deben interpretarse dentro de las condiciones experimentales documentadas.



\*\*Estado del módulo:\*\* Disponible para revisión técnica en la rama `ml-avanzado`, pendiente de consolidación con el modelo definitivo.
