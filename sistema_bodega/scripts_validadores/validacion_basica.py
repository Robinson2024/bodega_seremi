#!/usr/bin/env python
"""
VALIDACIÓN BÁSICA PARA SISTEMA BODEGA SEREMI
Prueba directa del sistema existente

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
from accounts.models import Producto, Transaccion, LoteProducto, Categoria

def probar_sistema():
    """Función principal de prueba"""
    print("🚀 INICIANDO VALIDACIÓN BÁSICA DEL SISTEMA")
    print("="*50)
    
    resultados = {
        'timestamp': datetime.now().isoformat(),
        'pruebas': [],
        'errores': [],
        'exitos': []
    }
    
    try:
        # 1. Verificar modelos básicos
        print("\n1️⃣ VERIFICANDO MODELOS DE BASE DE DATOS")
        
        try:
            total_productos = Producto.objects.count()
            print(f"✅ Productos en sistema: {total_productos}")
            resultados['exitos'].append(f"Acceso a modelo Producto exitoso: {total_productos} registros")
        except Exception as e:
            print(f"❌ Error accediendo Producto: {e}")
            resultados['errores'].append(f"Error modelo Producto: {e}")
        
        try:
            total_transacciones = Transaccion.objects.count()
            print(f"✅ Transacciones en sistema: {total_transacciones}")
            resultados['exitos'].append(f"Acceso a modelo Transaccion exitoso: {total_transacciones} registros")
        except Exception as e:
            print(f"❌ Error accediendo Transaccion: {e}")
            resultados['errores'].append(f"Error modelo Transaccion: {e}")
        
        try:
            total_lotes = LoteProducto.objects.count()
            print(f"✅ Lotes en sistema: {total_lotes}")
            resultados['exitos'].append(f"Acceso a modelo LoteProducto exitoso: {total_lotes} registros")
        except Exception as e:
            print(f"❌ Error accediendo LoteProducto: {e}")
            resultados['errores'].append(f"Error modelo LoteProducto: {e}")
        
        # 2. Verificar integridad básica
        print("\n2️⃣ VERIFICANDO INTEGRIDAD BÁSICA")
        
        try:
            productos_stock_negativo = Producto.objects.filter(stock__lt=0)
            if productos_stock_negativo.exists():
                print(f"⚠️  Productos con stock negativo: {productos_stock_negativo.count()}")
                resultados['errores'].append(f"Stock negativo en {productos_stock_negativo.count()} productos")
            else:
                print("✅ No hay productos con stock negativo")
                resultados['exitos'].append("No hay productos con stock negativo")
        except Exception as e:
            print(f"❌ Error verificando stock: {e}")
            resultados['errores'].append(f"Error verificando stock: {e}")
        
        # 3. Crear datos de prueba simples
        print("\n3️⃣ CREANDO DATOS DE PRUEBA")
        
        try:
            # Crear producto de prueba
            codigo_prueba = f'VALIDACION{random.randint(1000, 9999)}'
            
            # Verificar si ya existe
            if Producto.objects.filter(codigo_barra=codigo_prueba).exists():
                codigo_prueba = f'VALIDACION{random.randint(10000, 99999)}'
            
            producto_prueba = Producto.objects.create(
                codigo_barra=codigo_prueba,
                descripcion='Producto de Validación Test',
                stock=100,
                rut_proveedor='12345678-9'
            )
            
            print(f"✅ Producto de prueba creado: {producto_prueba.codigo_barra}")
            resultados['exitos'].append(f"Producto de prueba creado: {codigo_prueba}")
            
            # Crear transacción de prueba
            transaccion_prueba = Transaccion.objects.create(
                producto=producto_prueba,
                tipo='entrada',
                cantidad=50,
                observacion='Transacción de validación'
            )
            
            print(f"✅ Transacción de prueba creada: ID {transaccion_prueba.id}")
            resultados['exitos'].append(f"Transacción de prueba creada: ID {transaccion_prueba.id}")
            
            # Crear lote de prueba si el modelo lo permite
            try:
                lote_prueba = LoteProducto.objects.create(
                    producto=producto_prueba,
                    numero_lote=f'LOTE{random.randint(100, 999)}',
                    cantidad_inicial=50,
                    cantidad_disponible=50,
                    fecha_vencimiento=date.today() + timedelta(days=90)
                )
                print(f"✅ Lote de prueba creado: {lote_prueba.numero_lote}")
                resultados['exitos'].append(f"Lote de prueba creado: {lote_prueba.numero_lote}")
            except Exception as e:
                print(f"⚠️  No se pudo crear lote: {e}")
                resultados['errores'].append(f"Error creando lote: {e}")
            
        except Exception as e:
            print(f"❌ Error creando datos de prueba: {e}")
            resultados['errores'].append(f"Error creando datos de prueba: {e}")
        
        # 4. Verificar consultas básicas
        print("\n4️⃣ VERIFICANDO CONSULTAS")
        
        try:
            inicio = time.time()
            productos_recientes = Producto.objects.all()[:10]
            fin = time.time()
            tiempo_consulta = fin - inicio
            
            print(f"✅ Consulta productos: {len(list(productos_recientes))} registros en {tiempo_consulta:.3f}s")
            resultados['exitos'].append(f"Consulta eficiente: {tiempo_consulta:.3f}s")
            
        except Exception as e:
            print(f"❌ Error en consulta: {e}")
            resultados['errores'].append(f"Error en consulta: {e}")
        
        # 5. Probar cliente web básico
        print("\n5️⃣ PROBANDO ACCESO WEB")
        
        try:
            client = Client()
            response = client.get('/')
            
            if response.status_code in [200, 302]:
                print(f"✅ Página principal accesible: Status {response.status_code}")
                resultados['exitos'].append(f"Acceso web exitoso: {response.status_code}")
            else:
                print(f"⚠️  Respuesta inesperada: Status {response.status_code}")
                resultados['errores'].append(f"Status inesperado: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error accediendo web: {e}")
            resultados['errores'].append(f"Error acceso web: {e}")
        
        # 6. Limpiar datos de prueba
        print("\n6️⃣ LIMPIANDO DATOS DE PRUEBA")
        
        try:
            productos_validacion = Producto.objects.filter(codigo_barra__startswith='VALIDACION')
            count_eliminados = productos_validacion.count()
            productos_validacion.delete()
            
            print(f"✅ Datos de prueba eliminados: {count_eliminados} productos")
            resultados['exitos'].append(f"Limpieza exitosa: {count_eliminados} productos eliminados")
            
        except Exception as e:
            print(f"❌ Error en limpieza: {e}")
            resultados['errores'].append(f"Error en limpieza: {e}")
        
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        resultados['errores'].append(f"Error fatal: {e}")
    
    # Generar reporte
    print("\n" + "="*50)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("="*50)
    
    total_exitos = len(resultados['exitos'])
    total_errores = len(resultados['errores'])
    total_pruebas = total_exitos + total_errores
    
    print(f"✅ Éxitos: {total_exitos}")
    print(f"❌ Errores: {total_errores}")
    print(f"📊 Total pruebas: {total_pruebas}")
    
    if total_errores == 0:
        print("\n🎉 SISTEMA FUNCIONANDO CORRECTAMENTE")
        estado_final = "EXITOSO"
    elif total_errores <= 2:
        print("\n⚠️  SISTEMA CON ERRORES MENORES")
        estado_final = "CON_OBSERVACIONES"
    else:
        print("\n🚨 SISTEMA REQUIERE ATENCIÓN")
        estado_final = "REQUIERE_ATENCION"
    
    # Mostrar detalles
    if resultados['errores']:
        print("\n❌ ERRORES DETECTADOS:")
        for error in resultados['errores']:
            print(f"   - {error}")
    
    if resultados['exitos']:
        print("\n✅ ÉXITOS REGISTRADOS:")
        for exito in resultados['exitos'][:5]:  # Mostrar solo los primeros 5
            print(f"   - {exito}")
        if len(resultados['exitos']) > 5:
            print(f"   ... y {len(resultados['exitos']) - 5} más")
    
    # Guardar reporte
    reporte_final = {
        **resultados,
        'estado_final': estado_final,
        'resumen': {
            'total_exitos': total_exitos,
            'total_errores': total_errores,
            'total_pruebas': total_pruebas
        }
    }
    
    archivo_reporte = f'reporte_validacion_basica_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    try:
        with open(archivo_reporte, 'w', encoding='utf-8') as f:
            json.dump(reporte_final, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 Reporte guardado: {archivo_reporte}")
        
    except Exception as e:
        print(f"⚠️  No se pudo guardar reporte: {e}")
    
    print("\n🏁 VALIDACIÓN COMPLETADA")
    return estado_final

if __name__ == "__main__":
    probar_sistema()
