# System Contract — Cebada360

Versión: `0.3.0`
Estado: **Revisado contra las Bases de Participación y la Segunda sesión de preguntas y respuestas de FIRA (9 de octubre de 2026)**

Este documento define los contratos internos entre los componentes y roles de Cebada360.
No sustituye la convocatoria ni las aclaraciones oficiales de FIRA.

Para endpoints públicos consultar `docs/api-contract.md`.

---

# 0. Jerarquía de fuentes y reglas de interpretación

Cuando exista una contradicción, se utilizará este orden de autoridad:

1. **Bases de Participación del Reto AgroCebada FIRA 2026**.
2. **Aclaraciones oficiales del Comité Organizador/FIRA** enviadas por correo, plataforma o sesión de preguntas.
3. **Dataset oficial, diccionario de datos e información complementaria** publicada en la plataforma.
4. **Este System Contract y demás documentos internos del equipo**.
5. Suposiciones de implementación.

Una regla interna nunca debe presentarse como requisito de FIRA si no aparece en una fuente oficial.

Si una fuente oficial posterior contradice este documento, se debe actualizar el contrato antes de continuar la integración.

---

# 1. Hechos oficiales del reto relevantes al sistema

De acuerdo con las Bases:

- El objetivo es **predecir el rendimiento agrícola de parcelas de cebada** en Hidalgo, Tlaxcala y Puebla y convertir el modelo en una solución tecnológica funcional.
- El dataset oficial contiene **197 parcelas georreferenciadas**.
- FIRA proporciona variables asociadas como índices de vegetación, precipitación, temperatura y rendimiento del cultivo.
- El rendimiento se proporciona para aproximadamente el **70 %** de las parcelas y debe estimarse para el **30 %** restante.
- Los participantes **pueden utilizar otra información de acceso público que consideren pertinente**.
- La evaluación de la primera etapa pondera:
  - **70 % desempeño predictivo y justificación técnica**.
  - **30 % aplicación o interfaz web**.
- El prototipo debe permitir ejecutar el modelo y consultar resultados de manera interactiva.
- Deben entregarse el código fuente de la aplicación y del modelo, con documentación de ejecución.
- Debe entregarse un video demostrativo de máximo 5 minutos.
- Si se utiliza IA, debe indicarse dónde se utilizó y anexarse los prompts en el escrito.
- El reporte técnico debe incluir en anexos las actividades y aportaciones de cada integrante.

## 1.1 Aclaraciones oficiales de la segunda sesión (9 de octubre de 2026)

FIRA aclaró para el ciclo evaluado que:

- el ciclo corresponde a **abril–octubre de 2025** y las parcelas se cultivaron bajo condiciones de **temporal**;
- no se dispone de fecha exacta de siembra por parcela; solo se mencionó como referencia el inicio de siembra en los primeros días de mayo, sujeto a variación por clima y prácticas locales;
- el target es **rendimiento de grano por parcela**, expresado en **toneladas por hectárea (t/ha)**;
- para el conjunto de predicción se debe reportar **un valor puntual por parcela, en t/ha y con cuatro decimales**; la incertidumbre puede explicarse como complemento metodológico;
- cada rendimiento observado corresponde específicamente a la parcela asociada;
- las parcelas de entrenamiento fueron seleccionadas mediante **muestreo aleatorio estratificado**;
- no se cuenta con el historial de cultivos por parcela para 2022–2024; por tanto, no debe asumirse que la parcela tuvo cebada en esos años;
- los polígonos fueron delimitados mediante distintos métodos (puntos de campo/reportados por productor, procesamiento por proveedores externos y validación satelital);
- no se cuenta actualmente con dosis de siembra por parcela ni registros parcelarios de siniestros/pérdidas parciales de 2025;
- durante el ciclo se utilizaron principalmente las variedades Josefa y Voyager, pero **no existe identificación de variedad por parcela**, por lo que no puede tratarse como feature parcelaria oficial;
- la aplicación debe, además de mostrar la predicción, **identificar de forma sencilla los principales factores que influyen en el resultado** y producir información útil para decisiones oportunas del productor.

## 1.2 Elementos que siguen sin estar definidos de forma autoritativa

Ni las Bases ni esta sesión fijan por sí solas:

