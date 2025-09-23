#!/usr/bin/env python
"""
VALIDACIÓN COMPLETA PARA PRODUCCIÓN - SISTEMA BODEGA SEREMI
Pruebas específicas para deployment en entorno VPN institucional

Este script verifica:
- Funcionamiento básico del sistema
- Estabilidad bajo carga
- Escalabilidad de datos
- Integridad de la información
- Rendimiento de consultas

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

class ValidadorProduccion:
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.exitos = []
        self.metricas = {}
        print("🚀 VALIDADOR PARA PRODUCCIÓN INICIALIZADO")
        
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

    def verificar_estado_actual_bd(self):
        """Verifica el estado actual de la base de datos"""
        print("\n📊 VERIFICANDO ESTADO ACTUAL DE LA BASE DE DATOS")
        print("="*60)
        
        try:
            # Contar registros
            total_productos = Producto.objects.count()
            total_transacciones = Transaccion.objects.count()
            total_lotes = LoteProducto.objects.count()
            total_usuarios = User.objects.count()
            total_categorias = Categoria.objects.count()
            
            print(f"📦 Productos en sistema: {total_productos}")
            print(f"📋 Transacciones registradas: {total_transacciones}")
            print(f"🏷️  Lotes activos: {total_lotes}")
            print(f"👥 Usuarios registrados: {total_usuarios}")
            print(f"📂 Categorías: {total_categorias}")
            
            self.log_exito(f"Base de datos operativa con {total_productos} productos")
            
            # Verificar productos con stock
            productos_con_stock = Producto.objects.filter(stock__gt=0).count()
            productos_sin_stock = Producto.objects.filter(stock=0).count()
            productos_stock_negativo = Producto.objects.filter(stock__lt=0).count()
            
            print(f"📈 Productos con stock: {productos_con_stock}")
            print(f"📉 Productos sin stock: {productos_sin_stock}")
            print(f"⚠️  Productos con stock negativo: {productos_stock_negativo}")
            
            if productos_stock_negativo > 0:
                self.log_warning(f"{productos_stock_negativo} productos con stock negativo detectados")
            else:
                self.log_exito("No hay productos con stock negativo")
            
            return True
            
        except Exception as e:
            self.log_error("Error verificando estado de BD", str(e))
            return False

    def verificar_integridad_datos(self):
        """Verifica la integridad de los datos del sistema"""
        print("\n🔍 VERIFICANDO INTEGRIDAD DE DATOS")
        print("="*60)
        
        try:
            # 1. Verificar sincronización stock vs transacciones
            productos_con_problemas = []
            productos_verificados = 0
            
            for producto in Producto.objects.all():
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
                    productos_con_problemas.append({
                        'producto': producto.codigo_barra,
                        'stock_bd': producto.stock,
                        'stock_calculado': stock_calculado,
                        'diferencia': producto.stock - stock_calculado
                    })
                
                productos_verificados += 1
            
            if productos_con_problemas:
                self.log_warning(f"{len(productos_con_problemas)} productos con desincronización de stock")
                for problema in productos_con_problemas[:5]:  # Mostrar solo los primeros 5
                    print(f"   {problema['producto']}: BD={problema['stock_bd']}, Calc={problema['stock_calculado']}")
            else:
                self.log_exito(f"Sincronización de stock correcta en {productos_verificados} productos")
            
            # 2. Verificar lotes
            lotes_problemáticos = []
            
            for lote in LoteProducto.objects.all():
                # Verificar fechas de vencimiento
                if lote.fecha_vencimiento < date.today():
                    lotes_problemáticos.append({
                        'lote': lote.numero_lote,
                        'producto': lote.producto.codigo_barra,
                        'vencimiento': lote.fecha_vencimiento,
                        'problema': 'vencido'
                    })
                
                # Verificar stock negativo en lotes
                if lote.stock < 0:
                    lotes_problemáticos.append({
                        'lote': lote.numero_lote,
                        'producto': lote.producto.codigo_barra,
                        'stock': lote.stock,
                        'problema': 'stock_negativo'
                    })
            
            if lotes_problemáticos:
                vencidos = [l for l in lotes_problemáticos if l.get('problema') == 'vencido']
                stock_neg = [l for l in lotes_problemáticos if l.get('problema') == 'stock_negativo']
                
                if vencidos:
                    self.log_warning(f"{len(vencidos)} lotes vencidos detectados")
                if stock_neg:
                    self.log_warning(f"{len(stock_neg)} lotes con stock negativo")
            else:
                self.log_exito("Todos los lotes están en buen estado")
            
            return True
            
        except Exception as e:
            self.log_error("Error verificando integridad de datos", str(e))
            return False

    def probar_rendimiento_consultas(self):
        """Prueba el rendimiento de consultas importantes"""
        print("\n⚡ PROBANDO RENDIMIENTO DE CONSULTAS")
        print("="*60)
        
        consultas_prueba = [
            {
                'nombre': 'Productos con stock bajo',
                'query': lambda: list(Producto.objects.filter(stock__lt=10)),
                'limite_tiempo': 1.0
            },
            {
                'nombre': 'Transacciones del último mes',
                'query': lambda: list(Transaccion.objects.filter(
                    fecha__gte=date.today() - timedelta(days=30)
                ).select_related('producto')),
                'limite_tiempo': 2.0
            },
            {
                'nombre': 'Lotes próximos a vencer',
                'query': lambda: list(LoteProducto.objects.filter(
                    fecha_vencimiento__lte=date.today() + timedelta(days=30)
                ).select_related('producto')),
                'limite_tiempo': 1.5
            },
            {
                'nombre': 'Productos más movidos',
                'query': lambda: list(Producto.objects.annotate(
                    total_movimientos=models.Count('transaccion')
                ).order_by('-total_movimientos')[:10]),
                'limite_tiempo': 2.0
            }
        ]
        
        try:
            from django.db import models
            
            for consulta in consultas_prueba:
                inicio = time.time()
                resultado = consulta['query']()
                fin = time.time()
                tiempo = fin - inicio
                
                self.metricas[consulta['nombre']] = tiempo
                
                if tiempo <= consulta['limite_tiempo']:
                    self.log_exito(f"{consulta['nombre']}: {tiempo:.3f}s - RÁPIDO")
                else:
                    self.log_warning(f"{consulta['nombre']}: {tiempo:.3f}s - LENTO (>{consulta['limite_tiempo']}s)")
                
                print(f"   Registros obtenidos: {len(resultado)}")
            
            return True
            
        except Exception as e:
            self.log_error("Error en pruebas de rendimiento", str(e))
            return False

    def simular_carga_operaciones(self):
        """Simula operaciones típicas del sistema bajo carga"""
        print("\n🔥 SIMULANDO CARGA DE OPERACIONES")
        print("="*60)
        
        try:
            # Crear datos de prueba temporales
            productos_prueba = []
            
            for i in range(5):  # Crear 5 productos de prueba
                codigo = f'PROD_TEST_{i:03d}'
                
                # Verificar si ya existe
                if not Producto.objects.filter(codigo_barra=codigo).exists():
                    producto = Producto.objects.create(
                        codigo_barra=codigo,
                        descripcion=f'Producto de prueba {i} - Simulación de carga del sistema',
                        stock=0,
                        rut_proveedor='12345678-9',
                        tiene_vencimiento=False
                    )
                    productos_prueba.append(producto)
            
            self.log_exito(f"Creados {len(productos_prueba)} productos de prueba")
            
            # Simular múltiples transacciones concurrentes
            inicio_simulacion = time.time()
            transacciones_creadas = 0
            
            for producto in productos_prueba:
                for j in range(10):  # 10 transacciones por producto
                    cantidad = random.randint(1, 50)
                    
                    # Crear transacción de entrada
                    Transaccion.objects.create(
                        producto=producto,
                        tipo='entrada',
                        cantidad=cantidad,
                        observacion=f'Simulación carga {j}',
                        fecha=date.today()
                    )
                    
                    # Actualizar stock
                    producto.stock += cantidad
                    producto.save()
                    
                    transacciones_creadas += 1
            
            fin_simulacion = time.time()
            tiempo_total = fin_simulacion - inicio_simulacion
            
            self.log_exito(f"Creadas {transacciones_creadas} transacciones en {tiempo_total:.2f}s")
            self.metricas['simulacion_carga'] = tiempo_total
            
            if tiempo_total < 5.0:
                self.log_exito("Rendimiento bajo carga: EXCELENTE")
            elif tiempo_total < 10.0:
                self.log_exito("Rendimiento bajo carga: BUENO")
            else:
                self.log_warning("Rendimiento bajo carga: MEJORABLE")
            
            # Limpiar datos de prueba
            for producto in productos_prueba:
                Transaccion.objects.filter(producto=producto).delete()
                producto.delete()
            
            self.log_exito("Datos de prueba eliminados correctamente")
            
            return True
            
        except Exception as e:
            self.log_error("Error en simulación de carga", str(e))
            return False

    def verificar_configuracion_produccion(self):
        """Verifica configuraciones importantes para producción"""
        print("\n⚙️  VERIFICANDO CONFIGURACIÓN PARA PRODUCCIÓN")
        print("="*60)
        
        try:
            from django.conf import settings
            
            # Verificar DEBUG
            if settings.DEBUG:
                self.log_warning("DEBUG=True - Cambiar a False en producción")
            else:
                self.log_exito("DEBUG=False - Configuración correcta para producción")
            
            # Verificar SECRET_KEY
            if settings.SECRET_KEY and len(settings.SECRET_KEY) > 20:
                self.log_exito("SECRET_KEY configurada correctamente")
            else:
                self.log_warning("SECRET_KEY requiere revisión")
            
            # Verificar ALLOWED_HOSTS
            if '*' in settings.ALLOWED_HOSTS:
                self.log_warning("ALLOWED_HOSTS con '*' - Especificar hosts en producción")
            elif settings.ALLOWED_HOSTS:
                self.log_exito(f"ALLOWED_HOSTS configurado: {settings.ALLOWED_HOSTS}")
            else:
                self.log_warning("ALLOWED_HOSTS no configurado")
            
            # Verificar base de datos
            db_engine = settings.DATABASES['default']['ENGINE']
            if 'sqlite' in db_engine:
                self.log_warning("Usando SQLite - Considerar PostgreSQL/MySQL para producción")
            else:
                self.log_exito(f"Base de datos: {db_engine}")
            
            # Verificar archivos estáticos
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                self.log_exito("STATIC_ROOT configurado")
            else:
                self.log_warning("STATIC_ROOT no configurado")
            
            return True
            
        except Exception as e:
            self.log_error("Error verificando configuración", str(e))
            return False

    def generar_reporte_produccion(self):
        """Genera reporte específico para producción"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'entorno': 'pre-produccion',
            'destino': 'institucion_con_vpn',
            'resumen': {
                'total_validaciones': len(self.exitos) + len(self.errores) + len(self.warnings),
                'exitos': len(self.exitos),
                'errores': len(self.errores),
                'warnings': len(self.warnings),
                'estado_general': 'APTO' if len(self.errores) == 0 else 'REQUIERE_ATENCION'
            },
            'metricas_rendimiento': self.metricas,
            'validaciones': {
                'exitos': self.exitos,
                'errores': self.errores,
                'warnings': self.warnings
            },
            'recomendaciones_produccion': []
        }
        
        # Generar recomendaciones
        if len(self.errores) == 0:
            reporte['recomendaciones_produccion'].append("✅ Sistema apto para deployment en producción")
        
        if len(self.warnings) > 0:
            reporte['recomendaciones_produccion'].append("⚠️  Revisar warnings antes del deployment")
        
        reporte['recomendaciones_produccion'].extend([
            "🔒 Configurar HTTPS en el servidor de producción",
            "📊 Implementar monitoreo de rendimiento",
            "💾 Configurar backups automáticos de la BD",
            "🔐 Revisar permisos de usuarios en producción",
            "🌐 Verificar conectividad VPN institucional"
        ])
        
        # Guardar reporte
        archivo = f'reporte_produccion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            print(f"\n📄 REPORTE GUARDADO: {archivo}")
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        return reporte

    def mostrar_resumen_final(self):
        """Muestra el resumen final de la validación"""
        print("\n" + "="*80)
        print("📋 RESUMEN FINAL - VALIDACIÓN PARA PRODUCCIÓN")
        print("="*80)
        
        print(f"✅ Validaciones exitosas: {len(self.exitos)}")
        print(f"❌ Errores encontrados: {len(self.errores)}")
        print(f"⚠️  Advertencias: {len(self.warnings)}")
        
        if self.metricas:
            print(f"\n📊 MÉTRICAS DE RENDIMIENTO:")
            for metrica, valor in self.metricas.items():
                print(f"   {metrica}: {valor:.3f}s")
        
        print(f"\n🎯 ESTADO PARA PRODUCCIÓN:")
        if len(self.errores) == 0:
            print("   🟢 APTO - Sistema listo para deployment")
        elif len(self.errores) <= 2:
            print("   🟡 CONDICIONAL - Revisar errores menores")
        else:
            print("   🔴 NO APTO - Corregir errores críticos")
        
        if self.errores:
            print(f"\n❌ ERRORES A CORREGIR:")
            for error in self.errores:
                print(f"   • {error['mensaje']}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS A REVISAR:")
            for warning in self.warnings:
                print(f"   • {warning['mensaje']}")
        
        print(f"\n🚀 RECOMENDACIONES PARA VPN INSTITUCIONAL:")
        print("   • Verificar conectividad estable")
        print("   • Configurar timeouts apropiados")
        print("   • Implementar logs detallados")
        print("   • Preparar plan de rollback")

    def ejecutar_validacion_completa(self):
        """Ejecuta la validación completa para producción"""
        print("🚀 VALIDACIÓN COMPLETA PARA PRODUCCIÓN")
        print("Objetivo: Deployment en institución con VPN")
        print("="*80)
        
        try:
            # 1. Estado actual
            self.verificar_estado_actual_bd()
            
            # 2. Integridad de datos
            self.verificar_integridad_datos()
            
            # 3. Rendimiento
            self.probar_rendimiento_consultas()
            
            # 4. Simulación de carga
            self.simular_carga_operaciones()
            
            # 5. Configuración
            self.verificar_configuracion_produccion()
            
            # 6. Reporte final
            reporte = self.generar_reporte_produccion()
            self.mostrar_resumen_final()
            
            return reporte
            
        except Exception as e:
            self.log_error("Error fatal en validación", str(e))
            traceback.print_exc()
            return None

def main():
    """Función principal"""
    print("VALIDACIÓN PARA PRODUCCIÓN - SISTEMA BODEGA SEREMI")
    print("Destinado a: Institución con VPN")
    print("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("="*80)
    
    validador = ValidadorProduccion()
    
    try:
        reporte = validador.ejecutar_validacion_completa()
        return reporte
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        traceback.print_exc()
    finally:
        print("\n🏁 Validación finalizada")

if __name__ == "__main__":
    main()
