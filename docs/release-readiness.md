# Cierre técnico y producción

Actualización: 2026-10-19. System Contract 0.3.0 / API 0.1.0 conservados.

| Paso autorizado | Estado y evidencia |
|---|---|
| 1. Guardar Modelo, integrar y publicar | Completado en Git: Modelo en `b46079d`, integración de `origin/main` en `683c573`, correcciones de despliegue en `2dcd42f`. Publicados en `dev` y `main`, sin force push. Render ya sirve la entrega corregida. Vercel todavía requiere publicar esa revisión; ver paso 3. |
| 2. Reparar datos del mapa | Completado: 197 geometrías verificadas en el paquete y en la API pública. Modelo y data_version conservados. `data/deploy/acceptance.json`, `docs/deploy-api-acceptance-2026-10-19.json` y `docs/public-api-acceptance-2026-10-19.json`. |
| 3. Revisar aplicación pública | Parcial: API pública completa aprobada; frontend nuevo aprobado en preview local contra esa API, con seis rutas, recarga, escritorio, móvil de 390 px y separación mock/real. Vercel conserva el bundle anterior y devuelve 404 al cargar rutas internas directamente. Falta acceso al proyecto para publicar y repetir la aceptación pública. No se considera cerrado. |
| 4. Documentación | Completado: README restaurado deliberadamente con instrucciones reales, aportaciones contrastadas y limitaciones. Confirmación del usuario registrada: Persona 3 validó el mapeo de riesgo. No se certifican video/envíos ni autorías/fechas no comprobadas. |
| 6. Submission | Completado técnicamente: generador con IDs opacos, cobertura dinámica exacta y rechazo de duplicados/no finitos. `--validate-only` contrasta el CSV con predicciones congeladas y formato de cuatro decimales. CSV existente: 59 filas, SHA256 `cfaee38e238af7a813c7f2fdc4955e45d45a5733dde98c7d4889c48eaffdc318`; ver `docs/submission-acceptance-2026-10-19.json`. No se envió ningún correo ni archivo a FIRA. |

## Evidencia

- 263 pruebas Python, 25 pruebas de frontend, lint y build correctos.
- HTTP local sobre la entrega final: 59 predicciones, 59 SHAP, 59 prioridades (4 altas, 17 medias, 38 sin alerta combinada), cuatro regiones y 197 geometrías. Una carga del modelo, sin entrenamiento HTTP.
- API pública https://agrocebada-api.onrender.com: 197 geometrías iguales al catálogo versionado, 59 predicciones iguales a las salidas congeladas, 59 reconstrucciones SHAP, riesgos iguales a los artefactos, cuatro regiones y CORS válido para https://agrocebada360.vercel.app. `docs/public-api-acceptance-2026-10-19.json`.
- Compilación nueva en preview local con proxy hacia la API pública: `/`, `/regional`, `/modelo`, `/acerca`, `/parcela/AGC_029` y `/parcela/AGC_001`; acceso directo y recarga 200, sin desbordamiento a 390 px, Modelo con 138 puntos OOF y sin errores JS. `docs/frontend-release-acceptance-2026-10-19.json`. Esta prueba no equivale a un despliegue de Vercel.
- Frontend público anterior: portada 200; `/regional` y `/modelo` directos 404. Bundle observado `index-CmL2o_hA.js`; la compilación nueva produjo `index-D5PgTWm2.js`. `docs/public-deployment-acceptance-2026-10-19.json` registra el fallo restante.
- `scripts/pack_deploy_data.py --check-only` valida hashes, geometrías y módulos antes de crear opcionalmente un archivo de distribución. Render usa directamente el paquete de Git. Los bytes preparados en el índice Git se contrastaron con los manifiestos, incluidas todas las fuentes de datos.

El modelo continúa en SHA256 `f624c2324e418b642a41c98bed53977fa4eb9fa3e210c0341d239592b4bc33d6`; data_version `sha256:b045a212af57282a`.

## Acción restante en Vercel

No hay sesión CLI local ni acceso de navegador operativo al proyecto desde esta ejecución. El usuario confirmó que desconoce si está vinculado con GitHub. GitHub no devolvió deployments, check runs ni statuses para el commit publicado; esto no demuestra por sí solo cuál es la configuración de Vercel.

Quien tenga acceso debe abrir el proyecto que posee el dominio `agrocebada360.vercel.app`, comprobar su vínculo con `CeciG24/Agrocebada360` y publicar `main` en producción. Vercel permite crear un despliegue desde una referencia Git en **Deployments → Create Deployment**; ver [documentación oficial](https://vercel.com/docs/git). Comprobar que se construye la revisión nueva, sin volver a promover un despliegue antiguo.

Configuración prevista: raíz `frontend`, build `npm run build`, salida `dist`, `VITE_API_URL=https://agrocebada-api.onrender.com`. Si la raíz configurada es el repositorio, el nuevo `vercel.json` fija install/build/salida hacia frontend y la reescritura SPA. Ambas raíces disponen de configuración de rutas.

Después, abrir directamente `/modelo?demo=0` y `/regional?demo=0`, recargar y comprobar métricas, mapa y API real. Actualizar la evidencia pública solo cuando esa revisión esté servida.

## Pendientes externos

El listado oficial de IDs sigue pendiente de cotejo externo y falta conservar el correo citado de FIRA. La guía no resuelve por inferencia la discrepancia sobre extensión del reporte. El paso 5 no forma parte de esta ejecución. Reporte/video/publicación externa/envío final siguen bajo responsabilidad del equipo; este documento no acredita su entrega.
