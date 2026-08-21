# Sistema de Bodega SEREMI Salud Araucanía

Aplicación Django para inventario institucional: lotes FIFO, actas de entrega, bincard y control de vencimientos.

**Última actualización:** agosto 2026

## Qué incluye

- Productos con código de barra correlativo, categorías y stock
- Lotes y vencimientos con salida **FIFO**
- Actas de entrega en PDF
- **Bincard** por producto (búsqueda por código o nombre, columna OC)
- **Bincard general** (filtros, Excel de movimientos y bincard global con saldo)
- **Corregir ingreso** (solo Administrador Auditor): ajusta transacción, lote y stock sin dejar el kardex negativo
- Cuatro roles con menús distintos

## Roles

| Rol | Bodega (salidas, stock, vencimientos) | Usuarios, departamentos, categorías | Corregir ingreso | Panel Django `/admin/` |
|---|---|---|---|---|
| Usuario de Bodega | Sí | No | No | No |
| Auditor | Solo consulta (listar, documentos, informes) | No | No | No |
| Administrador | Sí | Sí | No | No |
| Administrador Auditor | Sí | Sí | Sí | Sí (`is_staff`) |

El **Administrador** no puede cambiarse el propio rol. El **Administrador Auditor** sí.

## Acceso local (Docker)

Requisitos: Docker Desktop.

```bash
copy .env.example .env
docker compose up --build -d
```

- URL: http://localhost:8010/
- Login: **RUT sin puntos ni guiones** + contraseña
- Base de datos: `data/db/db.sqlite3` (volumen; no va en Git)

Tras cambiar código hay que reconstruir: el código **no se monta** en el contenedor.

```bash
docker compose up --build -d
```

## Variables de entorno (`.env`)

Plantilla: `.env.example`.

| Variable | Uso |
|---|---|
| `DJANGO_DEBUG` | En servidor: `False` |
| `DJANGO_SECRET_KEY` | Clave propia; no usar la de ejemplo |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos (incluir `10.3.184.27` en el servidor) |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes con esquema, p. ej. `http://10.3.184.27:8010` |
| `DJANGO_DB_PATH` | En Docker: `/app/db/db.sqlite3` |

**No suba `.env` ni `*.sqlite3` al repositorio.**

## Pruebas

Desde `sistema_bodega/`:

```bash
python manage.py test accounts.test_qa accounts.tests --verbosity=2
```

No modifica `data/db/db.sqlite3`.

## Estructura relevante

```
bodega_seremi/
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh          # migrate + collectstatic + gunicorn
├── deploy/nginx.conf      # puerto 8010 → gunicorn
├── .env.example
├── data/db/               # SQLite persistente (solo .gitkeep en Git)
├── MANUAL_DE_USUARIO_COMPLETO.md
└── sistema_bodega/
    ├── manage.py
    ├── accounts/          # modelos, vistas, plantillas, migraciones, tests
    └── sistema_bodega/    # settings, urls, wsgi
```

## Dependencias

Ver `requirements.txt`: Django 5.0.3, gunicorn, openpyxl, ReportLab, Pillow, django-widget-tweaks, pytz. Imagen: Python 3.11.

## Backup

Antes de un rebuild o de llevar el sistema al servidor, copie `data/db/db.sqlite3`. Un `docker compose down -v` borra volúmenes nombrados (estáticos); la SQLite vive en `./data/db` y no se borra con `-v` salvo que elimine esa carpeta.

Manual de operación: `MANUAL_DE_USUARIO_COMPLETO.md`.
