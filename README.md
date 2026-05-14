# StoneLink

A real-time operational analytics platform for mining and aggregate processing networks. Visualize equipment relationships, simulate faults, and understand cascading impacts across your supply chain with two-tier impact analysis.

![StoneLink Architecture](docs/ARCHITECTURE.md)

## Features

✨ **Visual Graph Analytics**
- Interactive Cytoscape.js visualization of mining operations
- 6 node types: Mines, Trucks, Plants, Operators, Materials, Events
- 39 directed relationships capturing operational dependencies
- WebGL-accelerated rendering for 100+ node networks

⚡ **Two-Tier Fault Simulation**
- Simulate equipment failures and instantly see operational impact
- **Direct impacts** (Tier 1): Immediate operational dependency nodes in **red**
- **Indirect impacts** (Tier 2): Secondary effects through one intermediate connection in **yellow**
- No false positives—typed, directed graph traversal prevents hub contamination

📊 **Operational Dashboards**
- Real-time incident log with criticality sorting
- Node type counts and operational metrics
- Equipment status and capacity tracking
- Operational flow visualization (mines → materials → plants → products)

🔍 **Smart Filtering**
- Filter by equipment type (Mines, Trucks, Plants, Operators)
- Highlight node neighborhoods on click
- Color-coded visual hierarchy by impact severity

---

## Quick Start

### Prerequisites
- Python 3.8+
- Neo4j (local, self-hosted, or Aura cloud)
- Git

### Local Development (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/stonelink.git
cd stonelink

# Create virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
# or
venv\Scripts\activate              # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Neo4j credentials:
# NEO4J_URI=neo4j://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password

# Import sample data (creates 31 nodes, 39 relationships)
python scripts/import_data.py

# Start Flask development server
python app.py
```

Open **http://localhost:5000** in your browser. The graph loads automatically.

### Production Deployment (Render + Neo4j Aura)

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step guide:
1. Create Render Web Service (2 min)
2. Create Neo4j Aura instance (2 min)
3. Set environment variables (2 min)
4. Push to GitHub (auto-deploy)

**Result**: Live app at `https://stonelink-api-xxxxx.onrender.com`

---

## Project Structure

```
stonelink/
├── app.py                          # Flask backend (6 REST endpoints)
├── requirements.txt                # Python dependencies
├── Procfile                        # Render deployment config
├── runtime.txt                     # Python version for Render
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
│
├── static/
│   ├── index.html                  # Single-page app
│   ├── js/
│   │   └── app.js                  # Cytoscape visualization & fault simulation
│   └── css/
│       └── style.css               # Graph styling & impact colors
│
├── scripts/
│   ├── import_data.py              # Neo4j data import script
│   └── data/
│       ├── minas.csv               # Mining sites
│       ├── camiones.csv            # Trucks
│       ├── plantas.csv             # Processing plants
│       ├── operadores.csv          # Operators/drivers
│       ├── materiales.csv          # Materials
│       └── eventos.csv             # Incident logs
│
├── docs/
│   ├── ARCHITECTURE.md             # System design & topology
│   ├── API.md                      # REST endpoint reference
│   ├── DEPLOYMENT.md               # Production setup guide
│   └── README.md                   # This file
│
└── .claude/                        # Development metadata (ignored by git)
```

---

## API Summary

### Core Endpoints

| Endpoint | Method | Purpose | Time |
|----------|--------|---------|------|
| `/api/graph` | GET | Load full network graph | 50-100ms |
| `/api/simular_falla` | POST | Simulate fault & get direct + indirect impacts | 100-200ms |
| `/api/eventos` | GET | All incidents sorted by criticality | 30-50ms |
| `/api/metricas` | GET | Node counts & operational summary | 50-80ms |
| `/api/flujo` | GET | Operational flow (mines → plants) | 50-100ms |

### Example: Fault Simulation

```bash
curl -X POST http://localhost:5000/api/simular_falla \
  -H 'Content-Type: application/json' \
  -d '{"equipo": "Cantera Central"}'
```

Response:
```json
{
  "target": "Cantera Central",
  "target_label": "Mina",
  "target_id": "4",
  "direct_ids": ["8", "13", "17", "27"],
  "indirect_ids": ["5"],
  "direct_nodes": [
    {"id": 8, "label": "Camion", "nombre": "Volvo A40"},
    {"id": 13, "label": "Operador", "nombre": "Ana Rodriguez"},
    {"id": 17, "label": "Operador", "nombre": "Sofia Ruiz"},
    {"id": 27, "label": "Material", "nombre": "Grava gruesa"}
  ],
  "indirect_nodes": [
    {"id": 5, "label": "Planta", "nombre": "Planta B"}
  ]
}
```

