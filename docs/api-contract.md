# Contrato de API — Cebada360

Versión aprobada: `0.1.0`, con geometría opcional en el listado antes de implementar.
No hay endpoints ejecutables todavía. Los nombres siguientes son campos del
contrato público, no columnas asumidas del dataset.

## Convenciones

- Rutas relativas al origen del backend, sin prefijo `/api` por ahora.
- Solo lectura mediante `GET`; respuestas JSON en UTF-8.
- IDs de parcela: cadenas opacas, conservando ceros iniciales. No convertir a enteros.
- `region` es una clave opaca cuya definición y fuente debe acordar el equipo.
  El cliente debe codificar los valores al construir las URLs.
- Campos declarados siempre presentes en la variante solicitada; `geometry` se
  omite del listado cuando `include_geometry=false`. Los marcados como anulables usan `null`
  cuando no hay información. Colecciones vacías usan `[]`.
- Rendimientos, impactos y límites deben ser números finitos, nunca `NaN` ni infinito.
- Sin autenticación en esta versión de lectura para el hackathon. CORS se
  configurará con los orígenes autorizados de DEV y PROD al implementar la API.
- Los ejemplos son sintéticos; no representan parcelas ni resultados oficiales.

Todas las respuestas de dominio incluyen `meta`:

| Campo | Tipo | Regla |
|---|---|---|
| `contract_version` | string | `0.1.0` |
| `mode` | `mock` o `real` | Origen efectivo de la respuesta |
| `cycle` | string | `2025-04/2025-10` |
| `data_cutoff` | string, fecha | `2025-10-31`, límite máximo permitido |

`data_cutoff` declara una restricción, no prueba que el pipeline la cumpla.
La integración deberá verificar que ninguna observación usada sea posterior al
límite. En modo real, nunca sustituir silenciosamente resultados faltantes por mocks.

## Rutas

| Método y ruta | Respuesta 200 | Errores previstos |
|---|---|---|
| `GET /health` | Health | 503 |
| `GET /parcels` | ParcelList | 422, 503 |
| `GET /parcel/{id}` | ParcelDetail, incluye metadata | 404, 422, 503 |
| `GET /predict/{id}` | Prediction | 404, 422, 503 |
| `GET /explain/{id}` | Explanation | 404, 422, 503 |
| `GET /risk/{id}` | Risk | 404, 422, 503 |
| `GET /regions/{region}` | RegionSummary | 404, 422, 503 |

Todos pueden devolver 500 ante un fallo inesperado. No hay cuerpos de request.
Los parámetros de ruta deben contener al menos un carácter no blanco.

### GET /health

Indica si la API está lista para servir su modo configurado; no ejecuta inferencia.

| Campo | Tipo | Regla |
|---|---|---|
| `status` | `ok` o `degraded` | `ok` devuelve 200; `degraded`, 503 |
| `mode` | `mock` o `real` | Modo configurado |
| `contract_version` | string | `0.1.0` |
| `model_loaded` | boolean | `false` es normal en modo mock |
| `data_ready` | boolean | Catálogo disponible |

En modo real se requiere catálogo y modelo cargados para `ok`. En mock se requiere
el catálogo sintético. Esta respuesta es la excepción al sobre de errores de 503.
No expone rutas locales, secretos ni trazas.

### GET /parcels

Parámetros query opcionales:

| Parámetro | Tipo | Default | Regla |
|---|---|---|---|
| `region` | string | Sin filtro | No vacía |
| `include_geometry` | boolean | `false` | `true` incluye geometría en cada elemento; `false` la omite |

El cliente enviará `true` o `false` como representación canónica del booleano.
Un valor que no pueda interpretarse como booleano devuelve 422 `VALIDATION_ERROR`.
Ambos parámetros pueden combinarse: `/parcels?region=mock-region&include_geometry=true`.

Sin paginación inicial: el universo
del reto es de 197 parcelas. `total` refleja los registros realmente cargados,
no se fija artificialmente en 197. Orden estable por `id` lexicográfico ascendente.
Un filtro sin coincidencias devuelve 200, `items: []` y `total: 0`.

Respuesta: `items`, `total: integer >= 0`, `meta: Meta`.
Con `include_geometry=false` o ausente, `items: ParcelSummary[]` conserva
exactamente el comportamiento actual. Con `include_geometry=true`,
`items: ParcelMapItem[]`. Toda la lista usa la misma variante.
`total` es la cantidad después de filtrar y coincide con la longitud de `items`.

**ParcelSummary**:

