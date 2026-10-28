# Sistema de Visitas a Empresas

Sistema web para gestionar el procedimiento **ITQ-VI-PO-001 – Visitas a empresas** del Instituto Tecnológico de Querétaro: desde la solicitud del docente, la aprobación, la gestión con la empresa y el transporte, hasta el reporte de resultados y las constancias.

**Tecnologías:** Python 3.12+ · Django 5.2 · PostgreSQL 16 · Bootstrap 5

## Requisitos
- [Python 3.12 o superior](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para PostgreSQL)

## Instalación (cada integrante, una sola vez)

```bash
# 1. Clonar el repositorio y entrar a develop
git clone https://github.com/cesarzav29/Visitas-Industriales.git
cd Visitas-Industriales
git checkout develop

# 2. Crear y activar el entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear tu archivo .env
# Windows:
copy .env.example .env
# Mac / Linux:
cp .env.example .env

# 5. Levantar PostgreSQL
docker compose up -d

# 6. Crear las tablas y tu usuario administrador
python manage.py migrate
python manage.py createsuperuser

# 7. Correr el servidor
python manage.py runserver
```

Abre http://127.0.0.1:8000 → debe decir **"El proyecto está funcionando"**.

## Forma de trabajo (Scrum + Jira)
Lee [CONTRIBUTING.md](CONTRIBUTING.md) antes de tu primer commit.

## Equipo
| Integrante | Rol |
|---|---|
| César | Scrum Master · repositorio y diagrama de flujo |
| Mildret | Proyecto Django y base de datos |
| Ian | Diagrama entidad-relación y maquetas |
| Roberto | Backlog y despliegue |

Tablero en Jira: **TecNM_Qro_Visitas** (clave `TQV`).
