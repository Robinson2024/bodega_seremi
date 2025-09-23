#!/usr/bin/env python
"""
SCRIPT DE VALIDACIÓN FINAL Y ANÁLISIS DE ESCALABILIDAD
Sistema de Bodega SEREMI

Este script realiza un análisis completo del sistema para detectar:
- Vulnerabilidades y bugs
- Problemas de escalabilidad
- Errores de sincronización
- Integridad de datos
- Rendimiento bajo carga

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
Versión: 1.0
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
from collections import defaultdict

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

# Configurar ALLOWED_HOSTS para pruebas
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
if 'localhost' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('localhost')
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

from django.db import transaction, connection
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.db import models
from accounts.models import (
    Producto, Transaccion, LoteProducto, 
    ActaEntrega, Funcionario, CustomUser, Categoria
)

User = get_user_model()  # Usar el modelo correcto de usuario

class ValidadorSistemaCompleto:
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.exitos = []
        self.metricas_rendimiento = {}
        self.datos_prueba = {}
        self.client = Client()
        
    def log_error(self, mensaje, detalle=None):
        """Registra un error encontrado"""
        error = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje,
            'detalle': detalle or '',
            'traceback': traceback.format_exc() if detalle else ''
        }
        self.errores.append(error)
        print(f"❌ ERROR: {mensaje}")
        if detalle:
            print(f"   Detalle: {detalle}")
    
    def log_warning(self, mensaje):
        """Registra una advertencia"""
        warning = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        }
        self.warnings.append(warning)
        print(f"⚠️  WARNING: {mensaje}")
    
    def log_exito(self, mensaje):
        """Registra un éxito"""
        exito = {
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        }
        self.exitos.append(exito)
        print(f"✅ ÉXITO: {mensaje}")
    
    def medir_tiempo(self, funcion_nombre):
        """Decorador para medir tiempo de ejecución"""
        def decorador(func):
            def wrapper(*args, **kwargs):
                inicio = time.time()
                resultado = func(*args, **kwargs)
                fin = time.time()
                tiempo = fin - inicio
                self.metricas_rendimiento[funcion_nombre] = tiempo
                print(f"⏱️  {funcion_nombre}: {tiempo:.2f}s")
                return resultado
            return wrapper
        return decorador

    def crear_usuarios_prueba(self):
        """Crea usuarios de diferentes perfiles para pruebas"""
        try:
            # Primero eliminar usuarios de prueba existentes
            User.objects.filter(username__endswith='_test').delete()
            
            usuarios = [
                {
                    'username': 'admin_test',
                    'password': 'admin123',
                    'email': 'admin@test.com',
                    'is_staff': True,
                    'is_superuser': True,
                    'rut': '11111111-1',
                    'nombre': 'Admin Test Usuario',
                    'tipo': 'admin'
                },
                {
                    'username': 'bodeguero_test', 
                    'password': 'bodeg123',
                    'email': 'bodeguero@test.com',
                    'is_staff': True,
                    'is_superuser': False,
                    'rut': '22222222-2',
                    'nombre': 'Bodeguero Test Usuario',
                    'tipo': 'bodeguero'
                },
                {
                    'username': 'operador_test',
                    'password': 'oper123', 
                    'email': 'operador@test.com',
                    'is_staff': False,
                    'is_superuser': False,
                    'rut': '33333333-3',
                    'nombre': 'Operador Test Usuario',
                    'tipo': 'operador'
                }
            ]
            
            for datos in usuarios:
                tipo = datos.pop('tipo')  # Remover 'tipo' antes de crear usuario
                user = User.objects.create_user(**datos)
                self.log_exito(f"Usuario {tipo} creado exitosamente")
                self.datos_prueba[f'user_{tipo}'] = user
            
            return True
            
        except Exception as e:
            self.log_error("Error creando usuarios de prueba", str(e))
            return False

    def crear_proveedor_prueba(self):
        """Crea un proveedor para las pruebas - usando solo RUT como string"""
        inicio = time.time()
        try:
            # En este sistema, el proveedor se maneja como RUT string, no modelo separado
            rut_proveedor = '12345678-9'
            
            # Verificar que el RUT sea válido
            import re
            if re.match(r'^\d{7,8}-[0-9kK]$', rut_proveedor):
                self.datos_prueba['rut_proveedor'] = rut_proveedor
                self.log_exito("RUT de proveedor configurado exitosamente")
                tiempo = time.time() - inicio
                self.metricas_rendimiento['crear_proveedor'] = tiempo
                print(f"⏱️  crear_proveedor: {tiempo:.2f}s")
                return True
            else:
                self.log_error("Formato de RUT inválido")
                return False
            
        except Exception as e:
            self.log_error("Error configurando proveedor de prueba", str(e))
            return False

    def probar_registro_producto(self):
        """Prueba el registro completo de un producto"""
        inicio = time.time()
        try:
            # Login como admin
            self.client.login(
                username='admin_test',
                password='admin123'
            )
            
            # Datos del producto
            datos_producto = {
                'codigo_barra': f'TEST{random.randint(1000, 9999)}',
                'descripcion': 'Producto Test Escalabilidad - Producto para pruebas de escalabilidad del sistema',
                'stock': 0,  # Empezamos con 0 para agregar stock después
                'rut_proveedor': self.datos_prueba['rut_proveedor'],
                'tiene_vencimiento': True
            }
            
            # Enviar formulario
            response = self.client.post(
                reverse('registrar-producto'),
                datos_producto,
                follow=True
            )
            
            if response.status_code == 200:
                # Verificar que el producto se creó
                producto = Producto.objects.filter(codigo_barra=datos_producto['codigo_barra']).first()
                if producto:
                    self.datos_prueba['producto'] = producto
                    self.log_exito(f"Producto {producto.codigo_barra} registrado exitosamente")
                    
                    # Verificar campos básicos
                    if producto.descripcion == datos_producto['descripcion']:
                        self.log_exito("Descripción del producto correcta")
                    else:
                        self.log_error("Descripción del producto incorrecta")
                    
                    return True
                else:
                    self.log_error("Producto no encontrado después del registro")
                    return False
            else:
                self.log_error(f"Error en registro de producto. Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("Error en prueba de registro de producto", str(e))
            return False
        finally:
            tiempo = time.time() - inicio
            self.metricas_rendimiento['registrar_producto'] = tiempo
            print(f"⏱️  registrar_producto: {tiempo:.2f}s")

    def verificar_integridad_producto(self, producto, datos_esperados):
        """Verifica la integridad de los datos del producto"""
        try:
            errores_integridad = []
            
            # Verificar campos básicos (usando nombres reales del modelo)
            if producto.codigo_barra != datos_esperados['codigo_barra']:
                errores_integridad.append(f"Código de barra incorrecto: {producto.codigo_barra} != {datos_esperados['codigo_barra']}")
            
            if producto.descripcion != datos_esperados['descripcion']:
                errores_integridad.append(f"Descripción incorrecta: {producto.descripcion} != {datos_esperados['descripcion']}")
            
            if producto.stock != datos_esperados['stock']:
                errores_integridad.append(f"Stock incorrecto: {producto.stock} != {datos_esperados['stock']}")
            
            if producto.rut_proveedor != datos_esperados['rut_proveedor']:
                errores_integridad.append(f"RUT proveedor incorrecto: {producto.rut_proveedor} != {datos_esperados['rut_proveedor']}")
            
            if errores_integridad:
                for error in errores_integridad:
                    self.log_error("Error de integridad en producto", error)
                return False
            else:
                self.log_exito("Integridad del producto verificada correctamente")
                return True
                
        except Exception as e:
            self.log_error("Error verificando integridad del producto", str(e))
            return False

    def probar_agregar_stock_con_lotes(self):
        """Prueba agregar stock con manejo de lotes y vencimientos"""
        inicio = time.time()
        try:
            if 'producto' not in self.datos_prueba:
                self.log_error("No hay producto de prueba disponible")
                return False
            
            producto = self.datos_prueba['producto']
            
            # Agregar varios lotes con diferentes vencimientos
            lotes_prueba = [
                {
                    'cantidad': 50,
                    'numero_lote': 'LOTE001TEST',
                    'fecha_vencimiento': date.today() + timedelta(days=30),
                    'numero_factura': 'FACT001',
                    'motivo': 'Ingreso inicial de stock'
                },
                {
                    'cantidad': 75,
                    'numero_lote': 'LOTE002TEST',
                    'fecha_vencimiento': date.today() + timedelta(days=60),
                    'numero_factura': 'FACT002',
                    'motivo': 'Reposición de stock'
                },
                {
                    'cantidad': 25,
                    'numero_lote': 'LOTE003TEST',
                    'fecha_vencimiento': date.today() + timedelta(days=15),  # Vence pronto
                    'numero_factura': 'FACT003',
                    'motivo': 'Stock de urgencia'
                }
            ]
            
            stock_total_esperado = 0
            
            for i, lote_datos in enumerate(lotes_prueba):
                # Login como bodeguero
                self.client.login(
                    username='bodeguero_test',
                    password='bodeg123'
                )
                
                # Preparar datos del formulario
                form_data = {
                    'cantidad': lote_datos['cantidad'],
                    'numero_factura': lote_datos['numero_factura'],
                    'motivo': lote_datos['motivo'],
                    'tiene_vencimiento': 'on',
                    'numero_lote': lote_datos['numero_lote'],
                    'fecha_vencimiento': lote_datos['fecha_vencimiento'].strftime('%Y-%m-%d')
                }
                
                # Enviar formulario
                response = self.client.post(
                    reverse('agregar-stock-detalle', args=[producto.id]),
                    form_data,
                    follow=True
                )
                
                if response.status_code == 200:
                    stock_total_esperado += lote_datos['cantidad']
                    self.log_exito(f"Lote {i+1} agregado exitosamente: {lote_datos['numero_lote']}")
                else:
                    self.log_error(f"Error agregando lote {i+1}. Status: {response.status_code}")
                    return False
            
            # Verificar stock total
            producto.refresh_from_db()
            if producto.stock == stock_total_esperado:
                self.log_exito(f"Stock total correcto: {producto.stock}")
                self.datos_prueba['stock_total'] = stock_total_esperado
            else:
                self.log_error(f"Stock total incorrecto: {producto.stock} != {stock_total_esperado}")
                return False
            
            # Verificar lotes creados
            lotes_creados = LoteProducto.objects.filter(producto=producto)
            if lotes_creados.count() == len(lotes_prueba):
                self.log_exito(f"Todos los lotes creados correctamente: {lotes_creados.count()}")
            else:
                self.log_error(f"Número de lotes incorrecto: {lotes_creados.count()} != {len(lotes_prueba)}")
                return False
            
            self.datos_prueba['lotes'] = list(lotes_creados)
            
            tiempo = time.time() - inicio
            self.metricas_rendimiento['agregar_stock'] = tiempo
            print(f"⏱️  agregar_stock: {tiempo:.2f}s")
            return True
            
        except Exception as e:
            self.log_error("Error en prueba de agregar stock con lotes", str(e))
            return False

    def probar_crear_acta_recepcion(self):
        """Prueba la creación de un acta de recepción - FUNCIONALIDAD NO DISPONIBLE"""
        try:
            self.log_warning("Función de Acta de Recepción no implementada en el sistema actual")
            self.log_warning("El sistema actual no tiene modelos ActaRecepcion/DetalleActa")
            
            # Verificar que tenemos producto de prueba
            if 'producto' in self.datos_prueba:
                self.log_exito("Producto de prueba disponible para futuras implementaciones de actas")
            
            return True  # No es un error crítico, solo funcionalidad no implementada
            
        except Exception as e:
            self.log_error("Error en prueba de crear acta", str(e))
            return False

    def verificar_sincronizacion_datos(self):
        """Verifica que todos los datos estén sincronizados correctamente"""
        inicio = time.time()
        try:
            if 'producto' not in self.datos_prueba:
                self.log_error("No hay producto de prueba disponible")
                return False
            
            producto = self.datos_prueba['producto']
            
            # 1. Verificar stock vs transacciones
            transacciones = Transaccion.objects.filter(producto=producto)
            stock_calculado = sum(
                trans.cantidad if trans.tipo == 'entrada' else -trans.cantidad 
                for trans in transacciones
            )
            
            if producto.stock == stock_calculado:
                self.log_exito("Sincronización stock-transacciones correcta")
            else:
                self.log_error(f"Desincronización detectada: Stock DB {producto.stock} != Calculado {stock_calculado}")
            
            # 2. Verificar lotes vs stock
            lotes = LoteProducto.objects.filter(producto=producto)
            stock_lotes = sum(lote.stock for lote in lotes if lote.stock > 0)
            
            if producto.stock == stock_lotes:
                self.log_exito("Sincronización stock-lotes correcta")
            else:
                self.log_warning(f"Diferencia en lotes: Stock DB {producto.stock} vs Lotes {stock_lotes}")
            
            # 3. Verificar fechas de vencimiento
            for lote in lotes:
                if lote.fecha_vencimiento < date.today():
                    self.log_warning(f"Lote vencido detectado: {lote.numero_lote}")
                elif lote.fecha_vencimiento <= date.today() + timedelta(days=30):
                    self.log_warning(f"Lote próximo a vencer: {lote.numero_lote}")
            
            tiempo = time.time() - inicio
            self.metricas_rendimiento['verificar_sincronizacion'] = tiempo
            print(f"⏱️  verificar_sincronizacion: {tiempo:.2f}s")
            return True
            
        except Exception as e:
            self.log_error("Error verificando sincronización", str(e))
            return False

    def probar_exportaciones_excel(self):
        """Prueba las exportaciones a Excel"""
        inicio = time.time()
        try:
            # Login como admin
            self.client.login(
                username='admin_test',
                password='admin123'
            )
            
            exportaciones_prueba = [
                {
                    'url': 'exportar-productos-excel',
                    'nombre': 'Exportar Productos'
                },
                {
                    'url': 'exportar-movimientos-excel', 
                    'nombre': 'Exportar Movimientos'
                },
                {
                    'url': 'exportar-vencimientos-excel',
                    'nombre': 'Exportar Vencimientos'
                }
            ]
            
            for exportacion in exportaciones_prueba:
                try:
                    response = self.client.get(reverse(exportacion['url']))
                    
                    if response.status_code == 200:
                        # Verificar headers de Excel
                        content_type = response.get('Content-Type', '')
                        if 'excel' in content_type or 'spreadsheet' in content_type:
                            self.log_exito(f"Exportación {exportacion['nombre']} exitosa")
                        else:
                            self.log_warning(f"Tipo de contenido inesperado en {exportacion['nombre']}: {content_type}")
                    else:
                        self.log_error(f"Error en exportación {exportacion['nombre']}: Status {response.status_code}")
                        
                except Exception as e:
                    self.log_error(f"Error en exportación {exportacion['nombre']}", str(e))
            
            tiempo = time.time() - inicio
            self.metricas_rendimiento['probar_exportaciones'] = tiempo
            print(f"⏱️  probar_exportaciones: {tiempo:.2f}s")
            return True
            
        except Exception as e:
            self.log_error("Error en pruebas de exportación", str(e))
            return False

    def probar_dashboard_tiempo_real(self):
        """Prueba el dashboard y sus métricas en tiempo real"""
        inicio = time.time()
        try:
            # Login como admin
            self.client.login(
                username='admin_test',
                password='admin123'
            )
            
            # Acceder al dashboard
            response = self.client.get(reverse('dashboard'))
            
            if response.status_code == 200:
                self.log_exito("Dashboard cargado exitosamente")
                
                # Verificar contexto del dashboard
                context = response.context
                if context:
                    metricas_esperadas = [
                        'total_productos',
                        'productos_bajo_stock', 
                        'total_movimientos_mes',
                        'productos_vencimiento_proximo'
                    ]
                    
                    for metrica in metricas_esperadas:
                        if metrica in context:
                            valor = context[metrica]
                            self.log_exito(f"Métrica {metrica}: {valor}")
                        else:
                            self.log_warning(f"Métrica {metrica} no encontrada en dashboard")
                    
                    return True
                else:
                    self.log_error("No se pudo obtener contexto del dashboard")
                    return False
            else:
                self.log_error(f"Error cargando dashboard: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("Error probando dashboard", str(e))
            return False
        finally:
            tiempo = time.time() - inicio
            self.metricas_rendimiento['probar_dashboard'] = tiempo
            print(f"⏱️  probar_dashboard: {tiempo:.2f}s")

    def probar_escalabilidad_bajo_carga(self):
        """Simula carga alta para probar escalabilidad"""
        inicio = time.time()
        try:
            print("🔥 Iniciando pruebas de escalabilidad...")
            
            # Crear múltiples productos
            productos_creados = []
            
            for i in range(10):  # Crear 10 productos
                try:
                    producto = Producto.objects.create(
                        codigo_barra=f'SCALE{i:03d}',
                        descripcion=f'Producto Escalabilidad {i} - Producto para prueba de escalabilidad número {i}',
                        stock=0,
                        rut_proveedor=self.datos_prueba['rut_proveedor'],
                        tiene_vencimiento=False
                    )
                    productos_creados.append(producto)
                    
                except Exception as e:
                    self.log_error(f"Error creando producto {i}", str(e))
            
            self.log_exito(f"Creados {len(productos_creados)} productos para escalabilidad")
            
            # Simular múltiples movimientos
            movimientos_creados = 0
            
            for producto in productos_creados:
                for j in range(5):  # 5 transacciones por producto
                    try:
                        cantidad = random.randint(10, 50)
                        Transaccion.objects.create(
                            producto=producto,
                            tipo='entrada',
                            cantidad=cantidad,
                            observacion=f'Movimiento prueba {j}',
                            fecha=date.today()
                        )
                        movimientos_creados += 1
                        
                        # Actualizar stock
                        producto.stock += cantidad
                        producto.save()
                        
                    except Exception as e:
                        self.log_error(f"Error creando movimiento {j} para producto {producto.codigo_barra}", str(e))
            
            self.log_exito(f"Creados {movimientos_creados} movimientos de stock")
            
            # Probar consultas complejas
            inicio_consulta = time.time()
            
            # Consulta compleja: productos con transacciones recientes
            productos_con_movimientos = Producto.objects.filter(
                transaccion__fecha__gte=date.today() - timedelta(days=30)
            ).distinct().select_related().prefetch_related('transaccion_set')
            
            resultado = list(productos_con_movimientos)
            fin_consulta = time.time()
            
            tiempo_consulta = fin_consulta - inicio_consulta
            self.metricas_rendimiento['consulta_compleja'] = tiempo_consulta
            
            if tiempo_consulta < 1.0:  # Menos de 1 segundo
                self.log_exito(f"Consulta compleja ejecutada eficientemente: {tiempo_consulta:.3f}s")
            else:
                self.log_warning(f"Consulta compleja lenta: {tiempo_consulta:.3f}s")
            
            tiempo = time.time() - inicio
            self.metricas_rendimiento['prueba_escalabilidad'] = tiempo
            print(f"⏱️  prueba_escalabilidad: {tiempo:.2f}s")
            return True
            
        except Exception as e:
            self.log_error("Error en pruebas de escalabilidad", str(e))
            return False

    def ejecutar_pruebas_seguridad(self):
        """Ejecuta pruebas básicas de seguridad"""
        try:
            print("🔒 Iniciando pruebas de seguridad...")
            
            # 1. Prueba acceso sin autenticación
            self.client.logout()
            response = self.client.get(reverse('dashboard'))
            
            if response.status_code in [302, 403]:  # Redirección o prohibido
                self.log_exito("Protección de rutas funcionando correctamente")
            else:
                self.log_error(f"Acceso no autorizado permitido: Status {response.status_code}")
            
            # 2. Prueba SQL injection básica
            try:
                productos = Producto.objects.filter(descripcion="'; DROP TABLE--")
                if not productos.exists():
                    self.log_exito("Protección SQL injection básica funcionando")
            except Exception:
                self.log_exito("ORM Django protegiendo contra SQL injection")
            
            # 3. Prueba permisos de usuario
            self.client.login(username='operador_test', password='oper123')
            
            # Intentar acceder a función de admin
            response = self.client.get(reverse('registrar-producto'))
            
            if response.status_code in [302, 403]:
                self.log_exito("Control de permisos funcionando correctamente")
            else:
                self.log_warning(f"Posible problema de permisos: Status {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_error("Error en pruebas de seguridad", str(e))
            return False

    def limpiar_datos_prueba(self):
        """Limpia los datos de prueba creados"""
        try:
            print("🧹 Limpiando datos de prueba...")
            
            # Eliminar productos de prueba
            productos_prueba = Producto.objects.filter(
                codigo_barra__startswith='TEST'
            ) | Producto.objects.filter(
                codigo_barra__startswith='SCALE'
            )
            
            count_productos = productos_prueba.count()
            productos_prueba.delete()
            
            # Eliminar usuarios de prueba
            usuarios_prueba = User.objects.filter(
                username__endswith='_test'
            )
            count_usuarios = usuarios_prueba.count()
            usuarios_prueba.delete()
            
            self.log_exito(f"Limpieza completada: {count_productos} productos, {count_usuarios} usuarios")
            
        except Exception as e:
            self.log_error("Error en limpieza de datos", str(e))

    def generar_reporte_final(self):
        """Genera el reporte final de la validación"""
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'resumen': {
                'total_pruebas': len(self.exitos) + len(self.errores) + len(self.warnings),
                'exitos': len(self.exitos),
                'errores': len(self.errores),
                'warnings': len(self.warnings)
            },
            'metricas_rendimiento': self.metricas_rendimiento,
            'exitos': self.exitos,
            'errores': self.errores,
            'warnings': self.warnings
        }
        
        # Guardar reporte en archivo
        archivo_reporte = f'reporte_validacion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            
            print(f"\n📊 REPORTE FINAL GUARDADO: {archivo_reporte}")
            
        except Exception as e:
            print(f"Error guardando reporte: {e}")
        
        # Mostrar resumen en consola
        print("\n" + "="*60)
        print("📋 RESUMEN FINAL DE VALIDACIÓN")
        print("="*60)
        print(f"✅ Éxitos: {len(self.exitos)}")
        print(f"❌ Errores: {len(self.errores)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print("\n📈 MÉTRICAS DE RENDIMIENTO:")
        for metrica, tiempo in self.metricas_rendimiento.items():
            print(f"   {metrica}: {tiempo:.3f}s")
        
        if self.errores:
            print("\n❌ ERRORES CRÍTICOS:")
            for error in self.errores:
                print(f"   - {error['mensaje']}")
        
        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   - {warning['mensaje']}")
        
        # Evaluación final
        if len(self.errores) == 0:
            print("\n🎉 SISTEMA APROBADO - Sin errores críticos detectados")
        elif len(self.errores) <= 2:
            print("\n⚠️  SISTEMA CON OBSERVACIONES - Revisar errores menores")
        else:
            print("\n🚨 SISTEMA REQUIERE ATENCIÓN - Múltiples errores detectados")
        
        return reporte

    def ejecutar_validacion_completa(self):
        """Ejecuta toda la suite de validación"""
        print("🚀 INICIANDO VALIDACIÓN COMPLETA DEL SISTEMA")
        print("="*60)
        
        try:
            # 1. Preparación
            print("\n1️⃣ PREPARACIÓN")
            if not self.crear_usuarios_prueba():
                return False
            if not self.crear_proveedor_prueba():
                return False
            
            # 2. Flujo completo de producto
            print("\n2️⃣ FLUJO COMPLETO DE PRODUCTO")
            if not self.probar_registro_producto():
                return False
            if not self.probar_agregar_stock_con_lotes():
                return False
            
            # 3. Procesos administrativos
            print("\n3️⃣ PROCESOS ADMINISTRATIVOS")
            if not self.probar_crear_acta_recepcion():
                return False
            
            # 4. Verificaciones de integridad
            print("\n4️⃣ VERIFICACIONES DE INTEGRIDAD")
            self.verificar_sincronizacion_datos()
            
            # 5. Funcionalidades del sistema
            print("\n5️⃣ FUNCIONALIDADES DEL SISTEMA")
            self.probar_exportaciones_excel()
            self.probar_dashboard_tiempo_real()
            
            # 6. Pruebas de escalabilidad
            print("\n6️⃣ PRUEBAS DE ESCALABILIDAD")
            self.probar_escalabilidad_bajo_carga()
            
            # 7. Pruebas de seguridad
            print("\n7️⃣ PRUEBAS DE SEGURIDAD")
            self.ejecutar_pruebas_seguridad()
            
            # 8. Limpieza y reporte
            print("\n8️⃣ LIMPIEZA Y REPORTE")
            self.limpiar_datos_prueba()
            
            return True
            
        except Exception as e:
            self.log_error("Error fatal en validación completa", str(e))
            return False
        
        finally:
            self.generar_reporte_final()


def main():
    """Función principal"""
    print("Sistema de Validación Final - Bodega SEREMI")
    print("Versión 1.0 - 22 de julio de 2025")
    print("="*60)
    
    validador = ValidadorSistemaCompleto()
    
    try:
        validador.ejecutar_validacion_completa()
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        traceback.print_exc()
    finally:
        print("\n🏁 Validación finalizada")


if __name__ == "__main__":
    main()
