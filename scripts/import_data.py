import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from neo4j_conn import run_query, close_driver

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def clear_database():
    print("Limpiando base de datos...")
    run_query("MATCH (n) DETACH DELETE n")


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_minas():
    rows = load_csv("minas.csv")
    for r in rows:
        run_query(
            "CREATE (:Mina {id: $id, nombre: $nombre, ubicacion: $ubicacion, estado: $estado, capacidad_ton: toInteger($cap)})",
            {"id": r["id"], "nombre": r["nombre"], "ubicacion": r["ubicacion"], "estado": r["estado"], "cap": r["capacidad_ton"]},
        )
    print(f"  {len(rows)} minas importadas")


def import_plantas():
    rows = load_csv("plantas.csv")
    for r in rows:
        run_query(
            "CREATE (:Planta {id: $id, nombre: $nombre, tipo: $tipo, estado: $estado, capacidad_ton: toInteger($cap)})",
            {"id": r["id"], "nombre": r["nombre"], "tipo": r["tipo"], "estado": r["estado"], "cap": r["capacidad_ton"]},
        )
    print(f"  {len(rows)} plantas importadas")


def import_camiones():
    rows = load_csv("camiones.csv")
    for r in rows:
        run_query(
            "CREATE (:Camion {id: $id, modelo: $modelo, capacidad_ton: toInteger($cap), estado: $estado})",
            {"id": r["id"], "modelo": r["modelo"], "cap": r["capacidad_ton"], "estado": r["estado"]},
        )
    print(f"  {len(rows)} camiones importados")


def import_operadores():
    rows = load_csv("operadores.csv")
    for r in rows:
        run_query(
            "CREATE (:Operador {id: $id, nombre: $nombre, turno: $turno, experiencia: toInteger($exp)})",
            {"id": r["id"], "nombre": r["nombre"], "turno": r["turno"], "exp": r["experiencia_anios"]},
        )
    print(f"  {len(rows)} operadores importados")


def import_eventos():
    rows = load_csv("eventos.csv")
    for r in rows:
        run_query(
            "CREATE (:Evento {id: $id, tipo: $tipo, criticidad: $crit, descripcion: $desc, equipo_afectado: $eq})",
            {"id": r["id"], "tipo": r["tipo"], "crit": r["criticidad"], "desc": r["descripcion"], "eq": r["equipo_afectado"]},
        )
    print(f"  {len(rows)} eventos importados")


def import_materiales():
    rows = load_csv("materiales.csv")
    for r in rows:
        run_query(
            "CREATE (:Material {id: $id, nombre: $nombre, tipo: $tipo, unidad: $unidad})",
            {"id": r["id"], "nombre": r["nombre"], "tipo": r["tipo"], "unidad": r["unidad"]},
        )
    print(f"  {len(rows)} materiales importados")