- un corte diario exacto como `2025-10-31` (el ciclo sí está confirmado como abril–octubre de 2025);
- el nombre exacto de la columna ID;
- el CRS de las geometrías;
- el formato exacto y nombres de columnas del CSV de predicción;
- el nombre exacto del archivo CSV;
- el correo o mecanismo adicional para enviar predicciones;
- la definición de `region`;
- una metodología obligatoria de SHAP, intervalos o riesgo;
- una arquitectura backend/frontend específica.

Estos puntos deben obtenerse del dataset, documentación complementaria u otras aclaraciones oficiales. Si no están confirmados, deben permanecer marcados como `PENDIENTE`.

---

# 2. Política temporal y uso de datos históricos

Esta sección reemplaza la antigua regla ambigua:
> “No se usarán datos posteriores al 2025-10-31 para el modelo del ciclo abril–octubre 2025.”

## 2.1 Ciclo objetivo

El equipo está modelando el rendimiento correspondiente al ciclo objetivo **abril–octubre de 2025**, según la aclaración oficial recibida por el equipo.

Esta precisión debe conservarse junto con la evidencia de la aclaración oficial (correo, plataforma o minuta).
**No debe atribuirse a las Bases si no aparece literalmente en ellas.**

## 2.2 Datos permitidos como features

Se permite utilizar:

- datos del ciclo objetivo 2025 hasta el límite temporal válido;
- datos históricos anteriores a 2025;
- información pública externa pertinente;
- variables estáticas o históricas de la parcela, cuando sean válidas metodológicamente.

Ejemplos de información histórica potencialmente válida:

- climatología 2022–2024;
- índices satelitales históricos como contexto de superficie/vegetación;
- promedios o variabilidad interanual;
- topografía;
- elevación;
- características geoespaciales.

**Restricción semántica importante:** FIRA aclaró que no se cuenta con historial de cultivos por parcela para 2022–2024. Por ello, los datos históricos de esos años **no deben interpretarse como comportamiento histórico de cebada** ni como fenología de cebada, salvo que una fuente externa documentada permita identificar el cultivo. Pueden utilizarse como contexto ambiental o de cobertura, si la metodología lo justifica.

Esto es consistente con las Bases, que permiten utilizar otra información de acceso público.

## 2.3 Regla anti-leakage

Una feature utilizada para predecir el rendimiento del ciclo 2025 **no puede utilizar información que solamente estaría disponible después del momento/ciclo que se pretende predecir**.

Para el modelo de cierre del ciclo abril–octubre 2025, el equipo adopta como límite operativo:

```text
prediction_information_cutoff = 2025-10-31
```

El **mes de cierre (octubre de 2025) sí está confirmado oficialmente**. El día `31` se usa como convención técnica para representar el fin de ese mes; no debe citarse como una fecha diaria especificada por FIRA.

Por lo tanto:

- datos de 2022–2024: permitidos como contexto histórico;
- datos de abril–octubre 2025: permitidos para el modelo de cierre;
- datos posteriores al cierre del ciclo: no deben utilizarse para construir las features del modelo de ese ciclo;
- información del target o derivada del target de las parcelas de evaluación: prohibida.

## 2.4 Muestras supervisadas vs. features históricas

Debe distinguirse entre:

### Muestras de entrenamiento
Parcelas que cuentan con un rendimiento observado correspondiente al ciclo objetivo.

### Features históricas
Información de años previos utilizada para caracterizar una parcela.

Usar datos de 2022, 2023 o 2024 como features **no convierte automáticamente esos años en nuevas muestras supervisadas**.

Solo se puede tratar un año histórico como una observación adicional de entrenamiento si existe un rendimiento observado para esa misma parcela/ciclo y la metodología define explícitamente una estructura panel/longitudinal.

## 2.5 Fecha de siembra y alineación temporal

FIRA no dispone de la fecha exacta de siembra por parcela. Se mencionaron los primeros días de mayo únicamente como referencia general.

Por lo tanto:

- no crear una feature de `planting_date` parcelaria usando una fecha única inventada;
- no alinear series temporales a “días desde siembra” como si la fecha fuera observada;
- si se usa una fecha de referencia común para un experimento, debe etiquetarse explícitamente como aproximación y evaluarse su sensibilidad;
- preferir ventanas calendario o fenológicas derivadas de la señal cuando sea metodológicamente justificable.

