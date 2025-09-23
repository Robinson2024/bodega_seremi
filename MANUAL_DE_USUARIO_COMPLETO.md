# 📋 MANUAL DE USUARIO COMPLETO
## Sistema de Bodega SEREMI Salud Araucanía

---

**🏢 INSTITUCIÓN**: SEREMI Salud Araucanía  
**📅 FECHA**: Julio 2025  
**📝 VERSIÓN**: 1.0 - Validada para Producción  
**👨‍💻 DESARROLLADOR**: Robinson Bravo  

---

## 📖 Índice General

1. [**Introducción al Sistema**](#1-introducción-al-sistema)
2. [**Requisitos y Acceso**](#2-requisitos-y-acceso)
3. [**Manual Perfil ADMINISTRADOR**](#3-manual-perfil-administrador)
4. [**Manual Perfil USUARIO DE BODEGA**](#4-manual-perfil-usuario-de-bodega)
5. [**Manual Perfil AUDITOR**](#5-manual-perfil-auditor)
6. [**Procedimientos Comunes**](#6-procedimientos-comunes)
7. [**Solución de Problemas**](#7-solución-de-problemas)
8. [**Contacto y Soporte**](#8-contacto-y-soporte)

---

## 1. Introducción al Sistema

### 🎯 **Propósito del Sistema**
El Sistema de Bodega SEREMI Salud Araucanía es una plataforma web integral diseñada para la gestión completa del inventario institucional, implementando metodología **FIFO (First In, First Out)** y control riguroso de vencimientos.

### ✅ **Características Principales**
- **Control de Inventario**: Gestión completa de productos con códigos de barra únicos
- **Sistema FIFO**: Salida automática por orden de llegada para productos con vencimiento
- **Trazabilidad Completa**: Historial detallado de todos los movimientos (Bincard)
- **Documentos Oficiales**: Generación automática de actas PDF con logos institucionales
- **Roles Diferenciados**: Permisos específicos por tipo de usuario
- **Alertas Inteligentes**: Notificaciones automáticas de vencimientos y stock bajo
- **Exportación de Datos**: Reportes en Excel y PDF para auditorías

### 🔐 **Roles del Sistema**
1. **👑 ADMINISTRADOR**: Control total del sistema, usuarios y configuraciones
2. **📦 USUARIO DE BODEGA**: Gestión operativa de inventario y movimientos
3. **🔍 AUDITOR**: Acceso de solo lectura para revisión y auditorías

---

## 2. Requisitos y Acceso

### 💻 **Requisitos Técnicos**
- **Navegador**: Chrome, Firefox, Edge (versiones actuales)
- **Resolución**: Mínimo 1024x768 (recomendado 1920x1080)
- **Conexión**: Internet estable para VPN institucional
- **Sistema**: Compatible con Windows, Mac, Linux

### 🌐 **Acceso al Sistema**
```
🔗 URL del Sistema: http://[servidor-vpn-seremi]/
📧 Solicitud de credenciales: A través del administrador del sistema
🔑 Autenticación: RUT + contraseña institucional
```

### 🚨 **Normas de Seguridad**
- ✅ **Credenciales personales**: No compartir usuario y contraseña
- ✅ **Cierre de sesión**: Obligatorio al finalizar cada jornada
- ✅ **Navegación privada**: Recomendada para equipos compartidos
- ✅ **Reportar problemas**: Comunicar inmediatamente any incidencia

---

## 3. Manual Perfil ADMINISTRADOR

### 👑 **RESPONSABILIDADES DEL ADMINISTRADOR**
- Gestión completa de usuarios y permisos
- Configuración de departamentos y categorías
- Supervisión general del sistema
- Mantenimiento y respaldos
- Generación de reportes ejecutivos

---

### 🔐 **3.1 ACCESO Y PANEL PRINCIPAL**

#### **Paso 1: Inicio de Sesión**
1. Abrir navegador e ir a la URL del sistema
2. Ingresar **RUT** (sin puntos ni guiones): `robinson`
3. Ingresar **contraseña institucional**
4. Hacer clic en **"Iniciar Sesión"**

#### **Paso 2: Dashboard de Administrador**
Al ingresar verás el **Dashboard Ejecutivo** con:

```
📊 MÉTRICAS PRINCIPALES:
├── 📦 Total de Productos: [XX]
├── 📈 Transacciones del Mes: [XX]
├── ⚠️ Productos por Vencer: [XX]
├── 👥 Usuarios Activos: [XX]
└── 🏢 Departamentos: [XX]
```

#### **Paso 3: Navegación Principal**
El menú principal contiene:
- **🏠 Dashboard**: Vista general del sistema
- **👥 Gestión de Usuarios**: Crear, editar, eliminar usuarios
- **🏢 Departamentos**: Configurar departamentos institucionales
- **📂 Categorías**: Gestionar categorías de productos
- **📦 Productos**: Vista completa del inventario
- **📊 Reportes**: Informes ejecutivos y auditorías
- **⚙️ Configuración**: Ajustes del sistema

---

### 👥 **3.2 GESTIÓN DE USUARIOS**

#### **Crear Nuevo Usuario**

**Paso 1**: Hacer clic en **"Gestión de Usuarios"** → **"Crear Usuario"**

**Paso 2**: Completar formulario:
```
📝 DATOS REQUERIDOS:
├── RUT: Sin puntos ni guiones (ej: 12345678K)
├── Nombre Completo: Nombre y apellidos
├── Email: Correo institucional
├── Contraseña: Mínimo 8 caracteres
├── Confirmar Contraseña: Repetir contraseña
└── Rol: Seleccionar entre:
    ├── 👑 Administrador
    ├── 📦 Usuario de Bodega  
    └── 🔍 Auditor
```

**Paso 3**: Hacer clic en **"Crear Usuario"**

**Paso 4**: Verificar confirmación: *"Usuario creado exitosamente"*

#### **Modificar Usuario Existente**

**Paso 1**: En **"Gestión de Usuarios"**, buscar usuario por:
- RUT
- Nombre
- Filtro por rol

**Paso 2**: Hacer clic en **"Editar"** junto al usuario

**Paso 3**: Modificar campos necesarios:
- ✅ Cambiar nombre
- ✅ Cambiar email
- ✅ Cambiar rol (excepto el propio)
- ✅ Resetear contraseña

**Paso 4**: Guardar cambios con **"Actualizar Usuario"**

#### **Eliminar Usuario**

⚠️ **IMPORTANTE**: Solo eliminar usuarios que ya no pertenezcan a la institución

**Paso 1**: Localizar usuario en la lista
**Paso 2**: Hacer clic en **"Eliminar"** (botón rojo)
**Paso 3**: Confirmar eliminación en el popup
**Paso 4**: Verificar mensaje: *"Usuario eliminado exitosamente"*

---

### 🏢 **3.3 GESTIÓN DE DEPARTAMENTOS**

#### **Crear Nuevo Departamento**

**Paso 1**: Ir a **"Departamentos"** → **"Crear Departamento"**

**Paso 2**: Completar información:
```
📝 DATOS DEL DEPARTAMENTO:
├── Nombre: Nombre del departamento
├── Descripción: Función principal
├── Jefe de Departamento:
│   ├── Nombre completo
│   ├── RUT
│   └── Cargo
├── Secretaria:
│   ├── Nombre completo
│   ├── RUT
│   └── Cargo
└── Estado: Activo/Inactivo
```

**Paso 3**: Hacer clic en **"Crear Departamento"**

#### **Modificar Departamento**

**Paso 1**: En lista de departamentos, hacer clic en **"Editar"**
**Paso 2**: Actualizar información necesaria
**Paso 3**: Guardar con **"Actualizar Departamento"**

---

### 📂 **3.4 GESTIÓN DE CATEGORÍAS**

#### **Crear Nueva Categoría**

**Paso 1**: Ir a **"Categorías"** → **"Crear Categoría"**

**Paso 2**: Ingresar:
```
📝 DATOS DE CATEGORÍA:
├── Nombre: Nombre descriptivo
├── Descripción: Tipo de productos que incluye
└── Estado: Activa/Inactiva
```

**Paso 3**: Confirmar con **"Crear Categoría"**

#### **Ejemplos de Categorías Sugeridas**:
- 💊 Medicamentos
- 🧪 Insumos Médicos
- 📄 Material de Oficina
- 🧽 Productos de Limpieza
- 🔧 Equipamiento
- 📱 Tecnología
- 🍽️ Alimentación
- 🧴 Productos Químicos

---

### 📊 **3.5 SUPERVISIÓN Y REPORTES**

#### **Monitoreo del Dashboard**

**Verificaciones Diarias**:
1. **📦 Stock Crítico**: Productos con stock bajo o sin stock
2. **⏰ Vencimientos**: Productos próximos a vencer o vencidos
3. **📈 Actividad**: Transacciones del día
4. **👥 Usuarios**: Actividad de usuarios

#### **Reportes Ejecutivos**

**Reporte de Inventario General**:
1. Ir a **"Reportes"** → **"Inventario General"**
2. Seleccionar rango de fechas
3. Elegir formato: **Excel** o **PDF**
4. Descargar reporte

**Reporte de Vencimientos**:
1. Ir a **"Control de Vencimientos"**
2. Filtrar por estado:
   - 🔴 Vencidos
   - 🟡 Próximos a vencer (7 días)
   - 🟠 En precaución (30 días)
3. Exportar lista en Excel

**Reporte de Actividad de Usuarios**:
1. Ir a **"Gestión de Usuarios"**
2. Ver **"Última Actividad"** de cada usuario
3. Identificar usuarios inactivos

#### **Auditoría de Transacciones**

**Verificar Integridad**:
1. Ir a **"Productos"** → Seleccionar producto
2. Ver **"Bincard"** (historial completo)
3. Verificar:
   - ✅ Entradas coinciden con facturas
   - ✅ Salidas tienen actas generadas
   - ✅ Stock actual es correcto

---

### ⚙️ **3.6 MANTENIMIENTO DEL SISTEMA**

#### **Respaldos Recomendados**

**Diario**:
- Base de datos del sistema
- Archivos PDF generados

**Semanal**:
- Configuración completa
- Logs del sistema

**Mensual**:
- Exportar todos los datos a Excel
- Revisar estadísticas de uso

#### **Limpieza Periódica**

**Cada 3 meses**:
1. Ejecutar script de limpieza de lotes vencidos
2. Revisar usuarios inactivos
3. Depurar transacciones antiguas (>2 años)

---

## 4. Manual Perfil USUARIO DE BODEGA

### 📦 **RESPONSABILIDADES DEL USUARIO DE BODEGA**
- Gestión operativa del inventario
- Registro de entradas y salidas de productos
- Control de lotes y vencimientos
- Generación de actas de entrega
- Mantenimiento de stock actualizado

---

### 🔐 **4.1 ACCESO Y PANEL OPERATIVO**

#### **Paso 1: Inicio de Sesión**
1. Abrir navegador e ir a la URL del sistema
2. Ingresar **RUT** (sin puntos ni guiones)
3. Ingresar **contraseña** proporcionada por administrador
4. Hacer clic en **"Iniciar Sesión"**

#### **Paso 2: Dashboard Operativo**
Al ingresar verás el **Panel de Bodega** con:

```
📦 PANEL OPERATIVO:
├── 📊 Resumen de Stock: [XX productos]
├── ⚠️ Alertas de Vencimiento: [XX productos]
├── 📈 Movimientos del Día: [XX transacciones]
├── 🔄 Tareas Pendientes: [Notificaciones]
└── 🚚 Últimas Entregas: [Historial reciente]
```

#### **Paso 3: Menú de Bodega**
Las opciones disponibles son:
- **🏠 Dashboard**: Vista general operativa
- **➕ Registrar Producto**: Agregar nuevos productos al inventario
- **📦 Agregar Stock**: Entrada de mercancías con lotes
- **📤 Salida de Productos**: Entrega a departamentos con FIFO
- **⏰ Control de Vencimientos**: Gestión de fechas de vencimiento
- **📋 Listado de Productos**: Inventario completo con búsqueda
- **📊 Bincard**: Historial de movimientos por producto
- **📄 Reportes**: Exportar datos en Excel y PDF

---

### ➕ **4.2 REGISTRAR NUEVOS PRODUCTOS**

#### **Cuando Registrar un Producto Nuevo**
- ✅ Primera vez que llega un producto diferente
- ✅ Cambio de proveedor con código diferente
- ✅ Nueva presentación del mismo producto

#### **Proceso de Registro**

**Paso 1**: Hacer clic en **"Registrar Producto"**

**Paso 2**: Completar formulario:
```
📝 INFORMACIÓN BÁSICA:
├── Código de Barra: [Se genera automáticamente]
├── Descripción: Nombre detallado del producto
├── Categoría: Seleccionar de la lista
├── RUT Proveedor: Sin puntos ni guiones
├── Stock Inicial: Cantidad que ingresa
└── ¿Tiene Vencimiento?: Sí/No

📝 SI TIENE VENCIMIENTO:
├── Número de Lote: Identificador del lote
└── Fecha de Vencimiento: DD/MM/AAAA
```

**Paso 3**: Hacer clic en **"Registrar Producto"**

**Paso 4**: Verificar mensaje: *"Producto registrado exitosamente"*

#### **Ejemplos Prácticos**

**Ejemplo 1 - Medicamento**:
```
Descripción: Paracetamol 500mg x 20 tabletas
Categoría: Medicamentos
RUT Proveedor: 123456789
Stock Inicial: 50
¿Tiene Vencimiento?: Sí
Número de Lote: PARA2024-001
Fecha de Vencimiento: 15/12/2025
```

**Ejemplo 2 - Material de Oficina**:
```
Descripción: Resma papel carta 75gr
Categoría: Material de Oficina
RUT Proveedor: 987654321
Stock Inicial: 25
¿Tiene Vencimiento?: No
```

---

### 📦 **4.3 AGREGAR STOCK (ENTRADAS)**

#### **Cuando Agregar Stock**
- ✅ Llegada de nueva mercancía
- ✅ Compras adicionales de productos existentes
- ✅ Transferencias desde otras bodegas
- ✅ Devoluciones de departamentos

#### **Proceso de Entrada**

**Paso 1**: Hacer clic en **"Agregar Stock"**

**Paso 2**: Buscar producto existente:
- Por código de barra
- Por descripción
- Usar filtros por categoría

**Paso 3**: Seleccionar producto y completar:
```
📝 DATOS DE ENTRADA:
├── Cantidad a Ingresar: Número de unidades
├── Número de Factura: Referencia de compra
├── Motivo: Seleccionar de lista:
│   ├── 🛒 Compra
│   ├── 🔄 Transferencia
│   ├── 📬 Donación
│   ├── ↩️ Devolución
│   └── 🔧 Ajuste de inventario
└── [Si tiene vencimiento]:
    ├── Número de Lote: Nuevo o existente
    └── Fecha de Vencimiento: DD/MM/AAAA
```

**Paso 4**: Hacer clic en **"Agregar Stock"**

**Paso 5**: Verificar actualización de inventario

#### **Ejemplo Práctico - Entrada de Medicamentos**:
```
Producto: Paracetamol 500mg x 20 tabletas
Cantidad: 100 unidades
Número de Factura: FAC-2025-0456
Motivo: Compra
Número de Lote: PARA2025-002
Fecha de Vencimiento: 20/08/2026
```

---

### 📤 **4.4 SALIDA DE PRODUCTOS (ENTREGAS)**

#### **El Sistema FIFO Automático**
🔄 **FIFO (First In, First Out)**: El sistema selecciona automáticamente los lotes más antiguos para evitar vencimientos.

#### **Proceso de Entrega**

**Paso 1**: Hacer clic en **"Salida de Productos"**

**Paso 2**: Buscar productos a entregar:
- Usar buscador por descripción
- Filtrar por categoría
- Ver disponibilidad en tiempo real

**Paso 3**: Agregar productos a la entrega:
```
📝 POR CADA PRODUCTO:
├── Seleccionar producto disponible
├── Ingresar cantidad a entregar
├── [Opcional] Observaciones específicas
└── Hacer clic en "Agregar a Entrega"
```

**Paso 4**: Completar datos de entrega:
```
📝 INFORMACIÓN DE ENTREGA:
├── Departamento Receptor: Seleccionar de lista
├── Funcionario que Recibe: Nombre completo
├── Observaciones Generales: [Opcional]
└── Fecha de Entrega: [Se completa automáticamente]
```

**Paso 5**: Revisar lista de productos:
- ✅ Verificar cantidades
- ✅ Confirmar departamento
- ✅ Revisar que el stock sea suficiente

**Paso 6**: Hacer clic en **"Procesar Entrega"**

**Paso 7**: Descargar acta PDF generada automáticamente

#### **Ejemplo Práctico - Entrega a Departamento**:
```
PRODUCTOS A ENTREGAR:
├── Paracetamol 500mg: 10 unidades
├── Alcohol gel 500ml: 5 unidades
└── Mascarillas N95: 20 unidades

DEPARTAMENTO: Departamento de Acción Sanitaria
RECIBE: Juan Pérez (Jefe DAS)
OBSERVACIONES: Entrega mensual programada
```

#### **Qué Sucede Automáticamente**:
1. 🔄 **Sistema FIFO**: Selecciona lotes más antiguos
2. 📉 **Actualización de Stock**: Descuenta automáticamente
3. 📄 **Generación de Acta**: PDF con logos y firmas institucionales
4. 📊 **Registro en Bincard**: Historial de la transacción
5. ⚠️ **Alertas**: Notifica si queda stock bajo

---

### ⏰ **4.5 CONTROL DE VENCIMIENTOS**

#### **Monitoreo Diario Recomendado**

**Paso 1**: Ir a **"Control de Vencimientos"**

**Paso 2**: Revisar alertas por categorías:
```
🚨 ESTADOS DE VENCIMIENTO:
├── 🔴 VENCIDOS: Acción inmediata requerida
├── 🟠 VENCE HOY: Usar prioritariamente
├── 🟡 CRÍTICO (≤7 días): Programar uso urgente
├── 🟢 PRECAUCIÓN (≤30 días): Monitorear
└── 🔵 NORMAL (>30 días): Sin problemas
```

#### **Acciones por Estado**

**Para Productos Vencidos** 🔴:
1. **No entregar bajo ningún concepto**
2. Mover a área de productos vencidos
3. Registrar en libro de productos vencidos
4. Coordinar eliminación según protocolo institucional

**Para Productos que Vencen Hoy** 🟠:
1. **Usar prioritariamente**
2. Ofrecer primero a departamentos
3. Registrar motivo si no se puede usar

**Para Productos Críticos** 🟡:
1. **Programar entregas urgentes**
2. Comunicar a departamentos usuarios habituales
3. Considerar redistribución entre bodegas

#### **Actualización de Fechas de Vencimiento**

**Cuando es Necesario**:
- ✅ Error en registro inicial
- ✅ Cambio de lote
- ✅ Información adicional del proveedor

**Proceso**:
1. Buscar producto en **"Control de Vencimientos"**
2. Hacer clic en **"Editar Fecha"**
3. Ingresar nueva fecha: DD/MM/AAAA
4. Agregar justificación del cambio
5. Guardar modificación

---

### 📋 **4.6 CONSULTA Y BÚSQUEDA DE PRODUCTOS**

#### **Búsqueda Avanzada**

**Paso 1**: Ir a **"Listado de Productos"**

**Paso 2**: Usar filtros disponibles:
```
🔍 OPCIONES DE BÚSQUEDA:
├── Texto Libre: Código, descripción, proveedor
├── Categoría: Filtro por tipo de producto
├── Estado de Stock:
│   ├── 🟢 Con Stock
│   ├── 🔴 Sin Stock  
│   └── 🟡 Stock Bajo (≤10 unidades)
├── Estado de Vencimiento:
│   ├── Normal, Próximo a vencer, Vencido
├── Rango de Fechas: Ingreso, modificación
└── Proveedor: Por RUT específico
```

**Paso 3**: Aplicar filtros y revisar resultados

**Paso 4**: [Opcional] Exportar lista a Excel

#### **Consulta Rápida de Stock**

**Para Verificar Disponibilidad**:
1. Usar buscador principal (disponible en todas las páginas)
2. Escribir código o descripción
3. Ver stock disponible en tiempo real
4. [Si aplica] Ver próximas fechas de vencimiento

---

### 📊 **4.7 GENERACIÓN DE REPORTES**

#### **Reporte de Movimientos Diarios**

**Paso 1**: Ir a **"Reportes"** → **"Movimientos Diarios"**
**Paso 2**: Seleccionar fecha o rango de fechas
**Paso 3**: Elegir formato: Excel o PDF
**Paso 4**: Descargar reporte

**Incluye**:
- ✅ Todas las entradas del período
- ✅ Todas las salidas del período
- ✅ Stock inicial y final por producto
- ✅ Detalles de lotes utilizados

#### **Reporte de Inventario Actual**

**Paso 1**: Ir a **"Reportes"** → **"Inventario Actual"**
**Paso 2**: [Opcional] Filtrar por categoría
**Paso 3**: Exportar en Excel

**Incluye**:
- ✅ Lista completa de productos
- ✅ Stock actual por producto
- ✅ Estado de vencimiento
- ✅ Ubicación de lotes

#### **Bincard por Producto**

**Para Auditorías Específicas**:
1. Ir a **"Listado de Productos"**
2. Buscar producto específico
3. Hacer clic en **"Ver Bincard"**
4. Revisar historial completo:
   - Entradas con fechas y motivos
   - Salidas con departamentos y actas
   - Saldos en cada movimiento
5. [Opcional] Exportar a PDF

---

## 5. Manual Perfil AUDITOR

### 🔍 **RESPONSABILIDADES DEL AUDITOR**
- Revisión y verificación de procesos
- Análisis de integridad de datos
- Generación de reportes de auditoría
- Identificación de inconsistencias
- **IMPORTANTE**: Solo acceso de lectura, sin capacidad de modificación

---

### 🔐 **5.1 ACCESO Y PANEL DE AUDITORÍA**

#### **Paso 1: Inicio de Sesión**
1. Abrir navegador e ir a la URL del sistema
2. Ingresar **RUT** asignado (ej: 61601000k)
3. Ingresar **contraseña** proporcionada por administrador
4. Hacer clic en **"Iniciar Sesión"**

#### **Paso 2: Dashboard de Auditoría**
Al ingresar verás el **Panel de Auditoría** con:

```
🔍 PANEL DE AUDITORÍA:
├── 📊 Resumen Estadístico: Métricas generales
├── ⚠️ Alertas de Sistema: Inconsistencias detectadas
├── 📈 Indicadores de Integridad: Estado de datos
├── 📋 Actividad Reciente: Últimas transacciones
└── 🎯 Puntos de Control: Áreas críticas
```

#### **Paso 3: Menú de Auditoría**
Las opciones disponibles (solo lectura) son:
- **🏠 Dashboard**: Vista general de auditoría
- **📊 Análisis de Inventario**: Revisión completa del stock
- **🔍 Verificación de Transacciones**: Auditoría de movimientos
- **⏰ Control de Vencimientos**: Análisis de gestión de fechas
- **📋 Reportes de Auditoría**: Informes especializados
- **👥 Actividad de Usuarios**: Seguimiento de acciones
- **📄 Documentos Generados**: Revisión de actas y reportes

---

### 📊 **5.2 ANÁLISIS DE INVENTARIO**

#### **Verificación de Integridad del Stock**

**Paso 1**: Ir a **"Análisis de Inventario"**

**Paso 2**: Revisar indicadores clave:
```
🎯 PUNTOS DE CONTROL:
├── ✅ Productos sin inconsistencias: [XX]
├── ⚠️ Discrepancias menores: [XX]
├── 🚨 Problemas críticos: [XX]
├── 📊 Stock negativo: [Debe ser 0]
├── 🔄 Transacciones huérfanas: [Debe ser 0]
└── 📅 Fechas de vencimiento inválidas: [Debe ser 0]
```

**Paso 3**: Investigar cualquier inconsistencia:
- Hacer clic en **"Ver Detalles"** de productos con problemas
- Revisar historial de transacciones
- Identificar patrones de errores

#### **Auditoría por Categorías**

**Análisis Recomendado**:
1. **📊 Medicamentos**: Verificar FIFO y vencimientos
2. **🧪 Insumos Médicos**: Controlar rotación
3. **📄 Material de Oficina**: Verificar consumo normal
4. **🧽 Productos de Limpieza**: Controlar stock crítico

**Proceso de Verificación**:
1. Filtrar productos por categoría
2. Ordenar por:
   - Stock (menor a mayor)
   - Fecha de vencimiento (próximos primero)
   - Actividad reciente
3. Identificar patrones anómalos:
   - Productos sin movimiento >3 meses
   - Stock excesivo sin rotación
   - Vencimientos frecuentes

---

### 🔍 **5.3 VERIFICACIÓN DE TRANSACCIONES**

#### **Auditoría de Movimientos Diarios**

**Paso 1**: Ir a **"Verificación de Transacciones"**

**Paso 2**: Seleccionar período de auditoría:
- Día específico
- Semana completa
- Mes en revisión

**Paso 3**: Analizar tipos de movimientos:
```
📈 TIPOS DE TRANSACCIONES:
├── 📥 ENTRADAS:
│   ├── Compras (con factura)
│   ├── Transferencias (con documentación)
│   ├── Donaciones (con acta)
│   └── Ajustes (con justificación)
├── 📤 SALIDAS:
│   ├── Entregas a departamentos (con acta)
│   ├── Transferencias externas (con autorización)
│   ├── Productos vencidos (con protocolo)
│   └── Ajustes (con justificación)
```

#### **Verificación de Documentación**

**Validación de Actas PDF**:
1. Ir a **"Documentos Generados"**
2. Revisar actas por período
3. Verificar elementos obligatorios:
   - ✅ Logo institucional presente
   - ✅ Datos completos de productos
   - ✅ Firmas digitales correctas
   - ✅ Numeración secuencial
   - ✅ Fechas coherentes

**Validación de Facturas y Respaldos**:
1. Comparar entradas con facturas registradas
2. Verificar números de factura únicos
3. Confirmar concordancia de cantidades
4. Revisar fechas de ingreso vs. facturación

#### **Análisis de Patrón FIFO**

**Verificación del Sistema FIFO**:
1. Seleccionar productos con vencimiento
2. Revisar historial de salidas
3. Confirmar que las salidas siguen orden cronológico:
   - ✅ Lotes más antiguos salen primero
   - ✅ No hay "saltos" de lotes
   - ✅ Fechas de vencimiento en orden lógico

**Ejemplo de Auditoría FIFO**:
```
PRODUCTO: Paracetamol 500mg
LOTES DISPONIBLES:
├── Lote A (Vence: 15/03/2025) - Stock: 50
├── Lote B (Vence: 20/06/2025) - Stock: 30
└── Lote C (Vence: 10/09/2025) - Stock: 40

VERIFICAR: Las salidas deben usar Lote A primero
```

---

### ⏰ **5.4 AUDITORÍA DE VENCIMIENTOS**

#### **Análisis de Gestión de Vencimientos**

**Paso 1**: Ir a **"Control de Vencimientos"**

**Paso 2**: Revisar indicadores de gestión:
```
📊 MÉTRICAS DE VENCIMIENTOS:
├── 🎯 Productos Vencidos: [Objetivo: <5%]
├── ⚠️ Próximos a Vencer (7 días): [XX]
├── 🟡 En Precaución (30 días): [XX]
├── 📈 Rotación Promedio: [XX días]
└── 💰 Valor de Productos Vencidos: [$ XX]
```

#### **Identificación de Problemas Recurrentes**

**Patrones a Investigar**:
1. **Productos con Vencimientos Frecuentes**:
   - Identificar productos que vencen repetidamente
   - Analizar si las cantidades de compra son excesivas
   - Revisar rotación vs. demanda

2. **Departamentos con Baja Rotación**:
   - Identificar departamentos que solicitan poco
   - Analizar si hay productos sin usar
   - Verificar necesidades reales vs. stock

3. **Alertas No Atendidas**:
   - Revisar productos con alerta >30 días
   - Verificar si se tomaron acciones correctivas
   - Identificar fallas en el proceso

#### **Recomendaciones de Mejora**

**Basado en el Análisis**:
1. **Compras**: Sugerir ajustes en cantidades
2. **Distribución**: Proponer rotación entre bodegas
3. **Comunicación**: Mejorar alertas a departamentos
4. **Capacitación**: Identificar necesidades de entrenamiento

---

### 📋 **5.5 REPORTES DE AUDITORÍA**

#### **Reporte Mensual de Auditoría**

**Paso 1**: Ir a **"Reportes de Auditoría"** → **"Reporte Mensual"**

**Paso 2**: Seleccionar mes y año

**Paso 3**: Generar reporte que incluye:
```
📊 CONTENIDO DEL REPORTE:
├── 📈 Resumen Ejecutivo:
│   ├── Total de transacciones
│   ├── Valor total de movimientos
│   ├── Productos agregados/eliminados
│   └── Problemas identificados
├── 🔍 Análisis Detallado:
│   ├── Integridad de datos
│   ├── Cumplimiento FIFO
│   ├── Gestión de vencimientos
│   └── Documentación completa
├── ⚠️ Observaciones:
│   ├── Inconsistencias encontradas
│   ├── Patrones anómalos
│   └── Áreas de mejora
└── 💡 Recomendaciones:
    ├── Acciones correctivas inmediatas
    ├── Mejoras de proceso
    └── Capacitación sugerida
```

#### **Reporte de Actividad de Usuarios**

**Monitoreo de Accesos y Acciones**:
1. Ir a **"Actividad de Usuarios"**
2. Revisar por período:
   - Inicios de sesión por usuario
   - Transacciones realizadas por usuario
   - Tiempo promedio de sesión
   - Acciones críticas (eliminaciones, modificaciones)

**Identificar Patrones Sospechosos**:
- Accesos fuera de horario laboral
- Volumen anómalo de transacciones
- Modificaciones sin justificación
- Usuarios inactivos con sesiones abiertas

#### **Reporte de Cumplimiento Normativo**

**Verificación de Cumplimiento**:
1. **Trazabilidad**: 100% de movimientos documentados
2. **FIFO**: Cumplimiento del protocolo
3. **Vencimientos**: Gestión preventiva adecuada
4. **Documentación**: Actas completas y firmadas
5. **Respaldos**: Documentación de soporte presente

---

### 👥 **5.6 ANÁLISIS DE USUARIOS Y PROCESOS**

#### **Evaluación de Desempeño por Usuario**

**Métricas de Usuarios de Bodega**:
```
📊 INDICADORES POR USUARIO:
├── Transacciones procesadas/día
├── Tiempo promedio por transacción
├── Errores detectados/corregidos
├── Cumplimiento de procedimientos
└── Capacitación requerida
```

**Identificar Necesidades de Capacitación**:
1. Usuarios con errores frecuentes
2. Procesos no seguidos correctamente
3. Documentación incompleta
4. Falta de uso de funcionalidades del sistema

#### **Análisis de Procesos Institucionales**

**Eficiencia Operativa**:
1. **Tiempo de Procesamiento**:
   - Desde ingreso hasta disponibilidad
   - Desde solicitud hasta entrega
   - Tiempo de generación de reportes

2. **Calidad de Datos**:
   - Información completa en registros
   - Precisión de cantidades
   - Actualización oportuna de estados

3. **Cumplimiento de Protocolos**:
   - Seguimiento de procedimientos establecidos
   - Documentación adecuada
   - Autorización de operaciones críticas

---

## 6. Procedimientos Comunes

### 🔧 **6.1 PROCEDIMIENTOS DE EMERGENCIA**

#### **Falla del Sistema**

**Procedimiento Inmediato**:
1. **No entrar en pánico**
2. Verificar conexión a internet/VPN
3. Intentar refrescar página (F5)
4. Cerrar y abrir navegador
5. Si persiste: contactar administrador inmediatamente

**Registro Manual Temporal**:
```
📝 INFORMACIÓN A REGISTRAR:
├── Hora exacta del problema
├── Acción que se intentaba realizar
├── Mensaje de error (si aparece)
├── Usuario afectado
└── Productos/cantidades involucradas
```

#### **Error en Cantidades**

**Si se detecta error ANTES de confirmar**:
1. Corregir en pantalla
2. Verificar nuevamente
3. Proceder normalmente

**Si se detecta error DESPUÉS de confirmar**:
1. **NO intentar corregir directamente**
2. Documentar la situación:
   - Qué se hizo mal
   - Cuál debería ser la cantidad correcta
   - Impacto en el stock
3. Contactar inmediatamente al administrador
4. Esperar instrucciones para corrección oficial

---

### 📋 **6.2 PROCEDIMIENTOS DE CIERRE**

#### **Cierre Diario de Bodega**

**Lista de Verificación**:
```
✅ ANTES DE CERRAR:
├── Verificar todas las entregas completadas
├── Confirmar todos los ingresos registrados
├── Revisar alertas de vencimiento
├── Generar reporte del día
├── Verificar stock de productos críticos
├── Cerrar sesión correctamente
└── Apagar equipo siguiendo protocolo
```

#### **Cierre Mensual**

**Actividades Adicionales**:
1. **Inventario de Control**:
   - Verificar stock físico vs. sistema (muestra aleatoria)
   - Documentar diferencias encontradas
   - Reportar discrepancias al administrador

2. **Revisión de Vencimientos**:
   - Hacer reporte completo de productos próximos a vencer
   - Coordinar con departamentos el uso prioritario
   - Documentar productos que no pudieron ser utilizados

3. **Backup de Información**:
   - Exportar movimientos del mes en Excel
   - Guardar copia de reportes generados
   - Archivar actas físicas según protocolo

---

### 🚨 **6.3 PROTOCOLOS DE SEGURIDAD**

#### **Manejo de Productos Vencidos**

**Protocolo Estricto**:
1. **NUNCA entregar productos vencidos**
2. Segregar físicamente del stock disponible
3. Etiquetar claramente como "VENCIDO"
4. Registrar en libro de productos vencidos:
   - Fecha de detección
   - Producto y cantidad
   - Lote y fecha de vencimiento
   - Responsable que detectó
5. Coordinar eliminación según protocolo institucional

#### **Manejo de Información Confidencial**

**Normas de Confidencialidad**:
- ✅ **No compartir credenciales** con nadie
- ✅ **Cerrar sesión** al alejarse del equipo
- ✅ **No tomar capturas** de pantalla con datos sensibles
- ✅ **No imprimir** información innecesaria
- ✅ **Reportar** accesos no autorizados

#### **Protección de Datos**

**Responsabilidades**:
1. **Acceso Responsable**: Solo acceder a información necesaria
2. **Uso Profesional**: Solo para funciones laborales
3. **Protección Física**: No dejar pantallas abiertas sin supervisión
4. **Respaldo Seguro**: Solo guardar copias autorizadas

---

## 7. Solución de Problemas

### ❗ **7.1 PROBLEMAS TÉCNICOS COMUNES**

#### **No Puedo Iniciar Sesión**

**Posibles Causas y Soluciones**:

1. **Credenciales Incorrectas**:
   - ✅ Verificar RUT sin puntos ni guiones
   - ✅ Confirmar contraseña (cuidado con mayúsculas)
   - ✅ Verificar que no esté activado Bloq Mayús

2. **Problemas de Conexión**:
   - ✅ Verificar conexión a VPN institucional
   - ✅ Probar acceso a otras páginas web
   - ✅ Contactar soporte IT si VPN no funciona

3. **Usuario Bloqueado**:
   - ✅ Contactar administrador del sistema
   - ✅ Verificar si hay cambios en permisos

#### **El Sistema Va Lento**

**Soluciones Inmediatas**:
1. **Cerrar pestañas innecesarias** del navegador
2. **Limpiar caché** del navegador:
   - Chrome: Ctrl+Shift+Supr
   - Firefox: Ctrl+Shift+Supr
3. **Verificar otros programas** que consuman internet
4. **Reiniciar navegador** completamente

#### **Error al Generar PDF**

**Pasos de Solución**:
1. **Verificar bloqueador de pop-ups** (debe estar desactivado)
2. **Permitir descargas** en el navegador
3. **Liberar espacio** en disco duro
4. **Intentar con navegador diferente**
5. Si persiste: contactar administrador

#### **No Aparecen Productos en Búsqueda**

**Verificaciones**:
1. **Revisar filtros activos** (pueden estar limitando resultados)
2. **Limpiar búsqueda** con botón "Limpiar Filtros"
3. **Verificar ortografía** en texto de búsqueda
4. **Intentar búsqueda más amplia** (menos específica)

---

### 🔧 **7.2 PROBLEMAS OPERATIVOS**

#### **Stock Insuficiente para Entrega**

**Proceso de Verificación**:
1. **Confirmar stock real** consultando producto específico
2. **Verificar si hay lotes bloqueados** por vencimiento
3. **Revisar entregas pendientes** no confirmadas
4. **Considerar productos equivalentes** disponibles

**Acciones Posibles**:
- Entregar cantidad disponible y programar saldo
- Ofrecer producto sustituto de misma categoría
- Contactar proveedor para reposición urgente
- Coordinar con otras bodegas transferencia

#### **Producto No Aparece en Sistema**

**Verificación Step by Step**:
1. **Buscar por código alternativo** (puede tener código diferente)
2. **Buscar por descripción parcial** (puede estar registrado diferente)
3. **Verificar categoría** del producto
4. **Consultar con administrador** si es producto nuevo

#### **Error en Fecha de Vencimiento**

**Solo Usuarios con Permisos**:
1. **Documentar el error** encontrado
2. **Contactar administrador** para corrección
3. **No usar producto** hasta confirmación de fecha correcta
4. **Seguir protocolo** establecido para modificaciones

---

### 📞 **7.3 ESCALAMIENTO DE PROBLEMAS**

#### **Nivel 1: Auto-Resolución**
- Problemas técnicos menores
- Dudas de procedimiento básico
- Errores de operación simple

#### **Nivel 2: Administrador del Sistema**
- Problemas de permisos
- Errores de datos
- Funcionamiento anómalo del sistema
- Solicitudes de cambio de configuración

#### **Nivel 3: Soporte IT Institucional**
- Problemas de conectividad VPN
- Fallos de hardware
- Problemas de red institucional

#### **Nivel 4: Desarrollador**
- Bugs del sistema
- Nuevas funcionalidades requeridas
- Problemas técnicos complejos

---

## 8. Contacto y Soporte

### 📞 **8.1 INFORMACIÓN DE CONTACTO**

#### **Administrador del Sistema**
```
👤 Nombre: Robinson Bravo
🏢 Cargo: Desarrollador y Administrador del Sistema
📧 Email: [email institucional]
📱 Teléfono: [número institucional]
⏰ Horario: Lunes a Viernes, 8:00 - 17:00 hrs
```

#### **Soporte IT SEREMI**
```
🏢 Departamento: Tecnologías de la Información
📧 Email: [soporte-it@seremi.cl]
📱 Teléfono: [número soporte]
⏰ Horario: Lunes a Viernes, 8:30 - 16:30 hrs
```

### 🚨 **8.2 CANALES DE SOPORTE**

#### **Para Emergencias (Sistema Caído)**
1. **Llamada telefónica directa** al administrador
2. **Email con URGENTE** en asunto
3. **Registro manual temporal** de actividades críticas

#### **Para Consultas Generales**
1. **Email descriptivo** del problema
2. **Ticket interno** según protocolo institucional
3. **Consulta presencial** en horarios establecidos

#### **Para Capacitación**
1. **Solicitud formal** de capacitación adicional
2. **Sesiones grupales** programadas mensualmente
3. **Material de apoyo** disponible en sistema

### 📋 **8.3 INFORMACIÓN PARA REPORTES DE PROBLEMAS**

#### **Datos Necesarios en Reporte**
```
📝 INCLUIR SIEMPRE:
├── Nombre y cargo del usuario
├── Fecha y hora exacta del problema
├── Acción que se intentaba realizar
├── Mensaje de error completo (si aparece)
├── Navegador y versión utilizada
├── Pantalla o sección donde ocurrió
└── Pasos previos al problema
```

#### **Capturas de Pantalla**
- ✅ **Incluir cuando sea posible** (ayuda significativamente)
- ✅ **Cubrir información sensible** antes de enviar
- ✅ **Mostrar mensaje de error completo**
- ✅ **Incluir URL visible** en la captura

---

## 📚 **ANEXOS**

### **Anexo A: Glosario de Términos**

```
📖 TÉRMINOS TÉCNICOS:
├── FIFO: First In, First Out (Primero en entrar, primero en salir)
├── Bincard: Registro de movimientos por producto
├── Lote: Conjunto de productos con misma fecha de vencimiento
├── Stock: Cantidad disponible de un producto
├── Acta: Documento oficial de entrega
├── Dashboard: Panel principal con métricas
├── VPN: Red Privada Virtual para acceso seguro
└── PDF: Formato de documento portable
```

### **Anexo B: Códigos de Estado**

```
🎨 COLORES DE ESTADO:
├── 🟢 Verde: Normal, disponible
├── 🟡 Amarillo: Precaución, revisar
├── 🟠 Naranja: Crítico, acción inmediata
├── 🔴 Rojo: Problema, no usar
└── 🔵 Azul: Información, sin vencimiento
```

### **Anexo C: Atajos de Teclado**

```
⌨️ ATAJOS ÚTILES:
├── F5: Actualizar página
├── Ctrl+F: Buscar en página
├── Ctrl+P: Imprimir/Guardar PDF
├── Ctrl+S: Guardar (en formularios)
├── Tab: Moverse entre campos
└── Enter: Confirmar acción
```

---

## ✅ **LISTA DE VERIFICACIÓN FINAL**

### **Para Administradores**
- [ ] Sistema configurado y usuarios creados
- [ ] Departamentos y categorías establecidos
- [ ] Permisos asignados correctamente
- [ ] Backup programado y funcionando
- [ ] Capacitación completada para usuarios

### **Para Usuarios de Bodega**
- [ ] Credenciales recibidas y verificadas
- [ ] Capacitación en procesos básicos completada
- [ ] Procedimientos de emergencia conocidos
- [ ] Contactos de soporte disponibles
- [ ] Pruebas de operación realizadas exitosamente

### **Para Auditores**
- [ ] Acceso de solo lectura verificado
- [ ] Conocimiento de reportes disponibles
- [ ] Procedimientos de auditoría establecidos
- [ ] Cronograma de revisiones definido
- [ ] Formatos de reporte acordados

---

**📋 Manual Validado para Implementación Institucional**  
*SEREMI Salud Araucanía - Julio 2025*

**🎯 Estado del Sistema**: COMPLETAMENTE OPERATIVO  
**📊 Validación**: 41/41 pruebas exitosas (100%)  
**🚀 Preparación**: Lista para deployment en VPN institucional

---

*Fin del Manual de Usuario Completo*