| Campo | Tipo | Regla |
|---|---|---|
| `id` | string | Identificador de la parcela |
| `region` | string o null | Clave regional acordada |

**ParcelMapItem**: los campos de ParcelSummary más:

| Campo | Tipo | Regla |
|---|---|---|
| `geometry` | GeoJSON Polygon, MultiPolygon o null | Misma geometría y reglas que en `/parcel/{id}`; longitud/latitud WGS84, anillos cerrados |

Con `true`, `geometry` está presente en todos los elementos. Si una parcela no
tiene geometría disponible, su valor es `null`: la parcela sigue en `items` y
cuenta en `total`. El frontend omite su dibujo y puede indicar la falta de geometría.
Con `false`, la clave se omite por completo, no se devuelve como `null`.
Solicitar geometría no cambia IDs, regiones, orden, filtro ni número de parcelas.

Se conserva el sobre JSON `items/total/meta`; no se cambia a GeoJSON FeatureCollection.
Cada `geometry` es un objeto GeoJSON, no una cadena JSON ni un objeto Feature.
El frontend puede construir una FeatureCollection localmente a partir de los
elementos con geometría, usando `id` y `region` como propiedades.
Con el catálogo completo y sus geometrías disponibles, una sola petición a
`/parcels?include_geometry=true` permite dibujar las 197 parcelas, sin peticiones
individuales. No se fabrican geometrías para completar ese número.
Una indisponibilidad operativa de la fuente requerida devuelve 503 `DATA_UNAVAILABLE`;
no debe encubrirse devolviendo todas las geometrías como null.

Esta extensión evita otra ruta y mantiene pequeño el listado por defecto.
La transformación de coordenadas seguirá en el adaptador de datos compartido
con el detalle; no se exige consultar el endpoint de detalle por cada parcela.

No se incluyen features, rendimiento observado ni predicciones en este listado.

Ejemplo sintético con `include_geometry=true` (una parcela ilustrativa):

```json
{
  "items": [
    {
      "id": "mock-001",
      "region": null,
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [[-100.0, 20.0], [-99.999, 20.0], [-99.999, 20.001], [-100.0, 20.001], [-100.0, 20.0]]
        ]
      }
    }
  ],
  "total": 1,
  "meta": {
    "contract_version": "0.1.0",
    "mode": "mock",
    "cycle": "2025-04/2025-10",
    "data_cutoff": "2025-10-31"
  }
}
```

Con `include_geometry=false` o ausente, el mismo elemento sería
`{"id": "mock-001", "region": null}`; el sobre y `total` permanecen iguales.

### GET /parcel/{id}

Respuesta: `id`, `region` como en ParcelSummary; además:

| Campo | Tipo | Regla |
|---|---|---|
| `geometry` | GeoJSON Polygon, MultiPolygon o null | Coordenadas longitud/latitud WGS84; anillos cerrados |
| `meta` | Meta | Contexto de la respuesta |

Es también el endpoint de metadata de parcela. No se agregan nombres de
productores, superficies, fechas de siembra ni otras propiedades sin verificar
primero su existencia, semántica y autorización de exposición. `geometry: null`
significa que no está disponible en la API; el frontend debe poder mostrar el detalle.
La transformación del sistema de coordenadas será responsabilidad del adaptador de datos.

### GET /predict/{id}

| Campo | Tipo | Regla |
|---|---|---|
| `parcel_id` | string | ID solicitado |
| `prediction` | number | Estimación puntual finita |
| `unit` | string | Unidad explícita; debe confirmarse antes del modo real |
| `lower` | number o null | Límite inferior |
| `upper` | number o null | Límite superior |
| `interval_level` | number o null | Cobertura nominal entre 0 y 1, extremos excluidos |
| `interval_method` | string o null | Método provisto por ML avanzado |
| `model_version` | string | Versión del artefacto usado, `mock-v1` para el ejemplo |
| `meta` | Meta | Contexto |

Sin intervalos, los cuatro campos de intervalo son `null`. Con intervalos,
todos tienen valor y `lower <= prediction <= upper`; los límites comparten la
unidad de la predicción. Este requisito debe acordarse con ML avanzado: si su
método no contiene la estimación puntual, se revisará el contrato antes de integrarlo.
No se recortarán valores ni se fabricarán intervalos en la API.
La cobertura es nominal; no es una garantía individual por parcela.

