# Sistema de Bodega SEREMI Salud Araucanía

Sistema web integral para la gestión de inventario y control de productos de la bodega de SEREMI Salud Araucanía. Desarrollado con Django, permite el manejo completo de productos, lotes, stock, usuarios y generación de reportes con seguimiento de vencimientos.

## 📋 Características Principales

- **Gestión de Inventario**: Control completo de productos, lotes y stock
- **Control de Vencimientos**: Monitoreo automático de fechas de vencimiento con alertas
- **Gestión de Usuarios**: Sistema de permisos con roles diferenciados (Administrador, Bodeguero, Visualizador)
- **Reportes y PDFs**: Generación de actas de ingreso/salida con firmas digitales
- **Interfaz Moderna**: UI responsiva con Bootstrap y componentes intuitivos
- **Filtros Avanzados**: Sistema de filtrado en tiempo real para todas las vistas
- **Auditoría**: Registro completo de movimientos y cambios en el sistema

## Instalación y Configuración

### 1. Clonar el repositorio (rama dev)
```bash
git clone -b dev https://github.com/Robinson2024/bodega_seremi.git
cd bodega_seremi
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual (Windows)
```bash
venv\Scripts\activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. La base de datos ya está incluida
El archivo `sistema_bodega/db.sqlite3` contiene todos los datos y está incluido en el repositorio.

### 6. Ejecutar servidor
```bash
cd sistema_bodega
python manage.py runserver
```

El sistema estará disponible en: http://127.0.0.1:8000/

## 🏗️ Estructura del Proyecto

