# Reporte QA — Bodega SEREMI

**Fecha:** 21 de agosto de 2026  
**Entorno de pruebas:** suite Django en SQLite en memoria (no toca la base real)  
**Auditoría de datos reales:** lectura de `data/db/db.sqlite3` (Docker local, puerto 8008)  
**Resultado global:** 31/31 pruebas automáticas OK en 20,1 s

---

## 1. Qué se probó

| Área | Qué se verificó |
|---|---|
| Sincronización | Stock de Listar = suma de lotes = saldo del bincard = entradas − salidas |
| Falsos positivos | Dos ingresos en el mismo Lote #1 no duplican stock; el formulario crea lotes 1, 2, 3… |
| Salidas / FIFO | Tras una salida, lotes, listado y bincard quedan en el mismo número |
| Vistas HTTP | Listar y bincard muestran 171 cuando hay 191 entradas y 20 salidas (unidades, no filas) |
| Control de vencimientos | El producto aparece con el stock de lotes activos |
| Roles | Bodega, Auditor, Administrador y Administrador Auditor |
| Actas | No se puede repetir el mismo producto en el mismo N° de acta |
| Carga | 3000 insumos + 5000 filas de acta (100 actas × 50 productos) |

Los 12 tests anteriores de **corregir ingreso / kardex** también se reejecutaron y pasaron.

---

## 2. Resultados automáticos

### 2.1 Invariante de stock (pasa)

Para un producto con vencimiento, después de ingresos y una salida FIFO:

- suma de lotes = stock del producto
- saldo final del bincard = stock
- entradas − salidas = stock
- Listar Productos y el bincard individual muestran la misma cifra

Caso de referencia (el de las pruebas): **191 entradas − 20 salidas = 171** en listado y bincard. “191 entradas” son **unidades**, no cantidad de filas.

Dos filas de bincard con **Lote #1** (50 y luego 40) dejan **un solo lote** con 90. No es un duplicado.

### 2.2 Roles (pasa)

| Perfil | Salidas | Listar usuarios | Corregir ingreso | Panel `/admin/` |
|---|---|---|---|---|
| Usuario de Bodega | Sí | 403 | Redirige al inicio | No |
| Auditor | Redirige al inicio | 403 | Redirige al inicio | No |
| Administrador | Sí | Sí | Redirige al inicio | No (sin `is_staff`) |
| Administrador Auditor | Sí | Sí | Sí (HTTP 200) | Sí (con `is_staff`) |

### 2.3 Actas (pasa)

La restricción única `(número de acta, producto)` sigue vigente con 5000 filas. Un segundo renglón del mismo producto en el mismo acta falla como corresponde.

### 2.4 Carga (~3000 insumos / ~5000 actas)

Base de prueba aislada, no se insertó nada en la SQLite de Docker.

| Operación | Tiempo | Criterio |
|---|---|---|
| Listar productos (página 1, 20 ítems) | **0,020 s** | < 3 s |
| Búsqueda por código | **0,042 s** | < 2 s |
| Inicio (home) con 3000 productos y 500 con vencimiento | **0,99 s** | < 15 s |
| Control de vencimientos (500 con lote) | **2,09 s** | < 15 s |
| Crear 3000 productos + 5000 actas + 5000 salidas | incluido en los 20 s totales | — |

A esta escala SQLite alcanza para **un usuario de bodega**. Listar es inmediato. Lo más lento es Control de vencimientos / home, porque recorren en Python todos los productos con vencimiento.

Si los **3000 insumos tuvieran vencimiento** (no solo 500), Control de vencimientos podría acercarse a **~12 s** en el mismo equipo. Conviene no abrir “todos” sin filtro cuando eso ocurra.

---

## 3. Datos reales (Docker local)

Lectura de `data/db/db.sqlite3`. **No se modificó nada.**

| Métrica | Valor |
|---|---|
| Productos | 57 (52 con stock > 0) |
| Con vencimiento | 27 |
| Lotes | 61 |
| Transacciones | 376 (110 entradas / 266 salidas) |
| Unidades entradas / salidas | 18 017 / 11 156 |
| Filas de acta / N° de acta distintos | 266 / 154 |
| Usuarios | 15 |

Comprobaciones de consistencia:

- Stock vs suma de lotes: **0 desalineados**
- Stock vs entradas − salidas: **0 desalineados**
- Saldo histórico negativo en el kardex: **0 productos**
- Actas duplicadas (mismo N° + mismo producto): **0**

Hoy la base local está **alineada**. Aún está lejos de 3000 insumos / 5000 actas; la prueba de carga fue sintética.

### Usuarios a tener en cuenta

- **Robinson** (`195532052`): Administrador Auditor, `is_staff` y superusuario. Correcto para el perfil de prueba.
- **Bodeguero Test Usuario** (`222222222`): `is_staff=1` **sin grupo**. Podría entrar al panel Django aunque no tenga rol.
- **Admin Test Usuario**, **Operador Test Usuario**: sin grupo.
- Elizabeth, prueba2 y prueba3 son **Administrador** (operan bodega y usuarios, **sin** corregir ingreso ni panel).

Conviene borrar o desactivar las cuentas de prueba sin rol, y quitar `is_staff` a quien no sea Administrador Auditor.

---

## 4. Hallazgos (no son fallos de las pruebas)

### 4.1 Listar solo repara el stock de la página visible — confirmado

`_sincronizar_productos_pagina` recalcula lotes → stock **solo en los 20 productos de la página**.

La prueba lo demostró: 22 productos con lotes = 5 pero stock guardado = 99. Al abrir Listar, los 20 visibles pasan a 5; los 2 de la página siguiente **siguen en 99** hasta que alguien los abre.

En la base real **hoy no hay** ese desfase. El riesgo aparece si un proceso deja `producto.stock` distinto de la suma de lotes y nadie visita esa página.

**Recomendación (cuando se quiera corregir):** al guardar un lote o una salida, el stock del producto ya se sincroniza; el recálculo al listar es un red de seguridad. Si se mantiene, debería aplicarse a todo el queryset filtrado o a un comando/admin, no solo a la página.

### 4.2 Control de vencimientos y el home cargan todo en memoria

Ambas vistas recorren **todos** los productos con vencimiento y stock, calculan estado lote por lote y después paginan. Con 57 ítems no se nota. Con 500 midió ~2 s; con miles se va a notar.

### 4.3 Lo que esta corrida no cubrió en el navegador

No se pulsó la UI real (login, PDF de acta, Excel del bincard general con histórico largo). Eso sigue siendo una pasada manual de 10–15 minutos con el usuario Robinson.

Tampoco se midió exportar Excel de **todo el histórico** del bincard general: esa operación puede ser pesada cuando existan miles de movimientos.

---

## 5. Cómo repetir las pruebas

Desde `sistema_bodega/`:

```bash
python manage.py test accounts.test_qa accounts.tests --verbosity=2
```

Solo la suite nueva de QA:

```bash
python manage.py test accounts.test_qa --verbosity=2
```

No usa Docker ni escribe en `data/db/db.sqlite3`.

---

## 6. Conclusión

El sistema **mantiene alineados** listado, lotes, bincard y kardex en los flujos de ingreso, salida FIFO, actas y corrección de ingreso. Los roles quedan bloqueados como se definió. La carga de 3000 productos y 5000 actas **sí cabe** en SQLite para un operador; listar es instantáneo.

La base local actual está sana (0 desfases). Los puntos a vigilar son: recálculo de stock solo en la página visible, Control de vencimientos/home si crece mucho el catálogo con fecha de vencimiento, y limpiar usuarios de prueba con `is_staff` o sin grupo.