## 2.6 Modelo final

La selección de features, algoritmo e hiperparámetros debe realizarse mediante validación usando únicamente las parcelas etiquetadas.

Una vez congelada la configuración:

1. se reentrena el modelo final con **todas las parcelas oficiales etiquetadas disponibles**;
2. se generan predicciones para el conjunto oficial de evaluación;
3. el conjunto de evaluación nunca se utiliza para tuning o selección del modelo.

No se debe hardcodear `138` o `59` como verdad contractual.
Esas cantidades pueden corresponder al split actual, pero el código debe validar contra la lista oficial de IDs entregada por FIRA.

---

# 3. Principios generales de integración

1. Cada equipo entrega artefactos explícitos.
2. Ningún componente infiere silenciosamente estructuras no acordadas.
3. No se inventan columnas, features, unidades, regiones, targets ni políticas de faltantes.
4. Todo artefacto debe estar versionado.
5. Los IDs de parcela se tratan como cadenas opacas y se preservan exactamente.
6. Mock y real permanecen separados.
7. El backend no reentrena modelos durante una petición.
8. El frontend no redefine la lógica estadística o de ML.
9. Los artefactos deben ser reproducibles desde código y documentación.
10. Las decisiones internas deben distinguirse de los requisitos oficiales del reto.
11. Toda fuente externa utilizada debe documentarse para la justificación técnica.
12. Cualquier cambio que afecte el significado de un artefacto requiere actualizar este contrato.

---

# 4. Flujo general

```text
Datos oficiales + fuentes públicas documentadas
    ↓
Data / ETL
    ↓
features_master
    ↓
Modelado predictivo
    ↓
modelo final
    ↓
ML avanzado
    ├── intervalos (si se implementan)
    ├── SHAP / explicabilidad
    └── riesgo productivo (si se implementa)
    ↓
Backend
    ↓
API
    ↓
Frontend / prototipo funcional
```

Flujo de predicciones para evaluación:

```text
modelo final congelado
    ↓
IDs oficiales de evaluación
    ↓
predicciones
    ↓
validador del formato oficial
    ↓
archivo de entrega
```

El formato final debe seguir la instrucción oficial más reciente de FIRA, no una suposición del repositorio.

---

# 5. Contrato Data → Modelado / Backend

Data debe producir un dataset reproducible con una fila por parcela para el modelo de cierre, salvo que el equipo acuerde explícitamente otra granularidad.

Artefacto sugerido:

```text
data/processed/features_master.parquet
```

o:

```text
data/processed/features_master.csv
```

## 5.1 Identificador

La columna real del ID debe confirmarse con el dataset oficial.

Dentro del sistema puede normalizarse mediante un alias interno:

```text
parcel_id
```

pero debe existir un mapeo documentado entre el nombre oficial y el nombre interno.

Reglas:

- tratar como string;
- no eliminar ceros iniciales;
- no modificar contenido;
- único por parcela en `features_master`;
- no nulo;
- consistente con el catálogo y el conjunto de evaluación.

## 5.2 Target

El target oficial es **rendimiento de grano por parcela**, en **toneladas por hectárea (t/ha)**. El nombre físico de la columna en el dataset aún debe confirmarse con el diccionario/archivo oficial.

Cada rendimiento corresponde específicamente a la parcela con la que está asociado. FIRA indicó que la mayoría de los valores fueron reportados por la empresa comercializadora y una proporción menor directamente por el productor; esta heterogeneidad de fuente debe documentarse como posible fuente de ruido de medición, no “corregirse” sin evidencia.

Nunca incluir el target como feature.

Para las parcelas de evaluación, el rendimiento real no debe existir ni reconstruirse a partir de fuentes no autorizadas.

## 5.3 Features

Cada feature debe incluir, como mínimo, metadata técnica suficiente para conocer:

- nombre;
- fuente;
- sensor o dataset de origen;
- ventana temporal;
- transformación/agregación;
- política de faltantes;
- si utiliza información histórica;
- fecha máxima de información utilizada cuando aplique.

