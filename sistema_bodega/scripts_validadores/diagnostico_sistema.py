#!/usr/bin/env python
"""
Script de diagnóstico y monitoreo para prevenir errores JSON en el sistema.
Este script se puede ejecutar periódicamente para detectar problemas potenciales.
"""
import os
import sys
import django
import json
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from accounts.models import Producto, LoteProducto
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

class DiagnosticoSistema:
    """Diagnosticador del sistema para prevenir errores JSON."""
    
    def __init__(self):
        self.problemas_encontrados = []
        self.warnings = []
        
    def log_problema(self, mensaje, critico=False):
        """Registra un problema encontrado."""
        tipo = "🚨 CRÍTICO" if critico else "⚠️  PROBLEMA"
        self.problemas_encontrados.append(f"{tipo}: {mensaje}")
        print(f"{tipo}: {mensaje}")
    
    def log_warning(self, mensaje):
        """Registra una advertencia."""
        self.warnings.append(f"⚠️  WARNING: {mensaje}")
        print(f"⚠️  WARNING: {mensaje}")
    
    def log_info(self, mensaje):
        """Registra información."""
        print(f"ℹ️  INFO: {mensaje}")
    
    def verificar_productos_con_vencimiento(self):
        """Verifica productos con vencimiento que pueden causar errores."""
        print("\n🔍 VERIFICANDO PRODUCTOS CON VENCIMIENTO...")
        
        productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True)
        
        self.log_info(f"Productos con vencimiento: {productos_con_vencimiento.count()}")
        
        productos_problematicos = 0
        
        for producto in productos_con_vencimiento:
            try:
                # Verificar sincronización stock-lotes
                stock_calculado = producto.lotes.aggregate(
                    total=models.Sum('stock')
                )['total'] or 0
                
                if producto.stock != stock_calculado:
                    self.log_problema(
                        f"Producto {producto.codigo_barra}: Stock desincronizado ({producto.stock} vs {stock_calculado})",
                        critico=True
                    )
                    productos_problematicos += 1
                
                # Verificar métodos de lotes activos
                lotes_activos = producto.get_total_lotes_activos()
                lotes_con_stock = producto.lotes.filter(stock__gt=0).count()
                
                if lotes_activos != lotes_con_stock:
                    self.log_problema(
                        f"Producto {producto.codigo_barra}: Lotes activos desincronizados ({lotes_activos} vs {lotes_con_stock})",
                        critico=True
                    )
                    productos_problematicos += 1
                
                # Verificar lotes con stock negativo
                lotes_negativos = producto.lotes.filter(stock__lt=0)
                if lotes_negativos.exists():
                    self.log_problema(
                        f"Producto {producto.codigo_barra}: {lotes_negativos.count()} lotes con stock negativo",
                        critico=True
                    )
                    productos_problematicos += 1
                
                # Verificar serialización JSON
                try:
                    datos_producto = {
                        'codigo_barra': producto.codigo_barra,
                        'descripcion': producto.descripcion,
                        'stock': producto.stock,
                        'lotes_activos': producto.get_total_lotes_activos(),
                        'lotes_detalle': producto.get_lotes_detalle(),
                        'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                        'estadisticas': producto.get_estadisticas_lotes(),
                        'estado_vencimiento': producto.get_estado_vencimiento_completo()
                    }
                    
                    json.dumps(datos_producto, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    self.log_problema(
                        f"Producto {producto.codigo_barra}: Error serialización JSON: {e}",
                        critico=True
                    )
                    productos_problematicos += 1
                
            except Exception as e:
                self.log_problema(
                    f"Producto {producto.codigo_barra}: Error general: {e}",
                    critico=True
                )
                productos_problematicos += 1
        
        if productos_problematicos == 0:
            self.log_info("✅ Todos los productos con vencimiento están OK")
        else:
            self.log_problema(f"{productos_problematicos} productos con problemas", critico=True)
    
    def verificar_lotes_problematicos(self):
        """Verifica lotes que pueden causar problemas."""
        print("\n📋 VERIFICANDO LOTES PROBLEMÁTICOS...")
        
        # Lotes con fechas problemáticas
        try:
            # Lotes con fechas None
            lotes_sin_fecha = LoteProducto.objects.filter(fecha_vencimiento__isnull=True)
            if lotes_sin_fecha.exists():
                self.log_problema(f"{lotes_sin_fecha.count()} lotes sin fecha de vencimiento")
            
            # Lotes con fechas muy antiguas
            fecha_limite = date.today() - timedelta(days=3650)  # 10 años atrás
            lotes_antiguos = LoteProducto.objects.filter(fecha_vencimiento__lt=fecha_limite)
            if lotes_antiguos.exists():
                self.log_warning(f"{lotes_antiguos.count()} lotes con fechas muy antiguas")
            
            # Lotes con fechas muy futuras
            fecha_futura = date.today() + timedelta(days=3650)  # 10 años adelante
            lotes_futuros = LoteProducto.objects.filter(fecha_vencimiento__gt=fecha_futura)
            if lotes_futuros.exists():
                self.log_warning(f"{lotes_futuros.count()} lotes con fechas muy futuras")
            
            # Lotes con stock negativo
            lotes_negativos = LoteProducto.objects.filter(stock__lt=0)
            if lotes_negativos.exists():
                self.log_problema(f"{lotes_negativos.count()} lotes con stock negativo", critico=True)
            
            # Lotes con stock muy alto (posible error)
            lotes_stock_alto = LoteProducto.objects.filter(stock__gt=100000)
            if lotes_stock_alto.exists():
                self.log_warning(f"{lotes_stock_alto.count()} lotes con stock muy alto (>100,000)")
            
            # Verificar métodos de lotes individualmente
            lotes_problematicos = 0
            lotes_total = LoteProducto.objects.count()
            
            if lotes_total > 0:
                self.log_info(f"Verificando {lotes_total} lotes individuales...")
                
                for lote in LoteProducto.objects.all()[:100]:  # Verificar los primeros 100
                    try:
                        # Verificar métodos del lote
                        lote.get_dias_para_vencer()
                        lote.esta_vencido()
                        lote.get_estado_vencimiento()
                        lote.get_color_estado_vencimiento()
                        lote.puede_ser_usado()
                        lote.requiere_atencion()
                        lote.get_descripcion_estado()
                        
                        # Verificar serialización del lote
                        datos_lote = {
                            'numero_lote': lote.numero_lote,
                            'fecha_vencimiento': lote.fecha_vencimiento,
                            'stock': lote.stock,
                            'dias_restantes': lote.get_dias_para_vencer(),
                            'estado': lote.get_estado_vencimiento(),
                            'color': lote.get_color_estado_vencimiento(),
                            'esta_vencido': lote.esta_vencido()
                        }
                        
                        json.dumps(datos_lote, cls=DjangoJSONEncoder)
                        
                    except Exception as e:
                        self.log_problema(f"Lote {lote.producto.codigo_barra}#{lote.numero_lote}: {e}")
                        lotes_problematicos += 1
                
                if lotes_problematicos == 0:
                    self.log_info("✅ Todos los lotes verificados están OK")
                else:
                    self.log_problema(f"{lotes_problematicos} lotes con problemas")
            
        except Exception as e:
            self.log_problema(f"Error verificando lotes: {e}", critico=True)
    
    def verificar_productos_agotados(self):
        """Verifica productos agotados que pueden causar errores."""
        print("\n📊 VERIFICANDO PRODUCTOS AGOTADOS...")
        
        try:
            # Productos con stock 0 pero lotes activos
            productos_problematicos = []
            
            for producto in Producto.objects.filter(stock=0, tiene_vencimiento=True):
                lotes_activos = producto.get_total_lotes_activos()
                
                if lotes_activos > 0:
                    self.log_problema(
                        f"Producto {producto.codigo_barra}: Stock 0 pero {lotes_activos} lotes activos",
                        critico=True
                    )
                    productos_problematicos.append(producto)
                
                # Verificar que los métodos funcionen correctamente
                try:
                    datos_agotado = {
                        'codigo_barra': producto.codigo_barra,
                        'stock': producto.stock,
                        'lotes_activos': producto.get_total_lotes_activos(),
                        'lotes_detalle': producto.get_lotes_detalle(),
                        'lotes_activos_detalle': producto.get_lotes_activos_detalle(),
                        'estadisticas': producto.get_estadisticas_lotes()
                    }
                    
                    json.dumps(datos_agotado, cls=DjangoJSONEncoder)
                    
                except Exception as e:
                    self.log_problema(
                        f"Producto agotado {producto.codigo_barra}: Error serialización: {e}",
                        critico=True
                    )
                    productos_problematicos.append(producto)
            
            if not productos_problematicos:
                self.log_info("✅ Productos agotados funcionan correctamente")
            else:
                self.log_problema(f"{len(productos_problematicos)} productos agotados con problemas", critico=True)
            
        except Exception as e:
            self.log_problema(f"Error verificando productos agotados: {e}", critico=True)
    
    def verificar_metodos_criticos(self):
        """Verifica métodos críticos que pueden fallar."""
        print("\n⚙️  VERIFICANDO MÉTODOS CRÍTICOS...")
        
        try:
            # Obtener una muestra de productos
            productos_muestra = Producto.objects.filter(tiene_vencimiento=True)[:10]
            
            metodos_criticos = [
                'get_lotes_detalle',
                'get_lotes_activos_detalle',
                'get_total_lotes_activos',
                'get_estadisticas_lotes',
                'get_estado_vencimiento_completo',
                'get_proximo_vencimiento',
                'sincronizar_stock_con_lotes'
            ]
            
            for producto in productos_muestra:
                for metodo_nombre in metodos_criticos:
                    try:
                        metodo = getattr(producto, metodo_nombre)
                        resultado = metodo()
                        
                        # Intentar serializar el resultado
                        json.dumps(resultado, cls=DjangoJSONEncoder)
                        
                    except Exception as e:
                        self.log_problema(
                            f"Producto {producto.codigo_barra}, método {metodo_nombre}: {e}",
                            critico=True
                        )
            
            self.log_info("✅ Verificación de métodos críticos completada")
            
        except Exception as e:
            self.log_problema(f"Error verificando métodos críticos: {e}", critico=True)
    
    def generar_reporte_diagnostico(self):
        """Genera un reporte completo de diagnóstico."""
        print("\n📋 GENERANDO REPORTE DE DIAGNÓSTICO...")
        
        try:
            # Estadísticas generales
            total_productos = Producto.objects.count()
            productos_con_vencimiento = Producto.objects.filter(tiene_vencimiento=True).count()
            productos_sin_stock = Producto.objects.filter(stock=0).count()
            total_lotes = LoteProducto.objects.count()
            lotes_activos = LoteProducto.objects.filter(stock__gt=0).count()
            lotes_vacios = LoteProducto.objects.filter(stock=0).count()
            
            reporte = {
                'fecha_diagnostico': date.today().isoformat(),
                'estadisticas_generales': {
                    'total_productos': total_productos,
                    'productos_con_vencimiento': productos_con_vencimiento,
                    'productos_sin_stock': productos_sin_stock,
                    'total_lotes': total_lotes,
                    'lotes_activos': lotes_activos,
                    'lotes_vacios': lotes_vacios
                },
                'problemas_encontrados': self.problemas_encontrados,
                'warnings': self.warnings
            }
            
            # Intentar serializar el reporte completo
            json.dumps(reporte, cls=DjangoJSONEncoder)
            
            self.log_info("✅ Reporte de diagnóstico generado exitosamente")
            
            return reporte
            
        except Exception as e:
            self.log_problema(f"Error generando reporte: {e}", critico=True)
            return None
    
    def ejecutar_diagnostico_completo(self):
        """Ejecuta el diagnóstico completo del sistema."""
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO DEL SISTEMA")
        print("=" * 60)
        
        # Verificar productos con vencimiento
        self.verificar_productos_con_vencimiento()
        
        # Verificar lotes problemáticos
        self.verificar_lotes_problematicos()
        
        # Verificar productos agotados
        self.verificar_productos_agotados()
        
        # Verificar métodos críticos
        self.verificar_metodos_criticos()
        
        # Generar reporte
        reporte = self.generar_reporte_diagnostico()
        
        # Mostrar resumen
        self.mostrar_resumen(reporte)
        
        return len(self.problemas_encontrados) == 0
    
    def mostrar_resumen(self, reporte):
        """Muestra el resumen del diagnóstico."""
        print("\n" + "=" * 60)
        print("📊 RESUMEN DEL DIAGNÓSTICO")
        print("=" * 60)
        
        if reporte:
            stats = reporte['estadisticas_generales']
            print(f"📦 Total productos: {stats['total_productos']}")
            print(f"📅 Productos con vencimiento: {stats['productos_con_vencimiento']}")
            print(f"📋 Total lotes: {stats['total_lotes']}")
            print(f"🟢 Lotes activos: {stats['lotes_activos']}")
            print(f"⚪ Lotes vacíos: {stats['lotes_vacios']}")
        
        print(f"\n🚨 Problemas críticos: {len(self.problemas_encontrados)}")
        print(f"⚠️  Advertencias: {len(self.warnings)}")
        
        if self.problemas_encontrados:
            print(f"\n🚨 PROBLEMAS ENCONTRADOS:")
            for problema in self.problemas_encontrados:
                print(f"   {problema}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if not self.problemas_encontrados and not self.warnings:
            print(f"\n✅ SISTEMA SALUDABLE")
            print(f"   No se encontraron problemas críticos")
            print(f"   El sistema está funcionando correctamente")
        else:
            print(f"\n⚠️  SISTEMA REQUIERE ATENCIÓN")
            if self.problemas_encontrados:
                print(f"   🚨 Se encontraron {len(self.problemas_encontrados)} problemas críticos")
            if self.warnings:
                print(f"   ⚠️  Se encontraron {len(self.warnings)} advertencias")
        
        print("=" * 60)

def main():
    """Ejecuta el diagnóstico completo."""
    diagnostico = DiagnosticoSistema()
    sistema_saludable = diagnostico.ejecutar_diagnostico_completo()
    
    if sistema_saludable:
        print(f"\n🎉 DIAGNÓSTICO COMPLETADO: Sistema saludable")
        exit(0)
    else:
        print(f"\n⚠️  DIAGNÓSTICO COMPLETADO: Sistema requiere atención")
        exit(1)

if __name__ == "__main__":
    main()