```
bodega_seremi/
├── README.md                     # Documentación principal
├── requirements.txt              # Dependencias del proyecto
└── sistema_bodega/              # Aplicación Django principal
    ├── manage.py                # Comando de gestión de Django
    ├── db.sqlite3              # Base de datos SQLite
    ├── sistema_bodega/         # Configuración del proyecto
    │   ├── settings.py         # Configuraciones principales
    │   ├── urls.py            # URLs principales
    │   └── wsgi.py            # Configuración WSGI
    ├── accounts/              # Aplicación de gestión de usuarios
    │   ├── models.py          # Modelos de datos
    │   ├── views.py           # Lógica de vistas
    │   ├── urls.py            # URLs de la aplicación
    │   ├── forms.py           # Formularios
    │   ├── admin.py           # Configuración del admin
    │   └── templates/         # Templates HTML
    ├── static/                # Archivos estáticos
    │   ├── css/              # Hojas de estilo
    │   ├── js/               # JavaScript
    │   └── images/           # Imágenes
    └── [scripts utilitarios]  # Scripts de mantenimiento y validación
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.1.3**: Framework web principal
- **Python 3.x**: Lenguaje de programación
- **SQLite**: Base de datos
- **Pillow**: Procesamiento de imágenes
- **ReportLab**: Generación de PDFs

### Frontend
- **Bootstrap 5**: Framework CSS
- **HTML5/CSS3**: Estructura y estilos
- **JavaScript**: Interactividad del cliente
- **jQuery**: Manipulación del DOM

### Herramientas de Desarrollo
- **Django Admin**: Panel de administración
- **Django Forms**: Manejo de formularios
- **Django Auth**: Sistema de autenticación

## 📊 Modelos de Datos Principales

### Usuario (CustomUser)
- Información personal y profesional
- Roles: Administrador, Bodeguero, Visualizador
- Datos de contacto y firma digital

### Producto
- Información básica del producto
- Categorización y descripción
- Control de stock mínimo

### Lote
- Gestión de lotes por producto
- Control de fechas de vencimiento
- Seguimiento de stock por lote

### Movimiento
- Registro de entradas y salidas
- Trazabilidad completa
- Generación automática de actas

## 🔐 Sistema de Permisos

### Administrador
- Acceso completo al sistema
- Gestión de usuarios y permisos
- Configuración del sistema

### Bodeguero
- Gestión de inventario
- Registro de movimientos
- Generación de reportes

### Visualizador
- Solo lectura de inventario
- Consulta de reportes
- Sin permisos de modificación

## 📱 Funcionalidades Principales

### Dashboard
- Resumen del estado del inventario
- Alertas de vencimientos próximos
- Estadísticas de movimientos

### Gestión de Productos
- CRUD completo de productos
- Control de stock mínimo
- Búsqueda y filtrado avanzado

### Control de Lotes
- Seguimiento individual por lote
- Alertas automáticas de vencimiento
- Gestión de fechas críticas

### Reportes y PDFs
- Actas de ingreso y salida
- Reportes de vencimientos
- Firmas digitales automáticas
- Exportación en múltiples formatos

### Gestión de Usuarios
- Creación y edición de perfiles
- Asignación de roles y permisos
- Control de acceso granular

## 🔧 Scripts Utilitarios

El sistema incluye varios scripts de mantenimiento y validación:

- **Diagnóstico del Sistema**: Verificación de integridad de datos
- **Corrección de Stock**: Sincronización automática de inventario
- **Limpieza de Datos**: Eliminación de registros órfanos
- **Migración de Datos**: Herramientas de importación/exportación
- **Validación de Formularios**: Verificación de integridad

## 🚀 Uso del Sistema

### Primer Acceso
1. Acceder a http://127.0.0.1:8000/
2. Usar credenciales de administrador por defecto
3. Cambiar contraseñas por seguridad
4. Configurar usuarios adicionales

### Flujo de Trabajo Típico
1. **Registro de Productos**: Crear productos en el sistema
2. **Ingreso de Lotes**: Registrar lotes con fechas de vencimiento
3. **Control de Stock**: Monitorear niveles de inventario
4. **Gestión de Salidas**: Registrar entregas y consumos
5. **Generación de Reportes**: Crear actas y documentos PDF

## 🔍 Filtros y Búsquedas

Cada vista incluye filtros avanzados:
- **Búsqueda por texto**: Nombre, código, descripción
- **Filtros por fecha**: Rangos de vencimiento, ingreso
- **Filtros por estado**: Activo, vencido, por vencer
- **Filtros por usuario**: Responsable, creador
- **Botón "Limpiar Filtros"**: Reseteo rápido de búsquedas

## 📄 Generación de PDFs

### Características de los PDFs
- **Encabezados profesionales**: Logo y datos de SEREMI
- **Información detallada**: Productos, cantidades, fechas
- **Firmas digitales**: Posicionadas automáticamente al final
- **Formato profesional**: Diseño limpio y organizado

### Tipos de Documentos
- Actas de ingreso de productos
- Actas de salida de productos
- Reportes de vencimientos
- Listados de inventario

## ⚠️ Consideraciones Importantes

### Seguridad
- Cambiar contraseñas por defecto
- Configurar permisos apropiados
- Realizar respaldos regulares de la base de datos

### Mantenimiento
- Ejecutar scripts de diagnóstico periódicamente
- Monitorear espacio en disco
- Verificar integridad de datos regularmente

### Rendimiento
- La base de datos SQLite es adecuada para uso local/pequeño
- Para mayor escala, considerar PostgreSQL o MySQL
- Optimizar consultas en caso de gran volumen de datos

## 🆘 Solución de Problemas Comunes

### Error de Migración
```bash
cd sistema_bodega
python manage.py makemigrations
python manage.py migrate
```

### Problemas de Dependencias
```bash
pip install --upgrade -r requirements.txt
```

### Reset de Base de Datos (solo desarrollo)
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📞 Soporte y Contacto

Para soporte técnico o consultas sobre el sistema:
- **Desarrollador**: Robinson Bravo
- **Institución**: SEREMI Salud Araucanía
- **Repositorio**: https://github.com/Robinson2024/bodega_seremi

## 📝 Notas de Versión

### Versión Actual
- Sistema completamente funcional
- Base de datos incluida con datos de ejemplo
- Scripts de mantenimiento implementados
- Interfaz optimizada y responsiva

### Próximas Mejoras
- Integración con APIs externas
- Reportes más avanzados
- Notificaciones automáticas
- Dashboard mejorado

## 📄 Licencia

Este sistema fue desarrollado específicamente para SEREMI Salud Araucanía y está sujeto a las políticas de la institución.

---

**Nota Importante**: Este repositorio incluye la base de datos SQLite con todos los datos para facilitar la migración entre equipos. En un entorno de producción, se recomienda usar una base de datos más robusta y configurar respaldos automáticos.