Esto permite demostrar que no existe leakage temporal y facilita la justificación técnica.

## 5.4 Datos históricos

Si se crean features a partir de varios años:

- la agregación debe documentarse;
- no deben mezclarse fechas sin conservar la semántica temporal;
- debe ser posible reconstruir qué periodos alimentan cada feature;
- debe probarse empíricamente si el histórico mejora la validación;
- no debe asumirse que en 2022–2024 se cultivó cebada, porque FIRA indicó que no cuenta con el historial de cultivos por parcela para ese periodo;
- una señal histórica puede describirse como contexto ambiental/cobertura, pero no como “NDVI de cebada histórica” sin identificación externa del cultivo.

No asumir que más años implican mejor desempeño.

## 5.5 Valores faltantes

La política debe documentarse y pertenecer al pipeline de modelado o preparación de datos.

El backend no debe inventar imputaciones distintas a las utilizadas durante entrenamiento.

## 5.6 Variables no disponibles a nivel parcela

Con la información oficial de la segunda sesión, **no deben utilizarse como features parcelarias oficiales** salvo que FIRA entregue posteriormente nuevos datos o se incorpore una fuente externa válida y documentada:

- fecha exacta de siembra;
- dosis de siembra (kg/ha);
- historial de cultivo 2022–2024;
- siniestros o pérdidas parciales 2025 (granizo, heladas, plagas);
- variedad de cebada (Josefa/Voyager) por parcela.

Conocer que ciertas variedades estuvieron presentes en el ciclo no autoriza a asignarlas a parcelas individuales.

---

# 6. Contrato geoespacial

El dataset oficial contiene parcelas georreferenciadas, pero las Bases no especifican un CRS concreto.

El equipo debe registrar:

```text
source_crs = <CRS confirmado del archivo oficial>
api_crs = EPSG:4326
```

`EPSG:4326` es una **decisión interna de interoperabilidad para la API/frontend**, no un requisito de FIRA.

El adaptador geoespacial es responsable de:

- leer el CRS real;
- validar geometrías;
- transformar a `EPSG:4326` para API;
- no asumir el CRS por apariencia de coordenadas;
- preservar el vínculo con `parcel_id`.

FIRA aclaró que los polígonos fueron delimitados mediante distintos métodos y posteriormente validados con imágenes satelitales. Por ello, el sistema no debe asumir precisión geométrica homogénea entre todas las parcelas ni derivar falsas diferencias de calidad a partir del método de delimitación si ese método no está etiquetado por parcela.

Formato de salida de API:

```text
GeoJSON Polygon | MultiPolygon | null
```

con orden:

```text
[longitude, latitude]
```

---

# 7. Contrato Modelado → Backend

El equipo de modelado debe entregar un artefacto congelado y suficiente información para reproducir la inferencia.

Artefactos mínimos sugeridos:

```text
models/yield_model_<version>.joblib
models/feature_schema.json
```

Idealmente, el preprocesamiento aprendido debe viajar dentro de un único `Pipeline` de sklearn o artefacto equivalente para evitar diferencias entre entrenamiento e inferencia.

## 7.1 Consideraciones del split oficial

FIRA indicó que las parcelas de entrenamiento fueron seleccionadas mediante **muestreo aleatorio estratificado**.

Consecuencias:

- el conjunto oficial de evaluación permanece completamente fuera del proceso de selección/tuning;
- la validación interna debe realizarse únicamente dentro del conjunto etiquetado;
- si se conocen los estratos originales, conviene preservarlos en particiones internas cuando sea posible;
- si no se conocen, no inventarlos;
- la validación espacial adicional sigue siendo útil como prueba de robustez/generalización, pero no debe describirse como reproducción del procedimiento oficial de selección.

## 7.2 feature_schema.json

Formato mínimo:

```json
{
  "model_version": "yield-v1",
  "target_name": "<nombre confirmado>",
  "prediction_unit": "<unidad confirmada>",
  "features": [
    "feature_1",
    "feature_2"
  ],
  "target_cycle": "2025-04/2025-10",
  "prediction_information_cutoff": "2025-10-31",
  "training_id_source": "<artefacto/lista oficial>",
  "missing_value_policy": "<documentada>"
}
```

