# Cierre técnico y producción

Actualización: 2026-10-19. Contratos públicos conservados: System Contract 0.3.0 / API 0.1.0.

| Paso autorizado | Estado y evidencia |
|---|---|
| 1. Guardar Modelo e integrar despliegue | Corrección de Modelo en `b46079d`; integración de `origin/main` en `dev`, conservando Python fijado, CORS y reglas de bytes/hashes. Publicación y comprobación de producción en curso. |
| 2. Reparar datos del mapa | Paquete corregido: 197 geometrías verificadas, 59 predicciones/SHAP/prioridades y cuatro regiones. Modelo y data_version conservados. `data/deploy/acceptance.json` y `docs/deploy-api-acceptance-2026-10-19.json`. |
| 3. Revisar aplicación pública | URL confirmada por el usuario: https://agrocebada360.vercel.app . La inspección de sus peticiones confirmó API https://agrocebada-api.onrender.com . Antes de este cambio: portada 200, geometrías 0, recarga directa de `/modelo` 404. Se añade configuración SPA tanto en raíz como en frontend para cubrir la raíz del proyecto Vercel. Falta comprobar los despliegues finales; no se da por completado con el push. |
| 4. Documentación | README reemplazado deliberadamente por instrucciones reales, aportaciones contrastadas y limitaciones. Confirmación del usuario registrada: Persona 3 validó el mapeo de riesgo. No se certifican video/envíos ni autorías/fechas no comprobadas. |
| 6. Submission | Generador con IDs opacos, cobertura dinámica exacta y rechazo de duplicados/no finitos. Nuevo `--validate-only` contrasta el CSV con predicciones congeladas y formato de cuatro decimales. CSV existente: 59 filas, SHA256 `cfaee38e238af7a813c7f2fdc4955e45d45a5733dde98c7d4889c48eaffdc318`. |

Validación local: 263 pruebas Python, 25 de frontend, lint y build correctos. Verificador HTTP completo: 59 predicciones, 59 SHAP, 59 prioridades (4 altas, 17 medias, 38 sin alerta combinada), cuatro regiones y 197 geometrías; una carga del modelo, sin entrenamiento HTTP. `scripts/pack_deploy_data.py --check-only` comprueba hashes y módulos antes de crear opcionalmente un archivo de distribución. Render usa directamente el paquete incluido en Git.

El hash del modelo congelado continúa en `f624c2324e418b642a41c98bed53977fa4eb9fa3e210c0341d239592b4bc33d6`; data_version `sha256:b045a212af57282a`. El conjunto oficial de IDs sigue pendiente de cotejo externo y el correo citado de FIRA debe conservarse como fuente. La guía documental no resuelve por inferencia la discrepancia sobre extensión del reporte.

El paso 5 no forma parte de esta ejecución. Reporte/video/publicación externa/envío final siguen bajo responsabilidad del equipo; este documento no acredita su entrega.
