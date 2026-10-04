# Cebada360

Proyecto del Reto AgroCebada FIRA 2026 para predecir el rendimiento de cebada por parcela y presentar resultados en una herramienta web de análisis productivo.

## Estado actual

API FastAPI mock conforme al [contrato aprobado v0.1.0](docs/api-contract.md).
Implementados: `GET /health`, `GET /parcels`, `GET /parcel/{id}` y `GET /predict/{id}`.
No hay integración con datos reales, entrenamiento ni inferencia real.

## Ejecutar la API (PowerShell)

Requiere Python 3.11 o superior instalado y disponible como `python`.
Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn api.app.main:app --reload
```

No es necesario activar el entorno virtual. Para instalar únicamente las
dependencias del servidor, usar `api/requirements.txt`.
El servidor escucha en `http://127.0.0.1:8000`.

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/health'
Invoke-RestMethod 'http://127.0.0.1:8000/parcels?include_geometry=true'
Invoke-RestMethod 'http://127.0.0.1:8000/parcels?region=mock-region-1&include_geometry=true'
Invoke-RestMethod 'http://127.0.0.1:8000/parcel/mock-001'
Invoke-RestMethod 'http://127.0.0.1:8000/predict/mock-001'
```

`/health` debe devolver `ok`, modo `mock`, `model_loaded: false` y
`data_ready: true`. El listado completo devuelve 197 parcelas sintéticas;
`include_geometry` ausente o false omite la clave `geometry`.
El catálogo usa IDs `mock-001` a `mock-197`, regiones ficticias `mock-region-1`
y `mock-region-2`, cuadrados sintéticos y predicciones deterministas en
`mock_unit`. No representa las parcelas oficiales ni lee archivos del dataset.
Los intervalos son null. El catálogo se genera una vez por inicio del proceso.

Solo se exponen las cuatro rutas solicitadas: `/docs`, `/redoc` y
`/openapi.json` están desactivadas. No hay CORS configurado aún; la integración
con frontend y sus orígenes autorizados se realizará en otra tarea.
La configuración está en `api/app/core/config.py`; `CEBADA_LOG_LEVEL` permite
elegir DEBUG, INFO (default), WARNING, ERROR o CRITICAL. Solo se admite modo mock.

## Pruebas

Desde la raíz, con las dependencias de desarrollo instaladas:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

No requieren un servidor en ejecución. Cubren las variantes del listado,
197 geometrías en una sola petición, filtros, detalle, predicciones, validación
Pydantic, errores 404/422/503/500 y carga única del catálogo. La validación
temporal de artefactos y la carga del modelo se probarán al integrar ML real.

La caché opcional de pytest está desactivada en `pytest.ini` para evitar
conflictos de permisos entre el usuario local y el entorno aislado de Codex.
Esto no oculta warnings; las opciones que dependen del historial de caché,
como `--lf`, no están disponibles. AnyIO está fijado a una versión compatible
con el TestClient de la versión de Starlette utilizada.

## Estructura

```text
api/          Backend: API, configuración, schemas, routers y servicios.
ml/           Pipeline de inferencia y contrato de artefactos de ML.
frontend/     Interfaz web y servicios de consumo de la API.
data/         Datos locales; excluidos de Git por defecto.
notebooks/    Exploración y experimentación del equipo.
tests/        Pruebas automatizadas.
docs/         Documentación técnica y acuerdos de integración.
scripts/      Utilidades de ejecución, validación y submission.
```

Los archivos `.gitkeep` conservan las carpetas vacías en Git. Para esta estructura, `api/` será la ubicación del backend; no se crea un segundo directorio `backend/`.

## Acuerdos iniciales

El equipo trabaja con `main`, `develop` y ramas `feature/<area>-<tarea>`.
Consulta la [guía Git y revisión de PR](docs/git-workflow.md) y la
[plantilla de pull request](.github/pull_request_template.md).

- Mantener el entrenamiento fuera de la API.
- Definir las interfaces con el equipo de modelado antes de integrar datos o modelos reales.
- No usar datos posteriores a octubre de 2025 para predecir el rendimiento del ciclo abril–octubre de 2025.
- No versionar secretos, datos locales ni modelos serializados. Su distribución y respaldo se definirán en una tarea posterior.

## Validar la estructura

Desde la raíz del repositorio, ejecutar en PowerShell:

```powershell
$folders = 'api', 'ml', 'frontend', 'data', 'notebooks', 'tests', 'docs', 'scripts'
foreach ($folder in $folders) {
    if (-not (Test-Path -LiteralPath $folder -PathType Container)) {
        throw "Falta la carpeta: $folder"
    }
    if (-not (Test-Path -LiteralPath "$folder/.gitkeep" -PathType Leaf)) {
        throw "Falta .gitkeep en: $folder"
    }
}
Write-Output 'Estructura correcta: 8 carpetas con .gitkeep.'
git status --short
```

Esta última comprobación solo valida las carpetas; las pruebas de comportamiento
se ejecutan con pytest como se indica arriba.
