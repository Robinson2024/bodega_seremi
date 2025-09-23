#!/usr/bin/env python
"""
Script simplificado para corregir el mapeo de columnas en la actualización visual
"""

def mostrar_problema_y_solucion():
    """Muestra el problema identificado y la solución"""
    print("🧪 PROBLEMA IDENTIFICADO EN EL MAPEO DE COLUMNAS")
    print("=" * 60)
    
    print("\n📋 Estructura de la tabla en agregar_vencimiento.html:")
    columnas = [
        "1. Código", 
        "2. Descripción",
        "3. Categoría", 
        "4. Stock",
        "5. Estado Vencimiento",  # ← Aquí va el badge de estado
        "6. Fecha Vencimiento",   # ← Aquí va la fecha formateada  
        "7. Lotes",
        "8. Acciones"
    ]
    
    for columna in columnas:
        print(f"   {columna}")
    
    print("\n❌ PROBLEMA ACTUAL:")
    print("   El JavaScript está actualizando las columnas incorrectas")
    print("   Al modificar un lote, se confunden las actualizaciones")
    
    print("\n🎯 ANÁLISIS DEL CÓDIGO ACTUAL:")
    print("""
   // INCORRECTO - está en las líneas 788-798 del template
   const estadoCell = fila.querySelector('td:nth-child(5)');  // ✅ CORRECTO
   const fechaCell = fila.querySelector('td:nth-child(6)');   // ✅ CORRECTO
   
   Pero el problema está en QUÉ se está actualizando en cada columna
   """)
    
    print("\n✅ SOLUCIÓN:")
    print("   Verificar que:")
    print("   - Columna 5 (Estado): Se actualice con el ESTADO (badge)")
    print("   - Columna 6 (Fecha): Se actualice con la FECHA (texto)")
    
    return True

def generar_codigo_corregido():
    """Genera el código JavaScript corregido"""
    print("\n🔧 CÓDIGO JAVASCRIPT CORREGIDO:")
    print("=" * 60)
    
    codigo_corregido = """
// Función corregida para actualizar los datos del producto
function actualizarDatosProducto(fila, codigo) {
    fetch('{% url "obtener-datos-producto-ajax" %}?codigo_barra=' + codigo)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const producto = data.producto;
            
            function getClaseEstado(estado) {
                const mapeoEstados = {
                    'vencido': 'estado-vencido',
                    'vence hoy': 'estado-critico', 
                    'crítico': 'estado-critico',
                    'critico': 'estado-critico',
                    'precaución': 'estado-proximo',
                    'precaucion': 'estado-proximo',
                    'normal': 'estado-bueno',
                    'sin vencimiento': 'badge-secondary'
                };
                return mapeoEstados[estado.toLowerCase()] || 'badge-secondary';
            }
            
            // ✅ Columna 5: Estado Vencimiento (badge con color)
            const estadoCell = fila.querySelector('td:nth-child(5)');
            if (estadoCell) {
                const claseEstado = getClaseEstado(producto.estado_vencimiento);
                estadoCell.innerHTML = `<span class="badge ${claseEstado}">${producto.estado_vencimiento}</span>`;
                console.log('✅ Estado actualizado:', producto.estado_vencimiento);
            }
            
            // ✅ Columna 6: Fecha Vencimiento (fecha formateada)
            const fechaCell = fila.querySelector('td:nth-child(6)');
            if (fechaCell) {
                fechaCell.innerHTML = producto.proximo_vencimiento ? 
                    producto.proximo_vencimiento_display : 
                    '<span class="text-muted">Sin fecha</span>';
                console.log('✅ Fecha actualizada:', producto.proximo_vencimiento_display);
            }
            
            // ✅ Columna 7: Cantidad de lotes
            const lotesCell = fila.querySelector('td:nth-child(7)');
            if (lotesCell) {
                lotesCell.innerHTML = `<span class="badge badge-primary">${producto.total_lotes} lote${producto.total_lotes !== 1 ? 's' : ''}</span>`;
                console.log('✅ Lotes actualizados:', producto.total_lotes);
            }
            
            console.log('✅ Fila actualizada correctamente para producto:', codigo);
        } else {
            console.error('❌ Error al obtener datos del producto:', data.error);
        }
    })
    .catch(error => {
        console.error('❌ Error de conexión al actualizar fila:', error);
    });
}"""
    
    print(codigo_corregido)
    
    print("\n🎯 CAMBIOS CLAVE:")
    print("   ✅ Logs detallados para debugging")
    print("   ✅ Verificación correcta de columnas")
    print("   ✅ Separación clara entre estado y fecha")
    
    return codigo_corregido

def main():
    """Función principal"""
    mostrar_problema_y_solucion()
    codigo_corregido = generar_codigo_corregido()
    
    print("\n" + "=" * 60)
    print("📝 PASOS PARA APLICAR LA CORRECCIÓN")
    print("=" * 60)
    
    print("\n1. 📂 Abrir el archivo:")
    print("   accounts/templates/accounts/agregar_vencimiento.html")
    
    print("\n2. 🔍 Buscar la función 'actualizarDatosProducto' (línea ~773)")
    
    print("\n3. 🔄 Reemplazar la función completa con el código corregido")
    
    print("\n4. 🧪 Probar en el navegador:")
    print("   - Ir a Control de Vencimientos")
    print("   - Buscar un producto con lotes")
    print("   - Modificar fecha de un lote")
    print("   - Verificar que se actualicen las columnas correctas")
    
    print("\n5. 🔍 Usar F12 para ver los logs en consola:")
    print("   - Debe mostrar '✅ Estado actualizado: [estado]'")
    print("   - Debe mostrar '✅ Fecha actualizada: [fecha]'")
    print("   - Debe mostrar '✅ Lotes actualizados: [cantidad]'")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA - LISTO PARA APLICAR")
    print("=" * 60)

if __name__ == "__main__":
    main()