Los valores aún no confirmados deben permanecer como placeholders, no rellenarse por inferencia.

## 7.3 Reglas

El backend:

- usa exactamente las features esperadas;
- respeta el orden si el artefacto lo requiere;
- verifica que no falten columnas;
- utiliza el mismo preprocesamiento del entrenamiento;
- rechaza un artefacto incompatible;
- no entrena ni ajusta hiperparámetros durante inferencia.

Columnas adicionales en `features_master` no son necesariamente un error: se ignoran si no pertenecen al schema del modelo.
Una columna requerida ausente sí es error.

---

# 8. Contrato de inferencia

Flujo:

```text
parcel_id
    ↓
resolver features de la parcela
    ↓
validar schema y versiones
    ↓
aplicar pipeline de preprocesamiento congelado
    ↓
model.predict(...)
    ↓
predicción finita en unidad confirmada
```

Nunca devolver como predicción válida:

```text
NaN
+inf
-inf
```

El modelo se carga una vez por proceso de aplicación o mediante un mecanismo de caché equivalente.

---

# 9. Contrato ML avanzado → Backend

FIRA aclaró que la aplicación debe **identificar de forma sencilla los principales factores que influyen en el resultado**, además de mostrar la predicción. Por tanto, **algún mecanismo de explicabilidad orientado al usuario forma parte del comportamiento esperado de la aplicación**.

SHAP no es obligatorio específicamente: puede usarse SHAP u otro método técnicamente defendible. Los intervalos conformales, OOD y riesgo productivo siguen siendo extensiones opcionales de Cebada360.

Estas capacidades no deben desplazar el objetivo principal de desempeño predictivo.

## 9.1 Explicabilidad

La explicación debe corresponder exactamente a la misma versión del modelo utilizado para la predicción.

Si se utiliza SHAP, registrar:

- `model_version`;
- método/explainer;
- espacio de salida;
- `base_value`;
- contribuciones;
- tolerancia de reconstrucción.

Los nombres amigables son una capa semántica y no cambian las features del modelo.

## 9.2 Intervalos de incertidumbre

FIRA exige para el conjunto de predicción **un valor puntual por parcela en t/ha con cuatro decimales**. Los intervalos son un complemento metodológico y no sustituyen ese valor puntual.

Si se implementan:

- método documentado;
- nivel nominal documentado;
- calibración separada de la evaluación oficial;
- unidad consistente con la predicción;
- no presentar cobertura nominal como garantía individual.

## 9.3 Riesgo productivo

Es un módulo interno de apoyo a la interpretación.

No debe presentarse como:
- score crediticio;
- probabilidad de incumplimiento;
- decisión de otorgamiento de crédito.

Debe tener metodología y versión explícitas.

---

# 10. Contrato Backend → Frontend

La API pública se define en `docs/api-contract.md`.

El frontend debe consumir la API y no leer directamente artefactos internos del modelo.

El prototipo debe permitir **ejecutar el modelo predictivo y consultar resultados de manera interactiva**, en alineación con las Bases. Además, según la segunda sesión de preguntas, debe presentar de forma sencilla los principales factores que influyen en cada resultado y generar información útil para decisiones oportunas del productor.

El frontend puede:

- formatear;
- filtrar;
- ordenar;
- construir estructuras visuales a partir de la respuesta;
- representar geometrías;
- traducir nombres mediante catálogos autorizados.

No debe:

- reentrenar;
- recalcular SHAP con lógica distinta;
- modificar predicciones;
- cambiar unidades;
- redefinir riesgo.

---

# 11. Regiones y agregaciones

`region` es una abstracción interna hasta que se confirme una definición consistente con los datos oficiales.

Debe existir:

```text
region_key
region_label
region_source
```

No asumir que `region == municipio` sin confirmación.

Las estadísticas regionales deben indicar cobertura cuando no todas las parcelas tienen predicción.

---

# 12. Versionado

Mínimo:

```text
contract_version
model_version
feature_schema_version
data_version
```

Cuando aplique:

```text
explanation_version
interval_method_version
risk_method_version
```

Nunca mezclar, por ejemplo:

```text
predicción de yield-v2
+
SHAP calculado para yield-v1
```

---

# 13. Mock vs. real

