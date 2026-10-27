# StoneLink Deployment Guide

## Deployment to Render.com

### Prerequisites
- GitHub account with repository pushed
- Render.com account (free tier available)
- Neo4j instance (Aura cloud or self-hosted)

### Step 1: Prepare GitHub Repository

```bash
cd stonelink
git init
git add .
git commit -m "Initial: StoneLink with two-tier impact analysis"
git remote add origin https://github.com/yourusername/stonelink.git
git push -u origin main
```

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) and sign in
2. Click **New +** → **Web Service**
3. Select **GitHub** and authorize
4. Select your `stonelink` repository
5. Configure settings:
   - **Name**: `stonelink-api` (or your choice)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Region**: Choose closest to your users
   - **Instance Type**: Free (or Starter paid for production)

6. Click **Create Web Service**

### Step 3: Set Up Neo4j

#### Option A: Neo4j Aura (Recommended for Cloud)

1. Go to [aura.neo4j.io](https://aura.neo4j.io)
2. Sign up / log in with Google or email
3. Click **Create AuraDB Instance**
4. Select **Free** (3GB, 2 years free)
5. Click **Create**
6. Copy the connection details:
   - URI: `neo4j+s://xxxxxxxx.neo4j.io`
   - Username: `neo4j`
   - Password: (shown once, save it!)
7. Download Neo4j's recommended driver (neo4j-python)

#### Option B: Self-Hosted (EC2, DigitalOcean, etc.)

1. Provision a server (1 vCPU, 2GB RAM minimum)
2. SSH into the server
3. Install Neo4j Community:
   ```bash
   curl https://dist.neo4j.org/neo4j-community-latest-unix.tar.gz | tar xzv
   cd neo4j-latest-unix
   bin/neo4j start
   ```
4. Access at `http://your-server-ip:7474`
5. Change password (default: neo4j/neo4j)
6. Expose Bolt port (7687) to Render's IP range in firewall rules
7. Use URL format: `bolt://your-server-ip:7687`

### Step 4: Configure Environment Variables in Render

In Render dashboard:
1. Go to your Web Service → **Environment**
2. Add the following variables:

```
NEO4J_URI=neo4j+s://your-aura-host.neo4j.io:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
FLASK_ENV=production
SECRET_KEY=your-random-secret-key-here
HOST=0.0.0.0
PORT=10000
```

**Note**: Render assigns `PORT=10000`; our app will respect `$PORT` from environment.

To generate a secure `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Import Sample Data

After Neo4j is running (cloud or self-hosted):

1. Clone the repo locally:
   ```bash
   git clone https://github.com/yourusername/stonelink.git
   cd stonelink
   ```

2. Create `.env` with your Neo4j credentials:
   ```env
   NEO4J_URI=neo4j+s://your-aura-host.neo4j.io:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   ```

3. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Import data:
   ```bash
   python scripts/import_data.py
   ```

   Output:
   ```
   === StoneLink - Importacion de datos ===
   Limpiando base de datos...
   Importando nodos...
     4 minas importadas
     3 plantas importadas
     5 camiones importados
     6 operadores importados
     8 eventos importados
     5 materiales importados
   Creando relaciones...
     Relaciones creadas
   === Importacion completa ===
   ```

5. Verify data in Neo4j:
   - Aura: Open Neo4j Browser from Aura console
   - Self-hosted: Visit `http://your-server:7474`
   - Run: `MATCH (n) RETURN count(n)` → Should return 31

### Step 6: Deploy to Render

Push to GitHub (Render auto-deploys):
```bash
git push origin main
```

**Monitor deployment:**
1. Go to Render dashboard → Your Web Service
2. Click **Logs** tab
3. Wait for "Listening on..." message

Expected logs:
```
Feb 15 10:23:45 AM  ==> Deploying...
Feb 15 10:24:12 AM  ==> Build successful
Feb 15 10:24:18 AM  ==> Launching application...
Feb 15 10:24:22 AM  Listening on 0.0.0.0:10000
```

### Step 7: Access Your Application

Your app is now live at:
```
https://stonelink-api-xxxxx.onrender.com
```

Test the API:
```bash
curl https://stonelink-api-xxxxx.onrender.com/api/graph | python -m json.tool | head -20
```

## Troubleshooting

### Build Fails: "ModuleNotFoundError: No module named 'flask'"

**Cause**: `requirements.txt` not found or missing dependencies

**Fix**:
```bash
# Ensure requirements.txt is in root
# Redeploy: Go to Render → Manual Deploy
```

### 502 Bad Gateway / App Won't Start

**Cause 1**: Neo4j connection failed

**Check**:
```bash
# In Render Logs, look for:
# "Connection error: Could not connect to neo4j://..."
# Verify:
# 1. NEO4J_URI is correct
# 2. Neo4j instance is running
# 3. Firewall allows connection (if self-hosted)
```

**Cause 2**: Gunicorn misconfiguration

**Fix**:
```
# Start Command should be: gunicorn app:app
# (NOT: gunicorn -b 0.0.0.0:5000 app:app)
# Render manages the port via $PORT env var
```

### "Equipo no encontrado" when simulating

**Cause**: Sample data not imported

**Fix**:
```bash
# Locally:
python scripts/import_data.py

# Then redeploy:
git add . && git commit -m "Data imported" && git push
```

### Graph/API returns empty

**Cause**: Neo4j connection successful but no data

**Check**:
```bash
# In Neo4j Browser:
MATCH (n) RETURN count(n)

# Should return 31 nodes. If 0:
# Re-run: python scripts/import_data.py
```

## Production Checklist

- [ ] Repository pushed to GitHub
- [ ] Render Web Service created
- [ ] Neo4j instance created (Aura or self-hosted)
- [ ] Environment variables set in Render:
  - [ ] `NEO4J_URI`
  - [ ] `NEO4J_USER`
  - [ ] `NEO4J_PASSWORD`
  - [ ] `SECRET_KEY`
  - [ ] `FLASK_ENV=production`
- [ ] Sample data imported
- [ ] Application loads at `https://your-app.onrender.com`
- [ ] Simulation works (POST `/api/simular_falla`)
- [ ] All metrics display correctly

## Monitoring & Maintenance

### Check Status
```bash
curl https://stonelink-api-xxxxx.onrender.com/api/graph | jq '.nodes | length'
# Should return: 31
```

### View Logs
Render Dashboard → Your Service → **Logs** tab
- Deploy logs: Shows build & startup
- Runtime logs: Show request activity & errors

### Restart Service
Render Dashboard → Your Service → **Settings** → **Manual Deploy**

### Scale Resources
For production:
1. Render Dashboard → Your Service → **Settings**
2. Change **Instance Type** to Starter ($7/month) or higher
3. Add **Autoscaling** if needed

### Backup Neo4j

**Aura**: Automatic daily backups included in free tier

**Self-hosted**: Use Neo4j backup:
```bash
neo4j/bin/neo4j-admin backup --to-path=/backups --database=neo4j
```

## Custom Domain Setup

1. Render Dashboard → Your Service → **Settings**
2. Under **Custom Domain**, add your domain (e.g., `stonelink.yourdomain.com`)
3. Add Render's DNS CNAME record to your domain registrar
4. Wait for DNS propagation (~24 hours)
5. HTTPS auto-enabled with Let's Encrypt

## Costs

| Component | Cost |
|-----------|------|
| Render Web Service (Free) | $0/month |
| Render Web Service (Starter) | $7/month |
| Neo4j Aura (Free tier) | $0/month (3GB, 2 years) |
| Neo4j Aura (Professional) | $99/month |
| Custom domain | ~$10/year |

**Recommended for small deployments**: Free Render + Free Aura = $0/month

## Next Steps

1. **Share the app**: Send teammates the URL
2. **Customize data**: Edit CSV files in `scripts/data/` and re-import
3. **Add monitoring**: Integrate Sentry for error tracking
4. **Set up CI/CD**: GitHub Actions for automated testing before deploy

See [README.md](../README.md) for features & usage.
