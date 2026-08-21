"""Suite QA: sincronización de stock, roles, actas y carga esperada."""
import time
from datetime import date, timedelta
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.db.models import Sum
from django.test import Client, TestCase
from django.urls import reverse

from accounts.forms import AgregarStockConVencimientoForm
from accounts.models import (
    ActaEntrega,
    CustomUser,
    LoteProducto,
    Producto,
    Transaccion,
)


def _kardex(producto):
    entradas = Transaccion.objects.filter(producto=producto, tipo='entrada').aggregate(
        s=Sum('cantidad')
    )['s'] or 0
    salidas = Transaccion.objects.filter(producto=producto, tipo='salida').aggregate(
        s=Sum('cantidad')
    )['s'] or 0
    return entradas, salidas, entradas - salidas


def _assert_invariante(test, producto):
    producto.refresh_from_db()
    entradas, salidas, neto = _kardex(producto)
    test.assertEqual(
        producto.stock, neto,
        f'{producto.codigo_barra}: stock Listar ({producto.stock}) != entradas-salidas ({neto})',
    )
    saldos = Transaccion.simular_saldos(producto)
    saldo_final = saldos[-1][1] if saldos else 0
    test.assertEqual(
        saldo_final, producto.stock,
        f'{producto.codigo_barra}: saldo bincard ({saldo_final}) != stock ({producto.stock})',
    )
    if producto.tiene_vencimiento:
        total_lotes = producto.lotes.aggregate(s=Sum('stock'))['s'] or 0
        test.assertEqual(
            total_lotes, producto.stock,
            f'{producto.codigo_barra}: suma lotes ({total_lotes}) != stock ({producto.stock})',
        )


def _usuario(rut, nombre, grupo_nombre, is_staff=False):
    user = CustomUser.objects.create_user(
        username=rut,
        rut=rut,
        password='test123',
        nombre=nombre,
        is_staff=is_staff,
    )
    user.groups.add(Group.objects.get(name=grupo_nombre))
    return user