```text
MODE=mock | real
```

En `mock`:
- usar únicamente datos sintéticos;
- declarar explícitamente `mode=mock`.

En `real`:
- no utilizar fallbacks mock silenciosos;
- si falta un artefacto esencial, fallar de forma explícita.

---

# 14. Predicciones y submission

Las Bases establecen el split aproximado 70/30 y FIRA aclaró que la selección de entrenamiento se realizó mediante muestreo aleatorio estratificado. El sistema debe validar contra los IDs oficiales de evaluación, no contra una constante numérica.

El generador debe recibir como entrada:

```text
official_evaluation_ids
predictions
submission_schema
```

y validar:

- cobertura exacta de los IDs requeridos;
- ningún ID extra;
- IDs únicos;
- ningún valor faltante;
- ningún `NaN`/infinito;
- valor puntual de rendimiento por parcela;
- unidad **t/ha**;
- **cuatro decimales** en el entregable de predicción;
- columnas y orden exigidos por la instrucción oficial vigente.

El nombre exacto del archivo y canal de envío deben provenir de una aclaración oficial/documentación complementaria y quedar registrados en:

```text
docs/fira-submission-instructions.md
```

No deben codificarse en este contrato como si provinieran de las Bases.

---

# 15. Requisitos de entrega derivados de la convocatoria

Antes del 19 de octubre de 2026 a las 23:59, el equipo debe garantizar que el paquete de entrega incluya lo requerido por FIRA.

## 15.1 Reporte técnico

Mantener la estructura y límites indicados por las Bases:

- Introducción;
- Justificación;
- Objetivos;
- Metodología;
- Resultados y discusión;
- Uso de la ciencia de datos en la inclusión financiera del sector agro;
- Conclusiones;
- Bibliografía;
- Anexos.

Los anexos deben incluir las actividades y aportaciones de cada integrante.

## 15.2 Aplicación

Debe existir un prototipo funcional capaz de:

- ejecutar el modelo predictivo;
- consultar resultados;
- visualizarlos de forma interactiva.

## 15.3 Código y documentación

Debe entregarse:

- código fuente de la aplicación;
- código fuente del modelo predictivo;
- documentación necesaria para ejecutarlos.

Por ello, la reproducibilidad no es opcional.

## 15.4 Video

Debe prepararse un video demostrativo de máximo 5 minutos.

## 15.5 Uso de IA

Si se utiliza IA:

- documentar dónde se utilizó;
- conservar los prompts relevantes;
- anexarlos al escrito según las Bases.

Mantener un registro, por ejemplo:

```text
docs/ai-usage-log.md
```

No registrar secretos, tokens ni datos sensibles.

---

# 16. Prioridad de desarrollo alineada a evaluación

Debido a la ponderación oficial:

```text
70 % desempeño predictivo + justificación técnica
30 % aplicación/interfaz
```

se adopta la siguiente prioridad:

1. integridad y ausencia de leakage;
2. validación correcta;
3. desempeño predictivo;
4. justificación de variables/modelo;
5. reproducibilidad;
6. aplicación funcional;
7. explicabilidad sencilla de los principales factores (esperada por FIRA);
8. intervalos/riesgo/OOD y otras innovaciones opcionales;
9. extras visuales.

Una mejora visual no debe retrasar un experimento crítico del modelo o comprometer reproducibilidad.

---

# 17. Reproducibilidad

Debe ser posible reconstruir:

```text
datos permitidos
↓
features
↓
entrenamiento/configuración congelada
↓
modelo final
↓
predicciones
↓
API
↓
submission
```

Todos los pasos manuales inevitables deben documentarse.

Scripts sugeridos:

```text
scripts/build_features.py
scripts/train_final_model.py
scripts/generate_predictions.py
scripts/generate_submission.py
```

No es obligatorio utilizar exactamente estos nombres.

---

# 18. Definition of Done de integración

Una versión real está lista cuando:

