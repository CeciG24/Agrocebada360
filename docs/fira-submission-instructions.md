# Generar, validar y entregar predicciones

Revisión técnica: 2026-10-18. El script genera archivos; no envía correos ni carga documentos en plataformas.

## Fuente y requisitos por confirmar

Las Bases y aclaraciones conservadas en `docs/system-contract.md` exigen estimaciones puntuales en t/ha con cuatro decimales, código e instrucciones, video de máximo cinco minutos y documentación del trabajo y uso de IA. El video forma parte de la entrega; no debe tratarse como opcional por una redacción interna.

La guía previa citaba un correo de FIRA del 18 de octubre: reporte de máximo cuatro cuartillas, tabla de predicciones, archivo `nombre_del_equipo_prediccion.csv` y envío a `innovacion@fira.gob.mx`. **El archivo citado `docs/additional/fira-instructions.txt` no está en el repositorio.** El equipo debe conservar ese correo y confirmar el formato/canal en la plataforma antes del envío. No se resuelve aquí la discrepancia entre cuatro cuartillas y la extensión por secciones de las Bases. Esta revisión no modifica los requisitos oficiales por inferencia.

La fecha comunicada por el equipo es 19 de octubre de 2026, 23:59; confirmar los detalles de recepción en la fuente oficial. La validación técnica del CSV no acredita envío ni aceptación por FIRA.

## Comandos ejecutables desde la raíz

```powershell
.\.venv\Scripts\python.exe scripts/generate_submission.py --team la_amariza --predictions ml/results/predictions_raw.csv --ids ml/split/official_ids_v1.json --out-dir submissions
.\.venv\Scripts\python.exe scripts/generate_submission.py --validate-only submissions/la_amariza_prediccion.csv --predictions ml/results/predictions_raw.csv --ids ml/split/official_ids_v1.json
```

`--team` se requiere al generar. `--validate-only` revisa un archivo existente sin escribirlo. No existen las opciones `--output` ni `verify_integrated_delivery.py --submission` de la guía anterior.

Formato interno vigente: encabezado exacto `parcel_id,rendimiento_t_ha`; IDs opacos sin cambios, únicos y con cobertura exacta de `eval_ids`; valores finitos con cuatro decimales. La cantidad se obtiene de la lista y no está fijada en el código. En la versión actual son 59 filas. El generador conserva el orden de esa lista y rechaza filas extra, faltantes o duplicadas. El validador además contrasta los valores con las predicciones congeladas redondeadas.

`ml/split/official_ids_v1.json` declara un split derivado de `dataset_split`, pendiente de cotejo con una lista autoritativa de FIRA. El nombre del archivo no acredita por sí mismo que esa confirmación ya ocurrió.

## Cierre del equipo

- [x] CSV existente con 59 filas, IDs únicos, valores finitos y cuatro decimales, contrastado con predicciones congeladas.
- [ ] Cotejar IDs y formato contra la instrucción oficial más reciente; conservar la fuente del correo citado.
- [ ] Confirmar nombre de equipo/archivo y canal de recepción.
- [ ] Completar reporte técnico, contribuciones y declaración/prompts de IA; resolver extensión con FIRA.
- [ ] Publicar video de máximo cinco minutos y comprobar permisos de acceso.
- [ ] Validar frontend y API públicos de la versión final.
- [ ] Realizar los envíos/cargas y conservar constancias.
- [ ] Confirmar respaldo y release si el equipo los incluye en su plan.
