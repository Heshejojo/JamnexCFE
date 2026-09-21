# Backend - Django + DRF

Este directorio será el proyecto Django principal para Agente CFE.

## Objetivo

- API REST con Django REST Framework
- Autenticación basada en JWT
- Registro y administración de usuarios, roles, trabajadores, dispositivos y SIMs
- Gestión de alertas, reportes y auditoría

## Base de datos

El backend usa PostgreSQL cuando `DATABASE_URL` está definida en `backend/.env`. La URL puede apuntar a PostgreSQL 17 o a Neon y debe incluir `sslmode=require` cuando el proveedor lo solicite. Si no existe, se usa SQLite local como respaldo.

```env
DATABASE_URL=postgresql://usuario:contraseña@host/neondb?sslmode=require
```

Una vez configurada la URL, ejecuta:

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

El módulo `areas` ya incluye el modelo, la migración `0001_initial`, los endpoints `GET/POST /api/areas/` y `GET/PUT/DELETE /api/areas/<id>/`.
