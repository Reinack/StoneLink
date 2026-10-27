# StoneLink - Quick Start Guide

**Repository Location**: `D:\Practicas\StoneLink`  
**Status**: ✅ Production-Ready | Git-Initialized | GitHub-Ready

---

## What's Included

✅ **Source Code**
- `app.py` — Flask backend with two-tier fault simulation
- `static/js/app.js` — Cytoscape.js visualization
- `static/css/style.css` — Impact coloring (red/yellow)
- `templates/index.html` — Single-page app template

✅ **Backend Integration**
- `neo4j_conn.py` — Neo4j database connection
- `scripts/import_data.py` — Data import automation
- `data/*.csv` — Sample dataset (31 nodes, 39 relationships)

✅ **Deployment Files**
- `requirements.txt` — Python dependencies (Flask, Neo4j, Gunicorn)
- `Procfile` — Render deployment config
- `runtime.txt` — Python version (3.13.9)
- `.gitignore` — Production-safe exclusions
- `.env.example` — Environment template

✅ **Documentation**
- `README.md` — Feature overview & quick-start
- `DEPLOYMENT_CHECKLIST.md` — Step-by-step verification
- `docs/ARCHITECTURE.md` — System design & two-tier logic
- `docs/API.md` — REST endpoint reference
- `docs/DEPLOYMENT.md` — Production setup guide

---

## 🚀 Start Local Development (5 minutes)

```bash
# 1. Navigate to directory
cd D:\Practicas\StoneLink

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (copy from template)
copy .env.example .env
# Edit .env with your Neo4j credentials:
# NEO4J_URI=neo4j://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password

# 5. Import sample data
python scripts/import_data.py

# 6. Start Flask server
python app.py
```

**Result**: Open http://localhost:5000 in your browser ✅

---

## 📊 Test the Application

### Verify Graph Loads
- [ ] Navigate to http://localhost:5000
- [ ] See 31 nodes with colors (mines=orange, trucks=green, plants=blue, etc.)
- [ ] All relationships visible

### Test Fault Simulation
1. Click on a mine (e.g., "Cantera Central")
2. Click "Simular Impacto" button
3. Observe:
   - Target mine: **RED with glow**
   - Direct impacts: **RED border**
   - Indirect impacts: **YELLOW/amber border**
   - Side panel: Shows "Impact Directo" and "Impact Indirecto" tiers

### Test API
```bash
# Get graph
curl http://localhost:5000/api/graph | python -m json.tool | head -30

# Get metrics
curl http://localhost:5000/api/metricas | python -m json.tool

# Simulate fault
curl -X POST http://localhost:5000/api/simular_falla ^
  -H "Content-Type: application/json" ^
  -d "{\"equipo\":\"Cantera Central\"}"
```

---

## 🌐 Deploy to Production (Render + Neo4j Aura)

See **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** for complete step-by-step guide.

Quick summary:
1. Create Neo4j Aura instance (free tier: 3GB, 2 years)
2. Create Render Web Service (connect GitHub)
3. Set environment variables in Render dashboard
4. Push to GitHub → **Auto-deploys** to Render

**Result**: Live at `https://your-app.onrender.com` ✅

---

## 📁 Directory Structure

```
D:\Practicas\StoneLink/
├── app.py                    # Flask backend
├── neo4j_conn.py             # Database connection
├── requirements.txt          # Dependencies
├── Procfile                  # Render config
├── runtime.txt               # Python version
├── .gitignore                # Git exclusions
├── .env.example              # Environment template
├── README.md                 # Full documentation
├── QUICK_START.md            # This file
├── DEPLOYMENT_CHECKLIST.md   # Deployment guide
│
├── static/
│   ├── js/
│   │   ├── app.js            # Visualization & simulation logic
│   │   └── cytoscape.min.js  # Graph library
│   └── css/
│       └── style.css         # Impact coloring
│
├── templates/
│   └── index.html            # Single-page app
│
├── scripts/
│   └── import_data.py        # Data import script
│
├── data/
│   ├── minas.csv             # Mining sites
│   ├── camiones.csv          # Trucks
│   ├── plantas.csv           # Processing plants
│   ├── operadores.csv        # Operators
│   ├── materiales.csv        # Materials
│   └── eventos.csv           # Incidents
│
└── docs/
    ├── ARCHITECTURE.md       # System design
    ├── API.md                # REST endpoints
    └── DEPLOYMENT.md         # Production setup
```