Full endpoint reference: [API.md](docs/API.md)

---

## Two-Tier Impact Analysis

The fault simulation uses a **directed, typed, depth-limited graph traversal** to prevent false positives:

### How It Works

When a node fails (e.g., Cantera Central mine):

**Tier 1 (Direct Impact)** — 1 hop with explicit relationship types:
```
Cantera Central (Mina)
├─ ← OPERA_EN → Volvo A40 (Camion)        [Trucks at this mine]
├─ ← TRABAJA_EN → Ana Rodriguez (Operador) [Workers there]
├─ ← TRABAJA_EN → Sofia Ruiz (Operador)   [Workers there]
└─ → GENERA → Grava gruesa (Material)     [What it produces]
```

**Tier 2 (Indirect Impact)** — 1 hop from each Tier-1 node:
```
Volvo A40 (Camion)
└─ → TRANSPORTA → Planta B (Planta)       [Delivery destination]

[Terminal: Operador and Material don't propagate further]
```

### Key Insight: Terminal Classification

Certain node types **don't propagate further** to prevent sibling contamination:
- **Operador** (operator): Reached via TRABAJA_EN or USA, but doesn't expand
- **Material** (material): Reached via GENERA or PROCESA, but doesn't expand
- **Evento** (incident): Reached via AFECTA, but doesn't expand

This ensures that trucks operating at *other* mines aren't falsely marked as impacted when Cantera Central fails.

### Visualization

- 🔴 **Red border** (red glow): Fault target
- 🔴 **Red border**: Direct impact nodes
- 🟡 **Yellow/amber border**: Indirect impact nodes
- 🔵 **Blue, green, etc.**: Not impacted

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed traversal logic and Cypher queries.

---

## Configuration

### Environment Variables

Create a `.env` file (or set in your deployment platform):

```env
# Neo4j connection
NEO4J_URI=neo4j://localhost:7687           # Local: neo4j://localhost:7687
                                           # Aura: neo4j+s://xxxxx.neo4j.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password

# Flask configuration
FLASK_ENV=development                      # or 'production'
SECRET_KEY=your-random-secret-key-here
HOST=0.0.0.0
PORT=5000                                  # Render overrides with $PORT env var
```

**Render Deployment**: Set these variables in Render dashboard → Web Service → Environment.

---

## Data Model

### Node Types (6)

| Type | Properties | Example |
|------|-----------|---------|
| **Mina** | id, nombre, ubicacion, estado, capacidad_ton | Cantera Norte, Zona A, activa, 10000t |
| **Camion** | id, modelo, capacidad_ton, estado | CAT 773, 30t, operativo |
| **Planta** | id, nombre, tipo, estado, capacidad_ton | Planta A, trituradora primaria, 100t/h |
| **Operador** | id, nombre, turno, experiencia | Carlos Mendez, diurno, 5 años |
| **Evento** | id, tipo, criticidad, descripcion | Falla trituradora, Alta |
| **Material** | id, nombre, tipo, unidad | Piedra caliza, stone, toneladas |

### Relationships (7 types)

All relationships are **directed**:

```
(Camion)-[:OPERA_EN]->(Mina)       # Truck operates at mine
(Camion)-[:TRANSPORTA]->(Planta)   # Truck transports to plant
(Operador)-[:USA]->(Camion)        # Operator drives truck
(Operador)-[:TRABAJA_EN]->(Mina)   # Operator works at mine
(Planta)-[:PROCESA]->(Material)    # Plant processes material
(Mina)-[:GENERA]->(Material)       # Mine generates material
(Evento)-[:AFECTA]->(Node)         # Event impacts any node
```

Total: **31 nodes**, **39 relationships** in sample dataset.

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "Equipo no encontrado" error | Sample data not imported | Run `python scripts/import_data.py` |
| Graph displays empty | Neo4j connection failed | Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env |
| Port 5000 already in use | Another app using port | `lsof -i :5000` (macOS/Linux) or kill in Task Manager (Windows) |
| Cytoscape not rendering | JavaScript error | Check browser console (F12) for errors |
| Render deployment fails | Build or start command issue | Check Render logs; ensure Procfile is `web: gunicorn app:app` |
| 502 Bad Gateway on Render | Neo4j Aura not reachable | Verify firewall allows Render IP range to Neo4j port 7687 |

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production troubleshooting.

---

## Technology Stack

### Frontend
- **Cytoscape.js** — WebGL graph rendering (100+ nodes smoothly)
- **HTML5 / CSS3** — Semantic markup and responsive design
- **Vanilla JavaScript** — No framework dependencies; ~500 lines

### Backend
- **Flask 3.1** — Minimal Python web framework
- **Neo4j Driver 5.28** — Property graph database access
- **Gunicorn 23.0** — Production WSGI server

