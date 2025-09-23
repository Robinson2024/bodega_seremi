#!/usr/bin/env python
"""
Script para crear un escenario de prueba específico y verificar la corrección
del problema visual en la actualización de fechas de lotes
"""
import os
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from django.contrib.auth import get_user_model

def crear_escenario_test():
    """Crea un escenario específico para probar la corrección"""
    print("🔧 Creando escenario de prueba específico...")
    
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    # Usar el producto de leche que ya sabemos que existe
    try:
        producto = Producto.objects.get(codigo_barra='100041')
        print(f"✅ Producto encontrado: {producto.codigo_barra} - {producto.descripcion}")
    except Producto.DoesNotExist:
        print("❌ Producto no encontrado")
        return None
    
    # Limpiar lotes existentes para empezar fresco
    LoteProducto.objects.filter(producto=producto).delete()
    print("🧹 Lotes anteriores eliminados")
    
    # Crear exactamente 2 lotes con fechas muy específicas
    fecha_critica = datetime.now().date() + timedelta(days=5)   # Crítico (5 días)
    fecha_normal = datetime.now().date() + timedelta(days=25)   # Normal (25 días)
    
    lote1 = LoteProducto.objects.create(
        producto=producto,
        numero_lote=1001,
        fecha_vencimiento=fecha_critica,
        stock=15
    )
    
    lote2 = LoteProducto.objects.create(
        producto=producto,
        numero_lote=1002, 
        fecha_vencimiento=fecha_normal,
        stock=35
    )
    
    # Sincronizar stock
    producto.actualizar_stock_total()
    
    print(f"✅ Lote crítico: {lote1.numero_lote} - {lote1.fecha_vencimiento} - {lote1.stock} unidades")
    print(f"✅ Lote normal: {lote2.numero_lote} - {lote2.fecha_vencimiento} - {lote2.stock} unidades")
    print(f"✅ Stock total: {producto.stock}")
    
    # Mostrar el estado actual del producto
    estado = producto.get_estado_vencimiento_completo()
    proximo = producto.get_proximo_vencimiento()
    
    print(f"\n📊 Estado actual del producto:")
    print(f"   Estado: {estado}")
    print(f"   Próximo vencimiento: {proximo}")
    print(f"   Total lotes: {LoteProducto.objects.filter(producto=producto).count()}")
    
    return producto, lote1, lote2

def simular_cambio_fecha_lote(producto, lote_a_cambiar, nueva_fecha):
    """Simula el cambio de fecha de un lote y muestra el resultado"""
    print(f"\n🔄 Simulando cambio de fecha del lote {lote_a_cambiar.numero_lote}...")
    print(f"   Fecha anterior: {lote_a_cambiar.fecha_vencimiento}")
    print(f"   Fecha nueva: {nueva_fecha}")
    
    # Cambiar la fecha del lote
    lote_a_cambiar.fecha_vencimiento = nueva_fecha
    lote_a_cambiar.save()
    
    # Refrescar el producto y recalcular
    producto.refresh_from_db()
    producto.actualizar_stock_total()
    
    # Mostrar el nuevo estado
    nuevo_estado = producto.get_estado_vencimiento_completo()
    nuevo_proximo = producto.get_proximo_vencimiento()
    
    print(f"\n📊 Nuevo estado del producto:")
    print(f"   Estado: {nuevo_estado}")
    print(f"   Próximo vencimiento: {nuevo_proximo}")
    
    print(f"\n🎯 Lo que debe mostrarse en la tabla:")
    print(f"   Columna 5 (Estado): <span class='badge estado-{nuevo_estado.lower()}'>{nuevo_estado}</span>")
    if nuevo_proximo:
        print(f"   Columna 6 (Fecha): {nuevo_proximo.strftime('%d/%m/%Y')}")
    else:
        print(f"   Columna 6 (Fecha): <span class='text-muted'>Sin fecha</span>")
    
    return nuevo_estado, nuevo_proximo

def main():
    """Función principal"""
    print("🧪 PRUEBA ESPECÍFICA: CORRECCIÓN VISUAL DE FECHAS DE LOTES")
    print("=" * 70)
    
    # 1. Crear escenario
    resultado = crear_escenario_test()
    if not resultado:
        print("❌ No se pudo crear el escenario de prueba")
        return
    
    producto, lote_critico, lote_normal = resultado
    
    # 2. Simular cambio que mejore el estado (crítico -> normal)
    print("\n" + "="*50)
    print("🧪 PRUEBA 1: Cambiar lote crítico a fecha normal")
    print("="*50)
    
    nueva_fecha_mejorada = datetime.now().date() + timedelta(days=30)
    nuevo_estado, nuevo_proximo = simular_cambio_fecha_lote(
        producto, lote_critico, nueva_fecha_mejorada
    )
    
    # 3. Simular cambio que empeore el estado (normal -> crítico)
    print("\n" + "="*50)
    print("🧪 PRUEBA 2: Cambiar lote normal a fecha crítica")
    print("="*50)
    
    nueva_fecha_critica = datetime.now().date() + timedelta(days=3)
    nuevo_estado2, nuevo_proximo2 = simular_cambio_fecha_lote(
        producto, lote_normal, nueva_fecha_critica
    )
    
    print("\n" + "="*70)
    print("📋 INSTRUCCIONES DE PRUEBA VISUAL")
    print("="*70)
    
    print(f"\n1. 🌐 Abrir en el navegador:")
    print(f"   http://127.0.0.1:8000/accounts/agregar-vencimiento/")
    
    print(f"\n2. 🔍 Buscar el producto:")
    print(f"   Código: {producto.codigo_barra}")
    print(f"   Descripción: {producto.descripcion}")
    
    print(f"\n3. 👀 Verificar estado inicial:")
    print(f"   Columna 'Estado Vencimiento': {nuevo_estado2}")
    print(f"   Columna 'Fecha Vencimiento': {nuevo_proximo2.strftime('%d/%m/%Y') if nuevo_proximo2 else 'Sin fecha'}")
    
    print(f"\n4. 🔧 Hacer clic en 'Lotes (2)' y modificar fecha de un lote")
    
    print(f"\n5. 🔍 Abrir F12 -> Console y verificar los logs:")
    print(f"   Debe mostrar: '🔍 Datos recibidos del servidor: ...'")
    print(f"   Debe mostrar: '✅ Estado actualizado en columna 5: ...'") 
    print(f"   Debe mostrar: '✅ Fecha actualizada en columna 6: ...'")
    print(f"   Debe mostrar: '📊 Resumen de actualización: ...'")
    
    print(f"\n6. ✅ Verificar que:")
    print(f"   - La columna 'Estado Vencimiento' se actualiza CORRECTAMENTE")
    print(f"   - La columna 'Fecha Vencimiento' se actualiza CORRECTAMENTE")
    print(f"   - NO desaparecen momentáneamente los valores")
    print(f"   - Los colores y estilos son correctos")
    
    print("\n" + "="*70)
    print("✅ ESCENARIO DE PRUEBA LISTO")
    print("="*70)
    
    print(f"\n💡 TIP: Si aún hay problemas visuales, revisar en los logs:")
    print(f"   - Qué datos llegan del servidor")
    print(f"   - En qué columnas se están actualizando")
    print(f"   - Si hay errores en el mapeo de estados a clases CSS")

if __name__ == "__main__":
    main()