---

## 🔧 Configuration

### Environment Variables (.env)

```env
# Neo4j Connection
NEO4J_URI=neo4j://localhost:7687           # Local development
# OR neo4j+s://xxxxx.neo4j.io:7687         # Neo4j Aura (production)
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Flask
FLASK_ENV=development                      # or 'production'
SECRET_KEY=your-random-key-here           # Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
HOST=0.0.0.0
PORT=5000
```

### For Render Production
Set these in Render Dashboard → Web Service → Environment:
- `NEO4J_URI` → Your Neo4j Aura URI
- `NEO4J_USER` → neo4j
- `NEO4J_PASSWORD` → Your Aura password
- `FLASK_ENV` → production
- `SECRET_KEY` → Generate new one (don't commit!)

---

## 📊 Two-Tier Impact Analysis (Key Feature)

When equipment fails:

**Tier 1 (Direct Impact)** — Immediate operational dependency:
- Red borders on nodes directly connected to fault target
- Example: Cantera Central mine fails → trucks operating there are directly impacted

**Tier 2 (Indirect Impact)** — Secondary effects through intermediaries:
- Yellow/amber borders on nodes 2 hops away
- Example: Volvo A40 truck is directly impacted → Planta B (receives deliveries) is indirectly impacted

**No False Positives**: Terminal node classification prevents hub contamination
- Operadores (operators) don't expand further
- Materiales (materials) don't expand further
- Eventos (incidents) don't expand further

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed traversal logic.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Equipo no encontrado" error | Run `python scripts/import_data.py` to import sample data |
| Graph displays empty | Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env |
| Port 5000 already in use | Kill process: `netstat -ano \| findstr :5000` then `taskkill /PID <pid> /F` |
| Import script fails | Verify Neo4j is running and connection details are correct |
| Console errors (F12) | Check browser console for JavaScript errors |

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for more troubleshooting.

---

## 📚 Documentation

- **[README.md](README.md)** — Complete feature overview and usage
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design, two-tier logic, performance
- **[API.md](docs/API.md)** — REST endpoint reference with examples
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Production deployment guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** — Step-by-step verification

---

## 🎯 Next Steps

1. **Local Development**: Follow "Start Local Development" section above
2. **Verify Features**: Test graph load and fault simulation
3. **Production Setup**: Follow [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
4. **GitHub Push**: Initialize remote repo and push code
5. **Render Deploy**: Connect to Render via GitHub (auto-deploys on push)

---

## 📈 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Cytoscape.js (graph) + Vanilla JS + HTML5/CSS3 |
| **Backend** | Flask 3.1 + Python 3.13 |
| **Database** | Neo4j (property graph) |
| **Server** | Gunicorn (WSGI) |
| **Hosting** | Render.com (platform-as-a-service) |
| **Cloud DB** | Neo4j Aura (optional) |

---

## ✨ Features Implemented

✅ Real-time graph visualization (31 nodes, 39 relationships)  
✅ Two-tier fault impact analysis (direct vs indirect)  
✅ Red/yellow visual distinction  
✅ No false positives (terminal node classification)  
✅ 6 REST API endpoints  
✅ Production deployment ready (Render + Neo4j Aura)  
✅ Complete documentation  
✅ GitHub-ready code structure  

---

## 📞 Support

- Check [docs/](docs/) folder for detailed documentation
- Review [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for verification steps
- See [README.md](README.md) for feature overview

---

**Ready to launch?** Start with "Start Local Development" above, then follow [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for production. 🚀