- [ ] IDs oficiales están validados.
- [ ] Split etiquetado/evaluación está validado contra artefactos oficiales.
- [ ] Target confirmado como rendimiento de grano y unidad t/ha.
- [ ] Features coinciden con el schema.
- [ ] Política de faltantes coincide entre entrenamiento e inferencia.
- [ ] Se documentaron periodos y fuentes de las features.
- [ ] No existe leakage del target.
- [ ] No existe leakage temporal.
- [ ] El histórico, si se utiliza, está documentado y evaluado sin asumir cultivo de cebada en 2022–2024.
- [ ] Modelo final fue seleccionado sin utilizar el conjunto oficial de evaluación.
- [ ] Modelo final se reentrenó con todas las muestras etiquetadas disponibles después de congelar la configuración.
- [ ] La predicción oficial es puntual, en t/ha y se exporta con cuatro decimales.
- [ ] La aplicación muestra principales factores de forma sencilla.
- [ ] Predicciones son finitas.
- [ ] Versiones de modelo/explicabilidad/intervalos son compatibles.
- [ ] CRS fuente fue confirmado y la transformación a API fue validada.
- [ ] Mock y real no se mezclan.
- [ ] Tests relevantes pasan.
- [ ] README/documentación permite ejecutar aplicación y modelo.
- [ ] Uso de IA y prompts relevantes están registrados.
- [ ] Aportaciones por integrante están documentadas.
- [ ] Video/demo y reporte técnico tienen responsables asignados.

---

# 19. Responsabilidades

## Persona 1 — Data / ETL / Geospatial
Responsable de:
- ingestión y limpieza;
- feature engineering;
- metadata;
- geometrías y CRS;
- trazabilidad temporal;
- reproducibilidad de datos.

## Persona 2 — Modelado predictivo
Responsable de:
- estrategia de validación del modelo;
- comparación y selección;
- modelo final;
- pipeline de preprocesamiento;
- feature schema;
- métricas;
- predicciones base.

## Persona 3 — ML avanzado / validación / explicabilidad
Responsable de:
- auditoría de validación;
- análisis espacial/robustez;
- explicabilidad;
- intervalos;
- riesgo productivo, si se utiliza;
- documentación metodológica asociada.

## Persona 4 — Backend & ML Engineering
Responsable de:
- validación de artefactos;
- carga del modelo;
- inferencia;
- API;
- integración;
- tests de backend;
- deploy;
- generador/validador de submission.

No modifica silenciosamente outputs de Data o ML.

## Persona 5 — Frontend / UX / Storytelling
Responsable de:
- consumo de API;
- mapa;
- vistas;
- gráficas;
- experiencia de uso;
- apoyo a demo/video/presentación.

---

# 20. Pendientes que requieren fuente autoritativa

No cerrar estos valores por inferencia:

- [ ] nombre oficial de columna ID;
- [ ] nombre oficial del target;
- [x] unidad exacta del rendimiento: `t/ha`;
- [ ] IDs exactos del conjunto de evaluación;
- [ ] definición final de región;
- [ ] CRS de los archivos geoespaciales oficiales;
- [ ] columnas y orden del submission;
- [ ] nombre exacto del archivo de submission;
- [ ] canal/correo oficial de envío del CSV, si aplica;
- [ ] esquema final de features;
- [ ] política final de faltantes;
- [ ] versión final del modelo;
- [ ] método de intervalos, si se usa;
- [ ] escala/método de explicabilidad;
- [ ] metodología de riesgo, si se usa;
- [x] referencia documental del ciclo abril–octubre 2025: Segunda sesión de preguntas y respuestas, 9 de octubre de 2026.
- [x] naturaleza del cultivo: temporal.
- [x] salida requerida por parcela: estimación puntual en t/ha con cuatro decimales.
- [ ] nombre físico de la columna de rendimiento en el dataset.

---

# 21. Regla para agentes de IA

Antes de modificar código o contratos, cualquier agente debe:

1. leer `docs/system-contract.md`;
2. leer `docs/api-contract.md` si toca backend/frontend;
3. consultar la fuente oficial relevante si existe;
4. distinguir:
   - requisito de FIRA;
   - aclaración oficial;
   - decisión interna;
   - propuesta aún no aprobada;
5. no convertir ejemplos en requisitos;
6. no rellenar valores `PENDIENTE` por conocimiento general;
7. detenerse y señalar la ambigüedad cuando dos fuentes entren en conflicto.

Una respuesta de un agente nunca tiene mayor autoridad que una fuente oficial.
