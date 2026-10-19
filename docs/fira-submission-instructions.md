# Instrucciones de Entrega — Reto AgroCebada FIRA 2026

Versión: `1.0.0`

---

## Fecha límite

**Lunes 19 de octubre de 2026 a las 23:59 hrs.**

Después de esa hora la plataforma cierra y no se aceptan entregas adicionales.
Cargar con anticipación y verificar que todos los componentes estén enviados.

---

## Componentes a entregar

### 1. Plataforma oficial FIRA

Subir directamente en la plataforma de recepción:

- **Reporte técnico** en PDF, máximo 4 cuartillas.
  - Puede incluir ecuaciones, gráficas, tablas y demás elementos metodológicos.
  - **Obligatorio:** tabla con `parcel_id` y `rendimiento_t_ha` (las 59 parcelas de evaluación).

### 2. Correo a `innovacion@fira.gob.mx`

Enviar con el mismo límite de fecha y hora:

#### Archivo CSV de predicciones (obligatorio)

| Campo | Valor |
|-------|-------|
| **Nombre del archivo** | `nombre_del_equipo_prediccion.csv` |
| **Filas** | 59 (una por parcela de evaluación) |
| **Columnas** | `parcel_id`, `rendimiento_t_ha` |
| **Formato `parcel_id`** | Identificador original de FIRA, sin modificaciones |
| **Formato `rendimiento_t_ha`** | Número decimal en t/ha, **4 decimales** (e.g., `3.9142`) |
| **Restricciones** | Sin NaN, sin Inf, sin IDs duplicados, sin filas extra |

Ejemplo de contenido esperado:

```csv
parcel_id,rendimiento_t_ha
PARCEL_001,3.9142
PARCEL_002,4.1087
...
```

> Los IDs deben coincidir exactamente con los 59 IDs del conjunto de evaluación oficial
> (`split/official_ids_v1.json`). No alterar el formato ni el valor del identificador.

#### Adjuntos opcionales en el mismo correo

- Enlace al repositorio de código fuente.
- Enlace al video demostrativo (≤ 5 minutos).
- Otros anexos que el equipo considere relevantes.

---

## Generación del CSV

Usar el script del repositorio:

```bash
python scripts/generate_submission.py \
  --predictions ml/predictions/predictions_raw.csv \
  --ids split/official_ids_v1.json \
  --output nombre_del_equipo_prediccion.csv
```

El script aplica automáticamente el validador (P4.17):
- Verifica 59 IDs únicos sin NaN ni Inf.
- Confirma que los IDs coincidan con `official_ids_v1.json`.
- Redondea a 4 decimales.

Para verificar manualmente antes de enviar:

```bash
python scripts/verify_integrated_delivery.py --submission nombre_del_equipo_prediccion.csv
```

---

## Checklist de entrega

- [ ] CSV generado y validado con `generate_submission.py`
- [ ] 59 filas exactas, sin duplicados ni NaN
- [ ] IDs coinciden con `split/official_ids_v1.json`
- [ ] Archivo nombrado exactamente `la_amariza_prediccion.csv`
- [ ] Reporte técnico en PDF (≤ 4 cuartillas) con tabla `parcel_id / rendimiento_t_ha`
- [ ] Reporte subido a la plataforma FIRA
- [ ] Correo enviado a `innovacion@fira.gob.mx` antes del 19 oct 2026, 23:59 hrs
- [ ] Enlace al repositorio incluido en el correo
- [ ] Video demo (≤ 5 min) incluido o enlazado en el correo
- [ ] Backup completo generado (P4.25)
- [ ] Release GitHub v1.0-agrocebada creado (P4.26)