class SincronizacionStockTests(TestCase):
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            username='211111111',
            rut='211111111',
            password='test123',
            nombre='QA Bodega',
        )
        self.usuario.groups.add(Group.objects.get(name='Usuario de Bodega'))
        self.vence = date.today() + timedelta(days=120)

    def test_dos_ingresos_mismo_lote_no_duplican_stock(self):
        """Dos filas de bincard en Lote #1: el stock es la suma, no un lote extra."""
        producto = Producto.objects.create(
            codigo_barra='800001',
            descripcion='Insumo mismo lote',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=self.vence,
        )
        lote = producto.agregar_lote(50, self.vence)
        Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=50, lote=lote,
            observacion='Lote #1 - Vence: %s' % self.vence,
        )
        lote.stock += 40
        lote.save()
        Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=40, lote=lote,
            observacion='Lote #1 - Vence: %s' % self.vence,
        )
        producto.refresh_from_db()
        self.assertEqual(producto.lotes.count(), 1)
        self.assertEqual(producto.stock, 90)
        self.assertEqual(Transaccion.objects.filter(producto=producto, tipo='entrada').count(), 2)
        _assert_invariante(self, producto)

    def test_formulario_crea_lotes_secuenciales_y_el_stock_cuadra(self):
        producto = Producto.objects.create(
            codigo_barra='800002',
            descripcion='Insumo lotes nuevos',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=self.vence,
        )
        form1 = AgregarStockConVencimientoForm(
            data={
                'cantidad': 50,
                'tiene_vencimiento_nuevo': 'on',
                'fecha_vencimiento': self.vence.isoformat(),
            },
            producto=producto,
        )
        self.assertTrue(form1.is_valid(), form1.errors)
        form1.agregar_stock_a_producto(producto)

        form2 = AgregarStockConVencimientoForm(
            data={
                'cantidad': 40,
                'tiene_vencimiento_nuevo': 'on',
                'fecha_vencimiento': (self.vence + timedelta(days=30)).isoformat(),
            },
            producto=producto,
        )
        self.assertTrue(form2.is_valid(), form2.errors)
        form2.agregar_stock_a_producto(producto)

        producto.refresh_from_db()
        self.assertEqual(producto.lotes.count(), 2)
        self.assertEqual(producto.stock, 90)
        _assert_invariante(self, producto)

    def test_salida_fifo_alinea_listar_bincard_lotes_y_kardex(self):
        producto = Producto.objects.create(
            codigo_barra='800003',
            descripcion='Insumo FIFO',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=self.vence,
        )
        lote1 = producto.agregar_lote(50, self.vence)
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=50, lote=lote1)
        lote2 = producto.agregar_lote(40, self.vence + timedelta(days=40))
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=40, lote=lote2)
        lote3 = producto.agregar_lote(100, self.vence + timedelta(days=80))
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=100, lote=lote3)

        self.assertTrue(producto.reducir_stock_fifo(20))
        Transaccion.objects.create(producto=producto, tipo='salida', cantidad=20)
        lote1.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(lote1.stock, 30)
        self.assertEqual(producto.stock, 170)
        _assert_invariante(self, producto)

    def test_vistas_listar_y_bincard_muestran_el_mismo_stock(self):
        producto = Producto.objects.create(
            codigo_barra='800004',
            descripcion='Gel QA vistas',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=self.vence,
        )
        lote = producto.agregar_lote(191, self.vence)
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=191, lote=lote)
        self.assertTrue(producto.reducir_stock_fifo(20))
        Transaccion.objects.create(producto=producto, tipo='salida', cantidad=20)

        client = Client()
        client.force_login(self.usuario)

        listar = client.get(reverse('listar-productos'), {'codigo_barra': '800004'})
        self.assertEqual(listar.status_code, 200)
        visto = listar.context['page_obj'].object_list[0]
        self.assertEqual(visto.stock, 171)

        bincard = client.get(reverse('bincard-historial', args=['800004']))
        self.assertEqual(bincard.status_code, 200)
        self.assertEqual(bincard.context['producto'].stock, 171)
        self.assertEqual(bincard.context['total_entradas'], 191)
        self.assertEqual(bincard.context['total_salidas'], 20)
        self.assertEqual(bincard.context['saldo_kardex'], 171)
        _assert_invariante(self, producto)

    def test_control_vencimientos_usa_stock_de_lotes_activos(self):
        producto = Producto.objects.create(
            codigo_barra='800005',
            descripcion='Vence QA',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=self.vence,
        )
        lote = producto.agregar_lote(12, self.vence)
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=12, lote=lote)

        client = Client()
        client.force_login(self.usuario)
        resp = client.get(reverse('control-vencimientos'), {'busqueda': '800005'})
        self.assertEqual(resp.status_code, 200)
        encontrados = [
            item['producto'] for item in resp.context['productos'].object_list
            if item['producto'].codigo_barra == '800005'
        ]
        self.assertEqual(len(encontrados), 1)
        self.assertEqual(encontrados[0].stock, 12)

    def test_listar_solo_resincroniza_la_pagina_visible(self):
        """Riesgo conocido: stock desalineado fuera de la página no se corrige al listar."""
        for i in range(22):
            p = Producto.objects.create(
                codigo_barra=f'8100{i:02d}',
                descripcion=f'Desync {i}',
                stock=0,
                tiene_vencimiento=True,
                fecha_vencimiento=self.vence,
            )
            LoteProducto.objects.create(
                producto=p, numero_lote=1, fecha_vencimiento=self.vence, stock=5,
            )
            Producto.objects.filter(pk=p.pk).update(stock=99)

        client = Client()
        client.force_login(self.usuario)
        resp = client.get(reverse('listar-productos'))
        self.assertEqual(resp.status_code, 200)
        visibles = list(resp.context['page_obj'].object_list)
        self.assertEqual(len(visibles), 20)
        for producto in visibles:
            producto.refresh_from_db()
            self.assertEqual(producto.stock, 5)

        ocultos = Producto.objects.filter(codigo_barra__startswith='8100').exclude(
            pk__in=[p.pk for p in visibles]
        )
        self.assertEqual(ocultos.count(), 2)
        self.assertTrue(all(p.stock == 99 for p in ocultos))


class RolesAccesoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.bodega = _usuario('221111111', 'Bodega', 'Usuario de Bodega')
        self.auditor = _usuario('331111111', 'Auditor', 'Auditor')
        self.admin = _usuario('441111111', 'Admin', 'Administrador')
        self.admin_auditor = _usuario(
            '551111111', 'Admin Auditor', 'Administrador Auditor', is_staff=True,
        )

    def test_helpers_de_rol(self):
        self.assertTrue(self.bodega.puede_operar_bodega())
        self.assertFalse(self.bodega.puede_corregir_ingreso())
        self.assertFalse(self.bodega.puede_panel_admin())

        self.assertFalse(self.auditor.puede_operar_bodega())
        self.assertFalse(self.auditor.puede_corregir_ingreso())
        self.assertFalse(self.auditor.puede_panel_admin())

        self.assertTrue(self.admin.es_admin_operativo())
        self.assertTrue(self.admin.puede_operar_bodega())
        self.assertFalse(self.admin.puede_corregir_ingreso())
        self.assertFalse(self.admin.puede_panel_admin())

        self.assertTrue(self.admin_auditor.puede_corregir_ingreso())
        self.assertTrue(self.admin_auditor.puede_panel_admin())
        self.assertTrue(self.admin_auditor.es_admin_operativo())

    def test_corregir_ingreso_solo_administrador_auditor(self):
        url = reverse('corregir-ingreso')
        for user in (self.bodega, self.auditor, self.admin):
            self.client.force_login(user)
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, user.nombre)
            self.assertEqual(resp.url, reverse('home'))

        self.client.force_login(self.admin_auditor)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_usuarios_requiere_permiso_de_gestion(self):
        url = reverse('listar-usuarios')
        self.client.force_login(self.bodega)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.auditor)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.admin_auditor)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_salida_bloqueada_para_auditor(self):
        url = reverse('salida-productos')
        self.client.force_login(self.auditor)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))
        self.client.force_login(self.bodega)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_panel_admin_solo_staff(self):
        self.client.force_login(self.admin)
        resp = self.client.get('/admin/')
        self.assertIn(resp.status_code, (302, 403))
        self.client.force_login(self.admin_auditor)
        resp = self.client.get('/admin/')
        self.assertEqual(resp.status_code, 200)


class ActasUnicasTests(TestCase):
    def test_no_permite_el_mismo_producto_dos_veces_en_un_acta(self):
        p1 = Producto.objects.create(codigo_barra='820001', descripcion='A', stock=10)
        p2 = Producto.objects.create(codigo_barra='820002', descripcion='B', stock=10)
        ActaEntrega.objects.create(
            numero_acta=7, departamento='Epidemiologia', producto=p1, cantidad=2,
        )
        ActaEntrega.objects.create(
            numero_acta=7, departamento='Epidemiologia', producto=p2, cantidad=3,
        )
        with self.assertRaises(IntegrityError):
            ActaEntrega.objects.create(
                numero_acta=7, departamento='Epidemiologia', producto=p1, cantidad=1,
            )

    def test_salida_con_acta_mantiene_invariante(self):
        vence = date.today() + timedelta(days=90)
        producto = Producto.objects.create(
            codigo_barra='820003',
            descripcion='Salida acta',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=vence,
        )
        lote = producto.agregar_lote(30, vence)
        Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=30, lote=lote)
        acta = ActaEntrega.objects.create(
            numero_acta=8, departamento='Bodega', producto=producto, cantidad=11,
        )
        self.assertTrue(producto.reducir_stock_fifo(11))
        Transaccion.objects.create(
            producto=producto, tipo='salida', cantidad=11, acta_entrega=acta,
        )
        _assert_invariante(self, producto)
        self.assertEqual(producto.stock, 19)


