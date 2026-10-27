const NODE_COLORS = {
    Mina: '#f59e0b',
    Planta: '#3b82f6',
    Camion: '#22c55e',
    Operador: '#06b6d4',
    Evento: '#ef4444',
    Material: '#a855f7',
};

const NODE_SHAPES = {
    Mina: 'diamond',
    Planta: 'round-rectangle',
    Camion: 'triangle',
    Operador: 'ellipse',
    Evento: 'octagon',
    Material: 'hexagon',
};

// Relationship colours and readable text (the edge label only shows on hover / selection).
const REL_COLORS = {
    OPERA_EN:   '#f59e0b',
    TRANSPORTA: '#22c55e',
    PROCESA:    '#3b82f6',
    GENERA:     '#a855f7',
    TRABAJA_EN: '#06b6d4',
    USA:        '#0e7490',
};

const REL_TEXT = {
    OPERA_EN:   'opera en',
    TRANSPORTA: 'transporta a',
    PROCESA:    'procesa',
    GENERA:     'genera',
    TRABAJA_EN: 'trabaja en',
    USA:        'usa',
};

const CRIT_COLORS = { Alta: '#ef4444', Media: '#f59e0b', Baja: '#eab308' };
const CRIT_RANK = { Alta: 3, Media: 2, Baja: 1 };

// Eventos are not drawn as nodes: each asset they affect gets a coloured ring
// (worst criticality) and a badge with the number of open events.
const BADGE_OFFSET = { x: 22, y: -22 };

const LAYOUT_KEY = 'stonelink-layout';

let cy;
let allElements = { nodes: [], edges: [] };
let flowPositions = {};   // column positions from the server, to come back from "Agrupado"
let _dbPollInterval = null;
let _dbPollSeconds = 0;

document.addEventListener('DOMContentLoaded', init);

window.addEventListener('resize', () => {
    if (cy) { cy.resize(); cy.fit(cy.nodes(), 40); }
});

// ── DB status / offline overlay ───────────────────────────────────────────────

function showDbOffline() {
    document.getElementById('db-offline-overlay').classList.add('visible');
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');
    dot.classList.add('offline');
    txt.textContent = 'BD OFFLINE';
}

function hideDbOffline() {
    document.getElementById('db-offline-overlay').classList.remove('visible');
    const dot = document.getElementById('status-dot');
    const txt = document.getElementById('status-text');
    dot.classList.remove('offline');
    txt.textContent = 'SISTEMA ACTIVO';
}

function updateDbTimer() {
    _dbPollSeconds++;
    const el = document.getElementById('db-offline-timer');
    if (el) el.textContent = `Esperando conexión… ${_dbPollSeconds}s`;
}

async function checkDbStatus() {
    try {
        const res = await fetch('/api/status', { cache: 'no-store' });
        return res.ok;
    } catch {
        return false;
    }
}

