# Revisión de ML contra System Contract v0.3.0

Base revisada: `aff61874bdc67d006adad444cc54ebd86764728f` de `ml`.
`dev` nace de ese commit. El documento proporcionado se conserva en
`docs/system-contract.md`. Esta revisión compara la implementación con él;
no autentica las fuentes oficiales que cita.

## Alineación existente

- `data.load()` lee IDs string y comprueba unicidad y consistencia entre fuentes.
- Modelos sklearn incorporan el preprocesamiento aprendido en el Pipeline.
- Existe schema de 207 features únicas, t/ha, versión del baseline y política
  de faltantes documentada.
- Selección/tuning usa parcelas etiquetadas; las de predicción no aportan targets.
  Hay CV anidada para tuning y diagnóstico espacial.
- Las 59 predicciones revisadas son finitas y tienen IDs únicos/coincidentes con
  la lista del maestro original disponible. La cantidad no es una regla contractual.
- Los 99 CSV OOF revisados tienen IDs/targets coincidentes con las parcelas
  etiquetadas del maestro disponible y predicciones finitas.

## Pendientes de Data/ML

1. **Schema v0.3.0 (§7.2, §12).** El actual declara contrato 0.1.0 y nombres
   antiguos `target`, `unit`, `data_cutoff`. Faltan `target_name`, `prediction_unit`,
   `target_cycle`, `prediction_information_cutoff`, `training_id_source` y
   `data_version`. ML debe confirmarlos y publicarlos, no inferirlos Backend.
2. **Identidad congelada del modelo (§7.3, §8, §12).** El predictor se guarda sin
   metadata, y su cargador no acredita pertenencia al schema/versiones. Una
   reproducción sintética aceptó modelo v0 con schema v9 y features invertidas:
   resultado 23 en vez de 32. Publicar una asociación verificable; consultar
   las alternativas admitidas en `docs/inference-pipeline.md`.
3. **Procedencia por feature (§5.3–5.4).** Faltan fuentes, sensores/datasets,
   ventanas, agregaciones, políticas, semántica histórica y fecha máxima para
   todas las features. El audit contrasta tres agregados en 40 parcelas y fechas
   de picos; no acredita todo el conjunto ni las matrices tempranas. Vincular
   evidencia al dataset exacto y no asumir cebada para históricos 2022–2024.
4. **Corte obligatorio (§2.3).** El baseline permite exportar si falta/falla el
   audit, salvo variable opcional. El audit guardado tampoco se vincula al contenido
   usado. Bloquear esas situaciones al publicar artefactos para integración.
5. **Split oficial variable (§2.6, §14).** Las constantes y aserciones de
   `data.load()`/`early.load_cut()`/`validate_predictions()` fijan 138/59.
   Usar listas oficiales versionadas y documentar los nombres físicos de ID/target.
6. **Cuatro decimales (§14).** El baseline exporta `round(3)`. Generar desde
   predicciones completas y formatear cuatro decimales en el entregable oficial,
   con columnas/orden confirmados. No inventar una cuarta cifra del CSV actual.
7. **Modelo final y reproducibilidad (§2.6, §17–18).** El schema describe Ridge
   baseline; el reporte de ensemble selecciona ExtraTrees individual. Faltan
   localmente el joblib y dataset procesado para verificar inferencia real, además
   de la entrega final congelada y versiones del entorno.

## Otros pendientes

- El notebook conserva imports/rutas del layout anterior. `ml/README.md` dice
  que el corte no se cumple mientras los resultados nuevos lo declaran verificado.
- El ensemble ponderado reconoce leakage en la validación de segundo nivel.
  No usar ese score como validación independiente sin evaluación anidada adecuada.
  La corrida entregada descarta el ensemble.
- Falta explicabilidad sencilla del modelo final para el prototipo; corresponde
  a ML avanzado. SHAP específico, intervalos y riesgo son opcionales.
- API-contract sigue en 0.1.0, distinto del contrato interno. No se cambió la API
  ni se activó modo real en esta tarea.

## Alcance en dev

Solo se adapta el pipeline 4.6, dependencias de inferencia, pruebas y documentación.
No se corrigen fuentes, schema ni resultados de Persona 2. `ml` conserva su commit.
La eliminación local previa del README raíz se conserva; no pertenece a esta tarea.

Los manifests/procedencias soportados son formatos internos, no requisitos
oficiales. No se fabricaron esos artefactos para los datos reales.
