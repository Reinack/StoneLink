# StoneLink API Reference

Base URL: `http://localhost:5000` (local) or `https://your-app.onrender.com` (production)

## GET `/`

Serves the main single-page application (HTML).

**Response**: HTML document with Cytoscape.js graph and UI panels

---

## GET `/api/graph`

Returns all nodes and edges with pre-computed positions.

**Response**: 
```json
{
  "nodes": [
    {
      "data": {
        "id": "0",
        "label": "Mina",
        "nombre": "Cantera Norte",
        "ubicacion": "Zona A",
        "estado": "activa",
        "capacidad_ton": 10000
      },
      "position": {"x": 60, "y": 100}
    }
  ],
  "edges": [
    {
      "data": {
        "source": "7",
        "target": "0",
        "label": "OPERA_EN"
      }
    }
  ]
}
```

**Field Descriptions**:
- `nodes[].data.id`: Unique Neo4j internal ID (string)
- `nodes[].data.label`: Node type (Mina, Camion, Planta, Operador, Evento, Material)
- `nodes[].data.nombre`: Display name
- `nodes[].position`: {x, y} in pixels for Cytoscape layout
- `edges[].data.source`: Source node ID
- `edges[].data.target`: Target node ID
- `edges[].data.label`: Relationship type (OPERA_EN, TRANSPORTA, PROCESA, etc.)

---

## POST `/api/simular_falla`

Simulates a fault on a given piece of equipment and returns direct + indirect impact nodes.

**Request**:
```json
{
  "equipo": "Cantera Central"
}
```

**Response**:
```json
{
  "target": "Cantera Central",
  "target_label": "Mina",
  "target_id": "4",
  "direct_ids": ["8", "13", "17", "27"],
  "indirect_ids": ["5"],
  "direct_nodes": [
    {
      "id": 8,
      "label": "Camion",
      "nombre": "Volvo A40"
    },
    {
      "id": 13,
      "label": "Operador",
      "nombre": "Ana Rodriguez"
    },
    {
      "id": 17,
      "label": "Operador",
      "nombre": "Sofia Ruiz"
    },
    {
      "id": 27,
      "label": "Material",
      "nombre": "Grava gruesa"
    }
  ],
  "indirect_nodes": [
    {
      "id": 5,
      "label": "Planta",
      "nombre": "Planta B"
    }
  ]
}
```

**Impact Tiers**:
- **Direct**: Nodes with immediate operational dependency on the faulted equipment
- **Indirect**: Secondary effects through one intermediate connection

**Example Interpretation** (Cantera Central fault):
1. Cantera Central (Mina) fails
2. Direct impact (Tier 1): 
   - Volvo A40 (Camion) → operates at this mine
   - Ana Rodriguez (Operador) → works at this mine
   - Sofia Ruiz (Operador) → works at this mine
   - Grava gruesa (Material) → generated at this mine
3. Indirect impact (Tier 2):
   - Planta B (Planta) → receives deliveries from Volvo A40

**Error Responses**:
- 404: Equipment not found
  ```json
  {"error": "Equipo no encontrado"}
  ```

---

## GET `/api/eventos`

Returns all logged incidents/events ordered by criticality.

**Response**:
```json
[
  {
    "id": "1",
    "tipo": "Falla trituradora",
    "criticidad": "Alta",
    "descripcion": "Rotor de trituradora en falla primaria",
    "equipo": "Planta A",
    "tipo_equipo": "Planta",
    "nombre_equipo": "Planta A"
  },
  {
    "id": "7",
    "tipo": "Retraso logistico",
    "criticidad": "Media",
    "descripcion": "Retraso en entrega a cliente final",
    "equipo": "Planta A",
    "tipo_equipo": "Planta",
    "nombre_equipo": "Planta A"
  }
]
```

**Sorted by** criticality (Alta → Media → Baja)

---

## GET `/api/metricas`

Returns operational summary metrics.

**Response**:
```json
{
  "conteo_nodos": {
    "Mina": 4,
    "Camion": 5,
    "Planta": 3,
    "Operador": 6,
    "Evento": 8,
    "Material": 5
  },
  "eventos_criticidad": {
    "Alta": 3,
    "Media": 2,
    "Baja": 3
  },
  "camiones_estado": {
    "operativo": 5
  }
}
```

---

## GET `/api/flujo`

Returns operational flow: mines → materials → transport → plants → products.