async function waitForDb() {
    showDbOffline();
    _dbPollSeconds = 0;
    return new Promise(resolve => {
        const timer = setInterval(updateDbTimer, 1000);
        _dbPollInterval = setInterval(async () => {
            if (await checkDbStatus()) {
                clearInterval(_dbPollInterval);
                clearInterval(timer);
                _dbPollInterval = null;
                hideDbOffline();
                resolve();
            }
        }, 5000);
    });
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function init() {
    initCytoscape();

    const online = await checkDbStatus();
    if (!online) await waitForDb();

    await Promise.all([
        loadGraph(),
        loadEventos(),
        loadMetricas(),
    ]);
    buildFlowBar();
    buildLegend();
    buildFilters();
    populateSimSelect();
}

function initCytoscape() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            {
                selector: 'node',
                style: {
                    'label': 'data(display)',
                    'background-color': function(ele) { return NODE_COLORS[ele.data('label')] || '#64748b'; },
                    'shape': function(ele) { return NODE_SHAPES[ele.data('label')] || 'ellipse'; },
                    'width': 45,
                    'height': 45,
                    'font-size': '10px',
                    'color': '#e2e8f0',
                    'text-valign': 'bottom',
                    'text-margin-y': 6,
                    'text-outline-color': '#0a0e17',
                    'text-outline-width': 2,
                    'border-width': 2,
                    'border-color': function(ele) { return NODE_COLORS[ele.data('label')] || '#64748b'; },
                    'border-opacity': 0.5,
                    'background-opacity': 0.85,
                    'text-max-width': '80px',
                    'text-wrap': 'ellipsis',
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1.5,
                    'line-color': function(ele) { return REL_COLORS[ele.data('label')] || '#2d3a4f'; },
                    'target-arrow-color': function(ele) { return REL_COLORS[ele.data('label')] || '#2d3a4f'; },
                    'line-opacity': 0.45,
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'font-size': '9px',
                    'color': '#e2e8f0',
                    'text-rotation': 'autorotate',
                    'text-outline-color': '#0a0e17',
                    'text-outline-width': 2,
                    'arrow-scale': 0.7,
                }
            },
            {
                // Label only on demand: hovering a node or edge, or a highlighted neighbourhood
                selector: 'edge.con-rotulo, edge.highlighted-edge',
                style: {
                    'label': function(ele) { return REL_TEXT[ele.data('label')] || ele.data('label'); },
                    'line-opacity': 1,
                    'width': 2.5,
                    'z-index': 20,
                }
            },
            {
                selector: 'node.con-alerta',
                style: {
                    'border-width': 4,
                    'border-color': function(ele) { return CRIT_COLORS[ele.data('criticidad_max')] || '#ef4444'; },
                    'border-opacity': 1,
                }
            },
            {
                selector: 'node.marca',
                style: {
                    'shape': 'ellipse',
                    'width': 18,
                    'height': 18,
                    'background-color': function(ele) { return CRIT_COLORS[ele.data('criticidad_max')] || '#ef4444'; },
                    'background-opacity': 1,
                    'border-width': 2,
                    'border-color': '#0a0e17',
                    'border-opacity': 1,
                    'label': 'data(display)',
                    'font-size': '10px',
                    'font-weight': 'bold',
                    'color': '#0a0e17',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'text-margin-y': 0,
                    'text-outline-width': 0,
                    'z-index': 40,
                    'events': 'no',
                }
            },
            {
                selector: 'node:active',
                style: {
                    'overlay-opacity': 0.1,
                    'overlay-color': '#f59e0b',
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'border-width': 4,
                    'border-color': '#f59e0b',
                    'background-opacity': 1,
                    'z-index': 10,
                }
            },
            {
                selector: '.highlighted-edge',
                style: {
                    'width': 3,
                    'line-color': '#f59e0b',
                    'target-arrow-color': '#f59e0b',
                }
            },
            {
                selector: '.faded',
                style: {
                    'opacity': 0.15,
                }
            },
            // ── Fault simulation tiers ────────────────────────────────────────
            {
                // The selected failed node — strongest red border + glow
                selector: '.impact-target',
                style: {
                    'border-width': 7,
                    'border-color': '#ef4444',
                    'border-opacity': 1,
                    'background-opacity': 1,
                    'z-index': 30,
                    'shadow-blur': 18,
                    'shadow-color': '#ef4444',
                    'shadow-opacity': 0.7,
                    'shadow-offset-x': 0,
                    'shadow-offset-y': 0,
                }
            },
            {
                // Tier 1: directly impacted nodes — solid red border
                selector: '.impact-direct',
                style: {
                    'border-width': 4,
                    'border-color': '#ef4444',
                    'border-opacity': 1,
                    'background-opacity': 1,
                    'z-index': 20,
                }
            },
            {
                // Tier 2: indirectly impacted nodes — amber/yellow border
                selector: '.impact-indirect',
                style: {
                    'border-width': 4,
                    'border-color': '#eab308',
                    'border-opacity': 1,
                    'background-opacity': 1,
                    'z-index': 10,
                }
            },
            {
                // Edges between target ↔ direct or direct ↔ direct
                selector: '.edge-direct',
                style: {
                    'width': 3,
                    'line-color': '#ef4444',
                    'target-arrow-color': '#ef4444',
                }
            },
            {
                // Edges between direct ↔ indirect nodes
                selector: '.edge-indirect',
                style: {
                    'width': 2.5,
                    'line-color': '#eab308',
                    'target-arrow-color': '#eab308',
                }
            },
            // ─────────────────────────────────────────────────────────────────
            {
                selector: '.dimmed',
                style: {
                    'opacity': 0.08,
                }
            },
            {
                selector: ':selected',
                style: {
                    'border-width': 4,
                    'border-color': '#f59e0b',
                }
            },
        ],
        layout: { name: 'preset' },
        wheelSensitivity: 0.3,
        minZoom: 0.3,
        maxZoom: 3,
    });

    cy.on('tap', 'node', onNodeTap);
    cy.on('tap', function(e) {
        if (e.target === cy) {
            hideTooltip();
            unhighlightAll();
        }
    });
    cy.on('mouseover', 'node', onNodeHover);
    cy.on('mouseout', 'node', e => {
        hideTooltip();
        e.target.connectedEdges().removeClass('con-rotulo');
    });
    cy.on('mouseover', 'edge', e => e.target.addClass('con-rotulo'));
    cy.on('mouseout', 'edge', e => e.target.removeClass('con-rotulo'));
    // Badges follow their asset when it is dragged.
    cy.on('position', 'node.con-alerta', e => placeBadge(e.target));
}

