from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import CustomUser, LoteProducto, Producto, Transaccion
from accounts.views import _aplicar_anulacion_ingreso, _aplicar_correccion_ingreso


class CorregirIngresoKardexTests(TestCase):
    def setUp(self):
        self.usuario = CustomUser.objects.create_user(
            username='111111111',
            rut='111111111',
            password='test123',
            nombre='Admin Test',
            is_superuser=True,
        )
        self.base = timezone.now() - timedelta(days=10)

    def _fechas(self, *pares):
        for transaccion, dias in pares:
            Transaccion.objects.filter(pk=transaccion.pk).update(
                fecha=self.base + timedelta(days=dias)
            )
            transaccion.refresh_from_db()

    def test_rechaza_correccion_que_deja_stock_negativo(self):
        producto = Producto.objects.create(
            codigo_barra='900001',
            descripcion='Gel test',
            stock=0,
        )
        entrada = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=100)
        producto.stock = 100
        producto.save(update_fields=['stock'])
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=40)
        producto.stock = 60
        producto.save(update_fields=['stock'])
        self._fechas((entrada, 0), (salida, 1))

        limites = Transaccion.limites_correccion_ingreso(entrada)
        self.assertEqual(limites['minimo'], 40)
        self.assertFalse(limites['puede_cero'])

        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 30, 'typo', self.usuario)
        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 0, 'no se puede cero', self.usuario)

        entrada.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(entrada.cantidad, 100)
        self.assertEqual(producto.stock, 60)

    def test_reduce_hasta_cero_el_lote_sin_dejar_negativo(self):
        producto = Producto.objects.create(
            codigo_barra='900009',
            descripcion='Lote a cero',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2026, 9, 6),
        )
        lote = producto.agregar_lote(20, date(2026, 9, 6))
        entrada = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=20, lote=lote,
            observacion='Lote #1 - Vence: 2026-09-06',
        )
        producto.reducir_stock_fifo(19)
        lote.refresh_from_db()
        self.assertEqual(lote.stock, 1)

        limites = Transaccion.limites_correccion_ingreso(entrada, lote)
        self.assertEqual(limites['minimo'], 19)
        self.assertFalse(limites['puede_cero'])

        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 0, 'no cabe cero', self.usuario, lote=lote)

        _aplicar_correccion_ingreso(entrada, 19, 'eran 19', self.usuario, lote=lote)
        entrada.refresh_from_db()
        lote.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(entrada.cantidad, 19)
        self.assertEqual(lote.stock, 0)
        self.assertEqual(producto.stock, 0)

    def test_cantidad_cero_anula_si_el_lote_sigue_completo(self):
        producto = Producto.objects.create(
            codigo_barra='900010',
            descripcion='Cero valido',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2027, 1, 1),
        )
        lote = producto.agregar_lote(5, date(2027, 1, 1))
        entrada = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=5, lote=lote
        )
        limites = Transaccion.limites_correccion_ingreso(entrada, lote)
        self.assertEqual(limites['minimo'], 0)
        self.assertTrue(limites['puede_cero'])

        _aplicar_correccion_ingreso(entrada, 0, 'no debió ingresar', self.usuario, lote=lote)
        self.assertFalse(Transaccion.objects.filter(pk=entrada.pk).exists())
        lote.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(lote.stock, 0)
        self.assertEqual(producto.stock, 0)

    def test_acepta_correccion_y_sincroniza_stock_sin_vencimiento(self):
        producto = Producto.objects.create(
            codigo_barra='900002',
            descripcion='Gel test 2',
            stock=0,
        )
        entrada = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=100)
        producto.stock = 100
        producto.save(update_fields=['stock'])
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=40)
        producto.stock = 60
        producto.save(update_fields=['stock'])
        entrada2 = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=80)
        producto.stock = 140
        producto.save(update_fields=['stock'])
        self._fechas((entrada, 0), (salida, 1), (entrada2, 2))

        _aplicar_correccion_ingreso(entrada, 50, 'era 50 no 100', self.usuario)

        entrada.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(entrada.cantidad, 50)
        self.assertEqual(producto.stock, 90)

        saldos = [saldo for _, saldo in Transaccion.simular_saldos(producto)]
        self.assertEqual(saldos, [50, 10, 90])
        self.assertTrue(all(saldo >= 0 for saldo in saldos))

    def test_acepta_correccion_y_sincroniza_lote(self):
        producto = Producto.objects.create(
            codigo_barra='900003',
            descripcion='Gel con lote',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2027, 1, 1),
        )
        lote1 = producto.agregar_lote(100, date(2027, 1, 1))
        entrada = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=100, lote=lote1
        )
        producto.reducir_stock_fifo(40)
        lote1.refresh_from_db()
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=40)
        lote2 = producto.agregar_lote(80, date(2028, 1, 1))
        entrada2 = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=80, lote=lote2
        )
        self._fechas((entrada, 0), (salida, 1), (entrada2, 2))

        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 30, 'demasiado bajo', self.usuario, lote=lote1)

        _aplicar_correccion_ingreso(entrada, 50, 'ajuste válido', self.usuario, lote=lote1)

        entrada.refresh_from_db()
        lote1.refresh_from_db()
        lote2.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(entrada.cantidad, 50)
        self.assertEqual(lote1.stock, 10)
        self.assertEqual(lote2.stock, 80)
        self.assertEqual(producto.stock, 90)
        total_lotes = sum(lote.stock for lote in LoteProducto.objects.filter(producto=producto))
        self.assertEqual(total_lotes, producto.stock)

        saldos = [saldo for _, saldo in Transaccion.simular_saldos(producto)]
        self.assertEqual(saldos, [50, 10, 90])
        self.assertTrue(all(saldo >= 0 for saldo in saldos))

    def test_formulario_bloquea_cantidad_bajo_el_minimo(self):
        from accounts.forms import CorregirIngresoForm

        producto = Producto.objects.create(
            codigo_barra='900004',
            descripcion='Form test',
            stock=0,
        )
        entrada = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=100)
        producto.stock = 100
        producto.save(update_fields=['stock'])
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=40)
        producto.stock = 60
        producto.save(update_fields=['stock'])
        self._fechas((entrada, 0), (salida, 1))

        form = CorregirIngresoForm(
            data={'cantidad_nueva': 30, 'motivo': 'error de tipeo claro'},
            transaccion=entrada,
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

    def test_observacion_se_reemplaza_en_segunda_correccion(self):
        producto = Producto.objects.create(
            codigo_barra='900005',
            descripcion='Obs test',
            stock=0,
        )
        entrada = Transaccion.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=20,
            observacion='Lote #1 - Vence: 2026-12-31',
        )
        producto.stock = 20
        producto.save(update_fields=['stock'])

        _aplicar_correccion_ingreso(entrada, 18, 'primer ajuste', self.usuario)
        entrada.refresh_from_db()
        self.assertIn('Lote #1 - Vence: 2026-12-31', entrada.observacion)
        self.assertIn('Última corrección: 20 → 18', entrada.observacion)
        self.assertEqual(entrada.observacion.count('Última corrección:'), 1)

        _aplicar_correccion_ingreso(entrada, 16, 'segundo ajuste', self.usuario)
        entrada.refresh_from_db()
        self.assertIn('Lote #1 - Vence: 2026-12-31', entrada.observacion)
        self.assertIn('Última corrección: 18 → 16', entrada.observacion)
        self.assertNotIn('20 → 18', entrada.observacion)
        self.assertEqual(entrada.observacion.count('Última corrección:'), 1)
        self.assertEqual(entrada.cantidad, 16)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 16)

    def test_anular_ingreso_deja_lote_en_cero_y_sincroniza(self):
        producto = Producto.objects.create(
            codigo_barra='900006',
            descripcion='Anular test',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2027, 1, 1),
        )
        lote = producto.agregar_lote(1, date(2027, 1, 1))
        entrada = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=1, lote=lote
        )
        limites = Transaccion.limites_correccion_ingreso(entrada, lote)
        self.assertTrue(limites['puede_anular'])
        self.assertTrue(limites['puede_reducir'])
        self.assertEqual(limites['minimo'], 0)

        _aplicar_anulacion_ingreso(entrada, 'no debió ingresarse', self.usuario, lote=lote)
        self.assertFalse(Transaccion.objects.filter(pk=entrada.pk).exists())
        lote.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(lote.stock, 0)
        self.assertEqual(producto.stock, 0)

    def test_no_anula_si_el_kardex_quedaria_negativo(self):
        producto = Producto.objects.create(
            codigo_barra='900007',
            descripcion='Anular bloqueado',
            stock=0,
        )
        entrada = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=10)
        producto.stock = 10
        producto.save(update_fields=['stock'])
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=8)
        producto.stock = 2
        producto.save(update_fields=['stock'])
        self._fechas((entrada, 0), (salida, 1))

        with self.assertRaises(ValueError):
            _aplicar_anulacion_ingreso(entrada, 'no se puede', self.usuario)
        self.assertTrue(Transaccion.objects.filter(pk=entrada.pk).exists())
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 2)

    def test_infere_lote_por_observacion_y_no_por_fk_equivocado(self):
        producto = Producto.objects.create(
            codigo_barra='900008',
            descripcion='Lote mismatch',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2026, 9, 6),
        )
        lote1 = producto.agregar_lote(80, date(2026, 9, 6))
        lote2 = producto.agregar_lote(0, date(2026, 8, 22))
        entrada = Transaccion.objects.create(
            producto=producto,
            tipo='entrada',
            cantidad=99,
            lote=lote2,
            observacion='Lote #1 - Vence: 2026-09-06. Stock inicial al registrar el producto',
        )
        self.assertEqual(entrada.inferir_lote().numero_lote, 1)
        self.assertTrue(entrada.alinear_lote_con_observacion())
        entrada.refresh_from_db()
        self.assertEqual(entrada.lote_id, lote1.pk)
        self.assertEqual(entrada.inferir_lote().stock, lote1.stock)

    def test_no_baja_ingreso_si_la_salida_deja_kardex_en_cero(self):
        """20 ingresadas y 20 salidas: no se puede bajar a 19 aunque el lote quede en 0."""
        producto = Producto.objects.create(
            codigo_barra='900011',
            descripcion='Salida igual al ingreso',
            stock=0,
            tiene_vencimiento=True,
            fecha_vencimiento=date(2026, 9, 6),
        )
        lote = producto.agregar_lote(20, date(2026, 9, 6))
        entrada = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=20, lote=lote
        )
        producto.reducir_stock_fifo(20)
        Transaccion.objects.create(producto=producto, tipo='salida', cantidad=20)
        lote2 = producto.agregar_lote(100, date(2026, 8, 22))
        entrada2 = Transaccion.objects.create(
            producto=producto, tipo='entrada', cantidad=100, lote=lote2
        )
        producto.reducir_stock_fifo(99)
        Transaccion.objects.create(producto=producto, tipo='salida', cantidad=99)
        salida = Transaccion.objects.filter(producto=producto, tipo='salida').order_by('id')
        self._fechas(
            (entrada, 0),
            (salida[0], 0),
            (entrada2, 1),
            (salida[1], 1),
        )
        lote.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(lote.stock, 0)
        self.assertEqual(producto.stock, 1)

        limites = Transaccion.limites_correccion_ingreso(entrada, lote)
        self.assertEqual(limites['minimo'], 20)
        self.assertFalse(limites['puede_reducir'])
        self.assertFalse(limites['puede_cero'])

        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 19, 'dejar lote en 0', self.usuario, lote=lote)

        entrada.refresh_from_db()
        self.assertEqual(entrada.cantidad, 20)
        saldos = [saldo for _, saldo in Transaccion.simular_saldos(producto)]
        self.assertTrue(all(saldo >= 0 for saldo in saldos))

    def test_exige_aumentar_si_el_bincard_ya_esta_negativo(self):
        """Si el ingreso ya quedó bajo la salida, el mínimo sube: hay que corregir hacia arriba."""
        producto = Producto.objects.create(
            codigo_barra='900012',
            descripcion='Kardex negativo',
            stock=0,
        )
        entrada = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=19)
        producto.stock = 19
        producto.save(update_fields=['stock'])
        salida = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=20)
        producto.stock = 0
        producto.save(update_fields=['stock'])
        entrada2 = Transaccion.objects.create(producto=producto, tipo='entrada', cantidad=100)
        producto.stock = 100
        producto.save(update_fields=['stock'])
        salida2 = Transaccion.objects.create(producto=producto, tipo='salida', cantidad=99)
        producto.stock = 0
        producto.save(update_fields=['stock'])
        self._fechas((entrada, 0), (salida, 0), (entrada2, 1), (salida2, 1))

        limites = Transaccion.limites_correccion_ingreso(entrada)
        self.assertEqual(limites['minimo'], 20)
        self.assertTrue(limites['debe_aumentar'])
        self.assertFalse(limites['puede_reducir'])

        with self.assertRaises(ValueError):
            _aplicar_correccion_ingreso(entrada, 18, 'peor', self.usuario)

        _aplicar_correccion_ingreso(entrada, 20, 'eran 20', self.usuario)
        entrada.refresh_from_db()
        producto.refresh_from_db()
        self.assertEqual(entrada.cantidad, 20)
        self.assertEqual(producto.stock, 1)
        saldos = [saldo for _, saldo in Transaccion.simular_saldos(producto)]
        self.assertEqual(saldos, [20, 0, 100, 1])
        self.assertTrue(all(saldo >= 0 for saldo in saldos))


