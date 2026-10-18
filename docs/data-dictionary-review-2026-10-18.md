# Contraste del diccionario de Persona 1 — 2026-10-18

El documento coincide estructuralmente con **215/215 columnas del maestro**: 7 de identificación, 162 satelitales, 14 fenológicas, 30 climáticas y 2 topográficas. También documenta por separado el target correcto `rendimiento_t_ha`. Las 30 entradas de P4.13 coinciden en significado, unidad y periodo con este documento y con P1.9. Se conservan las etiquetas actuales, que distinguen claramente los históricos y el ciclo 2025.

Se contrastaron las tablas del DOCX con `docs/system-contract.md`, los scripts P1.1/P1.6/P1.7/P1.8/P1.9, el schema congelado `features-v1` y el dataset `data/integrated/verified-2026-10-17/data`. Esta revisión valida cobertura documental y coherencia con los cálculos; no sustituye la auditoría numérica de reconstrucción del dataset ni la validación agronómica de los índices.

## Fuente y entregables

- Fuente: `DICCIONARIO_DE_DATOS.docx`, proporcionado por Persona 1 a través del usuario. SHA256: `9944d5a2388840c8490952c77d9347f8a45b7052a692a62c2cf84da6bc29315b`.
- [Transcripción de párrafos y las 11 tablas](persona1-data-dictionary-source.json): conserva lo recibido, sin modificar el Word original. Es documentación del equipo; no se presenta como diccionario oficial de FIRA.
- [Diccionario complementado de las 215 columnas y el target](data-dictionary.json): nombres técnicos, descripciones, tipos documentados, unidades, fuentes de cálculo, pertenencia al modelo, nulos observados y hashes de evidencia. Las interpretaciones espectrales del Word se conservan como afirmaciones de Persona 1 pendientes de verificación contra el proveedor.
- [Diccionario de las 30 variables del modelo](model-feature-dictionary.md): catálogo de presentación P4.13, acotado por hashes del modelo y schema. Las unidades SHAP siguen siendo t/ha.

## Precisiones incorporadas

| Tema | Documento recibido | Complemento comprobado en código |
|---|---|---|
| AUC de NDVI | Unidad del índice | **NDVI × día**: P1.8 integra por trapecios usando días reales desde la primera captura. Integra el intervalo observado, sin extrapolar al ciclo completo; requiere dos fechas. |
| Crecimiento y descenso | Unidad del índice | **NDVI/día**: diferencias divididas por días transcurridos. El descenso conserva el signo, no es una magnitud positiva absoluta. |
| Pico y fechas | Pico fenológico | Máximo de NDVI observado tras promediar registros de una misma fecha. En empates, primera fecha en orden cronológico. No equivale por sí solo a fecha fisiológica confirmada del cultivo. |
| Faltantes fenológicos | Puede faltar descenso | También puede faltar crecimiento si el pico ocurre al inicio; AUC necesita dos fechas. La desviación temporal devuelve 0.0 con una sola fecha; con más usa `ddof=1`. |
| Desviación estándar | Desviación estándar | P1.7 y P1.9 usan la desviación **muestral** de pandas (`ddof=1`); P1.8 aplica la excepción anterior. No representa incertidumbre predictiva. |
| Clima 2025 | Abril–octubre, excluye noviembre–diciembre | También excluye **enero–marzo de 2025**. La ventana conjunta agrega observaciones de 2022–2024 y abril–octubre de 2025; no promedia las medias anuales. |
| Temperaturas | Media mínima/máxima | Promedio de las temperaturas mínimas/máximas mensuales disponibles; no extremos absolutos del periodo. Amplitud = `tmax_c - tmin_c`. |
| Topografía | Elevación en m y pendiente en grados | Concuerda con los rasters y P1.6. Media simple de píxeles válidos de la primera banda, máscara `all_touched=True`, excluyendo NoData/no finitos; no ponderación por fracción del área de cada píxel. |
| Fecha de corte | 2025-10-31 | El contrato la define como convención técnica de fin de octubre; no fecha diaria especificada por FIRA. |
| Histórico | Ventanas 2022–2024 | Contexto ambiental; no se conoce el historial de cultivos y no debe llamarse histórico de cebada. |

## Comprobación del dataset integrado

- 197 filas, `parcel_id` único; cobertura exacta de las 215 columnas, sin entradas sobrantes o sin documentar.
- 138 parcelas `ENTRENAMIENTO` con target y 59 `PREDICCION` con target vacío. Los IDs del archivo de targets coinciden exactamente con el maestro; el target no está entre sus columnas de entrada.
- Los únicos vacíos observados en el maestro son `planet_ndvi_decay_rate` en `AGC_043` y `AGC_175`. Son compatibles con la ausencia de observaciones posteriores al pico documentada por P1.8; esta revisión no vuelve a reconstruir sus series para atribuir individualmente la causa. No se sustituyen por cero.
- El modelo usa 30/215 columnas, todas climáticas. No consume IDs, partición, fechas fenológicas ni el target como features. La política de imputación pertenece al pipeline serializado; el diccionario no crea una nueva.
- El JSON incluye hashes de los tres CSV examinados, del contrato, schema y scripts contrastados. Los nulos y conteos son evidencia de esta entrega, no restricciones universales para futuras versiones.

## Pendientes delimitados

1. **Persona 1 / proveedor:** confirmar fórmula, bandas, escala y unidad física de los índices originales, especialmente MRA, VI6T y variantes enhanced. El nombre del índice no basta para deducir su formulación; tampoco se asume que todos sean adimensionales ni equivalentes entre sensores. Las descripciones agronómicas del documento quedan atribuidas a su autor, no certificadas por esta revisión.
2. **Equipo / FIRA:** siguen pendientes la definición de `region` y el formato/identificadores oficiales de entrega. `municipio` no se convierte automáticamente en región. El Word acredita la convención interna del target, no resuelve por sí solo el formato oficial.
3. **Persona 1:** P1.9 filtra el histórico mediante `anio < 2025`, sin límite inferior explícito de 2022. La serie actual solo contiene 2022–2025 y concuerda con la documentación. Si llegan años anteriores, la ventana conjunta los incluiría: debe acotarse y reauditarse antes de cambiar la entrega/modelo congelados. Aquí no se altera ese cálculo ni su hash.
4. La recepción del documento permite contrastar la semántica; no equivale a aprobación explícita de las etiquetas de interfaz de P4.13. No bloquea su funcionamiento actual con los significados ya comprobados.

## Reproducción

Desde la raíz del repositorio:

```powershell
python scripts/reconcile_data_dictionary.py --data-root data/integrated/verified-2026-10-17/data
python scripts/build_feature_dictionary.py
```

La primera orden falla si no hay cobertura exacta de columnas, aparecen IDs/targets duplicados, cambian las particiones reconocidas o se viola la separación de targets. Produce `docs/data-dictionary.json`; la segunda regenera los artefactos P4.13. No se deserializa ni entrena el modelo y no se reescriben datos. No cambian endpoints, payloads públicos, predicciones ni valores SHAP.
