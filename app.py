from flask import Flask, render_template, jsonify, request
from neo4j_conn import run_query, close_driver, check_connection
from neo4j.exceptions import ServiceUnavailable, SessionExpired, AuthError
import atexit

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Fault-simulation: typed, directed, two-tier impact traversal
#
# Tier 1 — DIRECT: exactly one typed, directed hop from the fault target.
# Tier 2 — INDIRECT: exactly one further typed, directed hop from each
#           Tier-1 node, never reversing through shared hubs.
#
# Each query is keyed by the node label it starts from.
# Terminal labels (Mina reached via Camion, Operador, Material, Evento as
# intermediary) return None → no further expansion, preventing sibling
# contamination through shared hub nodes.
# ---------------------------------------------------------------------------

_DIRECT_QUERIES = {
    # Camiones that operate at the mine, operators assigned there, materials generated.
    'Mina': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)<-[:OPERA_EN]-(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)<-[:TRABAJA_EN]-(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:GENERA]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # Plant the camion delivers to, mine it operates at, operator who drives it.
    'Camion': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:TRANSPORTA]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:OPERA_EN]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)<-[:USA]-(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # Materials processed (production stops), camiones delivering (route disrupted).
    # NOTE: backward TRANSPORTA is valid only when the ORIGINAL target is a Planta;
    # the indirect query for Planta deliberately omits it to block sibling-Camion
    # contamination through a shared-destination hub.
    'Planta': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:PROCESA]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)<-[:TRANSPORTA]-(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # Truck the operator drives, mine they are assigned to.
    'Operador': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:USA]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:TRABAJA_EN]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # Resolve the event's target asset first, then apply normal rules from that asset.
    'Evento': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:AFECTA]->(n) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
}

_INDIRECT_QUERIES = {
    # From a directly-impacted Camion: the plant it delivers to loses supply;
    # the mine it operates at loses transport; the operator loses their vehicle.
    # OPERA_EN→Mina is included here but is filtered out at runtime when the
    # Mina happens to be the original fault target (avoids circular inclusion).
    'Camion': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:TRANSPORTA]->(n:Planta) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:OPERA_EN]->(n:Mina) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre "
        "UNION "
        "MATCH (t) WHERE id(t) = $tid MATCH (t)<-[:USA]-(n:Operador) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # From a directly-impacted Planta: materials it processes are disrupted.
    # Deliberately omits backward TRANSPORTA to prevent sibling-Camion
    # contamination (Rule 2 from the propagation analysis).
    'Planta': (
        "MATCH (t) WHERE id(t) = $tid MATCH (t)-[:PROCESA]->(n:Material) "
        "RETURN id(n) AS id, labels(n)[0] AS label, coalesce(n.nombre, n.modelo, n.tipo) AS nombre"
    ),
    # Terminal nodes: propagation stops here to avoid hub contamination.
    'Mina':     None,   # expanding from a reached Mina would pull in sibling Camiones
    'Operador': None,   # terminal — no further chain
    'Material': None,   # terminal output/leaf node
    'Evento':   None,   # informational record, never a propagation intermediary
}
atexit.register(close_driver)

_DB_OFFLINE_RESPONSE = (
    jsonify({"error": "db_offline", "message": "Base de datos iniciando, intente en unos segundos"}),
    503,
)


def db_offline_response():
    return jsonify({"error": "db_offline", "message": "Base de datos iniciando, intente en unos segundos"}), 503


@app.route("/api/status")
def db_status():
    if check_connection():
        return jsonify({"status": "ok"})
    return jsonify({"status": "offline", "message": "Base de datos no disponible"}), 503


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/graph")
def get_graph():
    nodes_query = """
    MATCH (n)
    RETURN id(n) AS id, labels(n)[0] AS label, properties(n) AS props
    """
    edges_query = """
    MATCH (a)-[r]->(b)
    RETURN id(a) AS source, id(b) AS target, type(r) AS rel_type, properties(r) AS props
    """
    try:
        nodes = run_query(nodes_query)
        edges = run_query(edges_query)
    except (ServiceUnavailable, SessionExpired, AuthError, Exception):
        return db_offline_response()

    # Pre-computed positions arranged in operational flow columns (compact for ~530px wide canvas)
    TYPE_COLS = {
        "Mina":     {"x": 60,  "spacing": 110},
        "Camion":   {"x": 190, "spacing": 90},
        "Planta":   {"x": 310, "spacing": 120},
        "Material": {"x": 430, "spacing": 90},
        "Operador": {"x": 550, "spacing": 90},
        "Evento":   {"x": 670, "spacing": 80},
    }
    type_counters = {}

    cyto_nodes = []
    for n in nodes:
        # Use Neo4j internal id as the Cytoscape node id (unique across all node types).
        # Strip the CSV "id" property first so it never overwrites the internal id.
        props = dict(n["props"])
        props.pop("id", None)
        data = {"id": str(n["id"]), "label": n["label"], **props}
        display = n["props"].get("nombre") or n["props"].get("modelo") or n["props"].get("tipo") or f"{n['label']} {n['id']}"
        data["display"] = display

        label = n["label"]
        col = TYPE_COLS.get(label, {"x": 600, "spacing": 140})
        idx = type_counters.get(label, 0)
        type_counters[label] = idx + 1
        pos = {"x": col["x"], "y": 100 + idx * col["spacing"]}

        cyto_nodes.append({"data": data, "position": pos})

    cyto_edges = []
    for e in edges:
        data = {
            "source": str(e["source"]),
            "target": str(e["target"]),
            "label": e["rel_type"],
            **e["props"],
        }
        cyto_edges.append({"data": data})

    return jsonify({"nodes": cyto_nodes, "edges": cyto_edges})


