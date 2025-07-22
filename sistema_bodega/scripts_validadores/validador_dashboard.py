#!/usr/bin/env python
"""
VALIDADOR DE DASHBOARD Y FUNCIONALIDADES EN TIEMPO REAL
Sistema de Bodega SEREMI

Este script valida específicamente:
- Dashboard y métricas en tiempo real
- Gráficos de donas y visualizaciones
- Exportaciones de Excel
- Notificaciones de vencimientos
- Rendimiento de consultas del dashboard

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F
from django.db import models
from accounts.models import Producto, MovimientoStock, LoteVencimiento

class ValidadorDashboardTiempoReal:
    def __init__(self):
        self.errores = []
        self.metricas_rendimiento = {}
        self.client = Client()
        self.driver = None
        
    def log_error(self, mensaje, detalle=None):
        """Registra un error"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje,
            'detalle': detalle or ''
        }
        self.errores.append(error)
        print(f"❌ ERROR: {mensaje}")
        if detalle:
            print(f"   Detalle: {detalle}")
    
    def log_exito(self, mensaje):
        """Registra un éxito"""
        print(f"✅ ÉXITO: {mensaje}")
    
    def medir_tiempo(self, nombre_metrica):
        """Decorador para medir tiempo de ejecución"""
        def decorador(func):
            def wrapper(*args, **kwargs):
                inicio = time.time()
                resultado = func(*args, **kwargs)
                fin = time.time()
                tiempo = fin - inicio
                self.metricas_rendimiento[nombre_metrica] = tiempo
                print(f"⏱️  {nombre_metrica}: {tiempo:.3f}s")
                return resultado
            return wrapper
        return decorador

    def crear_usuario_admin(self):
        """Crea usuario admin para pruebas"""
        try:
            user, created = User.objects.get_or_create(
                username='dashboard_admin',
                defaults={
                    'password': 'admin123',
                    'email': 'admin@dashboard.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                user.set_password('admin123')
                user.save()
            return user
        except Exception as e:
            self.log_error("Error creando usuario admin", str(e))
            return None

    @medir_tiempo('carga_dashboard')
    def probar_carga_dashboard(self):
        """Prueba la carga del dashboard principal"""
        try:
            # Login
            self.client.login(username='dashboard_admin', password='admin123')
            
            # Acceder al dashboard
            response = self.client.get(reverse('accounts:dashboard'))
            
            if response.status_code == 200:
                self.log_exito("Dashboard cargado correctamente")
                
                # Verificar contexto
                context = response.context
                if context:
                    metricas_requeridas = [
                        'total_productos',
                        'productos_bajo_stock',
                        'total_movimientos_mes',
                        'productos_vencimiento_proximo'
                    ]
                    
                    for metrica in metricas_requeridas:
                        if metrica in context:
                            valor = context[metrica]
                            print(f"   📊 {metrica}: {valor}")
                        else:
                            self.log_error(f"Métrica faltante en dashboard: {metrica}")
                    
                    return True
                else:
                    self.log_error("Dashboard sin contexto")
                    return False
            else:
                self.log_error(f"Error cargando dashboard: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("Error en prueba de dashboard", str(e))
            return False

    @medir_tiempo('metricas_tiempo_real')
    def validar_metricas_tiempo_real(self):
        """Valida que las métricas del dashboard sean precisas"""
        try:
            print("🔍 Validando precisión de métricas...")
            
            # Calcular métricas manualmente
            total_productos_real = Producto.objects.count()
            productos_bajo_stock_real = Producto.objects.filter(
                stock__lte=models.F('stock_minimo')
            ).count()
            
            hoy = date.today()
            inicio_mes = hoy.replace(day=1)
            movimientos_mes_real = MovimientoStock.objects.filter(
                fecha_movimiento__gte=inicio_mes
            ).count()
            
            fecha_limite = hoy + timedelta(days=30)
            productos_vencimiento_real = LoteVencimiento.objects.filter(
                fecha_vencimiento__lte=fecha_limite,
                cantidad_disponible__gt=0
            ).values('producto').distinct().count()
            
            # Obtener métricas del dashboard
            self.client.login(username='dashboard_admin', password='admin123')
            response = self.client.get(reverse('accounts:dashboard'))
            
            if response.status_code == 200 and response.context:
                context = response.context
                
                # Comparar métricas
                discrepancias = []
                
                if context.get('total_productos') != total_productos_real:
                    discrepancias.append(f"Total productos: Dashboard {context.get('total_productos')} vs Real {total_productos_real}")
                
                if context.get('productos_bajo_stock') != productos_bajo_stock_real:
                    discrepancias.append(f"Bajo stock: Dashboard {context.get('productos_bajo_stock')} vs Real {productos_bajo_stock_real}")
                
                if context.get('total_movimientos_mes') != movimientos_mes_real:
                    discrepancias.append(f"Movimientos mes: Dashboard {context.get('total_movimientos_mes')} vs Real {movimientos_mes_real}")
                
                if context.get('productos_vencimiento_proximo') != productos_vencimiento_real:
                    discrepancias.append(f"Próximos a vencer: Dashboard {context.get('productos_vencimiento_proximo')} vs Real {productos_vencimiento_real}")
                
                if discrepancias:
                    for discrepancia in discrepancias:
                        self.log_error("Discrepancia en métricas", discrepancia)
                    return False
                else:
                    self.log_exito("Todas las métricas son precisas")
                    return True
            else:
                self.log_error("No se pudo obtener contexto del dashboard")
                return False
                
        except Exception as e:
            self.log_error("Error validando métricas tiempo real", str(e))
            return False

    @medir_tiempo('exportacion_excel')
    def probar_exportaciones_excel(self):
        """Prueba todas las exportaciones de Excel"""
        try:
            print("📊 Probando exportaciones de Excel...")
            
            self.client.login(username='dashboard_admin', password='admin123')
            
            exportaciones = [
                ('accounts:exportar_productos_excel', 'Productos'),
                ('accounts:exportar_movimientos_excel', 'Movimientos'),
                ('accounts:exportar_vencimientos_excel', 'Vencimientos'),
            ]
            
            resultados_exportacion = {}
            
            for url_name, nombre in exportaciones:
                try:
                    inicio = time.time()
                    response = self.client.get(reverse(url_name))
                    fin = time.time()
                    
                    tiempo_exportacion = fin - inicio
                    
                    if response.status_code == 200:
                        content_type = response.get('Content-Type', '')
                        content_length = len(response.content)
                        
                        if 'excel' in content_type or 'spreadsheet' in content_type:
                            self.log_exito(f"Exportación {nombre} exitosa ({content_length} bytes en {tiempo_exportacion:.2f}s)")
                            resultados_exportacion[nombre] = {
                                'exitosa': True,
                                'tiempo': tiempo_exportacion,
                                'tamaño': content_length
                            }
                        else:
                            self.log_error(f"Tipo de contenido incorrecto en {nombre}", content_type)
                            resultados_exportacion[nombre] = {'exitosa': False}
                    else:
                        self.log_error(f"Error en exportación {nombre}", f"Status: {response.status_code}")
                        resultados_exportacion[nombre] = {'exitosa': False}
                        
                except Exception as e:
                    self.log_error(f"Error en exportación {nombre}", str(e))
                    resultados_exportacion[nombre] = {'exitosa': False}
            
            # Evaluar rendimiento
            exportaciones_exitosas = sum(1 for r in resultados_exportacion.values() if r.get('exitosa'))
            total_exportaciones = len(exportaciones)
            
            if exportaciones_exitosas == total_exportaciones:
                self.log_exito(f"Todas las exportaciones funcionan correctamente ({exportaciones_exitosas}/{total_exportaciones})")
                return True
            else:
                self.log_error(f"Fallos en exportaciones: {total_exportaciones - exportaciones_exitosas}/{total_exportaciones}")
                return False
                
        except Exception as e:
            self.log_error("Error en pruebas de exportación", str(e))
            return False

    def inicializar_selenium(self):
        """Inicializa el driver de Selenium para pruebas de UI"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Ejecutar sin ventana
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"⚠️  No se pudo inicializar Selenium: {e}")
            print("   Las pruebas de UI se saltarán")
            return False

    @medir_tiempo('graficos_donas')
    def probar_graficos_donas(self):
        """Prueba que los gráficos de donas se generen correctamente"""
        if not self.driver:
            print("⏭️  Saltando pruebas de gráficos (Selenium no disponible)")
            return True
        
        try:
            print("🍩 Probando gráficos de donas...")
            
            # Navegar al dashboard
            self.driver.get("http://localhost:8000/accounts/dashboard/")
            
            # Buscar elementos de gráficos
            time.sleep(3)  # Esperar a que carguen los gráficos
            
            graficos_encontrados = []
            
            # Buscar canvas de Chart.js
            canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
            graficos_encontrados.extend(canvas_elements)
            
            # Buscar elementos con clases específicas de gráficos
            chart_containers = self.driver.find_elements(By.CLASS_NAME, "chart-container")
            graficos_encontrados.extend(chart_containers)
            
            if graficos_encontrados:
                self.log_exito(f"Gráficos encontrados: {len(graficos_encontrados)}")
                return True
            else:
                self.log_error("No se encontraron gráficos en el dashboard")
                return False
                
        except Exception as e:
            self.log_error("Error probando gráficos de donas", str(e))
            return False

    @medir_tiempo('navegacion_menu')
    def probar_navegacion_menu(self):
        """Prueba la navegación del menú principal"""
        try:
            print("🧭 Probando navegación del menú...")
            
            self.client.login(username='dashboard_admin', password='admin123')
            
            urls_importantes = [
                ('accounts:dashboard', 'Dashboard'),
                ('accounts:productos', 'Lista de Productos'),
                ('accounts:movimientos', 'Movimientos'),
                ('accounts:control_vencimientos', 'Control de Vencimientos'),
                ('accounts:productos_vencimiento_proximo', 'Próximos a Vencer'),
            ]
            
            navegacion_exitosa = 0
            
            for url_name, nombre in urls_importantes:
                try:
                    response = self.client.get(reverse(url_name))
                    
                    if response.status_code == 200:
                        self.log_exito(f"Navegación a {nombre} exitosa")
                        navegacion_exitosa += 1
                    else:
                        self.log_error(f"Error navegando a {nombre}", f"Status: {response.status_code}")
                        
                except Exception as e:
                    self.log_error(f"Error navegando a {nombre}", str(e))
            
            if navegacion_exitosa == len(urls_importantes):
                self.log_exito("Toda la navegación funciona correctamente")
                return True
            else:
                self.log_error(f"Fallos en navegación: {len(urls_importantes) - navegacion_exitosa}/{len(urls_importantes)}")
                return False
                
        except Exception as e:
            self.log_error("Error en pruebas de navegación", str(e))
            return False

    @medir_tiempo('actualización_dinamica')
    def probar_actualizacion_dinamica(self):
        """Simula cambios y verifica que se reflejen en tiempo real"""
        try:
            print("🔄 Probando actualización dinámica...")
            
            # Obtener métricas iniciales
            response1 = self.client.get(reverse('accounts:dashboard'))
            metricas_inicial = response1.context if response1.status_code == 200 else {}
            
            # Simular cambio: crear un producto
            from accounts.models import Proveedor
            proveedor, _ = Proveedor.objects.get_or_create(
                rut='11111111-1',
                defaults={'nombre': 'Proveedor Test Dashboard'}
            )
            
            producto_test = Producto.objects.create(
                codigo='DASHBOARD_TEST',
                nombre='Producto Test Dashboard',
                descripcion='Producto para probar actualización dinámica',
                stock=5,  # Bajo stock para probar métricas
                stock_minimo=10,
                precio_unitario=1000,
                categoria='MEDICAMENTOS',
                unidad_medida='UNIDADES',
                ubicacion='TEST-001',
                proveedor=proveedor
            )
            
            # Obtener métricas después del cambio
            response2 = self.client.get(reverse('accounts:dashboard'))
            metricas_final = response2.context if response2.status_code == 200 else {}
            
            # Verificar que las métricas cambiaron
            cambios_detectados = []
            
            if metricas_inicial.get('total_productos', 0) + 1 == metricas_final.get('total_productos', 0):
                cambios_detectados.append("Total productos actualizado correctamente")
            
            if metricas_inicial.get('productos_bajo_stock', 0) + 1 == metricas_final.get('productos_bajo_stock', 0):
                cambios_detectados.append("Productos bajo stock actualizado correctamente")
            
            # Limpiar datos de prueba
            producto_test.delete()
            
            if cambios_detectados:
                for cambio in cambios_detectados:
                    self.log_exito(cambio)
                return True
            else:
                self.log_error("No se detectaron cambios dinámicos en métricas")
                return False
                
        except Exception as e:
            self.log_error("Error probando actualización dinámica", str(e))
            return False

    def cerrar_selenium(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            self.driver.quit()

    def generar_reporte_dashboard(self):
        """Genera reporte de validación del dashboard"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'metricas_rendimiento': self.metricas_rendimiento,
            'errores': self.errores,
            'resumen': {
                'total_errores': len(self.errores),
                'rendimiento_promedio': sum(self.metricas_rendimiento.values()) / len(self.metricas_rendimiento) if self.metricas_rendimiento else 0
            }
        }
        
        # Guardar reporte
        archivo_reporte = f'reporte_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Reporte guardado: {archivo_reporte}")
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        # Mostrar resumen
        print("\n" + "="*60)
        print("📋 REPORTE DE VALIDACIÓN DASHBOARD")
        print("="*60)
        
        print(f"❌ Errores encontrados: {len(self.errores)}")
        print("\n⏱️  MÉTRICAS DE RENDIMIENTO:")
        for metrica, tiempo in self.metricas_rendimiento.items():
            estado = "🟢" if tiempo < 1.0 else "🟡" if tiempo < 3.0 else "🔴"
            print(f"   {estado} {metrica}: {tiempo:.3f}s")
        
        if self.errores:
            print("\n❌ ERRORES DETECTADOS:")
            for error in self.errores:
                print(f"   - {error['mensaje']}")
        
        # Evaluación final
        if len(self.errores) == 0:
            print("\n🎉 DASHBOARD FUNCIONANDO PERFECTAMENTE")
        elif len(self.errores) <= 2:
            print("\n⚠️  DASHBOARD CON ERRORES MENORES")
        else:
            print("\n🚨 DASHBOARD REQUIERE ATENCIÓN INMEDIATA")
        
        return reporte

    def ejecutar_validacion_completa(self):
        """Ejecuta toda la validación del dashboard"""
        print("🚀 INICIANDO VALIDACIÓN DE DASHBOARD Y TIEMPO REAL")
        print("="*60)
        
        try:
            # Preparación
            print("\n🔧 PREPARACIÓN")
            if not self.crear_usuario_admin():
                return False
            
            selenium_disponible = self.inicializar_selenium()
            
            # 1. Carga básica del dashboard
            print("\n1️⃣ CARGA DEL DASHBOARD")
            self.probar_carga_dashboard()
            
            # 2. Validar métricas en tiempo real
            print("\n2️⃣ MÉTRICAS TIEMPO REAL")
            self.validar_metricas_tiempo_real()
            
            # 3. Exportaciones
            print("\n3️⃣ EXPORTACIONES EXCEL")
            self.probar_exportaciones_excel()
            
            # 4. Navegación
            print("\n4️⃣ NAVEGACIÓN")
            self.probar_navegacion_menu()
            
            # 5. Gráficos (si Selenium está disponible)
            if selenium_disponible:
                print("\n5️⃣ GRÁFICOS DE DONAS")
                self.probar_graficos_donas()
            
            # 6. Actualización dinámica
            print("\n6️⃣ ACTUALIZACIÓN DINÁMICA")
            self.probar_actualizacion_dinamica()
            
            return True
            
        except Exception as e:
            print(f"💥 Error fatal en validación: {e}")
            return False
        
        finally:
            self.cerrar_selenium()
            self.generar_reporte_dashboard()


def main():
    """Función principal"""
    print("Validador Dashboard y Tiempo Real - Sistema Bodega SEREMI")
    print("="*60)
    
    validador = ValidadorDashboardTiempoReal()
    
    try:
        validador.ejecutar_validacion_completa()
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
    finally:
        print("\n🏁 Validación de dashboard finalizada")


if __name__ == "__main__":
    main()
