# Diccionario de variables del modelo — P4.13

Versión interna `feature-labels-v1`. Cubre las 30 features de `yield-v1` / `features-v1`.

Los nombres se derivan del cálculo P1.9 auditado. Falta la revisión semántica de Persona 1; no se atribuyen como nomenclatura oficial de FIRA.

El catálogo ejecutable está en `api/app/catalogs/feature_labels.json`. Incluye definiciones, unidades, fórmulas, ventanas y hashes del cálculo/modelo/schema. Se regenera con `python scripts/build_feature_dictionary.py`; si cambia el cálculo o el conjunto de features, se detiene para revisión.

En 2025 se usa abril–octubre. La ventana conjunta incluye 2022–2024 y abril–octubre de 2025, sin enero–marzo de 2025. Los históricos representan contexto ambiental, no historial de cebada. La media conjunta pondera por observación mensual disponible, no por año.

**Las unidades de entrada (mm o °C) no son las unidades del impacto SHAP:** las contribuciones de este predictor siguen expresadas en t/ha. No se cambian identificadores, impactos, orden, versiones ni la identidad de reconstrucción.

| Feature técnica | Nombre para la interfaz | Unidad de entrada |
|---|---|---|
| `precip_total_mm_2022` | Precipitación acumulada · 2022 | mm |
| `precip_mean_mm_2022` | Precipitación mensual media · 2022 | mm |
| `tmin_mean_c_2022` | Temperatura mínima media · 2022 | °C |
| `tmax_mean_c_2022` | Temperatura máxima media · 2022 | °C |
| `amplitud_termica_mean_c_2022` | Amplitud térmica media · 2022 | °C |
| `amplitud_termica_std_c_2022` | Variabilidad de amplitud térmica · 2022 | °C |
| `precip_total_mm_2023` | Precipitación acumulada · 2023 | mm |
| `precip_mean_mm_2023` | Precipitación mensual media · 2023 | mm |
| `tmin_mean_c_2023` | Temperatura mínima media · 2023 | °C |
| `tmax_mean_c_2023` | Temperatura máxima media · 2023 | °C |
| `amplitud_termica_mean_c_2023` | Amplitud térmica media · 2023 | °C |
| `amplitud_termica_std_c_2023` | Variabilidad de amplitud térmica · 2023 | °C |
| `precip_total_mm_2024` | Precipitación acumulada · 2024 | mm |
| `precip_mean_mm_2024` | Precipitación mensual media · 2024 | mm |
| `tmin_mean_c_2024` | Temperatura mínima media · 2024 | °C |
| `tmax_mean_c_2024` | Temperatura máxima media · 2024 | °C |
| `amplitud_termica_mean_c_2024` | Amplitud térmica media · 2024 | °C |
| `amplitud_termica_std_c_2024` | Variabilidad de amplitud térmica · 2024 | °C |
| `precip_total_mm_2025` | Precipitación acumulada · abr–oct 2025 | mm |
| `precip_mean_mm_2025` | Precipitación mensual media · abr–oct 2025 | mm |
| `tmin_mean_c_2025` | Temperatura mínima media · abr–oct 2025 | °C |
| `tmax_mean_c_2025` | Temperatura máxima media · abr–oct 2025 | °C |
| `amplitud_termica_mean_c_2025` | Amplitud térmica media · abr–oct 2025 | °C |
| `amplitud_termica_std_c_2025` | Variabilidad de amplitud térmica · abr–oct 2025 | °C |
| `precip_total_mm_2022_2025` | Precipitación acumulada · histórico + ciclo 2025 | mm |
| `precip_mean_mm_2022_2025` | Precipitación mensual media · histórico + ciclo 2025 | mm |
| `tmin_mean_c_2022_2025` | Temperatura mínima media · histórico + ciclo 2025 | °C |
| `tmax_mean_c_2022_2025` | Temperatura máxima media · histórico + ciclo 2025 | °C |
| `amplitud_termica_mean_c_2022_2025` | Amplitud térmica media · histórico + ciclo 2025 | °C |
| `amplitud_termica_std_c_2022_2025` | Variabilidad de amplitud térmica · histórico + ciclo 2025 | °C |

La API aplica los nombres únicamente al modelo y schema cuyos hashes figuran en el catálogo. Ante otro modelo, feature desconocida o diccionario no disponible, conserva el nombre técnico; no adivina una traducción. No añade campos al contrato público: utiliza `FeatureImpact.friendly_name`. El frontend conserva el código técnico en el título de cada etiqueta y en un detalle desplegable de la gráfica completa.
