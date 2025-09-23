#!/usr/bin/env python
"""
VALIDADOR ESPECÍFICO DE BINCARD Y SINCRONIZACIÓN
Sistema de Bodega SEREMI

Este script se enfoca específicamente en:
- Validación de integridad de bincard
- Sincronización de stock vs movimientos
- Trazabilidad de lotes FIFO
- Consistencia de fechas de vencimiento
- Detección de discrepancias

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from collections import defaultdict
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.db import transaction
from django.db.models import Sum, F, Q
from accounts.models import (
    Producto, MovimientoStock, LoteVencimiento, 
    ActaRecepcion, DetalleActa
)

class ValidadorBincardSincronizacion:
    def __init__(self):
        self.errores_criticos = []
        self.warnings = []
        self.correciones_aplicadas = []
        self.estadisticas = {}
        
    def log_error_critico(self, producto_codigo, mensaje, detalle):
        """Registra un error crítico de sincronización"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'producto': producto_codigo,
            'mensaje': mensaje,
            'detalle': detalle
        }
        self.errores_criticos.append(error)
        print(f"🔴 ERROR CRÍTICO [{producto_codigo}]: {mensaje}")
        print(f"   Detalle: {detalle}")
    
    def log_warning(self, producto_codigo, mensaje):
        """Registra una advertencia"""
        warning = {
            'timestamp': datetime.now().isoformat(),
            'producto': producto_codigo,
            'mensaje': mensaje
        }
        self.warnings.append(warning)
        print(f"🟡 WARNING [{producto_codigo}]: {mensaje}")
    
    def log_correccion(self, producto_codigo, mensaje, valor_anterior, valor_nuevo):
        """Registra una corrección aplicada"""
        correccion = {
            'timestamp': datetime.now().isoformat(),
            'producto': producto_codigo,
            'mensaje': mensaje,
            'valor_anterior': valor_anterior,
            'valor_nuevo': valor_nuevo
        }
        self.correciones_aplicadas.append(correccion)
        print(f"🔧 CORRECCIÓN [{producto_codigo}]: {mensaje}")
        print(f"   {valor_anterior} → {valor_nuevo}")

    def validar_sincronizacion_stock_movimientos(self):
        """Valida que el stock coincida con la suma de movimientos"""
        print("🔍 Validando sincronización stock vs movimientos...")
        
        productos_con_errores = []
        total_productos = 0
        
        for producto in Producto.objects.all():
            total_productos += 1
            
            # Calcular stock según movimientos
            movimientos_entrada = MovimientoStock.objects.filter(
                producto=producto,
                tipo='ENTRADA'
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            movimientos_salida = MovimientoStock.objects.filter(
                producto=producto,
                tipo='SALIDA'
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            stock_calculado = movimientos_entrada - movimientos_salida
            stock_actual = producto.stock
            
            if stock_actual != stock_calculado:
                self.log_error_critico(
                    producto.codigo,
                    "Desincronización stock vs movimientos",
                    f"Stock DB: {stock_actual}, Calculado: {stock_calculado}, Diferencia: {stock_actual - stock_calculado}"
                )
                productos_con_errores.append({
                    'producto': producto,
                    'stock_db': stock_actual,
                    'stock_calculado': stock_calculado,
                    'diferencia': stock_actual - stock_calculado
                })
        
        self.estadisticas['sincronizacion_stock'] = {
            'total_productos': total_productos,
            'productos_con_errores': len(productos_con_errores),
            'porcentaje_error': (len(productos_con_errores) / total_productos * 100) if total_productos > 0 else 0
        }
        
        print(f"   Productos evaluados: {total_productos}")
        print(f"   Productos con errores: {len(productos_con_errores)}")
        
        return productos_con_errores

    def validar_lotes_fifo(self):
        """Valida que los lotes sigan el principio FIFO correctamente"""
        print("🔍 Validando lógica FIFO en lotes...")
        
        productos_con_errores_fifo = []
        
        for producto in Producto.objects.all():
            lotes = LoteVencimiento.objects.filter(
                producto=producto,
                cantidad_disponible__gt=0
            ).order_by('fecha_vencimiento')
            
            if lotes.count() > 1:
                # Verificar que no haya lotes con fecha posterior que tengan menos stock
                lotes_lista = list(lotes)
                
                for i in range(len(lotes_lista) - 1):
                    lote_actual = lotes_lista[i]
                    lote_siguiente = lotes_lista[i + 1]
                    
                    # Si el lote más próximo a vencer tiene menos cantidad que uno posterior
                    if (lote_actual.fecha_vencimiento < lote_siguiente.fecha_vencimiento and 
                        lote_actual.cantidad_disponible < lote_siguiente.cantidad_disponible):
                        
                        self.log_warning(
                            producto.codigo,
                            f"Posible violación FIFO: Lote {lote_actual.numero_lote} "
                            f"(vence {lote_actual.fecha_vencimiento}) tiene menos stock "
                            f"que lote {lote_siguiente.numero_lote} (vence {lote_siguiente.fecha_vencimiento})"
                        )
                        
                        productos_con_errores_fifo.append({
                            'producto': producto.codigo,
                            'lote_temprano': lote_actual.numero_lote,
                            'lote_tardio': lote_siguiente.numero_lote,
                            'fecha_temprana': lote_actual.fecha_vencimiento,
                            'fecha_tardia': lote_siguiente.fecha_vencimiento
                        })
        
        self.estadisticas['validacion_fifo'] = {
            'productos_evaluados': Producto.objects.count(),
            'violaciones_fifo': len(productos_con_errores_fifo)
        }
        
        return productos_con_errores_fifo

    def validar_consistencia_lotes(self):
        """Valida la consistencia entre lotes y stock total"""
        print("🔍 Validando consistencia de lotes vs stock...")
        
        productos_con_inconsistencias = []
        
        for producto in Producto.objects.all():
            # Sumar cantidades disponibles en lotes
            stock_lotes = LoteVencimiento.objects.filter(
                producto=producto
            ).aggregate(total=Sum('cantidad_disponible'))['total'] or 0
            
            stock_producto = producto.stock
            
            if stock_lotes != stock_producto:
                self.log_error_critico(
                    producto.codigo,
                    "Inconsistencia stock vs lotes",
                    f"Stock producto: {stock_producto}, Stock lotes: {stock_lotes}, Diferencia: {stock_producto - stock_lotes}"
                )
                
                productos_con_inconsistencias.append({
                    'producto': producto,
                    'stock_producto': stock_producto,
                    'stock_lotes': stock_lotes,
                    'diferencia': stock_producto - stock_lotes
                })
        
        self.estadisticas['consistencia_lotes'] = {
            'productos_evaluados': Producto.objects.count(),
            'inconsistencias': len(productos_con_inconsistencias)
        }
        
        return productos_con_inconsistencias

    def detectar_lotes_vencidos_no_procesados(self):
        """Detecta lotes vencidos que aún tienen stock disponible"""
        print("🔍 Detectando lotes vencidos no procesados...")
        
        hoy = date.today()
        lotes_vencidos = LoteVencimiento.objects.filter(
            fecha_vencimiento__lt=hoy,
            cantidad_disponible__gt=0
        )
        
        productos_afectados = []
        
        for lote in lotes_vencidos:
            self.log_warning(
                lote.producto.codigo,
                f"Lote vencido con stock: {lote.numero_lote} "
                f"(vencido el {lote.fecha_vencimiento}, stock: {lote.cantidad_disponible})"
            )
            
            productos_afectados.append({
                'producto': lote.producto.codigo,
                'numero_lote': lote.numero_lote,
                'fecha_vencimiento': lote.fecha_vencimiento,
                'cantidad_disponible': lote.cantidad_disponible,
                'dias_vencido': (hoy - lote.fecha_vencimiento).days
            })
        
        self.estadisticas['lotes_vencidos'] = {
            'total_lotes_vencidos': len(productos_afectados),
            'productos_afectados': len(set(p['producto'] for p in productos_afectados))
        }
        
        return productos_afectados

    def verificar_movimientos_huerfanos(self):
        """Detecta movimientos sin producto asociado o con datos inconsistentes"""
        print("🔍 Verificando movimientos huérfanos...")
        
        # Movimientos sin producto
        movimientos_huerfanos = MovimientoStock.objects.filter(producto__isnull=True)
        
        # Movimientos con cantidades negativas o cero
        movimientos_invalidos = MovimientoStock.objects.filter(
            Q(cantidad__lte=0)
        )
        
        errores_movimientos = []
        
        for mov in movimientos_huerfanos:
            self.log_error_critico(
                "SIN_PRODUCTO",
                f"Movimiento huérfano ID {mov.id}",
                f"Tipo: {mov.tipo}, Cantidad: {mov.cantidad}, Fecha: {mov.fecha_movimiento}"
            )
            errores_movimientos.append(mov)
        
        for mov in movimientos_invalidos:
            self.log_error_critico(
                mov.producto.codigo if mov.producto else "SIN_PRODUCTO",
                f"Movimiento con cantidad inválida ID {mov.id}",
                f"Cantidad: {mov.cantidad}"
            )
            errores_movimientos.append(mov)
        
        self.estadisticas['movimientos_problematicos'] = {
            'movimientos_huerfanos': movimientos_huerfanos.count(),
            'movimientos_invalidos': movimientos_invalidos.count(),
            'total_problematicos': len(errores_movimientos)
        }
        
        return errores_movimientos

    def validar_fechas_sistema(self):
        """Valida que las fechas del sistema sean consistentes"""
        print("🔍 Validando fechas del sistema...")
        
        hoy = date.today()
        errores_fechas = []
        
        # Movimientos con fechas futuras
        movimientos_futuros = MovimientoStock.objects.filter(
            fecha_movimiento__gt=hoy
        )
        
        for mov in movimientos_futuros:
            self.log_warning(
                mov.producto.codigo if mov.producto else "SIN_PRODUCTO",
                f"Movimiento con fecha futura: {mov.fecha_movimiento}"
            )
            errores_fechas.append(mov)
        
        # Lotes con fechas de vencimiento en el pasado reciente (posible error)
        lotes_fecha_sospechosa = LoteVencimiento.objects.filter(
            fecha_vencimiento__lt=hoy - timedelta(days=365)  # Más de 1 año vencido
        )
        
        for lote in lotes_fecha_sospechosa:
            self.log_warning(
                lote.producto.codigo,
                f"Lote con fecha muy antigua: {lote.numero_lote} - {lote.fecha_vencimiento}"
            )
        
        self.estadisticas['validacion_fechas'] = {
            'movimientos_futuros': movimientos_futuros.count(),
            'lotes_muy_vencidos': lotes_fecha_sospechosa.count()
        }
        
        return errores_fechas

    def aplicar_correcciones_automaticas(self, corregir=False):
        """Aplica correcciones automáticas a problemas detectados"""
        if not corregir:
            print("🔧 Modo de corrección deshabilitado. Use --corregir para aplicar correcciones.")
            return
        
        print("🔧 Aplicando correcciones automáticas...")
        
        correcciones_aplicadas = 0
        
        # Corregir stock según movimientos
        productos_con_errores = self.validar_sincronizacion_stock_movimientos()
        
        for error in productos_con_errores:
            producto = error['producto']
            stock_correcto = error['stock_calculado']
            stock_anterior = error['stock_db']
            
            if corregir:
                with transaction.atomic():
                    producto.stock = stock_correcto
                    producto.save()
                    
                    # Crear movimiento de ajuste
                    MovimientoStock.objects.create(
                        producto=producto,
                        tipo='AJUSTE',
                        cantidad=stock_correcto - stock_anterior,
                        motivo=f'Corrección automática de sincronización',
                        usuario_id=1  # Usuario del sistema
                    )
                    
                    self.log_correccion(
                        producto.codigo,
                        "Stock corregido por desincronización",
                        stock_anterior,
                        stock_correcto
                    )
                    correcciones_aplicadas += 1
        
        print(f"✅ Correcciones aplicadas: {correcciones_aplicadas}")

    def generar_reporte_bincard(self):
        """Genera un reporte detallado del estado del bincard"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'estadisticas': self.estadisticas,
            'errores_criticos': self.errores_criticos,
            'warnings': self.warnings,
            'correcciones_aplicadas': self.correciones_aplicadas,
            'resumen': {
                'total_errores_criticos': len(self.errores_criticos),
                'total_warnings': len(self.warnings),
                'total_correcciones': len(self.correciones_aplicadas)
            }
        }
        
        # Guardar reporte
        archivo_reporte = f'reporte_bincard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Reporte guardado: {archivo_reporte}")
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📋 REPORTE DE VALIDACIÓN BINCARD")
        print("="*60)
        
        print(f"🔴 Errores críticos: {len(self.errores_criticos)}")
        print(f"🟡 Warnings: {len(self.warnings)}")
        print(f"🔧 Correcciones aplicadas: {len(self.correciones_aplicadas)}")
        
        print("\n📊 ESTADÍSTICAS:")
        for categoria, stats in self.estadisticas.items():
            print(f"   {categoria.upper()}:")
            for key, value in stats.items():
                print(f"     - {key}: {value}")
        
        # Evaluación final
        if len(self.errores_criticos) == 0:
            print("\n🎉 BINCARD EN PERFECTO ESTADO")
        elif len(self.errores_criticos) <= 3:
            print("\n⚠️  BINCARD CON ERRORES MENORES - Requiere atención")
        else:
            print("\n🚨 BINCARD CON ERRORES CRÍTICOS - Requiere corrección inmediata")
        
        return reporte

    def ejecutar_validacion_completa(self, corregir=False):
        """Ejecuta toda la validación del bincard"""
        print("🚀 INICIANDO VALIDACIÓN COMPLETA DE BINCARD")
        print("="*60)
        
        try:
            # 1. Validar sincronización básica
            print("\n1️⃣ SINCRONIZACIÓN STOCK vs MOVIMIENTOS")
            self.validar_sincronizacion_stock_movimientos()
            
            # 2. Validar lógica FIFO
            print("\n2️⃣ VALIDACIÓN LÓGICA FIFO")
            self.validar_lotes_fifo()
            
            # 3. Consistencia de lotes
            print("\n3️⃣ CONSISTENCIA DE LOTES")
            self.validar_consistencia_lotes()
            
            # 4. Lotes vencidos
            print("\n4️⃣ LOTES VENCIDOS")
            self.detectar_lotes_vencidos_no_procesados()
            
            # 5. Movimientos problemáticos
            print("\n5️⃣ MOVIMIENTOS PROBLEMÁTICOS")
            self.verificar_movimientos_huerfanos()
            
            # 6. Validación de fechas
            print("\n6️⃣ VALIDACIÓN DE FECHAS")
            self.validar_fechas_sistema()
            
            # 7. Aplicar correcciones si está habilitado
            print("\n7️⃣ CORRECCIONES AUTOMÁTICAS")
            self.aplicar_correcciones_automaticas(corregir)
            
            return True
            
        except Exception as e:
            print(f"💥 Error fatal en validación: {e}")
            return False
        
        finally:
            self.generar_reporte_bincard()


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validador de Bincard y Sincronización')
    parser.add_argument('--corregir', action='store_true', 
                       help='Aplica correcciones automáticas a los problemas detectados')
    
    args = parser.parse_args()
    
    print("Validador de Bincard - Sistema Bodega SEREMI")
    print("="*50)
    
    validador = ValidadorBincardSincronizacion()
    
    try:
        validador.ejecutar_validacion_completa(corregir=args.corregir)
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
    finally:
        print("\n🏁 Validación de bincard finalizada")


if __name__ == "__main__":
    main()