async function loadGraph() {
    const res = await fetch('/api/graph');
    if (!res.ok) return;
    const data = await res.json();
    allElements = data;

    // Eventos become marks on the asset they AFFECT instead of nodes of their own.
    const eventoIds = new Set(data.nodes.filter(n => n.data.label === 'Evento').map(n => n.data.id));
    const eventoById = Object.fromEntries(data.nodes.filter(n => eventoIds.has(n.data.id)).map(n => [n.data.id, n.data]));
    const eventosPorEquipo = {};
    data.edges.forEach(e => {
        if (e.data.label === 'AFECTA' && eventoIds.has(e.data.source)) {
            (eventosPorEquipo[e.data.target] ||= []).push(eventoById[e.data.source]);
        }
    });

    const nodes = data.nodes.filter(n => !eventoIds.has(n.data.id));
    const edges = data.edges.filter(e => !eventoIds.has(e.data.source) && !eventoIds.has(e.data.target));
    nodes.forEach(n => {
        const evs = eventosPorEquipo[n.data.id];
        if (!evs) return;
        n.data.eventos = evs;
        n.data.criticidad_max = evs.reduce((a, ev) => (CRIT_RANK[ev.criticidad] || 0) > (CRIT_RANK[a] || 0) ? ev.criticidad : a, null);
        n.classes = 'con-alerta';
    });

    cy.add(nodes);
    cy.add(edges);
    cy.nodes('.con-alerta').forEach(n => {
        cy.add({
            group: 'nodes',
            data: {
                id: `marca-${n.id()}`,
                label: 'Marca',
                parentAsset: n.id(),
                display: String(n.data('eventos').length),
                criticidad_max: n.data('criticidad_max'),
            },
            classes: 'marca',
            grabbable: false,
            selectable: false,
        });
        placeBadge(n);
    });
    cy.nodes().not('.marca').forEach(n => { flowPositions[n.id()] = { ...n.position() }; });

    let saved = 'flujo';
    try { saved = localStorage.getItem(LAYOUT_KEY) || 'flujo'; } catch { /* storage blocked */ }
    setTimeout(() => {
        cy.resize();
        if (saved === 'agrupado') setLayout('agrupado', false);
        else cy.fit(cy.nodes(), 40);
    }, 400);
}

// "Flujo": columns by operational stage (server positions).
// "Agrupado": force layout, so each quarry sits with its trucks, operators and materials.
function setLayout(mode, animate = true) {
    document.querySelectorAll('.layout-btn').forEach(b => b.classList.toggle('active', b.dataset.layout === mode));
    try { localStorage.setItem(LAYOUT_KEY, mode); } catch { /* storage blocked */ }

    const common = { animate, animationDuration: 600, fit: true, padding: 40 };
    const options = mode === 'agrupado'
        ? {
            ...common,
            name: 'cose',
            randomize: false,
            nodeDimensionsIncludeLabels: true,
            idealEdgeLength: () => 90,
            nodeRepulsion: () => 9000,
            componentSpacing: 120,
            gravity: 0.25,
            numIter: 2500,
        }
        : { ...common, name: 'preset', positions: n => flowPositions[n.id()] };

    // Badges are not laid out: they follow their asset through the 'position' event.
    // The edges must be part of the collection, or cose sees every node as isolated.
    const assets = cy.nodes().not('.marca');
    assets.union(assets.connectedEdges()).layout(options).run();
}

function placeBadge(asset) {
    const pos = asset.position();
    cy.getElementById(`marca-${asset.id()}`).position({ x: pos.x + BADGE_OFFSET.x, y: pos.y + BADGE_OFFSET.y });
}

// Badges copy the visual state (faded / dimmed / highlighted) of their asset.
function syncBadges() {
    cy.nodes('.marca').forEach(b => {
        const asset = cy.getElementById(b.data('parentAsset'));
        ['faded', 'dimmed'].forEach(c => asset.hasClass(c) ? b.addClass(c) : b.removeClass(c));
    });
}

