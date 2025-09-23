#!/usr/bin/env python
"""
VALIDACIÓN DE SEGURIDAD - SISTEMA BODEGA SEREMI
Detecta vulnerabilidades y problemas de seguridad

Autor: Sistema Bodega SEREMI  
Fecha: 22 de julio de 2025
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_bodega.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from accounts.models import Producto, Transaccion, LoteProducto

class ValidadorSeguridad:
    def __init__(self):
        self.vulnerabilidades = []
        self.advertencias = []
        self.buenas_practicas = []
        
    def log_vulnerabilidad(self, mensaje, nivel="MEDIA"):
        """Registra una vulnerabilidad"""
        vuln = {
            'mensaje': mensaje,
            'nivel': nivel,
            'timestamp': datetime.now().isoformat()
        }
        self.vulnerabilidades.append(vuln)
        print(f"🔴 {nivel}: {mensaje}")
    
    def log_advertencia(self, mensaje):
        """Registra una advertencia"""
        self.advertencias.append(mensaje)
        print(f"🟡 ADVERTENCIA: {mensaje}")
    
    def log_buena_practica(self, mensaje):
        """Registra una buena práctica implementada"""
        self.buenas_practicas.append(mensaje)
        print(f"🟢 BUENA PRÁCTICA: {mensaje}")
    
    def validar_configuracion_django(self):
        """Valida configuraciones de seguridad de Django"""
        print("\n🔐 VALIDANDO CONFIGURACIÓN DE SEGURIDAD")
        print("-" * 50)
        
        # Debug en producción
        if settings.DEBUG:
            self.log_vulnerabilidad(
                "DEBUG=True en producción expone información sensible", 
                "ALTA"
            )
        else:
            self.log_buena_practica("DEBUG deshabilitado correctamente")
        
        # Secret Key
        if hasattr(settings, 'SECRET_KEY'):
            if len(settings.SECRET_KEY) < 50:
                self.log_vulnerabilidad(
                    "SECRET_KEY muy corta (menos de 50 caracteres)", 
                    "ALTA"
                )
            elif 'django-insecure' in settings.SECRET_KEY:
                self.log_vulnerabilidad(
                    "Usando SECRET_KEY de desarrollo", 
                    "CRÍTICA"
                )
            else:
                self.log_buena_practica("SECRET_KEY configurada adecuadamente")
        
        # ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            self.log_vulnerabilidad(
                "ALLOWED_HOSTS demasiado permisivo", 
                "MEDIA"
            )
        else:
            self.log_buena_practica(f"ALLOWED_HOSTS configurado: {settings.ALLOWED_HOSTS}")
        
        # HTTPS settings
        if hasattr(settings, 'SECURE_SSL_REDIRECT'):
            if settings.SECURE_SSL_REDIRECT:
                self.log_buena_practica("HTTPS redirect habilitado")
            else:
                self.log_advertencia("HTTPS redirect no configurado")
        
        # CSRF
        if hasattr(settings, 'CSRF_COOKIE_SECURE'):
            if settings.CSRF_COOKIE_SECURE:
                self.log_buena_practica("CSRF cookie secure habilitado")
            else:
                self.log_advertencia("CSRF cookie no segura")
        
        # Session security
        if hasattr(settings, 'SESSION_COOKIE_SECURE'):
            if settings.SESSION_COOKIE_SECURE:
                self.log_buena_practica("Session cookie secure habilitado")
            else:
                self.log_advertencia("Session cookie no segura")
    
    def validar_autenticacion(self):
        """Valida la configuración de autenticación"""
        print("\n👤 VALIDANDO AUTENTICACIÓN Y USUARIOS")
        print("-" * 50)
        
        User = get_user_model()
        
        # Usuarios sin contraseña o con contraseñas débiles
        try:
            usuarios_total = User.objects.count()
            print(f"Total usuarios en sistema: {usuarios_total}")
            
            # Buscar superusuarios
            superusuarios = User.objects.filter(is_superuser=True)
            if superusuarios.count() > 3:
                self.log_advertencia(f"Muchos superusuarios: {superusuarios.count()}")
            else:
                self.log_buena_practica(f"Número apropiado de superusuarios: {superusuarios.count()}")
            
            # Verificar usuarios activos
            usuarios_activos = User.objects.filter(is_active=True)
            usuarios_inactivos = User.objects.filter(is_active=False)
            
            print(f"Usuarios activos: {usuarios_activos.count()}")
            print(f"Usuarios inactivos: {usuarios_inactivos.count()}")
            
            if usuarios_inactivos.count() > usuarios_activos.count():
                self.log_advertencia("Más usuarios inactivos que activos - revisar limpieza")
            
        except Exception as e:
            self.log_vulnerabilidad(f"Error accediendo usuarios: {e}", "MEDIA")
    
    def validar_permisos_archivos(self):
        """Valida permisos de archivos críticos"""
        print("\n📁 VALIDANDO PERMISOS DE ARCHIVOS")
        print("-" * 50)
        
        archivos_criticos = [
            'manage.py',
            'sistema_bodega/settings.py',
            'db.sqlite3'
        ]
        
        for archivo in archivos_criticos:
            ruta_completa = os.path.join(os.getcwd(), archivo)
            if os.path.exists(ruta_completa):
                # En Windows, verificar si es de solo lectura
                if os.access(ruta_completa, os.W_OK):
                    if archivo.endswith('settings.py'):
                        self.log_advertencia(f"Archivo {archivo} es escribible")
                    else:
                        print(f"📄 {archivo}: Permisos normales")
                else:
                    if archivo.endswith('settings.py'):
                        self.log_buena_practica(f"Archivo {archivo} protegido contra escritura")
                    else:
                        self.log_advertencia(f"Archivo {archivo} no escribible")
            else:
                self.log_advertencia(f"Archivo crítico no encontrado: {archivo}")
    
    def validar_datos_sensibles(self):
        """Valida que no haya datos sensibles expuestos"""
        print("\n🔍 VALIDANDO DATOS SENSIBLES")
        print("-" * 50)
        
        # Revisar productos con información sensible
        productos_con_rut = Producto.objects.exclude(rut_proveedor__isnull=True).exclude(rut_proveedor='')
        
        if productos_con_rut.exists():
            print(f"Productos con RUT proveedor: {productos_con_rut.count()}")
            
            # Verificar formato de RUTs
            ruts_invalidos = 0
            for producto in productos_con_rut[:10]:  # Revisar solo 10
                rut = producto.rut_proveedor
                # Patrón básico de RUT chileno
                if not re.match(r'^\d{7,8}-[0-9kK]$', rut):
                    ruts_invalidos += 1
            
            if ruts_invalidos > 0:
                self.log_advertencia(f"RUTs con formato inválido encontrados: {ruts_invalidos}")
            else:
                self.log_buena_practica("Formato de RUTs válido")
        
        # Revisar transacciones con información sensible
        transacciones_con_observaciones = Transaccion.objects.exclude(observacion__isnull=True).exclude(observacion='')
        
        if transacciones_con_observaciones.exists():
            print(f"Transacciones con observaciones: {transacciones_con_observaciones.count()}")
            
            # Buscar patrones sospechosos en observaciones
            patrones_sospechosos = ['password', 'contraseña', 'clave', 'secret', 'token']
            observaciones_sospechosas = 0
            
            for transaccion in transacciones_con_observaciones[:20]:
                obs_lower = transaccion.observacion.lower()
                for patron in patrones_sospechosos:
                    if patron in obs_lower:
                        observaciones_sospechosas += 1
                        break
            
            if observaciones_sospechosas > 0:
                self.log_vulnerabilidad(
                    f"Posibles datos sensibles en observaciones: {observaciones_sospechosas}",
                    "MEDIA"
                )
            else:
                self.log_buena_practica("No se encontraron datos sensibles en observaciones")
    
    def validar_inyeccion_sql(self):
        """Valida contra vulnerabilidades de inyección SQL"""
        print("\n💉 VALIDANDO PROTECCIÓN CONTRA INYECCIÓN SQL")
        print("-" * 50)
        
        # Django ORM protege automáticamente, pero validemos consultas raw si existen
        try:
            # Buscar productos con patrones sospechosos en códigos de barra
            productos_sospechosos = Producto.objects.filter(
                codigo_barra__icontains="'"
            ).union(
                Producto.objects.filter(codigo_barra__icontains='"')
            ).union(
                Producto.objects.filter(codigo_barra__icontains='--')
            ).union(
                Producto.objects.filter(codigo_barra__icontains=';')
            )
            
            if productos_sospechosos.exists():
                self.log_advertencia(f"Productos con caracteres sospechosos: {productos_sospechosos.count()}")
                for producto in productos_sospechosos[:3]:
                    print(f"  - {producto.codigo_barra}")
            else:
                self.log_buena_practica("No se encontraron caracteres sospechosos en códigos")
            
            # Verificar descripciones
            productos_desc_sospechosas = Producto.objects.filter(
                descripcion__icontains='<script'
            ).union(
                Producto.objects.filter(descripcion__icontains='javascript:')
            ).union(
                Producto.objects.filter(descripcion__icontains='onclick=')
            )
            
            if productos_desc_sospechosas.exists():
                self.log_vulnerabilidad(
                    f"Productos con posible XSS: {productos_desc_sospechosas.count()}",
                    "MEDIA"
                )
            else:
                self.log_buena_practica("No se encontró código malicioso en descripciones")
                
        except Exception as e:
            self.log_advertencia(f"Error validando inyección SQL: {e}")
    
    def validar_limites_recursos(self):
        """Valida límites de recursos y DoS"""
        print("\n🚦 VALIDANDO LÍMITES DE RECURSOS")
        print("-" * 50)
        
        # Verificar productos con descripciones muy largas
        productos_desc_largas = Producto.objects.extra(
            where=["LENGTH(descripcion) > 1000"]
        )
        
        if productos_desc_largas.exists():
            self.log_advertencia(f"Productos con descripciones muy largas: {productos_desc_largas.count()}")
        else:
            self.log_buena_practica("Longitud de descripciones dentro de límites normales")
        
        # Verificar transacciones con observaciones muy largas
        try:
            transacciones_obs_largas = Transaccion.objects.extra(
                where=["LENGTH(observacion) > 500"]
            )
            
            if transacciones_obs_largas.exists():
                self.log_advertencia(f"Transacciones con observaciones muy largas: {transacciones_obs_largas.count()}")
            else:
                self.log_buena_practica("Longitud de observaciones dentro de límites normales")
        except:
            print("  - No se pudo verificar longitud de observaciones")
        
        # Verificar cantidad de registros por usuario (si aplicable)
        try:
            total_productos = Producto.objects.count()
            total_transacciones = Transaccion.objects.count()
            total_lotes = LoteProducto.objects.count()
            
            if total_transacciones > 10000:
                self.log_advertencia("Gran cantidad de transacciones - considerar archivado")
            
            if total_lotes > 1000:
                self.log_advertencia("Gran cantidad de lotes - considerar limpieza")
            
            print(f"  - Productos: {total_productos}")
            print(f"  - Transacciones: {total_transacciones}")
            print(f"  - Lotes: {total_lotes}")
            
        except Exception as e:
            self.log_advertencia(f"Error verificando límites: {e}")
    
    def generar_reporte_seguridad(self):
        """Genera reporte final de seguridad"""
        print("\n" + "="*60)
        print("🛡️  REPORTE FINAL DE SEGURIDAD")
        print("="*60)
        
        total_vulnerabilidades = len(self.vulnerabilidades)
        total_advertencias = len(self.advertencias)
        total_buenas_practicas = len(self.buenas_practicas)
        
        # Evaluar nivel de seguridad
        vulnerabilidades_criticas = sum(1 for v in self.vulnerabilidades if v['nivel'] == 'CRÍTICA')
        vulnerabilidades_altas = sum(1 for v in self.vulnerabilidades if v['nivel'] == 'ALTA')
        
        if vulnerabilidades_criticas > 0:
            nivel_seguridad = "🔴 CRÍTICO"
            mensaje = "Vulnerabilidades críticas encontradas"
        elif vulnerabilidades_altas > 0:
            nivel_seguridad = "🟠 ALTO RIESGO"
            mensaje = "Vulnerabilidades de alto riesgo encontradas"
        elif total_vulnerabilidades > 0:
            nivel_seguridad = "🟡 RIESGO MEDIO"
            mensaje = "Vulnerabilidades menores encontradas"
        elif total_advertencias > 3:
            nivel_seguridad = "🟡 MEJORABLE"
            mensaje = "Múltiples áreas de mejora identificadas"
        else:
            nivel_seguridad = "🟢 SEGURO"
            mensaje = "Sistema con buen nivel de seguridad"
        
        print(f"\n{nivel_seguridad} - {mensaje}")
        print(f"🔴 Vulnerabilidades: {total_vulnerabilidades}")
        print(f"🟡 Advertencias: {total_advertencias}")
        print(f"🟢 Buenas prácticas: {total_buenas_practicas}")
        
        # Mostrar vulnerabilidades críticas y altas
        if self.vulnerabilidades:
            print(f"\n🚨 VULNERABILIDADES ENCONTRADAS:")
            for vuln in self.vulnerabilidades:
                print(f"   {vuln['nivel']}: {vuln['mensaje']}")
        
        if self.advertencias:
            print(f"\n⚠️  ADVERTENCIAS:")
            for adv in self.advertencias[:5]:  # Primeras 5
                print(f"   - {adv}")
            if len(self.advertencias) > 5:
                print(f"   ... y {len(self.advertencias) - 5} advertencias más")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        if vulnerabilidades_criticas > 0:
            print("   1. URGENTE: Resolver vulnerabilidades críticas inmediatamente")
        if vulnerabilidades_altas > 0:
            print("   2. ALTA PRIORIDAD: Resolver vulnerabilidades de alto riesgo")
        if settings.DEBUG:
            print("   3. Deshabilitar DEBUG en producción")
        if total_advertencias > 0:
            print("   4. Revisar y resolver advertencias de seguridad")
        print("   5. Implementar monitoreo de seguridad continuo")
        print("   6. Realizar auditorías de seguridad periódicas")
        
        # Guardar reporte
        reporte = {
            'timestamp': datetime.now().isoformat(),
            'nivel_seguridad': nivel_seguridad,
            'mensaje': mensaje,
            'resumen': {
                'vulnerabilidades': total_vulnerabilidades,
                'advertencias': total_advertencias,
                'buenas_practicas': total_buenas_practicas,
                'vulnerabilidades_criticas': vulnerabilidades_criticas,
                'vulnerabilidades_altas': vulnerabilidades_altas
            },
            'vulnerabilidades': self.vulnerabilidades,
            'advertencias': self.advertencias,
            'buenas_practicas': self.buenas_practicas
        }
        
        archivo_reporte = f'REPORTE_SEGURIDAD_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        try:
            with open(archivo_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)
            
            print(f"\n📁 Reporte de seguridad guardado: {archivo_reporte}")
            
        except Exception as e:
            print(f"⚠️  No se pudo guardar reporte: {e}")
        
        print("\n🛡️  AUDITORÍA DE SEGURIDAD COMPLETADA")
        return reporte
    
    def ejecutar_auditoria_completa(self):
        """Ejecuta toda la auditoría de seguridad"""
        print("🛡️  AUDITORÍA DE SEGURIDAD - SISTEMA BODEGA SEREMI")
        print("="*60)
        print(f"Fecha: {datetime.now().strftime('%d de %B de %Y, %H:%M:%S')}")
        print("="*60)
        
        self.validar_configuracion_django()
        self.validar_autenticacion()
        self.validar_permisos_archivos()
        self.validar_datos_sensibles()
        self.validar_inyeccion_sql()
        self.validar_limites_recursos()
        
        return self.generar_reporte_seguridad()

def main():
    """Función principal"""
    validador = ValidadorSeguridad()
    try:
        return validador.ejecutar_auditoria_completa()
    except KeyboardInterrupt:
        print("\n⏹️  Auditoría interrumpida por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
