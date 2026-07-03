# Work Item Systray — Tasks

Proveedor genérico de [`work_item_systray`](https://github.com/csrocha/work_item_systray):
convierte cualquier `project.task` en un work item trabajable desde el
systray, sin nada específico de TaskJuggler.

- **Candidatos**: mis tareas abiertas con `date_deadline` esta semana (o la
  próxima si no hay ninguna).
- **Cierre de período**: crea una línea de `account.analytic.line` (parte de
  horas) combinando la nota de inicio ("qué se iba a hacer") con la de
  cierre ("qué se logró").
- **Cronómetro**: cuenta regresiva contra `remaining_hours` cuando la tarea
  tiene `allocated_hours`; si no, cuenta ascendente (comportamiento por
  defecto del systray base).

Ver [`insight_project`](https://github.com/csrocha/insight_project) para la
capa de decoración TaskJuggler (⚡ camino crítico, ❗ revisión pendiente,
`blocked`) montada encima de este addon.

## License

OPL-1 — Cristian S. Rocha <csrocha@gmail.com>
