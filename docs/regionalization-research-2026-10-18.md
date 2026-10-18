# Investigación de agrupación regional — 2026-10-18

Actualización: el equipo aprobó esta agrupación y se implementó como `state-regions-v1` en [P4.15](regional-integration.md). El texto siguiente y el JSON de propuesta conservan el estado de la investigación previa; la política activa está en `api/app/catalogs/regions.json`.

**Propuesta, todavía no activada en la API.** El dataset integrado contiene 197 parcelas en 9 municipios de Hidalgo, Puebla y Tlaxcala. Los municipios reales no son los ejemplos sintéticos del mock. Se recomienda agruparlos mediante regionalizaciones estatales documentadas, conservando el estado como parte de la clave y la versión/fuente de cada asignación.

| Clave propuesta | Región de referencia | Municipios presentes en nuestro dataset | Parcelas | Entrenamiento | Evaluación sin target |
|---|---|---|---:|---:|---:|
| `hgo-apan` | X: Apan, Hidalgo | Almoloya, Apan, Emiliano Zapata, Tepeapulco | 19 | 15 | 4 |
| `hgo-tulancingo` | II: Tulancingo, Hidalgo | Cuautepec de Hinojosa, Singuilucan | 32 | 21 | 11 |
| `pue-chignahuapan` | Microrregión 3: Chignahuapan, Puebla | Chignahuapan | 100 | 71 | 29 |
| `tlx-poniente-calpulalpan` | Poniente–Calpulalpan, Tlaxcala | Calpulalpan, Nanacamilpa de Mariano Arista | 46 | 31 | 15 |
| Total | 4 grupos | 9 municipios | 197 | 138 | 59 |

La tabla enumera únicamente municipios presentes en la entrega; no pretende enumerar todos los municipios integrantes de esas regiones oficiales. La región de Chignahuapan contiene más municipios aunque solo uno figure en nuestros datos. Tampoco son unidades equivalentes en superficie, número de municipios o criterios de planeación entre estados.

## Fuentes primarias

1. **Hidalgo:** [SIGEH, Infografías Regionales](https://sigeh.hidalgo.gob.mx/pags/info_reg/). Identifica Región II Tulancingo con Cuautepec de Hinojosa y Singuilucan, y Región X Apan con Almoloya, Apan, Emiliano Zapata y Tepeapulco. La tabla de la p.126 de las [Reglas de Operación publicadas el 31-01-2025](https://transparenciadocs.hidalgo.gob.mx/ENTIDADES/SEBISO/transparencia/pdfs/rops/2025/ROPs_Programa_Estatal_apoyo_para_el_Bienestar_y_el_Desarrollo_EF_2025.pdf) también documenta esas asignaciones bajo el PED 2022–2028.
2. **Puebla:** [Portal de Planeación, regionalización](https://planeader.puebla.gob.mx/regionalizacion) y [ficha cartográfica Microrregión 3 Chignahuapan](https://sei.puebla.gob.mx/mapas/mapas/microrregion-3-chignahuapan-1). Esta última está fechada en 2026, usa Marco Geoestadístico INEGI 2025 y la ubica en la macrorregión Sierra Norte. El portal también conserva programas de periodos anteriores con otra numeración: no mezclar la antigua región 7 con la microrregión 3 de esta propuesta.
3. **Tlaxcala:** [PED 2021–2027, figura 27](https://si.tlaxcala.gob.mx/images/Plan%20Estatal%20de%20Desarrollo%202021-2027.pdf) y [Periódico Oficial, 05-02-2025, p.69](https://publicaciones.tlaxcala.gob.mx/indices/Peri6-10a2025.pdf). Ambos incluyen Calpulalpan y Nanacamilpa de Mariano Arista en Poniente–Calpulalpan.

Consulta web del 18-10-2026: algunos servidores PDF y SIGEH no respondieron a la apertura directa; sus tablas se pudieron consultar mediante los extractos indexados de las páginas oficiales. Antes de congelar el catálogo de producción conviene conservar copias de las fuentes y su hash. Los enlaces, denominaciones y atribuciones quedan registrados aquí; no se afirma que los tres estados compartan una regionalización nacional uniforme.

## Alternativas y elección

- **Estado:** tres grupos de 51 parcelas en Hidalgo, 100 en Puebla y 46 en Tlaxcala. Es simple y reproducible, pero pierde el contraste Apan/Tulancingo. Se puede mantener como filtro superior.
- **Regionalización estatal de referencia:** los cuatro grupos propuestos. Ofrece nombres explicables y una correspondencia documentada para cada municipio observado. Es la recomendación para P4.15.
- **Municipio:** nueve unidades, varias con solo una o dos parcelas; útil como filtro de detalle, menos útil como resumen principal. Apan, Emiliano Zapata y Tepeapulco no tienen parcelas de evaluación en esta entrega.
- **Regiones agroclimáticas o clústeres:** requieren definir variables, escalas, algoritmo y validación de estabilidad/homogeneidad. Los clústeres espaciales de validación de ML no se convierten automáticamente en regiones de producto. No se justifica inventar esta metodología para resolver una agrupación visual que ya puede documentarse.

## Condiciones para P4.15

- Adoptar explícitamente el catálogo como una decisión de Cebada360 basada en referencias estatales; no llamarlo regionalización oficial de FIRA. Guardar `region_key`, `region_label`, `region_source` y versión en un artefacto interno, sin añadir campos al contrato público.
- Resolver asignaciones por `(estado, municipio)` con correspondencia documentada y validación de cobertura. Los nombres municipales son los entregados por Data; esta revisión no certifica sus límites mediante una intersección geoespacial. No reasignar coordenadas o polígonos para hacerlos coincidir con la propuesta.
- Mantener el modelo congelado: la región se usa para consulta y agregación, no como nueva feature.
- El contrato exige media aritmética por parcela, cobertura y una única versión/unidad/ciclo. No promediar medias municipales sin ponderar por el número de parcelas con predicción.
- Si el resumen usa exclusivamente las 59 predicciones de evaluación publicadas por ML, las coberturas serán 4/19, 11/32, 29/100 y 15/46. El pipeline también puede inferir parcelas etiquetadas; elegir esa otra población cambia la cobertura y debe indicarse, sin mezclar rendimientos observados y predichos.
- Nombrar los resultados como **resumen de las parcelas del dataset dentro de la región**. No estiman el rendimiento de todos sus productores ni representan una muestra probabilística del territorio. Apan tendría solo cuatro predicciones de evaluación: conservar una indicación clara de muestra pequeña, sin ocultarla ni prometer significancia.
- No añadir producción total, superficie regional ni distribución de prioridades al endpoint si no están en su schema. Riesgo puede consultarse por parcela con P4.14; una extensión regional requiere acordar su contrato.

La [propuesta estructurada](regionalization-proposal-2026-10-18.json) valida cobertura sin solapamientos de las 197 parcelas y conserva el hash del maestro utilizado. No se modificaron el catálogo activo, endpoints, predicciones o ramas de otros integrantes.
