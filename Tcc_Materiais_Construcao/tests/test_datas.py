import unittest
from datetime import date, datetime

from telas.helpers import _data_iso_segura


class TestDatas(unittest.TestCase):
    def test_iso_valido(self):
        self.assertEqual(_data_iso_segura('2026-10-22'), date(2026, 10, 22))

    def test_datetime(self):
        self.assertEqual(
            _data_iso_segura(datetime(2026, 10, 23, 15, 30)),
            date(2026, 10, 23),
        )

    def test_valor_invalido_usa_padrao(self):
        padrao = date(2026, 1, 2)
        self.assertEqual(_data_iso_segura('invalida', padrao), padrao)


if __name__ == '__main__':
    unittest.main()
