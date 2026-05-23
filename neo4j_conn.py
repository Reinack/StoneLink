import os
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, SessionExpired
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "stonelink123")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD),
    connection_timeout=10,
    max_connection_pool_size=10,
)


def get_driver():
    return driver


def close_driver():
    driver.close()


def check_connection():
    """Returns True if Neo4j is reachable, False otherwise."""
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False


def run_query(query, params=None):
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    except (ServiceUnavailable, SessionExpired, AuthError):
        raise
    except Exception:
        raise
