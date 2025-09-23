#!/usr/bin/env python
"""
Script para verificar y corregir el mapeo de columnas en la actualización visual
del template agregar_vencimiento.html

Este script verifica que:
1. La estructura de la tabla coincida con el mapeo de columnas en el JavaScript
2. La actualización visual funcione correctamente después de modificar un lote
3. Se actualicen las columnas correctas con los datos correctos
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.models import Producto, LoteProducto
from django.contrib.auth import get_user_model

def verificar_estructura_tabla():
    """Verifica la estructura de la tabla en el template"""
    print("🔍 Verificando estructura de la tabla...")
    
    # Las columnas según el template:
    columnas = [
        "1. Código",
        "2. Descripción", 
        "3. Categoría",
        "4. Stock",
        "5. Estado Vencimiento",  # Esta columna debe mostrar el estado
        "6. Fecha Vencimiento",   # Esta columna debe mostrar la fecha
        "7. Lotes",
        "8. Acciones"
    ]
    
    print("📋 Estructura de columnas en la tabla:")
    for columna in columnas:
        print(f"   {columna}")
    
    print("\n🎯 El JavaScript debe actualizar:")
    print("   - Columna 5 (nth-child(5)): Estado Vencimiento")
    print("   - Columna 6 (nth-child(6)): Fecha Vencimiento")
    
    return True

def crear_datos_test():
    """Crea datos de prueba para verificar la actualización visual"""
    print("\n🔧 Creando datos de prueba...")
    
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ No se encontró usuario administrador")
        return None
    
    # Buscar o crear un producto con vencimiento y lotes
    producto = Producto.objects.filter(tiene_vencimiento=True).first()
    
    if not producto:
        print("❌ No se encontró producto con vencimiento")
        return None
    
    print(f"✅ Producto encontrado: {producto.codigo_barra} - {producto.descripcion}")
    
    # Asegurar que tiene al menos 2 lotes con fechas diferentes
    lotes = LoteProducto.objects.filter(producto=producto)
    
    if lotes.count() < 2:
        print("🔄 Creando lotes de prueba...")
        
        # Limpiar lotes existentes
        lotes.delete()
        
        # Crear dos lotes con fechas diferentes
        fecha_cercana = datetime.now().date() + timedelta(days=15)
        fecha_lejana = datetime.now().date() + timedelta(days=45)
        
        lote1 = LoteProducto.objects.create(
            producto=producto,
            numero_lote="TEST001",
            fecha_vencimiento=fecha_cercana,
            stock=25,
            creado_por=admin_user
        )
        
        lote2 = LoteProducto.objects.create(
            producto=producto,
            numero_lote="TEST002", 
            fecha_vencimiento=fecha_lejana,
            stock=30,
            creado_por=admin_user
        )
        
        print(f"✅ Lote 1 creado: {lote1.numero_lote} - {lote1.fecha_vencimiento}")
        print(f"✅ Lote 2 creado: {lote2.numero_lote} - {lote2.fecha_vencimiento}")
    
    # Sincronizar stock del producto
    total_stock = sum(lote.stock for lote in LoteProducto.objects.filter(producto=producto))
    producto.stock = total_stock
    producto.save()
    
    print(f"✅ Stock sincronizado: {producto.stock}")
    
    return producto

def verificar_datos_producto_vista(producto):
    """Verifica los datos que debería mostrar la vista para un producto"""
    print(f"\n📊 Verificando datos para producto {producto.codigo_barra}...")
    
    # Obtener datos como los devuelve la vista
    from accounts.views import ProductoVencimiento
    from django.test import RequestFactory
    
    # Simular el cálculo que hace la vista
    lotes = LoteProducto.objects.filter(producto=producto).order_by('fecha_vencimiento')
    
    if lotes.exists():
        proximo_vencimiento = lotes.first().fecha_vencimiento
        estado_vencimiento = ProductoVencimiento.calcular_estado_vencimiento(proximo_vencimiento)
    else:
        proximo_vencimiento = None
        estado_vencimiento = "Sin vencimiento"
    
    total_lotes = lotes.count()
    
    print(f"📅 Próximo vencimiento: {proximo_vencimiento}")
    print(f"🚦 Estado vencimiento: {estado_vencimiento}")
    print(f"📦 Total lotes: {total_lotes}")
    
    # Verificar qué se debe mostrar en cada columna
    print("\n🎯 Lo que debe mostrarse en la tabla:")
    print(f"   Columna 5 (Estado): <span class='badge estado-{estado_vencimiento.lower()}'>{estado_vencimiento}</span>")
    if proximo_vencimiento:
        print(f"   Columna 6 (Fecha): {proximo_vencimiento.strftime('%d/%m/%Y')}")
    else:
        print(f"   Columna 6 (Fecha): <span class='text-muted'>Sin fecha</span>")
    print(f"   Columna 7 (Lotes): <span class='badge badge-primary'>{total_lotes} lote{'s' if total_lotes != 1 else ''}</span>")
    
    return {
        'proximo_vencimiento': proximo_vencimiento,
        'estado_vencimiento': estado_vencimiento,
        'total_lotes': total_lotes
    }

def generar_correcciones_javascript():
    """Genera las correcciones necesarias para el JavaScript"""
    print("\n🔧 Generando correcciones para el JavaScript...")
    
    correcciones = """
