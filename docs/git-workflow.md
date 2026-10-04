# Guía Git — Cebada360

## Flujo del equipo

```text
main                       versión estable y entregable
  └── develop              integración del equipo
        └── feature/...    una tarea concreta

feature/... → PR → develop → PR de entrega → main
```

| Rama | Uso | Regla |
|---|---|---|
| `main` | Versión estable | Recibe PR desde `develop`; no trabajo directo |
| `develop` | Integración | Recibe PR de tareas y debe poder ejecutarse |
| `feature/<area>-<tarea>` | Trabajo acotado | Nace de `develop` y vuelve a `develop` |

Usar minúsculas y guiones. Ejemplos: `feature/backend-api-mock`,
`feature/frontend-mapa`, `feature/model-baseline`, `feature/data-validacion`,
`feature/ml-advanced-intervalos`. Las ramas son por tarea, no permanentes por
persona. También se usan para correcciones y documentación, por ejemplo
`feature/backend-corregir-validacion` o `feature/docs-guia-git`.

Cada PR debe tener un objetivo revisable. Un responsable prepara el cambio y
al menos otro integrante lo revisa. Si modifica un contrato entre equipos,
solicitar revisión de quien lo consume antes de integrar.

## Preparación inicial de develop

Estos comandos son para el responsable del repositorio, una sola vez, si
`origin/develop` aún no existe. Ejecutarlos con el directorio de trabajo limpio:

```powershell
git status
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c develop
git push -u origin develop
```

Si `develop` ya existe en remoto pero no localmente:

```powershell
git fetch origin
git switch --track origin/develop
```

### Trabajo actual aún sin commit en main

Al redactar esta guía hay cambios locales del backend y documentación, y solo
se observa `main`. Antes de actualizar o cambiar la base, conservarlos en una
rama de tarea. Desde el estado actual, crear la rama mantiene esos archivos:

```powershell
git switch -c feature/backend-api-mock
git status --short
git add api tests pytest.ini README.md docs/api-contract.md docs/git-workflow.md .github/pull_request_template.md
git diff --cached --stat
git diff --cached
git commit -m "feat(api): agregar base FastAPI y respuestas mock"
git push -u origin feature/backend-api-mock
```

Revisar los archivos antes de confirmar el commit. No incluir `DataSet.zip`:
es un archivo local que actualmente no está cubierto por la regla `/data/**`
del `.gitignore`. Evitar `git add .` en este estado. Un archivo sin seguimiento
puede permanecer local; no borrarlo para limpiar el repositorio.

Después crear `develop` desde `main` con los pasos anteriores y abrir el PR
`feature/backend-api-mock → develop`. Si el equipo ya creó `develop`, usar esa
rama y sincronizar la tarea como se explica abajo. Este arranque excepcional
conserva el trabajo existente; las siguientes tareas nacen de `develop`.

## Trabajo diario

Con los cambios anteriores confirmados o guardados explícitamente, actualizar
la rama de integración y crear una tarea (nombre de ejemplo):

```powershell
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feature/backend-validacion
```

Implementar, ejecutar las pruebas relevantes y revisar el diff. Agregar rutas
específicas; el siguiente ejemplo solo aplica si se cambiaron esos directorios:

```powershell
git status --short
git diff
git add api tests
git diff --cached
git commit -m "fix(api): validar parámetros de parcelas"
git push -u origin feature/backend-validacion
```

Formato sugerido para commits y título del PR: `tipo(area): descripción`.
Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`. Describir el resultado,
no usar mensajes como `cambios` o `final`. Abrir un PR con **base `develop`** y
**compare la rama de tarea**, completar la plantilla y pedir revisión.

## Sincronizar y resolver conflictos

Con el trabajo de la tarea confirmado, traer la integración a la rama actual:

```powershell
git fetch origin
git merge origin/develop
```

Si hay conflictos, revisar `git status`, editar los archivos y acordar la
resolución con el autor del otro cambio cuando sea necesario. No elegir
automáticamente todos los cambios de un lado. Agregar los archivos resueltos
por nombre, ejecutar las pruebas y terminar con `git commit` y `git push`.
Para cancelar una resolución sin terminar, usar `git merge --abort`.

No usar force push ni reescribir el historial de ramas compartidas. Si
`pull --ff-only` falla, revisar la divergencia antes de continuar; no resolverla
con `reset --hard`. Para deshacer trabajo ya integrado, preparar un revert en
una rama de tarea y enviarlo por PR.

## Revisión e integración

Antes de integrar una tarea:

- Confirmar base `develop`, alcance y descripción completa.
- Revisar el diff, errores, compatibilidad del contrato y pruebas pertinentes.
- Obtener al menos una aprobación de otro integrante y resolver comentarios.
- Para backend ejecutar `.\.venv\Scripts\python.exe -m pytest tests -q -W error`.
  Para documentación basta validar enlaces, comandos y diff; explicarlo en el PR.
- Integrar tareas con **Squash and merge** para dejar un commit por cambio.

Después de integrar, eliminar solo la rama de tarea en GitHub cuando nadie la
esté usando. Actualizar `develop` y crear una nueva rama para el siguiente trabajo;
no reutilizar una rama integrada mediante squash. No eliminar `main` ni `develop`.

## Entrega de una versión

Cuando `develop` esté validada, abrir un PR con **base `main`** y **compare
`develop`**. Indicar cambios incluidos, pruebas, limitaciones y pasos de ejecución.
Integrar este PR con **Create a merge commit**, no squash ni rebase, para preservar
el historial compartido entre las dos ramas permanentes. No eliminar `develop`.

Después sincronizar `develop` con `main` (directorio de trabajo limpio):

```powershell
git fetch origin
git switch -c feature/sync-main origin/develop
git merge origin/main
git push -u origin feature/sync-main
```

Abrir `feature/sync-main → develop` e integrarlo también con **Create a merge
commit**: esta excepción conserva la relación de historial, no debe usar squash.
Si ambas ramas ya apuntan al mismo historial y no hay diferencias, no se requiere
un PR vacío. El release y tag `v1.0-agrocebada` se crearán cuando se autorice la
entrega final, sobre la versión aprobada de `main`.

## Configuración propuesta en GitHub

El responsable debe configurar las protecciones; esta guía no las aplica:

- En `main` y `develop`: exigir PR, una aprobación de otra persona y resolución
  de conversaciones; bloquear force push y eliminación de ramas permanentes.
- Permitir squash para tareas y merge commits para entregas/sincronizaciones.
  No exigir historial lineal, porque impediría estos últimos.
- Cuando exista CI, exigir el check real de tests. Actualmente la evidencia es
  manual; no declarar que existe un check automatizado sin haberlo configurado.

La plantilla está en [`.github/pull_request_template.md`](../.github/pull_request_template.md).
Para que GitHub la use automáticamente de forma habitual, debe estar integrada
en la rama predeterminada del repositorio; hasta entonces se puede copiar al PR.

## Datos y contratos

No subir entornos virtuales, secretos, datasets locales ni modelos serializados.
Verificar el diff incluso cuando exista `.gitignore`. Los resultados sintéticos
deben seguir identificados como mock. Los cambios de API se coordinan mediante
[el contrato](api-contract.md); no inventar columnas ni unidades de Data/ML.
Todo cambio que afecte features o predicciones de 2025 debe respetar el corte
de datos del 31 de octubre de 2025 y documentar cómo se comprobó.