function runLayout() {
    // No layout needed — positions come pre-computed from the server
    // Just ensure the graph is fit to the viewport
    cy.fit(cy.nodes(), 40);
}

function onNodeTap(e) {
    const node = e.target;
    unhighlightAll();

    const neighborhood = node.neighborhood().add(node);
    cy.elements().not(neighborhood).addClass('faded');
    neighborhood.nodes().addClass('highlighted');
    neighborhood.edges().addClass('highlighted-edge');
    syncBadges();

    showTooltip(node, e.renderedPosition);
}

function onNodeHover(e) {
    e.target.connectedEdges().addClass('con-rotulo');
    showTooltip(e.target, e.renderedPosition);
}

function showTooltip(node, pos) {
    const tooltip = document.getElementById('node-tooltip');
    const data = node.data();
    const color = NODE_COLORS[data.label] || '#64748b';

    const skip = ['id', 'label', 'display', 'eventos', 'criticidad_max'];
    let propsHtml = '';
    for (const [k, v] of Object.entries(data)) {
        if (skip.includes(k)) continue;
        propsHtml += `<span class="tooltip-key">${k}</span><span class="tooltip-value">${v}</span>`;
    }
    for (const ev of data.eventos || []) {
        propsHtml += `<span class="tooltip-key" style="color:${CRIT_COLORS[ev.criticidad] || '#ef4444'}">${ev.criticidad}</span>` +
            `<span class="tooltip-value">${ev.tipo}</span>`;
    }

    tooltip.innerHTML = `
        <div class="tooltip-header">
            <div class="tooltip-dot" style="background:${color}"></div>
            <div>
                <div class="tooltip-name">${data.display}</div>
                <div class="tooltip-label">${data.label}</div>
            </div>
        </div>
        <div class="tooltip-props">${propsHtml}</div>
    `;

    const graphArea = document.querySelector('.graph-area');
    const rect = graphArea.getBoundingClientRect();
    let x = pos.x + 16;
    let y = pos.y - 16;
    if (x + 260 > rect.width) x = pos.x - 260;
    if (y + 200 > rect.height) y = pos.y - 200;
    if (y < 0) y = 16;

    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
    tooltip.classList.add('visible');
}

function hideTooltip() {
    document.getElementById('node-tooltip').classList.remove('visible');
}

function unhighlightAll() {
    cy.elements().removeClass(
        'highlighted highlighted-edge faded dimmed ' +
        'impact-target impact-direct impact-indirect edge-direct edge-indirect'
    );
}

// Events
async function loadEventos() {
    const res = await fetch('/api/eventos');
    if (!res.ok) return;
    const data = await res.json();
    const list = document.getElementById('events-list');
    document.getElementById('event-count').textContent = data.length;

    list.innerHTML = data.map(e => `
        <div class="event-card ${e.criticidad.toLowerCase()}" onclick="focusEvent('${e.equipo}')">
            <div class="event-header">
                <span class="event-type">${e.tipo}</span>
                <span class="event-badge ${e.criticidad.toLowerCase()}">${e.criticidad}</span>
            </div>
            <div class="event-desc">${e.descripcion}</div>
            <div class="event-target">&#9654; ${e.equipo}</div>
        </div>
    `).join('');
}

function focusEvent(equipo) {
    unhighlightAll();
    const target = cy.nodes().filter(n => {
        const d = n.data();
        return d.nombre === equipo || d.modelo === equipo;
    });
    if (target.length) {
        const neighborhood = target.neighborhood().add(target);
        cy.elements().not(neighborhood).addClass('faded');
        neighborhood.nodes().addClass('highlighted');
        neighborhood.edges().addClass('highlighted-edge');
        syncBadges();
        cy.animate({ center: { eles: target }, zoom: 1.5 }, { duration: 500 });
    }
}

// Metrics
async function loadMetricas() {
    const res = await fetch('/api/metricas');
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById('header-metrics');

    const counts = data.conteo_nodos;
    const items = [
        { label: 'Minas', value: counts.Mina || 0 },
        { label: 'Plantas', value: counts.Planta || 0 },
        { label: 'Camiones', value: counts.Camion || 0 },
        { label: 'Operadores', value: counts.Operador || 0 },
        { label: 'Alertas', value: (data.eventos_criticidad.Alta || 0) },
    ];

    container.innerHTML = items.map(i => `
        <div class="header-metric">
            <div class="value">${i.value}</div>
            <div class="label">${i.label}</div>
        </div>
    `).join('');
}

