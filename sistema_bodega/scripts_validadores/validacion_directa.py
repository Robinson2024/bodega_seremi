#!/usr/bin/env python
"""
VALIDACIÓN DIRECTA DEL SISTEMA - SIN CLIENTE WEB
Prueba directamente los modelos y la lógica de negocio

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
import time
import traceback

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.db import transaction, connection
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.models import (
    Producto, Transaccion, LoteProducto, 
    ActaEntrega, Funcionario, CustomUser, Categoria
)

User = get_user_model()

class ValidadorDirecto:
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.exitos = []
        self.metricas = {}
        print("🎯 VALIDADOR DIRECTO INICIALIZADO")
        
    def log_error(self, mensaje, detalle=None):
        error = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje,
            'detalle': detalle or ''
        }
        self.errores.append(error)
        print(f"❌ ERROR: {mensaje}")
        if detalle:
            print(f"   Detalle: {detalle}")
    
    def log_warning(self, mensaje):
        warning = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        }
        self.warnings.append(warning)
        print(f"⚠️  WARNING: {mensaje}")
    
    def log_exito(self, mensaje):
        exito = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        }
        self.exitos.append(exito)
        print(f"✅ ÉXITO: {mensaje}")

    def probar_creacion_productos(self):
        """Prueba la creación directa de productos"""
        print("\n📦 PROBANDO CREACIÓN DE PRODUCTOS")
        print("="*50)
        
        try:
            # Limpiar productos de prueba previos
            Producto.objects.filter(codigo_barra__startswith='TEST_DIRECTO').delete()
            
            productos_creados = []
            
            for i in range(5):
                codigo = f'TEST_DIRECTO_{i:03d}'
                
                producto = Producto.objects.create(
                    codigo_barra=codigo,
                    descripcion=f'Producto Directo {i} - Prueba directa de funcionalidad del modelo Producto',
                    stock=0,
                    rut_proveedor='12345678-9',
                    tiene_vencimiento=True if i % 2 == 0 else False
                )
                
                productos_creados.append(producto)
                self.log_exito(f"Producto creado: {codigo}")
            
            # Verificar que se crearon correctamente
            productos_verificados = Producto.objects.filter(codigo_barra__startswith='TEST_DIRECTO')
            
            if productos_verificados.count() == 5:
                self.log_exito("Todos los productos verificados en BD")
            else:
                self.log_error(f"Productos esperados: 5, encontrados: {productos_verificados.count()}")
            
            return productos_creados
            
        except Exception as e:
            self.log_error("Error creando productos", str(e))
            return []

    def probar_transacciones_stock(self, productos):
        """Prueba las transacciones y manejo de stock"""
        print("\n📋 PROBANDO TRANSACCIONES Y STOCK")
        print("="*50)
        
        try:
            if not productos:
                self.log_error("No hay productos para probar transacciones")
                return False
            
            transacciones_creadas = 0
            
            for producto in productos:
                # Transacciones de entrada
                for j in range(3):
                    cantidad = random.randint(10, 50)
                    
                    transaccion = Transaccion.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=cantidad,
                        observacion=f'Entrada directa {j}',
                        fecha=date.today()
                    )
                    
                    # Actualizar stock
                    producto.stock += cantidad
                    producto.save()
                    
                    transacciones_creadas += 1
                    self.log_exito(f"Entrada creada: {cantidad} unidades para {producto.codigo_barra}")
                
                # Una transacción de salida
                if producto.stock > 0:
                    cantidad_salida = min(producto.stock // 2, 10)
                    
                    transaccion_salida = Transaccion.objects.create(
                        producto=producto,
                        tipo='salida',
                        cantidad=cantidad_salida,
                        observacion='Salida directa',
                        fecha=date.today()
                    )
                    
                    producto.stock -= cantidad_salida
                    producto.save()
                    
                    transacciones_creadas += 1
                    self.log_exito(f"Salida creada: {cantidad_salida} unidades para {producto.codigo_barra}")
            
            self.log_exito(f"Total transacciones creadas: {transacciones_creadas}")
            return True
            
        except Exception as e:
            self.log_error("Error en transacciones", str(e))
            return False

    def probar_lotes_vencimientos(self, productos):
        """Prueba la creación y manejo de lotes"""
        print("\n🏷️  PROBANDO LOTES Y VENCIMIENTOS")
        print("="*50)
        
        try:
            lotes_creados = 0
            
            for producto in productos:
                if producto.tiene_vencimiento:
                    # Crear varios lotes con diferentes vencimientos
                    fechas_vencimiento = [
                        date.today() + timedelta(days=15),  # Vence pronto
                        date.today() + timedelta(days=45),  # Vence en mes y medio
                        date.today() + timedelta(days=90)   # Vence en 3 meses
                    ]
                    
                    for idx, fecha_venc in enumerate(fechas_vencimiento):
                        lote = LoteProducto.objects.create(
                            producto=producto,
                            numero_lote=f'LOTE_{producto.codigo_barra}_{idx}',
                            fecha_vencimiento=fecha_venc,
                            stock=random.randint(10, 30)
                        )
                        
                        lotes_creados += 1
                        self.log_exito(f"Lote creado: {lote.numero_lote} (vence: {fecha_venc})")
            
            # Verificar lotes próximos a vencer
            lotes_criticos = LoteProducto.objects.filter(
                fecha_vencimiento__lte=date.today() + timedelta(days=30)
            )
            
            if lotes_criticos.exists():
                self.log_warning(f"{lotes_criticos.count()} lotes próximos a vencer")
            else:
                self.log_exito("No hay lotes críticos por vencimiento")
            
            self.log_exito(f"Total lotes creados: {lotes_creados}")
            return True
            
        except Exception as e:
            self.log_error("Error en lotes", str(e))
            return False

    def verificar_consistencia_stock(self, productos):
        """Verifica la consistencia del stock"""
        print("\n🔍 VERIFICANDO CONSISTENCIA DE STOCK")
        print("="*50)
        
        try:
            productos_inconsistentes = 0
            
            for producto in productos:
                # Calcular stock basado en transacciones
                transacciones = Transaccion.objects.filter(producto=producto)
                stock_calculado = 0
                
                for trans in transacciones:
                    if trans.tipo == 'entrada':
                        stock_calculado += trans.cantidad
                    elif trans.tipo == 'salida':
                        stock_calculado -= trans.cantidad
                
                # Comparar con stock registrado
                if producto.stock != stock_calculado:
                    self.log_error(f"Inconsistencia en {producto.codigo_barra}: BD={producto.stock}, Calculado={stock_calculado}")
                    productos_inconsistentes += 1
                else:
                    self.log_exito(f"Stock consistente en {producto.codigo_barra}: {producto.stock}")
            
            if productos_inconsistentes == 0:
                self.log_exito("Todos los productos tienen stock consistente")
                return True
            else:
                self.log_error(f"{productos_inconsistentes} productos con stock inconsistente")
                return False
            
        except Exception as e:
            self.log_error("Error verificando consistencia", str(e))
            return False

    def probar_consultas_rendimiento(self):
        """Prueba el rendimiento de consultas clave"""
        print("\n⚡ PROBANDO RENDIMIENTO DE CONSULTAS")
        print("="*50)
        
        consultas = [
            {
                'nombre': 'Productos con stock',
                'query': lambda: Producto.objects.filter(stock__gt=0).count(),
                'limite': 0.1
            },
            {
                'nombre': 'Transacciones recientes',
                'query': lambda: Transaccion.objects.filter(
                    fecha__gte=date.today() - timedelta(days=7)
                ).count(),
                'limite': 0.1
            },
            {
                'nombre': 'Lotes activos',
                'query': lambda: LoteProducto.objects.filter(stock__gt=0).count(),
                'limite': 0.1
            },
            {
                'nombre': 'Usuarios activos',
                'query': lambda: User.objects.filter(is_active=True).count(),
                'limite': 0.1
            }
        ]
        
        try:
            for consulta in consultas:
                inicio = time.time()
                resultado = consulta['query']()
                fin = time.time()
                tiempo = fin - inicio
                
                self.metricas[consulta['nombre']] = tiempo
                
                if tiempo <= consulta['limite']:
                    self.log_exito(f"{consulta['nombre']}: {tiempo:.4f}s ({resultado} registros)")
                else:
                    self.log_warning(f"{consulta['nombre']}: {tiempo:.4f}s - LENTO ({resultado} registros)")
            
            return True
            
        except Exception as e:
            self.log_error("Error en consultas de rendimiento", str(e))
            return False

    def probar_validaciones_modelo(self, productos):
        """Prueba las validaciones de los modelos"""
        print("\n✅ PROBANDO VALIDACIONES DE MODELO")
        print("="*50)
        
        try:
            # Probar validación de código de barra único
            try:
                Producto.objects.create(
                    codigo_barra=productos[0].codigo_barra,  # Código duplicado
                    descripcion='Producto duplicado',
                    stock=0,
                    rut_proveedor='12345678-9',
                    tiene_vencimiento=False
                )
                self.log_error("Validación de código único falló - permitió duplicado")
            except Exception:
                self.log_exito("Validación de código único funcionando")
            
            # Probar validación de stock negativo (si existe)
            producto_test = productos[0]
            stock_original = producto_test.stock
            
            try:
                producto_test.stock = -10
                producto_test.save()
                self.log_warning("Sistema permite stock negativo")
                # Restaurar stock
                producto_test.stock = stock_original
                producto_test.save()
            except Exception:
                self.log_exito("Validación de stock negativo funcionando")
                producto_test.stock = stock_original
                producto_test.save()
            
            # Probar validación de fechas de vencimiento
            try:
                LoteProducto.objects.create(
                    producto=productos[0],
                    numero_lote='LOTE_FECHA_PASADA',
                    fecha_vencimiento=date.today() - timedelta(days=30),  # Fecha pasada
                    stock=10
                )
                self.log_warning("Sistema permite crear lotes con fecha de vencimiento pasada")
            except Exception:
                self.log_exito("Validación de fechas de vencimiento funcionando")
            
            return True
            
        except Exception as e:
            self.log_error("Error en validaciones de modelo", str(e))
            return False

    def limpiar_datos_prueba(self):
        """Limpia todos los datos de prueba"""
        print("\n🧹 LIMPIANDO DATOS DE PRUEBA")
        print("="*50)
        
        try:
            # Eliminar lotes de prueba
            lotes_eliminados = LoteProducto.objects.filter(
                numero_lote__contains='LOTE_TEST_DIRECTO'
            ).delete()[0]
            
            # Eliminar transacciones de prueba
            transacciones_eliminadas = Transaccion.objects.filter(
                producto__codigo_barra__startswith='TEST_DIRECTO'
            ).delete()[0]
            
            # Eliminar productos de prueba
            productos_eliminados = Producto.objects.filter(
                codigo_barra__startswith='TEST_DIRECTO'
            ).delete()[0]
            
            self.log_exito(f"Limpieza completada: {productos_eliminados} productos, {transacciones_eliminadas} transacciones, {lotes_eliminados} lotes")
            
        except Exception as e:
            self.log_error("Error en limpieza", str(e))

    def generar_reporte_directo(self):
        """Genera reporte de la validación directa"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'tipo_validacion': 'directa_sin_web',
            'resumen': {
                'total_pruebas': len(self.exitos) + len(self.errores) + len(self.warnings),
                'exitos': len(self.exitos),
                'errores': len(self.errores),
                'warnings': len(self.warnings),
                'estado': 'APTO' if len(self.errores) == 0 else 'CON_OBSERVACIONES'
            },
            'metricas_rendimiento': self.metricas,
            'validaciones': {
                'exitos': self.exitos,
                'errores': self.errores,
                'warnings': self.warnings
            }
        }
        
        archivo = f'reporte_validacion_directa_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            print(f"\n📄 REPORTE GUARDADO: {archivo}")
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        return reporte

    def mostrar_resumen(self):
        """Muestra el resumen final"""
        print("\n" + "="*70)
        print("📋 RESUMEN - VALIDACIÓN DIRECTA DEL SISTEMA")
        print("="*70)
        
        print(f"✅ Éxitos: {len(self.exitos)}")
        print(f"❌ Errores: {len(self.errores)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.metricas:
            print(f"\n⚡ MÉTRICAS DE RENDIMIENTO:")
            for metrica, tiempo in self.metricas.items():
                print(f"   {metrica}: {tiempo:.4f}s")
        
        print(f"\n🎯 ESTADO DEL SISTEMA:")
        if len(self.errores) == 0:
            print("   🟢 EXCELENTE - Sistema funciona correctamente")
        elif len(self.errores) <= 2:
            print("   🟡 BUENO - Errores menores detectados")
        else:
            print("   🔴 PROBLEMAS - Requiere atención")
        
        if self.errores:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in self.errores:
                print(f"   • {error['mensaje']}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   • {warning['mensaje']}")

    def ejecutar_validacion_completa(self):
        """Ejecuta toda la validación directa"""
        print("🎯 VALIDACIÓN DIRECTA DEL SISTEMA")
        print("Método: Acceso directo a modelos (sin cliente web)")
        print("="*70)
        
        try:
            # 1. Crear productos
            productos = self.probar_creacion_productos()
            
            if productos:
                # 2. Transacciones y stock
                self.probar_transacciones_stock(productos)
                
                # 3. Lotes y vencimientos
                self.probar_lotes_vencimientos(productos)
                
                # 4. Verificar consistencia
                self.verificar_consistencia_stock(productos)
                
                # 5. Validaciones de modelo
                self.probar_validaciones_modelo(productos)
            
            # 6. Consultas de rendimiento
            self.probar_consultas_rendimiento()
            
            # 7. Limpiar
            self.limpiar_datos_prueba()
            
            # 8. Reporte
            reporte = self.generar_reporte_directo()
            self.mostrar_resumen()
            
            return reporte
            
        except Exception as e:
            self.log_error("Error fatal en validación", str(e))
            traceback.print_exc()
            return None

def main():
    """Función principal"""
    print("VALIDACIÓN DIRECTA - SISTEMA BODEGA SEREMI")
    print("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("="*70)
    
    validador = ValidadorDirecto()
    
    try:
        reporte = validador.ejecutar_validacion_completa()
        return reporte
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        traceback.print_exc()
    finally:
        print("\n🏁 Validación finalizada")

if __name__ == "__main__":
    main()