### Database
- **Neo4j Community** — Native graph database
- **Neo4j Aura** (optional) — Managed cloud hosting

### DevOps
- **Render.com** — PaaS deployment (free tier available)
- **GitHub** — Version control & CI/CD trigger
- **Python-dotenv** — Environment management

### Monitoring & Logging
- **Flask development server** — Built-in for local testing
- **Gunicorn** — Production HTTP server
- **Render Logs** — Real-time deployment & runtime logs

---

## Performance

### Load Times
- First load: ~500ms (parallel fetch of graph + events + metrics)
- Graph render: ~200ms (Cytoscape layout)
- **Total**: ~700ms to interactive

### Simulation Times
- Tier 1 query: 50-100ms
- Tier 2 queries: 50-100ms per direct node
- JavaScript processing: 20-50ms
- **Total**: 100-250ms (instant user feedback)

### Scalability
- Up to 1000 nodes: no visual degradation
- Up to 100k edges: Cytoscape force-directed layout handles it
- Query time: O(edges traversed), not O(all nodes)

See [ARCHITECTURE.md](docs/ARCHITECTURE.md#performance-characteristics) for detailed analysis.

---

## Deployment Checklist

### Development
- [ ] Clone repo
- [ ] Create venv & install requirements.txt
- [ ] Set .env with local Neo4j URI
- [ ] Run `python scripts/import_data.py`
- [ ] Start Flask: `python app.py`
- [ ] Verify graph at http://localhost:5000

### Production (Render + Neo4j Aura)
- [ ] Create Neo4j Aura instance (free 3GB, 2 years)
- [ ] Create Render Web Service (connect GitHub repo)
- [ ] Set Render environment variables (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, etc.)
- [ ] Push to GitHub (auto-deploy)
- [ ] Import data: `python scripts/import_data.py` (pointing to Aura)
- [ ] Test API: `curl https://your-app.onrender.com/api/graph`
- [ ] Verify simulation works and displays two-tier colors

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed step-by-step guide.

---

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, two-tier traversal logic, performance characteristics
- **[API.md](docs/API.md)** — Complete REST endpoint reference with examples
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Production setup (Render + Neo4j Aura), troubleshooting, monitoring

---

## Contributing

### Add a New Node Type
1. Add CSV in `scripts/data/`
2. Update `scripts/import_data.py` with import logic
3. Add color in `static/js/app.js`: `NODE_COLORS`
4. Add shape in `static/js/app.js`: `NODE_SHAPES`
5. Update `_DIRECT_QUERIES` and `_INDIRECT_QUERIES` in `app.py` if new relationships exist

### Add a New Relationship
1. Create in `scripts/import_data.py`
2. Update `_DIRECT_QUERIES` and `_INDIRECT_QUERIES` with traversal logic
3. Document impact semantics (forward, backward, or terminal)

### Add Analytics
1. Create new endpoint in `app.py` with Cypher query
2. Return JSON response
3. Call from `static/js/app.js` and render in UI

---

## Roadmap

### Short-term
- [ ] Real-time incident ingestion (Kafka / WebSocket)
- [ ] User authentication (Flask-Login)
- [ ] Dark mode toggle

### Medium-term
- [ ] Advanced filtering (multi-select, date range)
- [ ] Historical impact analysis (replay past faults)
- [ ] Automated alerts on threshold breaches
- [ ] SCADA system integration (real-time telemetry)

### Long-term
- [ ] Machine learning for impact prediction
- [ ] Recommendation engine (maintenance suggestions)
- [ ] Multi-site federation (multiple mines in one org)
- [ ] Mobile app (React Native / Flutter)

---

## Costs

| Component | Cost |
|-----------|------|
| Render Web Service (Free) | $0/month |
| Render Web Service (Starter) | $7/month |
| Neo4j Aura (Free tier) | $0/month (3GB, 2 years) |
| Neo4j Aura (Professional) | $99+/month |
| Custom domain | ~$10/year |

**Recommended for small deployments**: Free Render + Free Aura = **$0/month**

---

## Support

- **Documentation**: See [docs/](docs/) folder
- **Issues**: GitHub Issues (when repository is public)
- **Email**: [your-contact@example.com]

---

## License

MIT License — See LICENSE file for details

---

## Acknowledgments

Built with:
- [Cytoscape.js](https://js.cytoscape.org/) for graph visualization
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Neo4j](https://neo4j.com/) for the property graph database
- [Render](https://render.com/) for platform-as-a-service hosting

---

**Ready to deploy?** Start with [DEPLOYMENT.md](docs/DEPLOYMENT.md) → create a Render account → connect Neo4j Aura → push to GitHub.

Your operational analytics platform will be live in under 10 minutes. 🚀
