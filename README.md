# JamnexCFE

Sistema de monitoreo y administración de dispositivos Android, tarjetas SIM,
consumo de datos móviles, conectividad y métricas técnicas.

## Tecnologías utilizadas

### Backend y API

- **Python 3**
- **Django 5**
- **Django REST Framework**
- **SimpleJWT** para autenticación con tokens JWT
- **PostgreSQL** para producción
- **SQLite** como alternativa local
- **psycopg** como adaptador de PostgreSQL
- **django-cors-headers** para CORS
- **python-dotenv** para variables de entorno
- **Gunicorn** como servidor WSGI
- **WhiteNoise** para archivos estáticos
- **openpyxl** para exportación de reportes Excel

### Frontend web

- **Vue 3**
- **Vite**
- **JavaScript**
- **Vue Router**
- **Pinia**
- **Axios**
- **Bootstrap 5**

### Aplicación móvil

- **Flutter**
- **Dart**
- **Android SDK**
- **Kotlin** para integración nativa de Android
- **AndroidX WorkManager** para sincronización en segundo plano
- **battery_plus** para batería
- **connectivity_plus** para conectividad
- **device_info_plus** para información del dispositivo
- **shared_preferences** para persistencia local
- **http** para comunicación HTTP

### Servicios nativos de Android utilizados

- `SubscriptionManager` para detectar las SIM activas y sus ranuras.
- `NetworkStatsManager` para consultar el consumo de datos móviles.
- `WorkManager` para sincronización periódica.
- `ConnectivityManager` para detectar conectividad.
- `BatteryManager` para estado, porcentaje y temperatura de batería.
- `ActivityManager` para memoria RAM.
- `StatFs` para almacenamiento.

## Estructura del proyecto

```text
JamnexCFE/
├── backend/       API Django, modelos, autenticación y base de datos
├── frontend/      Panel administrativo web en Vue
├── mobile/        Aplicación Flutter para Android
├── README.md
└── .gitignore
```

## Componentes principales

### Backend

El backend expone la API bajo el prefijo `/api/` y contiene módulos para:

- Usuarios, roles y permisos.
- Áreas y trabajadores.
- Registro y monitoreo de dispositivos.
- SIMs, operadores y asignaciones.
- Historial de SIM por dispositivo y ranura.
- Consumo de datos móviles.
- Redes y tipo de conexión.
- Batería, RAM y almacenamiento.
- Reportes y exportaciones.
- Auditoría de acciones.

Rutas principales:

```text
/api/auth/
/api/dispositivos/
/api/device/
/api/sims/
/api/consumos/
/api/redes/
/api/reportes/
/api/bateria/
/api/ram/
/api/almacenamiento/
```

### Frontend

El panel permite:

- Consultar dispositivos registrados.
- Ver el estado en línea o fuera de línea.
- Revisar información técnica.
- Consultar SIMs y consumo.
- Filtrar SIMs activas, dadas de baja y compartidas.
- Dar de baja una SIM de forma reversible.
- Reactivar una SIM.
- Eliminar una SIM definitivamente con confirmación.
- Consultar historial de dispositivos de cada SIM.
- Exportar reportes.

### Aplicación Android

La aplicación móvil:

1. Registra o identifica el dispositivo.
2. Envía información técnica del equipo.
3. Detecta las SIM activas y su ranura.
4. Reporta el estado de las SIM.
5. Envía el consumo diario y semanal de datos móviles.
6. Reporta red, batería, RAM y almacenamiento.
7. Reintenta eventos pendientes cuando una sincronización falla.
8. Ejecuta sincronización automática en segundo plano.

## Lógica de SIMs

### Identificación

La SIM se busca principalmente por ICCID normalizado. Si no hay ICCID
disponible, se utiliza el identificador de suscripción o un identificador
derivado del dispositivo y la ranura.

Cada SIM conserva:

- ICCID.
- Número telefónico.
- Operador.
- Dispositivo actual.
- Ranura.
- Tipo físico o eSIM.
- Estado activo.
- Historial de dispositivos.

### Estados

- **En uso:** la SIM está activa.
- **Dada de baja:** la SIM está desactivada de forma reversible.
- **Eliminada:** la SIM y sus relaciones históricas con la SIM se eliminan
  definitivamente.

Dar de baja una SIM no elimina su historial ni su consumo. Reactivarla vuelve
a ponerla disponible. Si vuelve a reportarse desde un dispositivo, el reporte
la marca como activa.

