---
name: informe-estado-fixy-lunes
description: Informe de estado semanal del portfolio FIXY desde Asana, cada lunes a la mañana
---

Generá un informe de estado semanal del portfolio de proyectos de FIXY usando el conector de Asana. El usuario es Javier Bartaburu (rol: Operaciones), respondé en español.

Pasos:
1. Traé todos los proyectos de Asana con get_projects (incluí opt_fields: name, owner.name, task_counts, current_status_update, modified_at).
2. Traé las tareas abiertas del usuario con get_my_tasks (completed_since="now", opt_fields: name, due_on, projects.name, completed).
3. IMPORTANTE: filtrá el ruido — ignorá las tareas automáticas de Asana del tipo "Considera la posibilidad de actualizar el progreso de tu proyecto", "Es hora de actualizar tus objetivos" y "Actualiza y cierra tus objetivos". No son trabajo real.
4. Marcá como vencidas las tareas cuya due_on sea anterior a la fecha de hoy.

Armá el informe en markdown con esta estructura, siguiendo el formato de la skill operations:status-report:
- Título "Status Report: Portfolio FIXY — [mes/año]" con autor y fecha de hoy.
- Resumen ejecutivo (3-4 frases): qué está sano, qué necesita atención, riesgos clave.
- Estado general con semáforo 🟢/🟡/🔴.
- Tabla de Métricas clave por proyecto: Total / Completas / Abiertas / % Avance / Estado (semáforo según % de avance: <30% 🔴, 30-70% 🟡, >70% 🟢).
- Tabla "En progreso" con tareas relevantes (item, proyecto, vence, nota — marcando las vencidas).
- Tabla de Riesgos e incidencias (riesgo, impacto, mitigación, owner).
- Tabla de Decisiones necesarias.
- Prioridades del próximo período (lista numerada).

Presentá el informe en el chat con present_files solo si generás un archivo; si no, mostralo directo en el chat. Mantenelo conciso y accionable, liderando con el titular.