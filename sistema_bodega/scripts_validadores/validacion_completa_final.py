#!/usr/bin/env python
"""
VALIDACIÓN COMPLETA PARA SISTEMA BODEGA SEREMI
Versión Final con modelos correctos

Autor: Sistema Bodega SEREMI  
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
import random
from datetime import datetime, timedelta, date
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.db.models import Sum, Count
from accounts.models import Producto, Transaccion, LoteProducto, Categoria

class ValidadorSistemaCompleto:
    def __init__(self):
        self.resultados = {
            'timestamp': datetime.now().isoformat(),
            'pruebas': [],
            'errores': [],
            'exitos': [],
            'metricas': {}
        }
    
    def log_exito(self, mensaje):
        """Registra un éxito"""
        self.resultados['exitos'].append(mensaje)
        print(f"✅ {mensaje}")
    
    def log_error(self, mensaje):
        """Registra un error"""
        self.resultados['errores'].append(mensaje)
        print(f"❌ {mensaje}")
    
    def log_warning(self, mensaje):
        """Registra una advertencia"""
        print(f"⚠️  {mensaje}")
    
    def medir_tiempo(self, nombre, funcion):
        """Mide tiempo de ejecución de una función"""
        inicio = time.time()
        resultado = funcion()
        fin = time.time()
        tiempo = fin - inicio
        self.resultados['metricas'][nombre] = tiempo
        print(f"⏱️  {nombre}: {tiempo:.3f}s")
        return resultado
    
    def validar_modelos_basicos(self):
        """Valida que todos los modelos básicos funcionen"""
        print("\n1️⃣ VALIDANDO MODELOS BÁSICOS")
        print("-" * 40)
        
        try:
            # Contar registros existentes
            total_productos = Producto.objects.count()
            total_transacciones = Transaccion.objects.count()  
            total_lotes = LoteProducto.objects.count()
            total_categorias = Categoria.objects.count()
            
            self.log_exito(f"Productos en sistema: {total_productos}")
            self.log_exito(f"Transacciones en sistema: {total_transacciones}")
            self.log_exito(f"Lotes en sistema: {total_lotes}")
            self.log_exito(f"Categorías en sistema: {total_categorias}")
            
            # Guardar estadísticas
            self.resultados['estadisticas'] = {
                'productos': total_productos,
                'transacciones': total_transacciones,
                'lotes': total_lotes,
                'categorias': total_categorias
            }
            
            return True
            
        except Exception as e:
            self.log_error(f"Error validando modelos: {e}")
            return False
    
    def validar_integridad_datos(self):
        """Valida la integridad de los datos"""
        print("\n2️⃣ VALIDANDO INTEGRIDAD DE DATOS")
        print("-" * 40)
        
        try:
            # 1. Productos con stock negativo
            productos_stock_negativo = Producto.objects.filter(stock__lt=0)
            if productos_stock_negativo.exists():
                self.log_error(f"Productos con stock negativo: {productos_stock_negativo.count()}")
                for producto in productos_stock_negativo[:5]:  # Mostrar solo 5
                    self.log_error(f"  - {producto.codigo_barra}: {producto.stock}")
            else:
                self.log_exito("No hay productos con stock negativo")
            
            # 2. Lotes vencidos con stock
            lotes_vencidos_stock = LoteProducto.objects.filter(
                fecha_vencimiento__lt=date.today(),
                stock__gt=0
            )
            if lotes_vencidos_stock.exists():
                self.log_warning(f"Lotes vencidos con stock: {lotes_vencidos_stock.count()}")
                for lote in lotes_vencidos_stock[:3]:
                    print(f"     - Lote {lote.numero_lote}: {lote.stock} unidades (vencido {lote.fecha_vencimiento})")
            else:
                self.log_exito("No hay lotes vencidos con stock")
            
            # 3. Lotes próximos a vencer (30 días)
            fecha_limite = date.today() + timedelta(days=30)
            lotes_proximos = LoteProducto.objects.filter(
                fecha_vencimiento__lte=fecha_limite,
                stock__gt=0
            )
            if lotes_proximos.exists():
                self.log_warning(f"Lotes próximos a vencer (30 días): {lotes_proximos.count()}")
            else:
                self.log_exito("No hay lotes próximos a vencer en 30 días")
            
            # 4. Productos sin transacciones
            productos_sin_movimientos = Producto.objects.filter(
                transaccion__isnull=True
            ).distinct()
            if productos_sin_movimientos.exists():
                self.log_warning(f"Productos sin movimientos: {productos_sin_movimientos.count()}")
            else:
                self.log_exito("Todos los productos tienen movimientos registrados")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error validando integridad: {e}")
            return False
    
    def crear_datos_prueba(self):
        """Crea datos de prueba para validar funcionalidad"""
        print("\n3️⃣ CREANDO DATOS DE PRUEBA")
        print("-" * 40)
        
        try:
            # Crear producto de prueba
            codigo_prueba = f'VALIDACION{random.randint(10000, 99999)}'
            
            producto_prueba = Producto.objects.create(
                codigo_barra=codigo_prueba,
                descripcion='Producto Validación Sistema',
                stock=0,  # Empezamos con 0
                rut_proveedor='12345678-9',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=120)
            )
            
            self.log_exito(f"Producto de prueba creado: {codigo_prueba}")
            
            # Crear transacciones de entrada
            transacciones_creadas = []
            cantidades = [50, 30, 20]
            
            for i, cantidad in enumerate(cantidades):
                transaccion = Transaccion.objects.create(
                    producto=producto_prueba,
                    tipo='entrada',
                    cantidad=cantidad,
                    rut_proveedor='12345678-9',
                    observacion=f'Entrada de prueba {i+1}'
                )
                transacciones_creadas.append(transaccion)
                
                # Actualizar stock
                producto_prueba.stock += cantidad
                producto_prueba.save()
            
            self.log_exito(f"Creadas {len(transacciones_creadas)} transacciones de entrada")
            
            # Crear lotes de prueba
            lotes_creados = []
            fechas_vencimiento = [
                date.today() + timedelta(days=30),
                date.today() + timedelta(days=60),
                date.today() + timedelta(days=90)
            ]
            
            for i, fecha_venc in enumerate(fechas_vencimiento):
                lote = LoteProducto.objects.create(
                    producto=producto_prueba,
                    numero_lote=1000 + i,
                    stock=cantidades[i],
                    fecha_vencimiento=fecha_venc
                )
                lotes_creados.append(lote)
            
            self.log_exito(f"Creados {len(lotes_creados)} lotes de prueba")
            
            # Crear transacción de salida
            transaccion_salida = Transaccion.objects.create(
                producto=producto_prueba,
                tipo='salida',
                cantidad=25,
                observacion='Salida de prueba'
            )
            
            # Actualizar stock
            producto_prueba.stock -= 25
            producto_prueba.save()
            
            self.log_exito("Transacción de salida creada")
            
            # Guardar datos para limpieza posterior
            self.datos_prueba = {
                'producto': producto_prueba,
                'transacciones': transacciones_creadas + [transaccion_salida],
                'lotes': lotes_creados
            }
            
            return True
            
        except Exception as e:
            self.log_error(f"Error creando datos de prueba: {e}")
            return False
    
    def validar_consultas_rendimiento(self):
        """Valida el rendimiento de consultas complejas"""
        print("\n4️⃣ VALIDANDO RENDIMIENTO DE CONSULTAS")
        print("-" * 40)
        
        def consulta_productos_stock():
            return list(Producto.objects.filter(stock__gt=0)[:20])
        
        def consulta_transacciones_recientes():
            return list(Transaccion.objects.order_by('-fecha')[:50])
        
        def consulta_lotes_criticos():
            fecha_limite = date.today() + timedelta(days=30)
            return list(LoteProducto.objects.filter(
                fecha_vencimiento__lte=fecha_limite,
                stock__gt=0
            ))
        
        def consulta_agregada():
            return Producto.objects.aggregate(
                total_stock=Sum('stock'),
                total_productos=Count('id')
            )
        
        try:
            # Ejecutar consultas midiendo tiempo
            productos = self.medir_tiempo('Consulta productos con stock', consulta_productos_stock)
            transacciones = self.medir_tiempo('Consulta transacciones recientes', consulta_transacciones_recientes)  
            lotes = self.medir_tiempo('Consulta lotes críticos', consulta_lotes_criticos)
            agregados = self.medir_tiempo('Consulta agregada', consulta_agregada)
            
            self.log_exito(f"Consulta productos: {len(productos)} registros")
            self.log_exito(f"Consulta transacciones: {len(transacciones)} registros") 
            self.log_exito(f"Consulta lotes críticos: {len(lotes)} registros")
            self.log_exito(f"Consulta agregada: {agregados}")
            
            # Evaluar rendimiento
            tiempos = list(self.resultados['metricas'].values())
            tiempo_promedio = sum(tiempos) / len(tiempos)
            
            if tiempo_promedio < 0.1:
                self.log_exito(f"Rendimiento excelente: {tiempo_promedio:.3f}s promedio")
            elif tiempo_promedio < 0.5:
                self.log_exito(f"Rendimiento bueno: {tiempo_promedio:.3f}s promedio")
            else:
                self.log_warning(f"Rendimiento lento: {tiempo_promedio:.3f}s promedio")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error en consultas de rendimiento: {e}")
            return False
    
    def validar_logica_fifo(self):
        """Valida que la lógica FIFO funcione correctamente"""
        print("\n5️⃣ VALIDANDO LÓGICA FIFO")
        print("-" * 40)
        
        try:
            # Buscar productos con múltiples lotes
            productos_con_lotes = Producto.objects.annotate(
                num_lotes=Count('lotes')
            ).filter(num_lotes__gt=1)[:5]
            
            if not productos_con_lotes.exists():
                self.log_warning("No hay productos con múltiples lotes para validar FIFO")
                return True
            
            violaciones_fifo = 0
            
            for producto in productos_con_lotes:
                lotes = producto.lotes.filter(stock__gt=0).order_by('fecha_vencimiento')
                
                if lotes.count() > 1:
                    lotes_lista = list(lotes)
                    
                    # Verificar que lotes más próximos a vencer tengan prioridad
                    for i in range(len(lotes_lista) - 1):
                        lote_actual = lotes_lista[i]
                        lote_siguiente = lotes_lista[i + 1]
                        
                        if (lote_actual.fecha_vencimiento < lote_siguiente.fecha_vencimiento and
                            lote_actual.stock > lote_siguiente.stock * 2):  # Tolerancia para diferencias naturales
                            
                            violaciones_fifo += 1
                            self.log_warning(
                                f"Posible violación FIFO en {producto.codigo_barra}: "
                                f"Lote {lote_actual.numero_lote} (vence {lote_actual.fecha_vencimiento}) "
                                f"tiene más stock que lote {lote_siguiente.numero_lote}"
                            )
            
            if violaciones_fifo == 0:
                self.log_exito("Lógica FIFO funcionando correctamente")
            else:
                self.log_warning(f"Posibles violaciones FIFO: {violaciones_fifo}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error validando FIFO: {e}")
            return False
    
    def probar_funcionalidad_web(self):
        """Prueba funcionalidades web básicas"""
        print("\n6️⃣ PROBANDO FUNCIONALIDADES WEB")
        print("-" * 40)
        
        try:
            from django.conf import settings
            
            # Agregar testserver a ALLOWED_HOSTS temporalmente
            allowed_hosts_original = settings.ALLOWED_HOSTS[:]
            if 'testserver' not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append('testserver')
            
            client = Client()
            
            # Probar página principal
            response = client.get('/')
            if response.status_code in [200, 302]:
                self.log_exito(f"Página principal accesible: {response.status_code}")
            else:
                self.log_error(f"Error en página principal: {response.status_code}")
            
            # Crear usuario de prueba para login
            user_test, created = User.objects.get_or_create(
                username='validacion_user',
                defaults={'password': 'test123'}
            )
            if created:
                user_test.set_password('test123')
                user_test.save()
            
            # Probar login
            login_success = client.login(username='validacion_user', password='test123')
            if login_success:
                self.log_exito("Login de prueba exitoso")
                
                # Probar algunas páginas después del login
                try:
                    response = client.get('/')
                    if response.status_code == 200:
                        self.log_exito("Acceso post-login funcionando")
                except:
                    self.log_warning("Error accediendo páginas post-login")
            else:
                self.log_warning("Login de prueba falló")
            
            # Restaurar ALLOWED_HOSTS
            settings.ALLOWED_HOSTS = allowed_hosts_original
            
            # Limpiar usuario de prueba
            if created:
                user_test.delete()
            
            return True
            
        except Exception as e:
            self.log_error(f"Error probando funcionalidad web: {e}")
            return False
    
    def limpiar_datos_prueba(self):
        """Limpia todos los datos de prueba creados"""
        print("\n7️⃣ LIMPIANDO DATOS DE PRUEBA")
        print("-" * 40)
        
        try:
            if hasattr(self, 'datos_prueba'):
                # Eliminar lotes
                for lote in self.datos_prueba.get('lotes', []):
                    lote.delete()
                
                # Eliminar transacciones  
                for transaccion in self.datos_prueba.get('transacciones', []):
                    transaccion.delete()
                
                # Eliminar producto
                if 'producto' in self.datos_prueba:
                    self.datos_prueba['producto'].delete()
                
                self.log_exito("Datos de prueba eliminados correctamente")
            
            # Eliminar productos de validación que puedan haber quedado
            productos_validacion = Producto.objects.filter(codigo_barra__startswith='VALIDACION')
            count_eliminados = productos_validacion.count()
            productos_validacion.delete()
            
            if count_eliminados > 0:
                self.log_exito(f"Eliminados {count_eliminados} productos de validación adicionales")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error limpiando datos: {e}")
            return False
    
    def generar_reporte_final(self):
        """Genera y guarda el reporte final"""
        print("\n" + "="*60)
        print("📊 GENERANDO REPORTE FINAL")
        print("="*60)
        
        total_exitos = len(self.resultados['exitos'])
        total_errores = len(self.resultados['errores'])
        total_pruebas = total_exitos + total_errores
        
        # Evaluar estado del sistema
        if total_errores == 0:
            estado_sistema = "🟢 EXCELENTE"
            mensaje = "Sistema funcionando perfectamente"
        elif total_errores <= 2:
            estado_sistema = "🟡 BUENO"
            mensaje = "Sistema con errores menores"
        elif total_errores <= 5:
            estado_sistema = "🟠 REGULAR" 
            mensaje = "Sistema requiere atención"
        else:
            estado_sistema = "🔴 CRÍTICO"
            mensaje = "Sistema con problemas graves"
        
        # Actualizar resultados finales
        self.resultados.update({
            'estado_final': estado_sistema,
            'mensaje_final': mensaje,
            'resumen': {
                'total_exitos': total_exitos,
                'total_errores': total_errores,
                'total_pruebas': total_pruebas,
                'porcentaje_exito': (total_exitos / total_pruebas * 100) if total_pruebas > 0 else 0
            }
        })
        
        # Mostrar resumen
        print(f"\n{estado_sistema} - {mensaje}")
        print(f"✅ Éxitos: {total_exitos}")
        print(f"❌ Errores: {total_errores}")
        print(f"📊 Total pruebas: {total_pruebas}")
        print(f"🎯 Porcentaje éxito: {self.resultados['resumen']['porcentaje_exito']:.1f}%")
        
        # Mostrar métricas de rendimiento
        if self.resultados['metricas']:
            print(f"\n⏱️  MÉTRICAS DE RENDIMIENTO:")
            for metrica, tiempo in self.resultados['metricas'].items():
                print(f"   {metrica}: {tiempo:.3f}s")
        
        # Mostrar estadísticas del sistema
        if 'estadisticas' in self.resultados:
            stats = self.resultados['estadisticas']
            print(f"\n📈 ESTADÍSTICAS DEL SISTEMA:")
            print(f"   Productos: {stats['productos']}")
            print(f"   Transacciones: {stats['transacciones']}")
            print(f"   Lotes: {stats['lotes']}")
            print(f"   Categorías: {stats['categorias']}")
        
        # Mostrar errores si existen
        if self.resultados['errores']:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in self.resultados['errores'][:5]:  # Solo primeros 5
                print(f"   - {error}")
            if len(self.resultados['errores']) > 5:
                print(f"   ... y {len(self.resultados['errores']) - 5} errores más")
        
        # Guardar reporte
        archivo_reporte = f'REPORTE_VALIDACION_COMPLETA_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(self.resultados, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 Reporte completo guardado: {archivo_reporte}")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar reporte: {e}")
        
        print("\n🏁 VALIDACIÓN COMPLETA FINALIZADA")
        return self.resultados
    
    def ejecutar_validacion_completa(self):
        """Ejecuta toda la suite de validación"""
        print("🚀 SISTEMA DE VALIDACIÓN COMPLETA - BODEGA SEREMI")
        print("="*60)
        print(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*60)
        
        # Ejecutar todas las validaciones
        self.validar_modelos_basicos()
        self.validar_integridad_datos()
        self.crear_datos_prueba()
        self.validar_consultas_rendimiento()
        self.validar_logica_fifo()
        self.probar_funcionalidad_web()
        self.limpiar_datos_prueba()
        
        # Generar reporte final
        return self.generar_reporte_final()

def main():
    """Función principal"""
    validador = ValidadorSistemaCompleto()
    try:
        return validador.ejecutar_validacion_completa()
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
