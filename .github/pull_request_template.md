## Qué cambia y por qué

<!-- Describe el problema y el comportamiento final. Incluye tarea/issue si existe. -->

## Alcance e integración

- Rama origen:
- Rama destino: <!-- develop para tareas; main para entrega desde develop -->
- Áreas afectadas:
- Contratos o dependencias con otros integrantes: <!-- Indica cambios o “Sin cambios”. -->

## Validación

<!-- Escribe comandos/pasos y resultados reales. No marques pruebas no ejecutadas.
Backend: .\.venv\Scripts\python.exe -m pytest tests -q -W error
Para documentación, explica la revisión de enlaces/comandos/diff.
Para cambios visuales, añade una captura si ayuda a revisarlos. -->

- Cómo probar:
- Resultado:
- Limitaciones o pruebas pendientes:

## Checklist

- [ ] La rama destino es correcta y el PR tiene un objetivo concreto.
- [ ] Revisé el diff y no incluye secretos, datasets locales ni artefactos de modelos.
- [ ] Documenté la validación realizada y actualicé tests/documentación cuando aplica.
- [ ] Los contratos afectados están coordinados con sus consumidores, o no cambiaron.
- [ ] Si afecta datos/ML, los mocks están identificados y se respeta el corte de octubre de 2025; si no aplica, lo indiqué abajo.

<!-- Notas de “no aplica”, riesgos concretos o instrucciones adicionales, si existen. -->