@app.route("/api/impacto/<equipo>")
def get_impacto(equipo):
    query = """
    MATCH (e:Evento)-[:AFECTA]->(target)
    WHERE target.nombre = $equipo OR target.modelo = $equipo
    OPTIONAL MATCH (target)<-[:TRANSPORTA]-(c:Camion)
    OPTIONAL MATCH (target)<-[:OPERA_EN]-(c2:Camion)
    OPTIONAL MATCH (o:Operador)-[:USA]->(c)
    OPTIONAL MATCH (o2:Operador)-[:USA]->(c2)
    OPTIONAL MATCH (c)-[:OPERA_EN]->(m:Mina)
    OPTIONAL MATCH (c2)-[:OPERA_EN]->(m2:Mina)
    RETURN e.tipo AS evento, e.criticidad AS criticidad, e.descripcion AS descripcion,
           collect(DISTINCT c.modelo) + collect(DISTINCT c2.modelo) AS camiones_afectados,
           collect(DISTINCT o.nombre) + collect(DISTINCT o2.nombre) AS operadores_afectados,
           collect(DISTINCT m.nombre) + collect(DISTINCT m2.nombre) AS minas_relacionadas
    """
    try:
        results = run_query(query, {"equipo": equipo})
    except Exception:
        return db_offline_response()
    return jsonify(results)


@app.route("/api/eventos")
def get_eventos():
    query = """
    MATCH (e:Evento)-[:AFECTA]->(target)
    RETURN e.id AS id, e.tipo AS tipo, e.criticidad AS criticidad,
           e.descripcion AS descripcion, e.equipo_afectado AS equipo,
           labels(target)[0] AS tipo_equipo,
           target.nombre AS nombre_equipo
    ORDER BY CASE e.criticidad WHEN 'Alta' THEN 1 WHEN 'Media' THEN 2 ELSE 3 END
    """
    try:
        return jsonify(run_query(query))
    except Exception:
        return db_offline_response()


@app.route("/api/flujo")
def get_flujo():
    query = """
    MATCH (m:Mina)-[:GENERA]->(mat:Material)
    OPTIONAL MATCH (c:Camion)-[:OPERA_EN]->(m)
    OPTIONAL MATCH (c)-[:TRANSPORTA]->(p:Planta)
    OPTIONAL MATCH (p)-[:PROCESA]->(mat2:Material)
    RETURN m.nombre AS mina, collect(DISTINCT mat.nombre) AS materiales_origen,
           collect(DISTINCT c.modelo) AS transporte,
           collect(DISTINCT p.nombre) AS plantas_destino,
           collect(DISTINCT mat2.nombre) AS productos
    """
    try:
        return jsonify(run_query(query))
    except Exception:
        return db_offline_response()


@app.route("/api/metricas")
def get_metricas():
    try:
        counts = run_query("""
        MATCH (n) RETURN labels(n)[0] AS tipo, count(n) AS total
        """)
        eventos_crit = run_query("""
        MATCH (e:Evento) RETURN e.criticidad AS criticidad, count(e) AS total
        """)
        camiones_estado = run_query("""
        MATCH (c:Camion) RETURN c.estado AS estado, count(c) AS total
        """)
    except Exception:
        return db_offline_response()
    return jsonify({
        "conteo_nodos": {r["tipo"]: r["total"] for r in counts},
        "eventos_criticidad": {r["criticidad"]: r["total"] for r in eventos_crit},
        "camiones_estado": {r["estado"]: r["total"] for r in camiones_estado},
    })


@app.route("/api/simular_falla", methods=["POST"])
def simular_falla():
    data = request.json
    nombre = data.get("equipo", "")

    try:
        # 1. Resolve the fault target node.
        target_rows = run_query(
            "MATCH (t) WHERE t.nombre = $nombre OR t.modelo = $nombre "
            "RETURN id(t) AS id, labels(t)[0] AS label, "
            "coalesce(t.nombre, t.modelo) AS nombre LIMIT 1",
            {"nombre": nombre},
        )
    except Exception:
        return db_offline_response()

    if not target_rows:
        return jsonify({"error": "Equipo no encontrado"}), 404

    t = target_rows[0]
    tid     = t["id"]
    tlabel  = t["label"]
    tnombre = t["nombre"]

    try:
        # 2. Tier 1 — Direct impact (typed, directed, exactly 1 hop).
        dq = _DIRECT_QUERIES.get(tlabel)
        direct_raw   = run_query(dq, {"tid": tid}) if dq else []
        direct_nodes = [r for r in direct_raw if r.get("id") is not None]
        direct_ids   = {str(r["id"]) for r in direct_nodes}

        # 3. Tier 2 — Indirect impact (1 hop from each Tier-1 node).
        #    Excludes: the original target, any Tier-1 node, duplicates.
        seen_indirect = set()
        indirect_nodes: list = []
        indirect_ids: set   = set()

        for dn in direct_nodes:
            iq = _INDIRECT_QUERIES.get(dn["label"])
            if not iq:
                continue  # terminal label — propagation stops here
            for r in run_query(iq, {"tid": dn["id"]}):
                if r.get("id") is None:
                    continue
                rid = str(r["id"])
                if rid == str(tid) or rid in direct_ids or rid in seen_indirect:
                    continue
                seen_indirect.add(rid)
                indirect_nodes.append(r)
                indirect_ids.add(rid)
    except Exception:
        return db_offline_response()

    return jsonify({
        "target":         tnombre,
        "target_label":   tlabel,
        "target_id":      str(tid),
        "direct_ids":     list(direct_ids),
        "indirect_ids":   list(indirect_ids),
        "direct_nodes":   direct_nodes,
        "indirect_nodes": indirect_nodes,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
