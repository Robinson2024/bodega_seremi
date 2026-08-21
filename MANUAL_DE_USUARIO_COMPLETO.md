# Manual de usuario — Sistema de Bodega SEREMI Salud Araucanía

**Institución:** SEREMI Salud Araucanía  
**Versión:** 2.0 (agosto 2026)  
**Desarrollo:** Robinson Bravo

Este manual describe lo que el sistema hace hoy: menús, roles, bincard, corrección de ingresos y flujos de bodega.

---

## Índice

1. [Introducción](#1-introducción)
2. [Acceso](#2-acceso)
3. [Roles y menú](#3-roles-y-menú)
4. [Inicio](#4-inicio)
5. [Productos y stock](#5-productos-y-stock)
6. [Salida de productos y actas](#6-salida-de-productos-y-actas)
7. [Informes: bincard](#7-informes-bincard)
8. [Corregir ingreso](#8-corregir-ingreso)
9. [Control de vencimientos](#9-control-de-vencimientos)
10. [Departamentos, categorías y usuarios](#10-departamentos-categorías-y-usuarios)
11. [Preguntas frecuentes](#11-preguntas-frecuentes)
12. [Soporte](#12-soporte)

---

## 1. Introducción

El sistema registra ingresos, stock por lotes, entregas a programas y el historial (bincard). Los productos con fecha de vencimiento salen por **FIFO** (primero el lote que vence antes).

Funciones principales:

- Inventario con código de barra automático
- Ingresos con guía, factura, OC y RUT de proveedor
- Lotes y alertas de vencimiento
- Actas de entrega en PDF
- Bincard por producto y bincard general (Excel)
- Corrección de un ingreso mal digitado (solo Administrador Auditor)

---

## 2. Acceso

- **URL local:** http://localhost:8010/
- **Servidor institucional:** `http://10.3.184.27:8010/`
- **Usuario:** RUT **sin puntos ni guiones** (ejemplo: `12345678K`)
- **Contraseña:** la asignada por quien gestiona usuarios

Normas:

- No compartir credenciales
- Cerrar sesión al terminar
- Si olvida la clave, pida el cambio a un Administrador o Administrador Auditor (Gestión de usuarios)

---

## 3. Roles y menú

Hay **cuatro** perfiles. El menú cambia según el rol.

| Función | Usuario de Bodega | Auditor | Administrador | Administrador Auditor |
|---|---|---|---|---|
| Inicio, Listar productos, Documentos, Informes | Sí | Sí | Sí | Sí |
| Salida de productos | Sí | No | Sí | Sí |
| Agregar (registrar producto, agregar stock) | Sí | No | Sí | Sí |
| Corregir ingreso | No | No | No | Sí |
| Control de vencimientos | Sí | No | Sí | Sí |
| Departamentos y categorías | No | No | Sí | Sí |
| Gestión de usuarios y roles | No | No | Sí | Sí |
| Panel de administración Django | No | No | No | Sí |

### Barra de menú (botones)

- **Inicio** — todos
- **Salida de Productos** — bodega y ambos administradores
- **Listar Productos** — todos
- **Documentos** — listado de actas PDF; todos
- **Informes**
  - **Bincard** — historial de un producto
  - **Bincard general** — movimientos de todos, con filtros y Excel
- **Agregar**
  - Registrar producto
  - Agregar stock
  - **Corregir ingreso** (solo Administrador Auditor)
- **Gestión de Departamentos** / **Gestión de Categorías** — ambos administradores
- **Control de Vencimientos** — bodega y ambos administradores
- **Gestión de Usuarios y Roles** — ambos administradores
- **Panel de Administración** — solo Administrador Auditor (pide de nuevo la contraseña)
- **Cerrar sesión** — todos

### Qué distingue a cada rol

**Usuario de Bodega.** Operación diaria: registrar, ingresar stock, entregar, consultar vencimientos e informes.

**Auditor.** Solo consulta: listar, actas y bincard. No entrega ni agrega stock. No entra a vencimientos ni a usuarios.

**Administrador.** Opera bodega **y** gestiona usuarios, departamentos y categorías. **No** corrige ingresos ni entra al panel Django. **No** puede cambiarse el propio rol (debe pedirlo a un Administrador Auditor).

**Administrador Auditor.** Igual que Administrador, más **Corregir ingreso** y el **panel Django**. Puede cambiarse el propio rol. Pensado para jefatura o informática.

---

## 4. Inicio

Tras el login aparece el panel con:

- Distribución de productos según stock (bajo / medio / alto)
- Resumen de vencimientos (vencidos, críticos, precaución, normales)
- Accesos del menú superior

El gráfico cuenta productos **con stock mayor a cero**.

---

## 5. Productos y stock

### 5.1 Listar productos

**Listar Productos.** Filtros: código, nombre y categoría. Botones **Filtrar**, **Limpiar filtros** y **Exportar a Excel**.

El stock que se ve es el vigente para salidas. En productos con vencimiento coincide con la **suma de lotes**.

### 5.2 Registrar producto

**Agregar → Registrar Producto.**

- El **código de barra** se asigna solo (desde 100000) y no se edita
- Campo **Nombre del producto**
- Categoría, stock inicial (puede ser 0)
- Guía, factura, OC y RUT de proveedor (opcionales)
- Casilla **¿Este producto tiene fecha de vencimiento?**  
  La fecha **solo se pide si marca esa casilla**. Si hay stock inicial y vencimiento, se crea el lote 1 y la primera entrada del bincard.

### 5.3 Agregar stock

**Agregar → Agregar Stock**, elegir el producto.

Indique cantidad, documentos (guía, factura, OC, proveedor) y, si el producto vence, la fecha del lote. El número de lote es **automático** (1, 2, 3…). Dos ingresos con distinta fecha de vencimiento son dos lotes.

Si el producto ya vence, el nuevo stock **también** debe llevar fecha.

El Administrador Auditor ve además el botón **Corregir ingreso** en esta pantalla.

---

## 6. Salida de productos y actas

### 6.1 Armar la entrega

**Salida de Productos** (no disponible para Auditor).

1. Busque por código o nombre y agregue cantidades a la lista de la sesión.
2. Pase a la selección de **departamento/programa** y **responsable**.
3. Confirme. El sistema:
   - descuenta stock (FIFO si hay vencimiento)
   - crea el acta (mismo número para todos los renglones de esa entrega)
   - registra la salida en el bincard
   - genera el **PDF** del acta

No se puede poner el **mismo producto dos veces** en la misma acta.

### 6.2 Documentos

**Documentos** lista las actas. Puede ver o descargar el PDF.

---

## 7. Informes: bincard

Todo está en **Informes**.

### 7.1 Bincard de un producto

**Informes → Bincard.**

- Busque por **código o nombre** (ya no hace falta el código exacto)
- Aunque haya una sola coincidencia, aparece una **lista** para elegir
- **Limpiar** vacía la búsqueda

En el historial verá tres cifras:

| Dato | Significado |
|---|---|
| Stock vigente | Unidades en bodega (para la próxima salida) |
| Historial | Suma de **unidades** de entradas y de salidas (no es el número de filas) |
| Saldo del kardex | Entradas menos salidas de **todo** el historial |

Columnas: fecha, guía o factura, **OC**, N° acta, proveedor, programa/departamento, entrada, salida, saldo.

El Administrador Auditor tiene **Corregir** en cada fila de **entrada**.

Si una página muestra saldo histórico negativo, un aviso lo indica. El stock a usar es el **vigente**, no la última celda de esa página.

**Exportar a Excel** baja el kardex de ese producto.

### 7.2 Bincard general

**Informes → Bincard general.** Movimientos de **todos** los productos.

Al abrir, el rango por defecto es **los últimos 30 días**.

Filtros:

- Desde / hasta
- Tipo: entradas y salidas, solo entradas o solo salidas
- Guía
- OC
- Código o nombre
- **Filtrar** / **Limpiar** (vuelve a 30 días)
- **Todo el histórico** (fechas vacías)

Dos Excel (respetan el filtro):

1. **Exportar movimientos** — listado cronológico (sin columna de saldo)
2. **Exportar bincard global** — un kardex debajo del otro, **con saldo** por producto. El saldo se calcula con el historial **completo** de cada producto, no solo con las filas filtradas. Incluye filtro automático en Excel.

No hay PDF del bincard general; solo Excel.

---

## 8. Corregir ingreso

**Solo Administrador Auditor.** Sirve cuando se digitó mal la cantidad de una **entrada**. No borra el historial a menos que anule (cantidad 0) y el lote siga completo.

### Cómo entrar

1. **Agregar → Corregir ingreso**, o  
2. Botón **Corregir** en una fila de entrada del bincard, o  
3. Desde **Agregar stock** del producto (si tiene el rol)

Luego elija el producto y la entrada.

### Qué hace

- Cambia la cantidad de esa transacción
- Ajusta el lote (si hay vencimiento) y el stock del producto
- Deja **una** línea de observación: `Última corrección: X → Y` (si corrige de nuevo, **reemplaza** esa línea; no acumula)

El **mínimo** permitido es el mayor entre:

- lo que exige el lote (lo ya entregado de ese ingreso), y
- lo que exige el bincard (para que el saldo histórico no quede negativo)

Ejemplos:

- Ingresó 20 y salieron 20: no puede bajar a 19
- El kardex ya está en −1 por un ingreso corto: el mínimo **sube**; hay que corregir **hacia arriba**
- Si todo ese ingreso sigue en bodega, **0 anula** la entrada y deja el lote en 0

El lote se toma de la observación (`Lote #N`) si no coincide con el dato interno.

**Administrador, bodega y auditor no pueden usar esta pantalla** aunque escriban la URL: el sistema los devuelve al inicio.

---

## 9. Control de vencimientos

**Control de Vencimientos** (bodega y administradores).

Muestra productos con vencimiento y lotes con stock. Filtros por estado (vencidos, críticos, precaución) y búsqueda. **Exportar a Excel** y **Limpiar**.

Los lotes vacíos (stock 0) se conservan para el bincard; no aparecen como stock vigente.

---

## 10. Departamentos, categorías y usuarios

Visible para **Administrador** y **Administrador Auditor**.

### Departamentos y categorías

Alta, modificación y deshabilitación. En la salida de productos solo aparecen departamentos activos; en listar productos, categorías activas.

### Usuarios

**Gestión de Usuarios y Roles:** buscar por RUT, nombre o rol; crear, editar, deshabilitar.

Al crear o editar:

- RUT, nombre, correo (opcional), contraseña, **rol** (los cuatro de la tabla)
- Si asigna **Administrador Auditor**, esa persona queda con acceso al panel Django

El Administrador **no** puede cambiarse el propio rol. El Administrador Auditor sí.

### Panel de administración

Solo Administrador Auditor. El botón pide la contraseña otra vez y abre `/admin/` (datos técnicos). La operación diaria se hace en las pantallas del menú, no en Django admin.

---

## 11. Preguntas frecuentes

**¿Por qué el bincard muestra dos filas “Lote #1”?**  
Pueden ser dos ingresos al mismo lote. El stock es la **suma**, no un lote duplicado.

**¿“191 entradas · 20 salidas” son 191 movimientos?**  
No: son **unidades**. 191 ingresadas menos 20 entregadas = 171 de stock, si no hay más movimientos.

**Listar, vencimientos, salida y bincard ¿pueden mostrar números distintos?**  
No deberían. Si hay vencimiento, la fuente es la suma de lotes. Si ve un desfase, pida a un Administrador Auditor que revise el bincard o use **Corregir ingreso**.

**¿El Auditor puede sacar productos?**  
No. Solo consulta.

**¿Puedo corregir una salida?**  
No. Solo entradas, y solo Administrador Auditor. Una salida mal hecha se resuelve con un nuevo movimiento o con soporte.

**Excel del bincard general tarda mucho**  
Con “todo el histórico” el archivo es grande. Filtre por fechas o por producto.

---

## 12. Soporte

1. Cerrar sesión, volver a entrar y repetir la operación  
2. Anotar: RUT usado, pantalla, producto (código), hora y mensaje de error  
3. Avisar al Administrador Auditor / informática

**No** intente “arreglar” stock a mano en la base de datos. Use **Corregir ingreso** o el comando interno `sincronizar_stock` que aplica informática.

---

### Lista rápida por perfil

**Bodega:** salidas, registrar, stock, vencimientos, listar, documentos, ambos bincard.

**Auditor:** listar, documentos, ambos bincard. Sin salidas ni Agregar.

**Administrador:** lo de bodega + usuarios, departamentos y categorías. Sin corregir ingreso ni `/admin/`.

**Administrador Auditor:** todo lo anterior + corregir ingreso + panel Django.
