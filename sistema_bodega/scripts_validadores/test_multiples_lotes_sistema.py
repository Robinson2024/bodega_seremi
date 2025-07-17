#!/usr/bin/env python
"""
Script de validación exhaustiva para detectar errores en el sistema
cuando se realizan múltiples ingresos de lotes y luego se agota el stock completamente.

Este script simula el escenario exacto que causó el error:
1. Crear productos con múltiples lotes (30 lotes diferentes)
2. Realizar salidas gradualmente hasta agotar stock
3. Validar que no haya errores en el proceso
4. Verificar integridad del sistema después del agotamiento
"""
import os
import sys
import django
import json
from datetime import date, timedelta
import random

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto, Transaccion, CustomUser
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

class ValidadorSistemaCompleto:
    """Validador exhaustivo del sistema de lotes."""
    
    def __init__(self):
        self.productos_test = []
        self.errores_encontrados = []
        self.warnings = []
        
    def log_error(self, mensaje):
        """Registra un error encontrado."""
        self.errores_encontrados.append(mensaje)
        print(f"❌ ERROR: {mensaje}")
        
    def log_warning(self, mensaje):
        """Registra una advertencia."""
        self.warnings.append(mensaje)
        print(f"⚠️  WARNING: {mensaje}")
        
    def log_info(self, mensaje):
        """Registra información."""
        print(f"ℹ️  INFO: {mensaje}")
        
    def limpiar_datos_test(self):
        """Limpia datos de pruebas previas."""
        print("\n🧹 LIMPIANDO DATOS DE PRUEBAS PREVIAS...")
        
        # Eliminar productos de prueba
        productos_eliminados = Producto.objects.filter(
            codigo_barra__startswith='TEST'
        ).delete()
        
        if productos_eliminados[0] > 0:
            self.log_info(f"Eliminados {productos_eliminados[0]} productos de prueba")
        
    def crear_productos_multiples_lotes(self, num_productos=3, lotes_por_producto=30):
        """Crea productos con múltiples lotes para testing."""
        print(f"\n🏭 CREANDO {num_productos} PRODUCTOS CON {lotes_por_producto} LOTES CADA UNO...")
        
        for i in range(num_productos):
            try:
                # Crear producto
                producto = Producto.objects.create(
                    codigo_barra=f'TEST{i+1:03d}',
                    descripcion=f'Producto Test {i+1}',
                    tiene_vencimiento=True,
                    fecha_vencimiento=date.today() + timedelta(days=90),
                    stock=0
                )
                
                stock_total = 0
                
                # Crear múltiples lotes
                for j in range(lotes_por_producto):
                    cantidad_lote = random.randint(10, 100)
                    dias_vencimiento = random.randint(30, 365)
                    
                    lote = LoteProducto.objects.create(
                        producto=producto,
                        numero_lote=j+1,
                        fecha_vencimiento=date.today() + timedelta(days=dias_vencimiento),
                        stock=cantidad_lote
                    )
                    
                    stock_total += cantidad_lote
                    
                    # Crear transacción de entrada
                    Transaccion.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=cantidad_lote,
                        rut_proveedor='123456789',
                        guia_despacho=f'GD{i+1:03d}{j+1:03d}'
                    )
                
                # Actualizar stock del producto
                producto.stock = stock_total
                producto.save()
                
                self.productos_test.append({
                    'producto': producto,
                    'stock_inicial': stock_total,
                    'lotes_creados': lotes_por_producto
                })
                
                self.log_info(f"Producto {producto.codigo_barra} creado con {lotes_por_producto} lotes ({stock_total} unidades)")
                
            except Exception as e:
                self.log_error(f"Error creando producto {i+1}: {e}")
                
    def validar_integridad_inicial(self):
        """Valida la integridad inicial del sistema."""
        print(f"\n🔍 VALIDANDO INTEGRIDAD INICIAL...")
        
        for item in self.productos_test:
            producto = item['producto']
            
            try:
                # Validar stock vs lotes
                stock_calculado = producto.lotes.aggregate(
                    total=models.Sum('stock')
                )['total'] or 0
                
                if producto.stock != stock_calculado:
                    self.log_error(f"Producto {producto.codigo_barra}: Stock desincronizado ({producto.stock} vs {stock_calculado})")
                
                # Validar métodos de lotes activos
                lotes_activos = producto.get_total_lotes_activos()
                lotes_con_stock = producto.lotes.filter(stock__gt=0).count()
                
                if lotes_activos != lotes_con_stock:
                    self.log_error(f"Producto {producto.codigo_barra}: Lotes activos desincronizados ({lotes_activos} vs {lotes_con_stock})")
                
                # Validar serialización JSON
                try:
                    lotes_detalle = producto.get_lotes_detalle()
                    json.dumps(lotes_detalle, cls=DjangoJSONEncoder)
                    
                    lotes_activos_detalle = producto.get_lotes_activos_detalle()
                    json.dumps(lotes_activos_detalle, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    self.log_error(f"Producto {producto.codigo_barra}: Error serialización JSON: {e}")
                
                self.log_info(f"✅ Producto {producto.codigo_barra}: Integridad inicial OK")
                
            except Exception as e:
                self.log_error(f"Error validando producto {producto.codigo_barra}: {e}")
                
    def simular_salidas_graduales(self, porcentaje_salida=0.1):
        """Simula salidas graduales hasta agotar stock."""
        print(f"\n📤 SIMULANDO SALIDAS GRADUALES HASTA AGOTAR STOCK...")
        
        for item in self.productos_test:
            producto = item['producto']
            producto.refresh_from_db()
            
            self.log_info(f"Iniciando salidas del producto {producto.codigo_barra} (Stock: {producto.stock})")
            
            salida_numero = 1
            
            while producto.stock > 0:
                try:
                    # Calcular cantidad a sacar (10% del stock actual o mínimo 1)
                    cantidad_salida = max(1, int(producto.stock * porcentaje_salida))
                    cantidad_salida = min(cantidad_salida, producto.stock)
                    
                    self.log_info(f"  Salida #{salida_numero}: {cantidad_salida} unidades")
                    
                    # Aplicar FIFO
                    resultado_fifo = producto.reducir_stock_fifo(cantidad_salida)
                    
                    if not resultado_fifo:
                        self.log_error(f"Producto {producto.codigo_barra}: Error en FIFO (salida #{salida_numero})")
                        break
                    
                    # Crear transacción de salida
                    Transaccion.objects.create(
                        producto=producto,
                        tipo='salida',
                        cantidad=cantidad_salida
                    )
                    
                    # Refrescar datos
                    producto.refresh_from_db()
                    
                    # Validar integridad después de cada salida
                    self.validar_integridad_salida(producto, salida_numero)
                    
                    salida_numero += 1
                    
                    # Protección contra bucles infinitos
                    if salida_numero > 1000:
                        self.log_error(f"Producto {producto.codigo_barra}: Demasiadas salidas (posible bucle infinito)")
                        break
                        
                except Exception as e:
                    self.log_error(f"Producto {producto.codigo_barra}: Error en salida #{salida_numero}: {e}")
                    break
            
            self.log_info(f"✅ Producto {producto.codigo_barra}: Stock agotado después de {salida_numero-1} salidas")
            
    def validar_integridad_salida(self, producto, salida_numero):
        """Valida integridad después de cada salida."""
        try:
            # Verificar sincronización stock-lotes
            stock_calculado = producto.lotes.aggregate(
                total=models.Sum('stock')
            )['total'] or 0
            
            if producto.stock != stock_calculado:
                self.log_error(f"Producto {producto.codigo_barra} (salida #{salida_numero}): Stock desincronizado ({producto.stock} vs {stock_calculado})")
            
            # Verificar métodos de lotes activos
            lotes_activos = producto.get_total_lotes_activos()
            lotes_con_stock = producto.lotes.filter(stock__gt=0).count()
            
            if lotes_activos != lotes_con_stock:
                self.log_error(f"Producto {producto.codigo_barra} (salida #{salida_numero}): Lotes activos desincronizados")
            
            # Verificar serialización JSON (aquí suele fallar)
            try:
                lotes_detalle = producto.get_lotes_detalle()
                json.dumps(lotes_detalle, cls=DjangoJSONEncoder)
                
                lotes_activos_detalle = producto.get_lotes_activos_detalle()
                json.dumps(lotes_activos_detalle, cls=DjangoJSONEncoder)
                
            except Exception as e:
                self.log_error(f"Producto {producto.codigo_barra} (salida #{salida_numero}): Error serialización JSON: {e}")
            
            # Verificar que no haya lotes con stock negativo
            lotes_negativos = producto.lotes.filter(stock__lt=0)
            if lotes_negativos.exists():
                self.log_error(f"Producto {producto.codigo_barra} (salida #{salida_numero}): Lotes con stock negativo detectados")
                
        except Exception as e:
            self.log_error(f"Error validando integridad (salida #{salida_numero}): {e}")
            
    def validar_estado_final(self):
        """Valida el estado final después de agotar todo el stock."""
        print(f"\n🎯 VALIDANDO ESTADO FINAL (STOCK AGOTADO)...")
        
        for item in self.productos_test:
            producto = item['producto']
            producto.refresh_from_db()
            
            try:
                # Verificar que el stock esté en 0
                if producto.stock != 0:
                    self.log_error(f"Producto {producto.codigo_barra}: Stock no está en 0 ({producto.stock})")
                
                # Verificar que no haya lotes con stock > 0
                lotes_con_stock = producto.lotes.filter(stock__gt=0).count()
                if lotes_con_stock > 0:
                    self.log_error(f"Producto {producto.codigo_barra}: Aún hay {lotes_con_stock} lotes con stock")
                
                # Verificar que todos los lotes estén en 0
                stock_total_lotes = producto.lotes.aggregate(
                    total=models.Sum('stock')
                )['total'] or 0
                
                if stock_total_lotes != 0:
                    self.log_error(f"Producto {producto.codigo_barra}: Stock total de lotes no está en 0 ({stock_total_lotes})")
                
                # Verificar métodos de lotes activos
                lotes_activos = producto.get_total_lotes_activos()
                if lotes_activos != 0:
                    self.log_error(f"Producto {producto.codigo_barra}: Lotes activos no están en 0 ({lotes_activos})")
                
                # Verificar que los lotes históricos se preserven
                total_lotes = producto.lotes.count()
                if total_lotes == 0:
                    self.log_error(f"Producto {producto.codigo_barra}: Los lotes históricos fueron eliminados")
                
                # Verificar serialización JSON final
                try:
                    lotes_detalle = producto.get_lotes_detalle()
                    json.dumps(lotes_detalle, cls=DjangoJSONEncoder)
                    
                    lotes_activos_detalle = producto.get_lotes_activos_detalle()
                    json.dumps(lotes_activos_detalle, cls=DjangoJSONEncoder)
                    
                    # Verificar que lotes_activos_detalle esté vacío
                    if len(lotes_activos_detalle) != 0:
                        self.log_error(f"Producto {producto.codigo_barra}: lotes_activos_detalle no está vacío")
                        
                except Exception as e:
                    self.log_error(f"Producto {producto.codigo_barra}: Error serialización JSON final: {e}")
                
                self.log_info(f"✅ Producto {producto.codigo_barra}: Estado final validado")
                
            except Exception as e:
                self.log_error(f"Error validando estado final del producto {producto.codigo_barra}: {e}")
                
    def simular_operaciones_vistas(self):
        """Simula operaciones típicas de las vistas para detectar errores."""
        print(f"\n🖥️ SIMULANDO OPERACIONES DE VISTAS...")
        
        for item in self.productos_test:
            producto = item['producto']
            producto.refresh_from_db()
            
            try:
                # Simular vista de control de vencimientos
                productos_control = []
                if producto.tiene_vencimiento and producto.stock > 0:
                    if producto.get_total_lotes_activos() > 0:
                        productos_control.append(producto)
                
                # Simular vista de gestión de vencimientos
                info_gestion = {
                    'total_lotes': len(producto.get_lotes_activos_detalle()),
                    'lotes_detalle': producto.get_lotes_detalle(),
                    'estadisticas': producto.get_estadisticas_lotes()
                }
                
                # Simular serialización para AJAX
                try:
                    json.dumps(info_gestion, cls=DjangoJSONEncoder)
                except Exception as e:
                    self.log_error(f"Producto {producto.codigo_barra}: Error serialización AJAX: {e}")
                
                # Simular limpieza de sesión
                productos_salida = [
                    {
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'lotes_activos': producto.get_total_lotes_activos()
                    }
                ]
                
                try:
                    json.dumps(productos_salida, cls=DjangoJSONEncoder)
                except Exception as e:
                    self.log_error(f"Producto {producto.codigo_barra}: Error serialización sesión: {e}")
                
                self.log_info(f"✅ Producto {producto.codigo_barra}: Operaciones de vistas OK")
                
            except Exception as e:
                self.log_error(f"Error simulando operaciones de vistas para {producto.codigo_barra}: {e}")
                
    def ejecutar_validacion_completa(self):
        """Ejecuta la validación completa del sistema."""
        print("🚀 INICIANDO VALIDACIÓN COMPLETA DEL SISTEMA DE LOTES")
        print("=" * 70)
        
        try:
            with transaction.atomic():
                # Limpiar datos previos
                self.limpiar_datos_test()
                
                # Crear productos con múltiples lotes
                self.crear_productos_multiples_lotes()
                
                # Validar integridad inicial
                self.validar_integridad_inicial()
                
                # Simular salidas graduales
                self.simular_salidas_graduales()
                
                # Validar estado final
                self.validar_estado_final()
                
                # Simular operaciones de vistas
                self.simular_operaciones_vistas()
                
                # Levantar excepción si hay errores para hacer rollback
                if self.errores_encontrados:
                    raise Exception("Se encontraron errores en el sistema")
                
        except Exception as e:
            print(f"\n💥 EXCEPCIÓN DURANTE LA VALIDACIÓN: {e}")
            
        finally:
            # Limpiar datos de prueba
            self.limpiar_datos_test()
            
        # Mostrar resumen
        self.mostrar_resumen()
        
    def mostrar_resumen(self):
        """Muestra el resumen de la validación."""
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 70)
        
        print(f"🧪 Productos testados: {len(self.productos_test)}")
        print(f"❌ Errores encontrados: {len(self.errores_encontrados)}")
        print(f"⚠️  Advertencias: {len(self.warnings)}")
        
        if self.errores_encontrados:
            print("\n❌ ERRORES DETALLADOS:")
            for error in self.errores_encontrados:
                print(f"   • {error}")
        
        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errores_encontrados and not self.warnings:
            print("\n✅ SISTEMA VALIDADO CORRECTAMENTE")
            print("   El sistema maneja correctamente múltiples lotes y agotamiento de stock")
        else:
            print("\n❌ SISTEMA REQUIERE CORRECCIONES")
            print("   Se encontraron problemas que deben ser corregidos")
        
        print("=" * 70)

def main():
    """Función principal."""
    validador = ValidadorSistemaCompleto()
    validador.ejecutar_validacion_completa()

if __name__ == "__main__":
    main()
