# Aportaciones del equipo: estado comprobable

Revisión: 2026-10-18. Este documento distingue el reparto de responsabilidades de la evidencia presente en Git. No certifica autorías individuales, fechas de ejecución ni entregas externas sin evidencia; cada integrante debe confirmar su nombre y aportaciones para el anexo del reporte.

| Responsable previsto | Trabajo observable en el repositorio | Alcance y pendientes |
|---|---|---|
| Persona 1 — Data | Preparación de sensores, clima, topografía, matriz maestra y cortes; diccionario contrastado e integración geoespacial | 197 filas, 215 columnas en features_master; el modelo usa 30 climáticas. La entrega de despliegue incluye 197 geometrías. La selección oficial de IDs debe confirmarse con su fuente autoritativa. |
| Persona 2 — ML | Comparativas, validación repetida y espacial, modelo congelado, schema, predicciones y OOF | Ridge `yield-v1`, 138 etiquetas y 59 predicciones. Documentar resultados internos y limitaciones; no atribuir métricas al conjunto oficial sin etiquetas. |
| Persona 3 — ML avanzado | SHAP, intervalos exploratorios, OOD y prioridades de revisión | SHAP cumple base + suma(impactos) ≈ predicción. Los intervalos no tienen calibración independiente y permanecen desactivados. El usuario confirmó que Persona 3 validó el mapeo de riesgo implementado en P4.14. |
| Persona 4 — Backend/integración (Cecilia, según reparto del equipo) | P4.6–P4.9, P4.12–P4.15: inferencia, serialización, API real, mapa, nombres amigables, riesgo y regiones; generador/validador del CSV | API versionada sin entrenamiento HTTP; artefactos y pruebas reproducibles. El detalle público conserva id, región, geometría y meta; no publica área/elevación/pendiente. Regiones agrega rendimiento y cobertura, sin riesgo regional ni producción inventados. |
| Persona 5 — Frontend/UX | Dashboard, Regional, Modelo y Acerca de; diseño oscuro, responsive y separación mock/real | La ficha Modelo se genera de resultados versionados y verifica compatibilidad con la API. El reparto de mejoras de integración debe ser confirmado por quienes participaron; no se deduce autoría personal de esta tabla. |

La integración y las revisiones asistidas por IA forman parte del trabajo técnico: el reporte debe declarar el uso de IA y anexar los prompts pertinentes según las Bases. Esta tabla no sustituye ese anexo.

## Evidencia reproducible

- `docs/model-view.md` y `docs/model-view-acceptance-2026-10-18.json`: métricas, gráfica OOF y compatibilidad de Modelo.
- `docs/risk-integration.md` y `docs/regional-integration.md`: metodologías y límites de ambos adaptadores.
- `data/deploy/acceptance.json` y `docs/deploy-api-acceptance-2026-10-19.json`: integridad de artefactos y respuestas reales del paquete destinado al despliegue.
- `scripts/generate_submission.py --validate-only submissions/la_amariza_prediccion.csv`: validación del CSV existente contra IDs y predicciones congeladas.
- Historial Git para atribución técnica; los integrantes deben confirmar identidad, participación y fechas antes de entregar el reporte.

## Aún no acreditado por este documento

No se marcan como terminados el reporte final, el video, su publicación, el envío del CSV, la carga en FIRA, un respaldo externo ni una release de GitHub sin sus respectivos archivos/enlaces/constancias. El estado de producción se registra separadamente en `docs/release-readiness.md`.