// Filters
function buildFilters() {
    const types = Object.keys(NODE_COLORS);
    const container = document.getElementById('filter-chips');
    container.innerHTML = `<button class="filter-chip active" data-type="all" onclick="toggleFilter(this)">Todos</button>` +
        types.map(t => `<button class="filter-chip" data-type="${t}" onclick="toggleFilter(this)">${t}</button>`).join('');
}

function toggleFilter(chip) {
    const type = chip.dataset.type;
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');

    if (type === 'all') {
        cy.elements().removeClass('dimmed');
        return;
    }

    // "Evento" shows the assets that carry an event mark.
    const matches = n => type === 'Evento' ? n.hasClass('con-alerta') : n.data('label') === type;
    cy.nodes().not('.marca').forEach(n => {
        if (matches(n)) {
            n.removeClass('dimmed');
            n.connectedEdges().removeClass('dimmed');
        } else {
            n.addClass('dimmed');
            n.connectedEdges().addClass('dimmed');
        }
    });
    syncBadges();
}

// Flow bar
function buildFlowBar() {
    const bar = document.getElementById('bottom-bar');
    const stages = [
        { icon: '⛏', name: 'Extraccion', detail: 'Canteras activas' },
        { icon: '⭢', name: 'Transporte', detail: 'Flota de camiones' },
        { icon: '⚙', name: 'Trituracion', detail: 'Plantas primarias' },
        { icon: '▦', name: 'Clasificacion', detail: 'Separacion por tamano' },
        { icon: '✓', name: 'Producto', detail: 'Material procesado' },
    ];

    const flowHtml = stages.map((s, i) => {
        let html = `<div class="flow-stage">
            <span class="flow-stage-icon">${s.icon}</span>
            <div class="flow-stage-info">
                <span class="flow-stage-name">${s.name}</span>
                <span class="flow-stage-detail">${s.detail}</span>
            </div>
        </div>`;
        if (i < stages.length - 1) html += '<span class="flow-arrow">&#10132;</span>';
        return html;
    }).join('');

    bar.innerHTML = `<span class="flow-label">Flujo Operacional</span>${flowHtml}`;
}

// Legend
function buildLegend() {
    const container = document.getElementById('legend');
    const nodos = Object.entries(NODE_COLORS).filter(([type]) => type !== 'Evento').map(([type, color]) => `
        <div class="legend-item">
            <div class="legend-dot" style="background:${color}"></div>
            <span>${type}</span>
        </div>
    `).join('');
    const marcas = Object.entries(CRIT_COLORS).map(([crit, color]) => `
        <div class="legend-item">
            <div class="legend-dot legend-ring" style="border-color:${color}"></div>
            <span>Evento ${crit.toLowerCase()}</span>
        </div>
    `).join('');
    const relaciones = Object.entries(REL_COLORS).map(([rel, color]) => `
        <div class="legend-item">
            <div class="legend-line" style="background:${color}"></div>
            <span>${REL_TEXT[rel]}</span>
        </div>
    `).join('');
    container.innerHTML = nodos + marcas +
        `<div class="legend-subtitle">Relaciones</div>` + relaciones;
}

// Simulation
function populateSimSelect() {
    const select = document.getElementById('sim-select');
    const equipos = new Set();
    cy.nodes().forEach(n => {
        const d = n.data();
        if (['Mina', 'Planta', 'Camion'].includes(d.label)) {
            equipos.add(d.display);
        }
    });

    select.innerHTML = '<option value="">Seleccionar equipo...</option>' +
        [...equipos].sort().map(e => `<option value="${e}">${e}</option>`).join('');
}

