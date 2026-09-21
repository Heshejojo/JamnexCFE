# Agente CFE

Agente CFE es una plataforma empresarial para administrar dispositivos Android y SIM corporativas asignadas a trabajadores.

## Estructura principal

- backend/: Django + Django REST Framework
- frontend/: Vue.js + Bootstrap
- mobile/: Flutter + Android
- docs/: documentación del proyecto

## Fase actual

El entorno local incluye API, panel administrativo y agente Flutter/Android.

La base de datos se selecciona mediante `backend/.env`: si existe `DATABASE_URL`, Django usa PostgreSQL (incluido Neon); si no, usa SQLite local en `backend/db.sqlite3`.

## Reglas de desarrollo aplicadas

- Los servicios de producción no se crean desde el entorno local.
- Las variables se mantienen en archivos `.env` fuera de Git.
- El teléfono físico usa `--dart-define=API_BASE_URL=http://192.168.1.74:8000/api`.

## Arranque local

```powershell
cd backend; .\.venv\Scripts\Activate.ps1; python manage.py runserver 0.0.0.0:8000
cd frontend; $env:Path="C:\Program Files\nodejs;$env:Path"; npm.cmd run dev
cd mobile; flutter run -d edge
```

Para usar PostgreSQL 17 o Neon, copia la URL de conexión en `backend/.env`:

```env
DATABASE_URL=postgresql://usuario:contraseña@host/neondb?sslmode=require
```

Después aplica las migraciones:

```powershell
cd backend; python manage.py migrate
```
