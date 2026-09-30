# Cebada360

Proyecto del Reto AgroCebada FIRA 2026 para predecir el rendimiento de cebada por parcela y presentar resultados en una herramienta web de análisis productivo.

## Estado actual

Estructura inicial del repositorio. Todavía no hay API, frontend ejecutable, modelo ni datos incorporados. No se han definido columnas del dataset.

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

Esta etapa no requiere instalar dependencias. No hay aplicación que ejecutar ni pruebas de comportamiento todavía; la validación comprueba la estructura solicitada.