**Response**:
```json
[
  {
    "mina": "Cantera Norte",
    "materiales_origen": ["Piedra caliza", "Polvo de roca"],
    "transporte": ["CAT 773", "Komatsu HD465"],
    "plantas_destino": ["Planta A"],
    "productos": ["Piedra caliza", "Roca basaltica"]
  }
]
```

---

## GET `/api/impacto/<equipo>` (Deprecated)

Legacy endpoint. Use `/api/simular_falla` instead.

---

## Error Handling

All endpoints return JSON responses with appropriate HTTP status codes:

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Valid query completed |
| 404 | Not Found | Equipment name doesn't exist |
| 500 | Server Error | Neo4j connection failed |

Error response format:
```json
{
  "error": "descriptive error message"
}
```

---

## Rate Limiting

No rate limiting on free tier. For production, consider:
- Render free tier: ~100 requests/minute suggested
- Implement cache headers for `/api/graph` (30 seconds)
- Use Redis for session data if expanding

---

## Data Model

### Node Types & Properties

**Mina** (Mining site)
- `id`, `nombre`, `ubicacion`, `estado`, `capacidad_ton`
- Example: "Cantera Norte" in "Zona A", capacity 10000 tons

**Camion** (Truck)
- `id`, `modelo`, `capacidad_ton`, `estado`
- Example: "CAT 773", capacity 30 tons, "operativo"

**Planta** (Processing plant)
- `id`, `nombre`, `tipo`, `estado`, `capacidad_ton`
- Example: "Planta A" (primary crusher), 100 ton/hour

**Operador** (Operator/driver)
- `id`, `nombre`, `turno`, `experiencia`
- Example: "Carlos Mendez", turno "diurno", 5 years

**Evento** (Incident log)
- `id`, `tipo`, `criticidad`, `descripcion`, `equipo_afectado`
- Example: "Falla trituradora", criticidad "Alta"

**Material** (Extracted/processed resource)
- `id`, `nombre`, `tipo`, `unidad`
- Example: "Piedra caliza" (stone), unit "toneladas"

### Relationship Types

All relationships are **directed**:

| Relationship | Source | Target | Meaning |
|---|---|---|---|
| OPERA_EN | Camion | Mina | Truck operates at mine |
| TRANSPORTA | Camion | Planta | Truck transports to plant |
| USA | Operador | Camion | Operator drives truck |
| TRABAJA_EN | Operador | Mina | Operator works at mine |
| PROCESA | Planta | Material | Plant processes material |
| GENERA | Mina | Material | Mine generates material |
| AFECTA | Evento | Node | Event impacts node |

---

## Usage Examples

### JavaScript / Fetch

Simulate a fault:
```javascript
const response = await fetch('http://localhost:5000/api/simular_falla', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ equipo: 'Cantera Central' })
});
const data = await response.json();
console.log('Direct impacts:', data.direct_nodes);
console.log('Indirect impacts:', data.indirect_nodes);
```

Get graph:
```javascript
const response = await fetch('http://localhost:5000/api/graph');
const { nodes, edges } = await response.json();
console.log(`Graph has ${nodes.length} nodes and ${edges.length} edges`);
```

### Python / Requests

```python
import requests

# Simulate fault
resp = requests.post('http://localhost:5000/api/simular_falla', 
    json={'equipo': 'CAT 773'})
data = resp.json()
print(f"Direct: {len(data['direct_ids'])} nodes")
print(f"Indirect: {len(data['indirect_ids'])} nodes")

# Get metrics
resp = requests.get('http://localhost:5000/api/metricas')
metrics = resp.json()
print(f"Total mines: {metrics['conteo_nodos']['Mina']}")
```

### cURL

```bash
# Get graph
curl http://localhost:5000/api/graph | jq '.nodes | length'

# Simulate fault
curl -X POST http://localhost:5000/api/simular_falla \
  -H 'Content-Type: application/json' \
  -d '{"equipo": "Volvo A45"}' | jq '.direct_ids'
```

---

## Response Times

Typical latencies:
- `/api/graph`: 50-100ms (all nodes & edges)
- `/api/simular_falla`: 100-200ms (Neo4j traversal)
- `/api/eventos`: 30-50ms
- `/api/metricas`: 50-80ms

---

## CORS

Cross-Origin requests are blocked by default. To enable for external clients:

In `app.py`:
```python
from flask_cors import CORS
CORS(app)
```

Then install:
```bash
pip install flask-cors
```

---

See [README.md](../README.md) for application overview and [DEPLOYMENT.md](DEPLOYMENT.md) for production setup.