Una parcela existente sin features o predicción utilizable devuelve 503
`PREDICTION_UNAVAILABLE`. Un ID inexistente devuelve 404 `PARCEL_NOT_FOUND`.
El modelo se cargará una vez al iniciar; esta ruta no entrenará ni recargará el modelo.

### GET /explain/{id}

| Campo | Tipo | Regla |
|---|---|---|
| `parcel_id` | string | ID solicitado |
| `status` | `available` o `unavailable` | Disponibilidad de explicación |
| `reason` | string o null | `EXPLANATION_NOT_READY` cuando no está disponible |
| `method` | string o null | `shap` cuando está disponible |
| `model_version` | string o null | Misma versión que la predicción explicada |
| `output_space` | string o null | Escala de salida explicada, definida por ML avanzado |
| `base_value` | number o null | Referencia SHAP finita, en `output_space` |
| `explained_output` | number o null | Salida explicada finita, en `output_space` |
| `features` | FeatureImpact[] | Todas las contribuciones para esta explicación |
| `meta` | Meta | Contexto |

**FeatureImpact**: `feature: string` (nombre técnico confirmado),
`friendly_name: string`, `impact: number`,
`direction: positive | negative | neutral`.
La dirección corresponde al signo del impacto: mayor, menor o igual a cero.
Los elementos se ordenan por impacto absoluto descendente y luego por `feature`.
Si no existe nombre amigable, se usa el técnico; el diccionario no cambia las features.
No se inventan nombres de variables antes de recibir el esquema del modelo.

Con `available`, todos los campos de contexto de explicación tienen valor,
`reason` es null y la lista contiene contribuciones. Debe cumplirse la identidad
SHAP `base_value + suma(impact) ≈ explained_output`, con tolerancia acordada para
el artefacto. Solo se iguala a `prediction` si ambas están en la misma escala.
Con `unavailable`, `features` es `[]`, `reason` es `EXPLANATION_NOT_READY`
y los campos desde `method` hasta `explained_output` son null.
La ausencia esperada de SHAP devuelve 200; un fallo de su servicio devuelve 503.

### GET /risk/{id}

| Campo | Tipo | Regla |
|---|---|---|
| `parcel_id` | string | ID solicitado |
| `status` | `available` o `unavailable` | Disponibilidad de evaluación |
| `reason` | string o null | `RISK_NOT_READY` si no está disponible |
| `level` | `low`, `medium`, `high` o null | Clasificación del equipo de ML avanzado |
| `method_version` | string o null | Versión de metodología y umbrales |
| `model_version` | string o null | Modelo asociado a la evaluación |
| `description` | string o null | Explicación legible del resultado |
| `meta` | Meta | Contexto |

Con `available`, nivel, metodología, modelo y descripción tienen valor, y `reason`
es null. Con `unavailable`, esos cuatro campos son null y `reason` es `RISK_NOT_READY`.
La ausencia esperada devuelve 200; fallos operativos, 503. El backend no deduce
riesgo a partir del rendimiento ni inventa umbrales o probabilidades.

### GET /regions/{region}

| Campo | Tipo | Regla |
|---|---|---|
| `region` | string | Clave solicitada |
| `parcel_count` | integer >= 1 | Total de parcelas de la región |
| `predicted_count` | integer >= 0 | Parcelas con predicción disponible |
| `mean_prediction` | number o null | Media aritmética por parcela, no ponderada por superficie |
| `unit` | string o null | Misma unidad que las predicciones agregadas |
| `model_version` | string o null | Versión común de los resultados agregados |
| `meta` | Meta | Contexto |

`predicted_count <= parcel_count`. Si es cero, media, unidad y versión son null.
Si es positivo, esos tres campos tienen valor. No mezclar unidades, versiones,
ciclos ni resultados mock y reales. Resultados incompatibles producen 503
`REGION_SUMMARY_UNAVAILABLE`. La media puede ser parcial: el frontend debe mostrar
la cobertura `predicted_count / parcel_count`. No representa producción total.
Región desconocida: 404 `REGION_NOT_FOUND`. Si la fuente de regiones aún no está
integrada: 503 `REGION_DATA_UNAVAILABLE`, sin fabricar agrupaciones.

## Errores uniformes

```json
{
  "error": {
    "code": "PARCEL_NOT_FOUND",
    "message": "No se encontró la parcela solicitada.",
    "details": []
  }
}
```

`details` es una lista de objetos con `field: string` y `message: string`.
Se usa en 422 para señalar parámetros inválidos, sin repetir valores sensibles.
El cliente decide por `code`, no por el texto de `message`.