def create_relationships():
    print("Creando relaciones...")

    # Camiones operan en minas
    run_query("MATCH (c:Camion {id:'1'}), (m:Mina {id:'1'}) CREATE (c)-[:OPERA_EN]->(m)")
    run_query("MATCH (c:Camion {id:'2'}), (m:Mina {id:'2'}) CREATE (c)-[:OPERA_EN]->(m)")
    run_query("MATCH (c:Camion {id:'3'}), (m:Mina {id:'1'}) CREATE (c)-[:OPERA_EN]->(m)")
    run_query("MATCH (c:Camion {id:'4'}), (m:Mina {id:'3'}) CREATE (c)-[:OPERA_EN]->(m)")
    run_query("MATCH (c:Camion {id:'5'}), (m:Mina {id:'4'}) CREATE (c)-[:OPERA_EN]->(m)")

    # Camiones transportan a plantas
    run_query("MATCH (c:Camion {id:'1'}), (p:Planta {id:'1'}) CREATE (c)-[:TRANSPORTA {material: 'Piedra caliza'}]->(p)")
    run_query("MATCH (c:Camion {id:'2'}), (p:Planta {id:'2'}) CREATE (c)-[:TRANSPORTA {material: 'Grava gruesa'}]->(p)")
    run_query("MATCH (c:Camion {id:'3'}), (p:Planta {id:'1'}) CREATE (c)-[:TRANSPORTA {material: 'Roca basaltica'}]->(p)")
    run_query("MATCH (c:Camion {id:'4'}), (p:Planta {id:'3'}) CREATE (c)-[:TRANSPORTA {material: 'Piedra caliza'}]->(p)")
    run_query("MATCH (c:Camion {id:'5'}), (p:Planta {id:'2'}) CREATE (c)-[:TRANSPORTA {material: 'Arena fina'}]->(p)")

    # Plantas procesan materiales
    run_query("MATCH (p:Planta {id:'1'}), (mat:Material {id:'1'}) CREATE (p)-[:PROCESA]->(mat)")
    run_query("MATCH (p:Planta {id:'1'}), (mat:Material {id:'4'}) CREATE (p)-[:PROCESA]->(mat)")
    run_query("MATCH (p:Planta {id:'2'}), (mat:Material {id:'2'}) CREATE (p)-[:PROCESA]->(mat)")
    run_query("MATCH (p:Planta {id:'2'}), (mat:Material {id:'3'}) CREATE (p)-[:PROCESA]->(mat)")
    run_query("MATCH (p:Planta {id:'3'}), (mat:Material {id:'1'}) CREATE (p)-[:PROCESA]->(mat)")

    # Operadores trabajan en minas
    run_query("MATCH (o:Operador {id:'1'}), (m:Mina {id:'1'}) CREATE (o)-[:TRABAJA_EN]->(m)")
    run_query("MATCH (o:Operador {id:'2'}), (m:Mina {id:'2'}) CREATE (o)-[:TRABAJA_EN]->(m)")
    run_query("MATCH (o:Operador {id:'3'}), (m:Mina {id:'1'}) CREATE (o)-[:TRABAJA_EN]->(m)")
    run_query("MATCH (o:Operador {id:'4'}), (m:Mina {id:'3'}) CREATE (o)-[:TRABAJA_EN]->(m)")
    run_query("MATCH (o:Operador {id:'5'}), (m:Mina {id:'4'}) CREATE (o)-[:TRABAJA_EN]->(m)")
    run_query("MATCH (o:Operador {id:'6'}), (m:Mina {id:'2'}) CREATE (o)-[:TRABAJA_EN]->(m)")

    # Operadores usan camiones
    run_query("MATCH (o:Operador {id:'1'}), (c:Camion {id:'1'}) CREATE (o)-[:USA]->(c)")
    run_query("MATCH (o:Operador {id:'2'}), (c:Camion {id:'2'}) CREATE (o)-[:USA]->(c)")
    run_query("MATCH (o:Operador {id:'3'}), (c:Camion {id:'3'}) CREATE (o)-[:USA]->(c)")
    run_query("MATCH (o:Operador {id:'4'}), (c:Camion {id:'4'}) CREATE (o)-[:USA]->(c)")
    run_query("MATCH (o:Operador {id:'5'}), (c:Camion {id:'5'}) CREATE (o)-[:USA]->(c)")

    # Eventos afectan equipos
    run_query("MATCH (e:Evento {id:'1'}), (p:Planta {id:'1'}) CREATE (e)-[:AFECTA]->(p)")
    run_query("MATCH (e:Evento {id:'2'}), (p:Planta {id:'2'}) CREATE (e)-[:AFECTA]->(p)")
    run_query("MATCH (e:Evento {id:'3'}), (c:Camion {id:'1'}) CREATE (e)-[:AFECTA]->(c)")
    run_query("MATCH (e:Evento {id:'4'}), (p:Planta {id:'3'}) CREATE (e)-[:AFECTA]->(p)")
    run_query("MATCH (e:Evento {id:'5'}), (c:Camion {id:'2'}) CREATE (e)-[:AFECTA]->(c)")
    run_query("MATCH (e:Evento {id:'6'}), (c:Camion {id:'3'}) CREATE (e)-[:AFECTA]->(c)")
    run_query("MATCH (e:Evento {id:'7'}), (p:Planta {id:'1'}) CREATE (e)-[:AFECTA]->(p)")
    run_query("MATCH (e:Evento {id:'8'}), (c:Camion {id:'4'}) CREATE (e)-[:AFECTA]->(c)")

    # Minas generan materiales
    run_query("MATCH (m:Mina {id:'1'}), (mat:Material {id:'1'}) CREATE (m)-[:GENERA]->(mat)")
    run_query("MATCH (m:Mina {id:'2'}), (mat:Material {id:'2'}) CREATE (m)-[:GENERA]->(mat)")
    run_query("MATCH (m:Mina {id:'3'}), (mat:Material {id:'4'}) CREATE (m)-[:GENERA]->(mat)")
    run_query("MATCH (m:Mina {id:'4'}), (mat:Material {id:'3'}) CREATE (m)-[:GENERA]->(mat)")
    run_query("MATCH (m:Mina {id:'1'}), (mat:Material {id:'5'}) CREATE (m)-[:GENERA]->(mat)")

    print("  Relaciones creadas")


if __name__ == "__main__":
    print("=== StoneLink - Importacion de datos ===")
    clear_database()
    print("Importando nodos...")
    import_minas()
    import_plantas()
    import_camiones()
    import_operadores()
    import_eventos()
    import_materiales()
    create_relationships()
    close_driver()
    print("=== Importacion completa ===")