class CargaVolumenTests(TestCase):
    """Carga esperada: ~3000 insumos y ~5000 actas. No toca la SQLite real."""

    @classmethod
    def setUpTestData(cls):
        vence = date.today() + timedelta(days=200)
        productos = []
        for i in range(3000):
            con_vto = i < 500
            productos.append(Producto(
                codigo_barra=str(300000 + i),
                descripcion=f'Insumo carga {i:04d}',
                stock=10,
                tiene_vencimiento=con_vto,
                fecha_vencimiento=vence if con_vto else None,
            ))
        Producto.objects.bulk_create(productos, batch_size=500)

        lotes = [
            LoteProducto(
                producto_id=prod.pk,
                numero_lote=1,
                fecha_vencimiento=vence,
                stock=10,
            )
            for prod in Producto.objects.filter(tiene_vencimiento=True)
        ]
        LoteProducto.objects.bulk_create(lotes, batch_size=250)

        ids = list(Producto.objects.order_by('codigo_barra').values_list('id', flat=True)[:50])
        actas = []
        txs = []
        for numero in range(1, 101):
            for producto_id in ids:
                actas.append(ActaEntrega(
                    numero_acta=numero,
                    departamento='Carga QA',
                    producto_id=producto_id,
                    cantidad=1,
                ))
        ActaEntrega.objects.bulk_create(actas, batch_size=500)
        for acta in ActaEntrega.objects.all().iterator():
            txs.append(Transaccion(
                producto_id=acta.producto_id,
                tipo='salida',
                cantidad=acta.cantidad,
                acta_entrega_id=acta.pk,
            ))
        Transaccion.objects.bulk_create(txs, batch_size=500)

        cls.usuario = CustomUser.objects.create_user(
            username='661111111',
            rut='661111111',
            password='test123',
            nombre='Carga QA',
        )
        cls.usuario.groups.add(Group.objects.get(name='Usuario de Bodega'))
        cls.tiempos = {}

    def test_conteos_de_carga(self):
        self.assertEqual(Producto.objects.count(), 3000)
        self.assertEqual(ActaEntrega.objects.count(), 5000)
        self.assertEqual(Transaccion.objects.filter(tipo='salida').count(), 5000)
        self.assertEqual(LoteProducto.objects.count(), 500)

    def test_listar_productos_paginado_es_aceptable(self):
        client = Client()
        client.force_login(self.usuario)
        t0 = time.perf_counter()
        resp = client.get(reverse('listar-productos'))
        elapsed = time.perf_counter() - t0
        self.tiempos['listar_s'] = round(elapsed, 3)
        print(f'\n[QA carga] listar-productos página 1: {elapsed:.3f}s')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['page_obj'].object_list), 20)
        self.assertLess(elapsed, 3.0)

    def test_buscar_producto_por_codigo_es_aceptable(self):
        client = Client()
        client.force_login(self.usuario)
        t0 = time.perf_counter()
        resp = client.get(reverse('listar-productos'), {'codigo_barra': '301234'})
        elapsed = time.perf_counter() - t0
        print(f'[QA carga] búsqueda por código: {elapsed:.3f}s')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['page_obj'].object_list), 1)
        self.assertLess(elapsed, 2.0)

    def test_control_vencimientos_con_500_productos(self):
        client = Client()
        client.force_login(self.usuario)
        t0 = time.perf_counter()
        resp = client.get(reverse('control-vencimientos'))
        elapsed = time.perf_counter() - t0
        print(f'[QA carga] control-vencimientos (500 con vto): {elapsed:.3f}s')
        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed, 15.0)

    def test_home_con_carga_completa(self):
        client = Client()
        client.force_login(self.usuario)
        t0 = time.perf_counter()
        resp = client.get(reverse('home'))
        elapsed = time.perf_counter() - t0
        print(f'[QA carga] home (3000 productos / 500 vto): {elapsed:.3f}s')
        self.assertEqual(resp.status_code, 200)
        self.assertLess(elapsed, 15.0)

    def test_acta_sigue_siendo_unica_con_carga(self):
        producto_id = Producto.objects.filter(codigo_barra='300000').values_list('id', flat=True).get()
        with self.assertRaises(IntegrityError):
            ActaEntrega.objects.create(
                numero_acta=1,
                departamento='Carga QA',
                producto_id=producto_id,
                cantidad=9,
            )
