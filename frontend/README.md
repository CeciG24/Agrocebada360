# Cebada360 — Frontend

React + Vite. Se incorporó la entrega de `origin/gian-dev` (`d42530b`) dentro de
`frontend/` y se adaptó al contrato público `docs/api-contract.md` 0.1.0 y al
contrato de sistema 0.3.0. No se modificaron las ramas de ML ni los contratos.

## Ejecutar

Desde la raíz del repositorio, iniciar la API existente en una terminal:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Abrir `http://localhost:5173/`. `?demo=1` selecciona la demostración local;
`?demo=0` consulta la API. El selector permite cambiar después. La API actual
opera en **mock**: consultar la API no implica que sus predicciones sean reales.
La interfaz muestra el origen efectivo recibido en `meta.mode`.

Vite reenvía únicamente las rutas públicas de la API a `http://127.0.0.1:8000`,
evitando necesitar CORS durante desarrollo. Para cambiar el destino, copiar
`.env.example` a `.env.local` y ajustar `VITE_API_TARGET`. Opcionalmente,
`VITE_API_URL` permite un origen directo; ese caso necesita CORS en el backend.
En producción configurar el proxy equivalente en el servidor web, o un origen
de API explícito con CORS. Las rutas UI `/parcela/:id`, `/regional`, `/modelo`
siguen perteneciendo al frontend; las rutas API son las siguientes.

## Consumo del contrato

| Consulta | Ruta pública |
|---|---|
| Listado y mapa | `GET /parcels?include_geometry=true` |
| Listado opcional sin geometría/filtro | `GET /parcels?include_geometry=false&region=...` |
| Metadata de parcela | `GET /parcel/{id}` |
| Estimación puntual | `GET /predict/{id}` |
| Explicación | `GET /explain/{id}` |
| Riesgo | `GET /risk/{id}` |
| Resumen de una región del catálogo | `GET /regions/{region}` |

`ApiRepository` traduce las respuestas públicas al modelo de presentación.
Preserva IDs como strings y codifica segmentos de URL. Listado y mapa comparten
una consulta; las geometrías `null` no eliminan parcelas ni se sustituyen por
polígonos inventados. Solo la demostración local genera geometrías sintéticas.

La API actual aún no implementa explicaciones, riesgo ni resúmenes regionales.
Sus errores se muestran por `error.code`; no se completa con datos demo. Una
predicción no disponible se representa con `null` y un aviso, nunca con cero.
Las respuestas de dominio validan `meta`, ciclo, corte y campos principales;
el detalle rechaza mezclar orígenes o explicaciones/riesgo de otra versión de
modelo. Las unidades vienen de la respuesta: `mock_unit` no se rotula `t/ha`.

La vista regional muestra `predicted_count / parcel_count` y la media recibida
sin recalcularla ni asumir municipios, superficie o producción. Mantiene los
grupos con cobertura cero o errores y señala parcelas sin región.

El contrato no define rutas de vecinos, cortes tempranos, métricas o resumen
global. En modo API esas funciones devuelven estados de no disponibilidad sin
realizar HTTP. La demostración mantiene sus ejemplos separados y etiquetados.
El selector de cortes solo aparece cuando la fuente entrega cortes; los SHAP,
riesgo e intervalos del cierre no se reutilizan como resultados de otro corte.

## Verificar

```powershell
npm test
npm run lint
npm run build
# Con FastAPI iniciado:
node scripts/check-api.mjs http://127.0.0.1:8000
# Con Vite también iniciado, comprueba el proxy:
node scripts/check-api.mjs http://localhost:5173
```

Las pruebas usan `node:test`, sin añadir un framework. Cubren URLs, IDs opacos,
197 parcelas en una petición de geometrías, valores ausentes, errores,
incompatibilidad de metadata/modelo, intervalos y cobertura regional. El script
de integración usa el backend disponible, sin suponer resultados reales ni
implementar rutas adicionales. Requiere un catálogo no vacío.

Verificación realizada el 16 de octubre de 2026: 15 pruebas aprobadas,
lint y build correctos; integración directa con FastAPI y a través de Vite
con 197 parcelas/geometrías. Se comprobaron en navegador dashboard, detalle,
modo demo, estados de indisponibilidad, tabla regional y ancho móvil, sin
errores JavaScript. Las explicaciones, riesgo y regiones del backend actual
siguen pendientes de implementación; esta reparación no agrega esos servicios.

## Presentación de la demo

La revisión visual conserva la paleta oscura y separa rendimiento,
incertidumbre y explicación. El Dashboard cuenta parcelas, geometrías y claves
regionales del catálogo; esos contadores no se presentan como cobertura de
predicciones. Los tres factores principales se ordenan por magnitud desde la
explicación recibida, sin recalcular contribuciones.

Regional muestra indicadores de una región seleccionada y compara únicamente
medias con igual unidad y versión. Riesgo y producción regional permanecen
pendientes porque la fuente actual no los entrega. Modelo conserva sus secciones
visibles cuando no hay métricas; no dibuja puntos de observado/predicho sin
pares de datos ni utiliza resultados del repositorio como fallback. La demo
local mantiene exclusivamente los ejemplos sintéticos ya existentes.

Se comprobaron Dashboard, Regional, Modelo y Acerca de en modo API mock y
demo local, con escritorio y ancho móvil de 390 px, sin errores de JavaScript
ni desbordamiento horizontal. Se conservan controles nativos de teclado,
foco visible, texto además de color y respeto a movimiento reducido.