async function simulateFault() {
    const select = document.getElementById('sim-select');
    const equipo = select.value;
    if (!equipo) return;

    const res = await fetch('/api/simular_falla', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ equipo }),
    });

    if (!res.ok) return;
    const data = await res.json();

    unhighlightAll();
    cy.elements().addClass('dimmed');

    const targetId    = data.target_id;
    const directIds   = new Set(data.direct_ids);
    const indirectIds = new Set(data.indirect_ids);
    // Union of all impacted IDs (used to undim edges)
    const allImpacted = new Set([targetId, ...directIds, ...indirectIds]);

    // ── Nodes ────────────────────────────────────────────────────────────────
    cy.nodes().forEach(n => {
        const nid = n.data('id');
        if (nid === targetId) {
            n.removeClass('dimmed').addClass('impact-target');
        } else if (directIds.has(nid)) {
            n.removeClass('dimmed').addClass('impact-direct');
        } else if (indirectIds.has(nid)) {
            n.removeClass('dimmed').addClass('impact-indirect');
        }
    });
    syncBadges();

    // ── Edges ─────────────────────────────────────────────────────────────────
    // An edge is shown only when at least one endpoint is in the impacted set.
    // Edges between high-severity nodes inherit the higher-severity colour.
    cy.edges().forEach(e => {
        const src = e.data('source');
        const tgt = e.data('target');
        if (!allImpacted.has(src) && !allImpacted.has(tgt)) return;

        e.removeClass('dimmed');

        const srcIsHigh = (src === targetId || directIds.has(src));
        const tgtIsHigh = (tgt === targetId || directIds.has(tgt));
        const srcIsLow  = indirectIds.has(src);
        const tgtIsLow  = indirectIds.has(tgt);

        if (srcIsHigh && tgtIsHigh) {
            e.addClass('edge-direct');
        } else if ((srcIsHigh && tgtIsLow) || (srcIsLow && tgtIsHigh)) {
            e.addClass('edge-indirect');
        }
        // Edge touching only indirect nodes or leaving the impacted subgraph
        // remains undimmed but unstyled (shows default edge colour).
    });

    // ── Focus ─────────────────────────────────────────────────────────────────
    const targetNode = cy.getElementById(targetId);
    if (targetNode.length) {
        cy.animate({ center: { eles: targetNode }, zoom: 1.3 }, { duration: 500 });
    }

    showImpactPanel(data);
    document.getElementById('sim-reset').style.display = 'block';
}

function showImpactPanel(data) {
    const panel   = document.getElementById('impact-overlay');
    const content = document.getElementById('impact-content');

    // Group nodes by label within each tier
    const groupDirect   = groupByLabel(data.direct_nodes   || []);
    const groupIndirect = groupByLabel(data.indirect_nodes || []);

    const directCount   = (data.direct_ids   || []).length;
    const indirectCount = (data.indirect_ids || []).length;

    let html = `
        <div class="impact-fault-target">
            <span class="impact-fault-dot"></span>
            <span class="impact-fault-name">${data.target}</span>
            <span class="impact-fault-label">${data.target_label}</span>
        </div>`;

    // ── Tier 1: Direct ───────────────────────────────────────────────────────
    html += `
        <div class="impact-tier">
            <div class="impact-tier-header direct">
                <span class="impact-tier-dot direct"></span>
                <span class="impact-tier-label">Impacto Directo</span>
                <span class="impact-tier-count direct">${directCount}</span>
            </div>`;

    if (directCount === 0) {
        html += `<p class="impact-empty">Sin impacto directo</p>`;
    } else {
        for (const [label, names] of Object.entries(groupDirect)) {
            html += `
            <div class="impact-section">
                <div class="impact-section-title">${label}</div>
                ${names.map(n => `<div class="impact-item direct">${n}</div>`).join('')}
            </div>`;
        }
    }
    html += `</div>`;

    // ── Tier 2: Indirect ─────────────────────────────────────────────────────
    html += `
        <div class="impact-tier">
            <div class="impact-tier-header indirect">
                <span class="impact-tier-dot indirect"></span>
                <span class="impact-tier-label">Impacto Indirecto</span>
                <span class="impact-tier-count indirect">${indirectCount}</span>
            </div>`;

    if (indirectCount === 0) {
        html += `<p class="impact-empty">Sin impacto indirecto</p>`;
    } else {
        for (const [label, names] of Object.entries(groupIndirect)) {
            html += `
            <div class="impact-section">
                <div class="impact-section-title">${label}</div>
                ${names.map(n => `<div class="impact-item indirect">${n}</div>`).join('')}
            </div>`;
        }
    }
    html += `</div>`;

    content.innerHTML = html;
    panel.classList.add('visible');
}

function groupByLabel(nodes) {
    const groups = {};
    nodes.forEach(n => {
        if (!groups[n.label]) groups[n.label] = [];
        groups[n.label].push(n.nombre);
    });
    return groups;
}

function closeImpact() {
    document.getElementById('impact-overlay').classList.remove('visible');
}

function resetSimulation() {
    unhighlightAll();
    closeImpact();
    document.getElementById('sim-reset').style.display = 'none';
    document.getElementById('sim-select').value = '';
}