| HTTP | Códigos |
|---|---|
| 404 | `PARCEL_NOT_FOUND`, `REGION_NOT_FOUND`, `ROUTE_NOT_FOUND` |
| 422 | `VALIDATION_ERROR` |
| 503 | `DATA_UNAVAILABLE`, `MODEL_UNAVAILABLE`, `PREDICTION_UNAVAILABLE`, `EXPLANATION_UNAVAILABLE`, `RISK_UNAVAILABLE`, `REGION_DATA_UNAVAILABLE`, `REGION_SUMMARY_UNAVAILABLE` |
| 500 | `INTERNAL_ERROR` |

Al implementar FastAPI se normalizarán sus errores de validación al mismo sobre.
Los errores internos se registrarán en el servidor; la respuesta no incluirá
excepciones, rutas de archivos ni trazas. Una respuesta 503 no es una predicción cero.

## Ejemplos sintéticos

Predicción sin intervalos (la unidad `mock_unit` no es una unidad oficial):

```json
{
  "parcel_id": "mock-001",
  "prediction": 3.2,
  "unit": "mock_unit",
  "lower": null,
  "upper": null,
  "interval_level": null,
  "interval_method": null,
  "model_version": "mock-v1",
  "meta": {
    "contract_version": "0.1.0",
    "mode": "mock",
    "cycle": "2025-04/2025-10",
    "data_cutoff": "2025-10-31"
  }
}
```

Explicación aún no entregada por ML avanzado:

```json
{
  "parcel_id": "mock-001",
  "status": "unavailable",
  "reason": "EXPLANATION_NOT_READY",
  "method": null,
  "model_version": null,
  "output_space": null,
  "base_value": null,
  "explained_output": null,
  "features": [],
  "meta": {
    "contract_version": "0.1.0",
    "mode": "mock",
    "cycle": "2025-04/2025-10",
    "data_cutoff": "2025-10-31"
  }
}
```

## Validación y próximos acuerdos

Revisión de diseño: las siete rutas tienen respuesta, tipos, nulabilidad y errores;
el detalle incluye metadata; los mocks están identificados; no se asumen columnas.
No se agregan tests ejecutables en esta tarea documental. Al implementar los
schemas Pydantic y las rutas, los siguientes casos serán las pruebas de aceptación:

1. Health devuelve 200 en mock listo y 503 cuando faltan dependencias requeridas.
2. Listado estable, IDs preservados como cadenas y filtro sin coincidencias vacío.
3. Detalle válido con geometría presente o null; ID inexistente devuelve 404.
4. Predicción finita, unidad explícita y versión; artefacto ausente devuelve 503.
5. Intervalos completos y ordenados, o todos sus campos null; rechazar NaN e infinito.
6. SHAP disponible con signos coherentes; ausencia devuelve 200 sin contribuciones falsas.
7. Riesgo disponible con metodología; ausencia devuelve 200 sin clasificar como bajo.
8. Resumen regional con cobertura parcial y cero predicciones; no mezclar versiones.
9. Errores 404, 422, 503 y 500 con el sobre acordado, salvo health 503.
10. Un artefacto que use observaciones posteriores a octubre de 2025 no se acepta.
11. El modelo se carga una vez al iniciar, no por cada solicitud de predicción.
12. `/parcels` y `/parcels?include_geometry=false` producen el mismo listado sin
    clave `geometry`; con `true` todos los elementos incluyen esa clave.
13. La variante con geometría preserva IDs, orden, regiones y total; una geometría
    ausente es null y no elimina la parcela. El listado coincide con el detalle.
14. El filtro regional funciona con ambas variantes; sin coincidencias devuelve
    `items: []`, `total: 0`. Un booleano inválido produce 422 `VALIDATION_ERROR`.
15. Con un catálogo de prueba de 197 parcelas con geometría, una sola petición
    devuelve las 197 geometrías sin paginación ni consultas HTTP individuales al detalle.

Antes de integrar datos reales, confirmar con los equipos responsables:

- Columna oficial del ID, su mapeo a string y unidad exacta del rendimiento.
- Fuente, definición y claves de regiones; formato y CRS de geometrías.
- Esquema y orden de features, tratamiento de faltantes y versión del modelo.
- Método/cobertura de intervalos, escala SHAP y método de riesgo.
- Evidencia de corte temporal y contrato de columnas de submission, que es
  independiente del JSON de la API.

La siguiente tarea podrá traducir este diseño a schemas Pydantic y OpenAPI generado
por FastAPI, manteniendo una única definición ejecutable de tipos.