### Dos SIMs en el mismo dispositivo

Un equipo con doble SIM mantiene dos registros independientes. La interfaz
identifica cada línea por su ranura:

```text
Dispositivo X - Ranura 1
Dispositivo X - Ranura 2
```

El historial se compacta únicamente en la interfaz cuando hay registros
consecutivos del mismo dispositivo y la misma ranura. No se borran datos de la
base de datos.

## Historial y consumo

Cada presencia de una SIM se registra en `HistorialSim`, con:

- Dispositivo.
- Ranura.
- Fecha de inicio.
- Fecha de finalización.
- Último reporte.
- Consumo asociado.

El consumo se relaciona con la combinación:

```text
dispositivo + SIM + fecha
```

El contador de sincronización también está separado por:

```text
dispositivo + fecha + SIM
```

Esto evita mezclar el acumulado de SIM 1 con SIM 2 y permite conservar el
consumo cuando una SIM cambia de dispositivo.

## Sincronización automática

La aplicación Android realiza:

- Una sincronización al iniciar.
- Una sincronización periódica aproximadamente cada **2 horas**.
- Una sincronización adicional al detectar conexión Wi-Fi.
- Reintentos de eventos que no pudieron enviarse.

Android puede retrasar la ejecución exacta por restricciones de batería o del
sistema operativo.

## Alertas de reportes SIM

La aplicación registra `sims_reported_at` cada vez que el dispositivo reporta
el estado de sus SIMs.

- Si reporta cero SIMs recientemente, se muestra el resultado del reporte.
- Si pasan **72 horas o más** desde el último reporte, se muestra la alerta:
  **“Este dispositivo no ha enviado datos de ninguna SIM”**.
- Si tenía SIMs y deja de actualizarse durante 72 horas, se muestra que el
  reporte está desactualizado.
- La vista web revisa automáticamente la información cada 30 segundos.

## Requisitos

- Python 3.10 o superior.
- Node.js 18 o superior.
- npm.
- Flutter 3 o compatible con Dart `>=3.3.0 <4.0.0`.
- Android SDK con soporte para la versión configurada por Flutter.
- PostgreSQL para producción o SQLite para desarrollo local.

## Configuración del backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La API queda disponible normalmente en:

```text
http://127.0.0.1:8000/api/
```

### Variables de entorno del backend

Las variables principales son:

```text
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
USE_POSTGRES=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=
```

Si `DATABASE_URL` está definida, se utiliza PostgreSQL. Si no se configura
PostgreSQL, el proyecto utiliza SQLite localmente.

## Configuración del frontend

```powershell
cd frontend
npm install
npm run dev
```

Para una compilación de producción:

```powershell
npm run build
```

Configura la URL de la API en `frontend/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Configuración de la aplicación móvil

```powershell
cd mobile
flutter pub get
flutter run
```

Para generar un APK:

```powershell
flutter build apk
```

La aplicación necesita que la URL del backend sea accesible desde el
dispositivo Android. `localhost` dentro del celular apunta al propio celular;
para un backend local normalmente se utiliza la IP de la computadora en la
misma red Wi-Fi o `10.0.2.2` si se usa el emulador de Android.

## Migraciones importantes

Después de cambiar modelos o recibir una versión nueva del proyecto:

```powershell
cd backend
python manage.py makemigrations
python manage.py migrate
```

La lógica de contadores de consumo por SIM requiere aplicar la migración:

```text
backend/consumos/migrations/0003_consumosyncstate_sim_scope.py
```

## Seguridad y operación

- No subir archivos `.env` ni credenciales al repositorio.
- Cambiar `SECRET_KEY` antes de producción.
- Usar `DEBUG=False` en producción.
- Configurar `ALLOWED_HOSTS`, CORS y CSRF con dominios reales.
- Usar HTTPS para la API y el panel.
- Configurar una base PostgreSQL administrada para producción.
- Aplicar migraciones antes de iniciar una nueva versión.
- Mantener permisos de ubicación, teléfono y estado de SIM según la versión de
  Android.

## Estado del proyecto

El proyecto contiene backend, panel web y aplicación Android integrados para
monitorear dispositivos, SIMs y consumo móvil. Antes de un despliegue
productivo se recomienda ejecutar el build del frontend, las pruebas de
Django y una prueba real de sincronización desde un dispositivo Android.