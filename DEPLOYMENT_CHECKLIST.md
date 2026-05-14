# StoneLink Deployment Checklist

This checklist guides you through deploying StoneLink to production on Render + Neo4j Aura.

---

## Phase 1: Local Development (Verify Everything Works)

- [ ] **Python Environment**
  - [ ] Python 3.8+ installed
  - [ ] Virtual environment created: `python -m venv venv`
  - [ ] Activated: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)
  - [ ] Dependencies installed: `pip install -r requirements.txt`

- [ ] **Neo4j Local Instance**
  - [ ] Neo4j Community running (port 7687) or Neo4j Aura instance created
  - [ ] `.env` file created with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
  - [ ] Connection tested: `python neo4j_conn.py` (if script exists)

- [ ] **Sample Data Import**
  - [ ] Run: `python scripts/import_data.py`
  - [ ] Output shows: "4 minas, 5 camiones, 3 plantas, 6 operadores, 8 eventos, 5 materiales"
  - [ ] Verify in Neo4j Browser: `MATCH (n) RETURN count(n)` → Should return **31**

- [ ] **Flask Application**
  - [ ] Run: `python app.py`
  - [ ] Output shows: "Running on http://127.0.0.1:5000"
  - [ ] Open browser to http://localhost:5000
  - [ ] Graph displays with all 31 nodes and relationships visible

- [ ] **Fault Simulation Testing**
  - [ ] Click on a mine (e.g., "Cantera Central")
  - [ ] Click "Simular Impacto" button
  - [ ] Observe: Target node turns RED, direct impacts turn RED, indirect impacts turn YELLOW
  - [ ] Click different equipment types and verify impact colors
  - [ ] Verify no false positives (e.g., unrelated trucks not highlighted)

- [ ] **API Verification**
  - [ ] Test `/api/graph`: `curl http://localhost:5000/api/graph | python -m json.tool | head -30`
  - [ ] Test `/api/metricas`: `curl http://localhost:5000/api/metricas | python -m json.tool`
  - [ ] Test `/api/simular_falla`: `curl -X POST http://localhost:5000/api/simular_falla -H 'Content-Type: application/json' -d '{"equipo":"Cantera Central"}' | python -m json.tool`

---

## Phase 2: GitHub Repository Setup

- [ ] **Initialize Repository** (If not already done)
  ```bash
  cd stonelink
  git init
  git add .
  git commit -m "Initial: StoneLink operational analytics platform"
  git remote add origin https://github.com/yourusername/stonelink.git
  git branch -M main
  git push -u origin main
  ```

- [ ] **Verify Files Tracked**
  - [ ] `.gitignore` is respected (no `.env`, `venv/`, `__pycache__/`)
  - [ ] All source files committed: `app.py`, `requirements.txt`, `Procfile`, `runtime.txt`, `scripts/`, `static/`, `data/`, `docs/`, `templates/`
  - [ ] Repository visible on GitHub at `https://github.com/yourusername/stonelink`

---

## Phase 3: Neo4j Aura Setup (Recommended for Cloud)

