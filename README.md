# Sistema de Bodega SEREMI Salud Araucanía

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

## Nota Importante
Este repositorio incluye la base de datos SQLite con todos los datos para facilitar la migración entre equipos.