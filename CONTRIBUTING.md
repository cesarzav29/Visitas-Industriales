# Cómo trabajamos

## Ramas
- `main` → versión estable que se entrega. Nadie sube directo.
- `develop` → integración del trabajo del equipo. Nadie sube directo.
- Una rama por tarea, creada desde `develop`, con la clave de Jira:
  `TQV-12-login-docente`

```bash
git checkout develop
git pull
git checkout -b TQV-12-login-docente
# ... trabajas ...
git add .
git commit -m "TQV-12 Agrega login para docentes"
git push -u origin TQV-12-login-docente
```
Luego abres un **Pull Request hacia `develop`** en GitHub.

## Commits
Siempre empiezan con la clave de Jira, así aparecen en la tarjeta:
`TQV-12 Descripción corta en presente`

## Definition of Done
Una tarea está **Lista** cuando:
1. El código está en GitHub en su rama con la clave de Jira.
2. Otro integrante revisó y aprobó el Pull Request.
3. Funciona en local y no rompe lo anterior.
4. Cumple sus criterios de aceptación.
5. La tarjeta se movió a "Listo" en Jira.

## Ceremonias
- **Daily:** 10 min diarios — ¿qué hice?, ¿qué haré?, ¿qué me bloquea?
- **Sprint Planning:** inicio de cada sprint.
- **Sprint Review:** con el profe al final del sprint.
- **Retrospectiva:** al final del sprint.