- [ ] **Create Aura Instance**
  - [ ] Go to [aura.neo4j.io](https://aura.neo4j.io)
  - [ ] Sign up with Google or email
  - [ ] Click "Create AuraDB Instance"
  - [ ] Select **Free tier** (3GB, 2 years)
  - [ ] Click "Create"
  - [ ] Save connection details:
    - [ ] **URI**: `neo4j+s://xxxxxxxx.neo4j.io:7687`
    - [ ] **Username**: `neo4j`
    - [ ] **Password**: (shown once, save securely!)

- [ ] **Test Aura Connection Locally**
  ```bash
  # Update .env with Aura credentials
  NEO4J_URI=neo4j+s://your-aura-uri.neo4j.io:7687
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your-password
  
  # Test connection
  python -c "from neo4j_conn import run_query; print(run_query('MATCH (n) RETURN count(n)'))"
  ```

- [ ] **Import Sample Data to Aura**
  ```bash
  # With Aura URI in .env, run:
  python scripts/import_data.py
  
  # Verify in Aura Browser (from console):
  # MATCH (n) RETURN count(n)  → Should be 31
  ```

---

## Phase 4: Render.com Deployment

- [ ] **Create Render Account**
  - [ ] Go to [render.com](https://render.com)
  - [ ] Sign up (free tier available)
  - [ ] Authorize GitHub access

- [ ] **Create Web Service**
  - [ ] Render Dashboard → **New +** → **Web Service**
  - [ ] Select your `stonelink` GitHub repository
  - [ ] Configure:
    - [ ] **Name**: `stonelink-api` (or your choice)
    - [ ] **Environment**: `Python 3`
    - [ ] **Build Command**: `pip install -r requirements.txt`
    - [ ] **Start Command**: `gunicorn app:app`
    - [ ] **Instance Type**: Free (or Starter $7/month for production)
    - [ ] **Region**: Closest to users
  - [ ] Click **Create Web Service**

- [ ] **Set Environment Variables in Render**
  - [ ] Go to your Web Service → **Environment**
  - [ ] Add these variables:
    ```
    NEO4J_URI=neo4j+s://your-aura-uri.neo4j.io:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your-aura-password
    FLASK_ENV=production
    SECRET_KEY=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">
    HOST=0.0.0.0
    PORT=10000
    ```
  - [ ] **Do NOT commit `SECRET_KEY` to GitHub** — set only in Render dashboard

- [ ] **Monitor Deployment**
  - [ ] Render Dashboard → Your Service → **Logs** tab
  - [ ] Wait for message: `Listening on 0.0.0.0:10000` (or equivalent)
  - [ ] Deployment time: ~2-3 minutes

- [ ] **Test Production URL**
  - [ ] Copy your service URL: `https://stonelink-api-xxxxx.onrender.com`
  - [ ] Test in browser: Open the URL in browser
  - [ ] Graph should load (may take ~30 seconds on free tier first load)
  - [ ] Test API: `curl https://stonelink-api-xxxxx.onrender.com/api/graph | python -m json.tool | head -20`
  - [ ] Test simulation: `curl -X POST https://stonelink-api-xxxxx.onrender.com/api/simular_falla -H 'Content-Type: application/json' -d '{"equipo":"Cantera Central"}'`

---

## Phase 5: Verification Checklist

- [ ] **Frontend**
  - [ ] Graph renders with all 31 nodes
  - [ ] Node colors match types (orange=Mina, green=Camion, blue=Planta, etc.)
  - [ ] Click node → neighborhood highlights
  - [ ] Filter buttons work (Minas, Camiones, etc.)

- [ ] **Fault Simulation**
  - [ ] Select equipment from dropdown
  - [ ] Click "Simular Impacto"
  - [ ] Target node: RED with glow
  - [ ] Direct impacts: RED border
  - [ ] Indirect impacts: YELLOW/amber border
  - [ ] Side panel shows "Impact Directo" and "Impact Indirecto" sections
  - [ ] Counts match API response

- [ ] **API Endpoints**
  - [ ] GET `/api/graph` → Returns nodes & edges
  - [ ] GET `/api/metricas` → Returns node counts by type
  - [ ] GET `/api/eventos` → Returns incident list sorted by criticality
  - [ ] GET `/api/flujo` → Returns operational flow
  - [ ] POST `/api/simular_falla` → Returns direct & indirect impact IDs
  - [ ] 404 error when equipment not found

- [ ] **Performance**
  - [ ] Graph load: < 2 seconds
  - [ ] Simulation response: < 300ms
  - [ ] No console errors (F12 → Console tab)

---

## Phase 6: Post-Deployment

- [ ] **Documentation Review**
  - [ ] README.md is readable and accurate
  - [ ] [ARCHITECTURE.md](docs/ARCHITECTURE.md) describes system correctly
  - [ ] [API.md](docs/API.md) has complete endpoint reference
  - [ ] [DEPLOYMENT.md](docs/DEPLOYMENT.md) matches your setup

- [ ] **Backup & Monitoring**
  - [ ] Neo4j Aura: Verify automatic daily backups enabled
  - [ ] Render: Set up email notifications for build/deploy failures
  - [ ] Monitor logs regularly: Render Dashboard → **Logs** tab

- [ ] **Optional: Custom Domain**
  - [ ] Render Dashboard → Your Service → **Settings** → **Custom Domain**
  - [ ] Add your domain (e.g., `stonelink.yourdomain.com`)
  - [ ] Add CNAME record to domain registrar
  - [ ] Wait for DNS propagation (~24 hours)
  - [ ] HTTPS auto-enabled

- [ ] **Share with Team**
  - [ ] Send your Render URL to teammates
  - [ ] Share [docs/API.md](docs/API.md) for developers
  - [ ] Share usage instructions from README.md

---

## Troubleshooting Quick Reference

| Problem | Command | Expected Result |
|---------|---------|-----------------|
| Check local graph | `curl http://localhost:5000/api/graph \| python -m json.tool \| head -20` | JSON with nodes array |
| Check local metricas | `curl http://localhost:5000/api/metricas` | JSON with conteo_nodos |
| Verify Neo4j connection | `python -c "from neo4j_conn import run_query; print(run_query('MATCH (n) RETURN count(n)'))"` | Integer (should be 31) |
| Check Render logs | Render Dashboard → Service → **Logs** | Build & runtime output |
| Restart Render service | Render Dashboard → Service → **Settings** → **Manual Deploy** | Service restarts |
| Test Aura connection | Neo4j Aura Console → Open Browser | Neo4j Browser interface |

---

## Success Criteria

Your deployment is complete when:

✅ Local app runs at http://localhost:5000 with all features  
✅ Sample data imported (31 nodes visible)  
✅ Fault simulation shows red/yellow colors correctly  
✅ Production URL at Render loads the app  
✅ API endpoints respond with correct data  
✅ No errors in Render logs  

---

## Next Steps

1. **Customize Data**: Edit CSV files in `scripts/data/` or `data/` folder, re-import
2. **Add Features**: See [ARCHITECTURE.md → Extensibility Points](docs/ARCHITECTURE.md#extensibility-points)
3. **Scale Up**: Render free tier → Starter ($7/month) for production traffic
4. **Integrate**: Connect to your SCADA systems or incident management tools

---

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed step-by-step guide.
