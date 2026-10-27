"""Posiciones del grafo: columnas por etapa operativa, ordenadas para cruzar lo menos posible.

Cada tipo de nodo va en una columna fija (el flujo se lee de izquierda a derecha). Dentro de cada
columna el orden sale de la heurística del baricentro: cada nodo se ubica a la altura promedio de
sus vecinos, en barridos alternados de izquierda a derecha y de derecha a izquierda. Se cuentan los
cruces reales (segmentos rectos) después de cada barrido y se queda el mejor orden; al final se
intercambian vecinos de columna mientras eso siga bajando los cruces.

Los Eventos no van en el canvas: el frontend los dibuja como marcas sobre el equipo que afectan.
"""

COLUMNAS = ["Mina", "Camion", "Planta", "Material", "Operador"]
PASO_X = 220
PASO_Y = 110
BARRIDOS = 12


def _cruzan(p1, p2, p3, p4):
    """True si los segmentos p1-p2 y p3-p4 se cortan en un punto interior."""
    def orient(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 1e-9) - (v < -1e-9)

    o1, o2 = orient(p1, p2, p3), orient(p1, p2, p4)
    o3, o4 = orient(p3, p4, p1), orient(p3, p4, p2)
    return o1 * o2 < 0 and o3 * o4 < 0


def contar_cruces(posiciones, aristas):
    """Cantidad de pares de aristas que se cruzan, sin contar las que comparten un extremo."""
    segs = [(a, b, posiciones[a], posiciones[b]) for a, b in aristas if a in posiciones and b in posiciones]
    total = 0
    for i in range(len(segs)):
        a1, b1, p1, p2 = segs[i]
        for j in range(i + 1, len(segs)):
            a2, b2, p3, p4 = segs[j]
            if {a1, b1} & {a2, b2}:
                continue
            if _cruzan(p1, p2, p3, p4):
                total += 1
    return total


def _posiciones(orden):
    """Columna i en x = i * PASO_X; cada columna centrada verticalmente en y = 0."""
    pos = {}
    for i, tipo in enumerate(COLUMNAS):
        ids = orden.get(tipo, [])
        mitad = (len(ids) - 1) / 2
        for k, nid in enumerate(ids):
            pos[nid] = (i * PASO_X, (k - mitad) * PASO_Y)
    return pos


def calcular_posiciones(nodos, aristas):
    """nodos: lista de (id, tipo). aristas: lista de (origen, destino).

    Devuelve {id: (x, y)} para los nodos de COLUMNAS. Los de otros tipos no reciben posición.
    El orden inicial es el de entrada, así que el resultado es determinista.
    """
    orden = {t: [nid for nid, tipo in nodos if tipo == t] for t in COLUMNAS}
    en_canvas = {nid for ids in orden.values() for nid in ids}
    aristas = [(a, b) for a, b in aristas if a in en_canvas and b in en_canvas and a != b]

    vecinos = {nid: [] for nid in en_canvas}
    for a, b in aristas:
        vecinos[a].append(b)
        vecinos[b].append(a)

    pos = _posiciones(orden)
    mejor_orden = {t: list(ids) for t, ids in orden.items()}
    mejor_cruces = contar_cruces(pos, aristas)

    for barrido in range(BARRIDOS):
        tipos = COLUMNAS if barrido % 2 == 0 else list(reversed(COLUMNAS))
        for t in tipos:
            ids = orden[t]

            def baricentro(item):
                k, nid = item
                ys = [pos[v][1] for v in vecinos[nid] if v not in ids]
                return (sum(ys) / len(ys) if ys else pos[nid][1], k)

            orden[t] = [nid for _, nid in sorted(enumerate(ids), key=baricentro)]
            pos = _posiciones(orden)

        cruces = contar_cruces(pos, aristas)
        if cruces < mejor_cruces:
            mejor_cruces = cruces
            mejor_orden = {t: list(ids) for t, ids in orden.items()}

    # Ajuste fino: intercambiar vecinos de columna mientras baje la cantidad de cruces.
    orden = {t: list(ids) for t, ids in mejor_orden.items()}
    mejoro = True
    while mejoro:
        mejoro = False
        for t in COLUMNAS:
            ids = orden[t]
            for k in range(len(ids) - 1):
                ids[k], ids[k + 1] = ids[k + 1], ids[k]
                cruces = contar_cruces(_posiciones(orden), aristas)
                if cruces < mejor_cruces:
                    mejor_cruces, mejoro = cruces, True
                else:
                    ids[k], ids[k + 1] = ids[k + 1], ids[k]

    return _posiciones(orden)
