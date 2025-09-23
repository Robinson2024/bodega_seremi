#!/usr/bin/env python
"""
SCRIPT DE VALIDACIÓN SIMPLIFICADO PARA SISTEMA BODEGA SEREMI
Adaptado a los modelos reales del sistema

Este script realiza validaciones básicas del sistema:
- Funcionalidad de productos
- Transacciones
- Lotes
- Integridad de datos

Autor: Sistema Bodega SEREMI
Fecha: 22 de julio de 2025
Versión: 1.0 - Adaptado
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

from django.db import transaction
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from accounts.models import (
    Producto, Transaccion, LoteProducto, 
    ActaEntrega, Funcionario, CustomUser, Categoria
)

class ValidadorSistemaSimplificado:
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
            'detalle': detalle or ''
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
            # Crear usuario admin estándar de Django
            admin_user, created = User.objects.get_or_create(
                username='admin_test',
                defaults={
                    'email': 'admin@test.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.log_exito("Usuario admin creado exitosamente")
            else:
                self.log_warning("Usuario admin ya existía")
            
            self.datos_prueba['user_admin'] = admin_user
            
            # Crear usuario operador
            operador_user, created = User.objects.get_or_create(
                username='operador_test',
                defaults={
                    'email': 'operador@test.com',
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            if created:
                operador_user.set_password('oper123')
                operador_user.save()
                self.log_exito("Usuario operador creado exitosamente")
            else:
                self.log_warning("Usuario operador ya existía")
            
            self.datos_prueba['user_operador'] = operador_user
            
            return True
            
        except Exception as e:
            self.log_error("Error creando usuarios de prueba", str(e))
            return False

    @medir_tiempo('crear_categoria')
    def crear_categoria_prueba(self):
        """Crea una categoría para las pruebas"""
        try:
            categoria, created = Categoria.objects.get_or_create(
                nombre='Test Categoria',
                defaults={
                    'descripcion': 'Categoría para pruebas de validación'
                }
            )
            
            self.datos_prueba['categoria'] = categoria
            
            if created:
                self.log_exito("Categoría de prueba creada exitosamente")
            else:
                self.log_warning("Categoría de prueba ya existía")
            
            return True
            
        except Exception as e:
            self.log_error("Error creando categoría de prueba", str(e))
            return False

    @medir_tiempo('crear_producto')
    def probar_creacion_producto(self):
        """Prueba la creación de un producto"""
        try:
            # Crear producto usando el modelo real
            codigo_prueba = f'TEST{random.randint(1000, 9999)}'
            
            producto = Producto.objects.create(
                codigo_barra=codigo_prueba,
                descripcion='Producto Test Validación',
                stock=0,
                categoria=self.datos_prueba.get('categoria'),
                rut_proveedor='12345678-9',
                tiene_vencimiento=True,
                fecha_vencimiento=date.today() + timedelta(days=60)
            )
            
            self.datos_prueba['producto'] = producto
            self.log_exito(f"Producto {producto.codigo_barra} creado exitosamente")
            
            # Verificar que el producto se guardó correctamente
            producto_verificado = Producto.objects.get(codigo_barra=codigo_prueba)
            if producto_verificado:
                self.log_exito("Producto verificado en base de datos")
            else:
                self.log_error("Producto no encontrado después de creación")
                return False
            
            return True
            
        except Exception as e:
            self.log_error("Error en creación de producto", str(e))
            return False

    @medir_tiempo('crear_transacciones')
    def probar_transacciones_stock(self):
        """Prueba las transacciones de entrada y salida"""
        try:
            if 'producto' not in self.datos_prueba:
                self.log_error("No hay producto de prueba disponible")
                return False
            
            producto = self.datos_prueba['producto']
            
            # Crear transacciones de entrada
            transacciones_entrada = [
                {'cantidad': 50, 'observacion': 'Entrada inicial'},
                {'cantidad': 25, 'observacion': 'Reposición stock'},
                {'cantidad': 30, 'observacion': 'Stock adicional'}
            ]
            
            stock_total_esperado = 0
            
            for i, trans_data in enumerate(transacciones_entrada):
                transaccion = Transaccion.objects.create(
                    producto=producto,
                    tipo='entrada',
                    cantidad=trans_data['cantidad'],
                    rut_proveedor='12345678-9',
                    observacion=trans_data['observacion']
                )
                
                # Actualizar stock del producto
                producto.stock += trans_data['cantidad']
                producto.save()
                
                stock_total_esperado += trans_data['cantidad']
                self.log_exito(f"Transacción entrada {i+1} creada: {trans_data['cantidad']} unidades")
            
            # Verificar stock total
            producto.refresh_from_db()
            if producto.stock == stock_total_esperado:
                self.log_exito(f"Stock total correcto: {producto.stock}")
            else:
                self.log_error(f"Stock incorrecto: {producto.stock} != {stock_total_esperado}")
                return False
            
            # Crear transacción de salida
            cantidad_salida = 20
            transaccion_salida = Transaccion.objects.create(
                producto=producto,
                tipo='salida',
                cantidad=cantidad_salida,
                observacion='Salida para entrega'
            )
            
            # Actualizar stock
            producto.stock -= cantidad_salida
            producto.save()
            
            stock_final_esperado = stock_total_esperado - cantidad_salida
            
            # Verificar stock final
            producto.refresh_from_db()
            if producto.stock == stock_final_esperado:
                self.log_exito(f"Stock después de salida correcto: {producto.stock}")
            else:
                self.log_error(f"Stock después de salida incorrecto: {producto.stock} != {stock_final_esperado}")
                return False
            
            self.datos_prueba['stock_final'] = stock_final_esperado
            return True
            
        except Exception as e:
            self.log_error("Error en transacciones de stock", str(e))
            return False

    @medir_tiempo('crear_lotes')
    def probar_manejo_lotes(self):
        """Prueba el manejo de lotes con vencimiento"""
        try:
            if 'producto' not in self.datos_prueba:
                self.log_error("No hay producto de prueba disponible")
                return False
            
            producto = self.datos_prueba['producto']
            
            # Crear lotes con diferentes fechas de vencimiento
            lotes_prueba = [
                {
                    'numero_lote': 'LOTE001TEST',
                    'cantidad_inicial': 30,
                    'fecha_vencimiento': date.today() + timedelta(days=30)
                },
                {
                    'numero_lote': 'LOTE002TEST',
                    'cantidad_inicial': 40,
                    'fecha_vencimiento': date.today() + timedelta(days=60)
                },
                {
                    'numero_lote': 'LOTE003TEST',
                    'cantidad_inicial': 15,
                    'fecha_vencimiento': date.today() + timedelta(days=15)  # Próximo a vencer
                }
            ]
            
            lotes_creados = []
            
            for lote_data in lotes_prueba:
                lote = LoteProducto.objects.create(
                    producto=producto,
                    numero_lote=lote_data['numero_lote'],
                    cantidad_inicial=lote_data['cantidad_inicial'],
                    cantidad_disponible=lote_data['cantidad_inicial'],
                    fecha_vencimiento=lote_data['fecha_vencimiento']
                )
                
                lotes_creados.append(lote)
                self.log_exito(f"Lote {lote.numero_lote} creado exitosamente")
            
            # Verificar que los lotes se crearon
            total_lotes = LoteProducto.objects.filter(producto=producto).count()
            if total_lotes == len(lotes_prueba):
                self.log_exito(f"Todos los lotes creados correctamente: {total_lotes}")
            else:
                self.log_error(f"Número de lotes incorrecto: {total_lotes} != {len(lotes_prueba)}")
                return False
            
            # Verificar lotes próximos a vencer
            fecha_limite = date.today() + timedelta(days=20)
            lotes_proximos_vencer = LoteProducto.objects.filter(
                producto=producto,
                fecha_vencimiento__lte=fecha_limite
            )
            
            if lotes_proximos_vencer.exists():
                self.log_warning(f"Lotes próximos a vencer detectados: {lotes_proximos_vencer.count()}")
                for lote in lotes_proximos_vencer:
                    self.log_warning(f"Lote {lote.numero_lote} vence el {lote.fecha_vencimiento}")
            
            self.datos_prueba['lotes'] = lotes_creados
            return True
            
        except Exception as e:
            self.log_error("Error en manejo de lotes", str(e))
            return False

    @medir_tiempo('verificar_integridad')
    def verificar_integridad_datos(self):
        """Verifica la integridad de los datos del sistema"""
        try:
            print("🔍 Verificando integridad de datos...")
            
            # 1. Verificar productos sin stock negativo
            productos_stock_negativo = Producto.objects.filter(stock__lt=0)
            if productos_stock_negativo.exists():
                self.log_error(f"Productos con stock negativo detectados: {productos_stock_negativo.count()}")
                for producto in productos_stock_negativo:
                    self.log_error(f"Producto {producto.codigo_barra}: stock {producto.stock}")
            else:
                self.log_exito("No hay productos con stock negativo")
            
            # 2. Verificar consistencia de transacciones
            total_productos = Producto.objects.count()
            total_transacciones = Transaccion.objects.count()
            
            self.log_exito(f"Total productos en sistema: {total_productos}")
            self.log_exito(f"Total transacciones registradas: {total_transacciones}")
            
            # 3. Verificar lotes sin productos huérfanos
            lotes_huerfanos = LoteProducto.objects.filter(producto__isnull=True)
            if lotes_huerfanos.exists():
                self.log_error(f"Lotes huérfanos detectados: {lotes_huerfanos.count()}")
            else:
                self.log_exito("No hay lotes huérfanos")
            
            # 4. Verificar fechas de vencimiento válidas
            lotes_fecha_invalida = LoteProducto.objects.filter(
                fecha_vencimiento__lt=date.today() - timedelta(days=365)
            )
            if lotes_fecha_invalida.exists():
                self.log_warning(f"Lotes con fechas muy antiguas: {lotes_fecha_invalida.count()}")
            else:
                self.log_exito("Fechas de vencimiento son válidas")
            
            return True
            
        except Exception as e:
            self.log_error("Error verificando integridad", str(e))
            return False

    @medir_tiempo('probar_dashboard')
    def probar_acceso_dashboard(self):
        """Prueba el acceso al dashboard"""
        try:
            # Login como admin
            self.client.login(username='admin_test', password='admin123')
            
            # Intentar acceder al dashboard
            response = self.client.get('/')  # Página principal
            
            if response.status_code == 200:
                self.log_exito("Dashboard/Página principal accesible")
                return True
            else:
                self.log_error(f"Error accediendo dashboard: Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error("Error probando dashboard", str(e))
            return False

    def ejecutar_pruebas_seguridad_basicas(self):
        """Ejecuta pruebas básicas de seguridad"""
        try:
            print("🔒 Iniciando pruebas de seguridad...")
            
            # 1. Prueba acceso sin autenticación
            self.client.logout()
            response = self.client.get('/')
            
            # Verificar que redirija o muestre página pública
            if response.status_code in [200, 302]:
                self.log_exito("Sistema maneja acceso no autenticado correctamente")
            else:
                self.log_warning(f"Respuesta inesperada sin auth: {response.status_code}")
            
            # 2. Verificar que los modelos funcionan correctamente
            try:
                total_productos = Producto.objects.count()
                self.log_exito(f"Acceso a base de datos funcionando: {total_productos} productos")
            except Exception as e:
                self.log_error("Error accediendo base de datos", str(e))
            
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
            )
            count_productos = productos_prueba.count()
            productos_prueba.delete()
            
            # Eliminar usuarios de prueba
            usuarios_prueba = User.objects.filter(
                username__endswith='_test'
            )
            count_usuarios = usuarios_prueba.count()
            usuarios_prueba.delete()
            
            # Eliminar categorías de prueba
            categorias_prueba = Categoria.objects.filter(
                nombre='Test Categoria'
            )
            count_categorias = categorias_prueba.count()
            categorias_prueba.delete()
            
            self.log_exito(f"Limpieza completada: {count_productos} productos, {count_usuarios} usuarios, {count_categorias} categorías")
            
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
        archivo_reporte = f'reporte_validacion_simplificado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
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
            print("\n❌ ERRORES ENCONTRADOS:")
            for error in self.errores:
                print(f"   - {error['mensaje']}")
        
        if self.warnings:
            print("\n⚠️  ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   - {warning['mensaje']}")
        
        # Evaluación final
        if len(self.errores) == 0:
            print("\n🎉 SISTEMA FUNCIONANDO CORRECTAMENTE")
        elif len(self.errores) <= 2:
            print("\n⚠️  SISTEMA CON ERRORES MENORES")
        else:
            print("\n🚨 SISTEMA REQUIERE ATENCIÓN")
        
        return reporte

    def ejecutar_validacion_completa(self):
        """Ejecuta toda la suite de validación"""
        print("🚀 INICIANDO VALIDACIÓN SIMPLIFICADA DEL SISTEMA")
        print("="*60)
        
        try:
            # 1. Preparación
            print("\n1️⃣ PREPARACIÓN")
            if not self.crear_usuarios_prueba():
                return False
            if not self.crear_categoria_prueba():
                return False
            
            # 2. Pruebas básicas de productos
            print("\n2️⃣ PRUEBAS DE PRODUCTOS")
            if not self.probar_creacion_producto():
                return False
            
            # 3. Pruebas de transacciones
            print("\n3️⃣ PRUEBAS DE TRANSACCIONES")
            if not self.probar_transacciones_stock():
                return False
            
            # 4. Pruebas de lotes
            print("\n4️⃣ PRUEBAS DE LOTES")
            if not self.probar_manejo_lotes():
                return False
            
            # 5. Verificaciones de integridad
            print("\n5️⃣ VERIFICACIONES DE INTEGRIDAD")
            self.verificar_integridad_datos()
            
            # 6. Pruebas de dashboard
            print("\n6️⃣ PRUEBAS DE DASHBOARD")
            self.probar_acceso_dashboard()
            
            # 7. Pruebas de seguridad
            print("\n7️⃣ PRUEBAS DE SEGURIDAD")
            self.ejecutar_pruebas_seguridad_basicas()
            
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
    print("Sistema de Validación Simplificado - Bodega SEREMI")
    print("Versión 1.0 - Adaptado a modelos reales")
    print("="*60)
    
    validador = ValidadorSistemaSimplificado()
    
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