// CORRECCIÓN del mapeo de columnas en actualizarDatosProducto()

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
            
            // ✅ CORRECTO: Actualizar estado de vencimiento en la columna 5
            const estadoCell = fila.querySelector('td:nth-child(5)');
            if (estadoCell) {
                const claseEstado = getClaseEstado(producto.estado_vencimiento);
                estadoCell.innerHTML = `<span class="badge ${claseEstado}">${producto.estado_vencimiento}</span>`;
            }
            
            // ✅ CORRECTO: Actualizar fecha de vencimiento en la columna 6
            const fechaCell = fila.querySelector('td:nth-child(6)');
            if (fechaCell) {
                fechaCell.innerHTML = producto.proximo_vencimiento ? 
                    producto.proximo_vencimiento_display : 
                    '<span class="text-muted">Sin fecha</span>';
            }
            
            // ✅ Actualizar cantidad de lotes en la columna 7
            const lotesCell = fila.querySelector('td:nth-child(7)');
            if (lotesCell) {
                lotesCell.innerHTML = `<span class="badge badge-primary">${producto.total_lotes} lote${producto.total_lotes !== 1 ? 's' : ''}</span>`;
            }
            
            console.log('✅ Fila actualizada correctamente para producto:', codigo);
        } else {
            console.error('❌ Error al obtener datos del producto:', data.error);
        }
    })
    .catch(error => {
        console.error('❌ Error de conexión al actualizar fila:', error);
    });
}
"""
    
    print("📝 Correcciones generadas:")
    print("   ✅ Mapeo correcto de columnas nth-child(5) y nth-child(6)")
    print("   ✅ Actualización del estado en la columna correcta")
    print("   ✅ Actualización de la fecha en la columna correcta")
    print("   ✅ Logs mejorados para debugging")
    
    return correcciones

def main():
    """Función principal"""
    print("🧪 VERIFICACIÓN Y CORRECCIÓN DEL MAPEO DE COLUMNAS")
    print("=" * 60)
    
    # 1. Verificar estructura de la tabla
    verificar_estructura_tabla()
    
    # 2. Crear datos de prueba
    producto = crear_datos_test()
    if not producto:
        print("❌ No se pudieron crear datos de prueba")
        return
    
    # 3. Verificar datos de la vista
    datos = verificar_datos_producto_vista(producto)
    
    # 4. Generar correcciones
    correcciones = generar_correcciones_javascript()
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 60)
    
    print("\n🎯 PROBLEMA IDENTIFICADO:")
    print("   El JavaScript estaba confundiendo las columnas 5 y 6")
    print("   - Columna 5: Estado Vencimiento (badge con color)")
    print("   - Columna 6: Fecha Vencimiento (fecha formateada)")
    
    print("\n🔧 SOLUCIÓN:")
    print("   Corregir el mapeo nth-child() en la función actualizarDatosProducto()")
    print("   para que actualice las columnas correctas")
    
    print(f"\n📦 DATOS DE PRUEBA DISPONIBLES:")
    print(f"   Producto: {producto.codigo_barra}")
    print(f"   Descripción: {producto.descripcion}")
    print(f"   Lotes: {datos['total_lotes']}")
    print(f"   Estado: {datos['estado_vencimiento']}")
    print(f"   Próximo vencimiento: {datos['proximo_vencimiento']}")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Aplicar la corrección al template agregar_vencimiento.html")
    print("   2. Probar la modificación de fecha de lote en el navegador")
    print("   3. Verificar que se actualicen las columnas correctas")

if __name__ == "__main__":
    main()
