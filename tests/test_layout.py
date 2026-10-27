import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from layout import COLUMNAS, PASO_X, calcular_posiciones, contar_cruces


class TestLayout(unittest.TestCase):
    # Dos minas y dos camiones cableados "en cruz" en el orden de entrada:
    # M1 ↔ C2 y M2 ↔ C1. En columnas sin ordenar, las dos aristas se cruzan.
    NODOS = [("m1", "Mina"), ("m2", "Mina"), ("c1", "Camion"), ("c2", "Camion"), ("e1", "Evento")]
    ARISTAS = [("c2", "m1"), ("c1", "m2"), ("e1", "c1")]

    def test_cruce_detectado(self):
        pos = {"m1": (0, 0), "m2": (0, 1), "c1": (1, 0), "c2": (1, 1)}
        self.assertEqual(contar_cruces(pos, [("m1", "c2"), ("m2", "c1")]), 1)

    def test_aristas_que_comparten_extremo_no_cuentan(self):
        pos = {"a": (0, 0), "b": (1, 1), "c": (1, -1)}
        self.assertEqual(contar_cruces(pos, [("a", "b"), ("a", "c")]), 0)

    def test_ordenar_elimina_el_cruce(self):
        pos = calcular_posiciones(self.NODOS, self.ARISTAS)
        self.assertEqual(contar_cruces(pos, self.ARISTAS), 0)

    def test_eventos_sin_posicion(self):
        pos = calcular_posiciones(self.NODOS, self.ARISTAS)
        self.assertNotIn("e1", pos)

    def test_columnas_y_centrado(self):
        pos = calcular_posiciones(self.NODOS, self.ARISTAS)
        self.assertEqual(pos["m1"][0], COLUMNAS.index("Mina") * PASO_X)
        self.assertEqual(pos["c1"][0], COLUMNAS.index("Camion") * PASO_X)
        self.assertEqual(sum(pos[n][1] for n in ("m1", "m2")), 0)

    def test_determinista(self):
        self.assertEqual(calcular_posiciones(self.NODOS, self.ARISTAS),
                         calcular_posiciones(self.NODOS, self.ARISTAS))


if __name__ == "__main__":
    unittest.main()
