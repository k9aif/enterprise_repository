const app = document.getElementById("app");

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

async function api(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ── Config (server-provided — avoids baking any URL into this file) ────────
let CONTINUUM_URL = null;
async function loadConfig() {
  try {
    const cfg = await api("/api/v1/config");
    CONTINUUM_URL = cfg.continuum_url;
  } catch (e) {
    CONTINUUM_URL = "https://continuum.k9x.ai"; // last-resort fallback if /api/v1/config itself is unreachable
  }
  const headerLink = document.getElementById("continuum-link");
  const footerLink = document.getElementById("continuum-footer-link");
  if (headerLink) headerLink.href = CONTINUUM_URL;
  if (footerLink) footerLink.href = CONTINUUM_URL;
}

// ── Theme ──────────────────────────────────────────────────────────────────
const DARK_KEY = "k9repo_dark";
function initTheme() {
  if (localStorage.getItem(DARK_KEY) === "1") document.body.classList.add("dark");
  updateThemeIcon();
}
function toggleTheme() {
  const dark = document.body.classList.toggle("dark");
  localStorage.setItem(DARK_KEY, dark ? "1" : "0");
  updateThemeIcon();
}
function updateThemeIcon() {
  const btn = document.getElementById("theme-btn");
  if (btn) btn.textContent = document.body.classList.contains("dark") ? "☀️" : "🌙";
}

// ── Sidebar (categories) ──────────────────────────────────────────────────

async function loadSidebar() {
  try {
    const cats = await api("/api/v1/search/categories");
    document.getElementById("nav-frameworks").innerHTML =
      cats.frameworks.length
        ? cats.frameworks.map(f => `<li><a href="#/standards?framework=${encodeURIComponent(f)}">${esc(f)}</a></li>`).join("")
        : `<li class="muted">none yet</li>`;
    document.getElementById("nav-artifact-types").innerHTML =
      cats.artifact_types.length
        ? cats.artifact_types.map(t => `<li><a href="#/search?artifact_type=${encodeURIComponent(t)}">${esc(t)}</a></li>`).join("")
        : `<li class="muted">none yet</li>`;
  } catch (e) {
    // sidebar is a convenience, fail quietly
  }
}

// ── Landing page ─────────────────────────────────────────────────────────

const HOW_IT_WORKS = [
  { n: 1, title: "Discover", body: "Search by name, or browse by TOGAF framework or artifact type — the same way you'd browse a package registry, not a folder of documents." },
  { n: 2, title: "Inspect", body: "Open an entity's article page: the real artifact content — YAML, PlantUML, code, specs — not a link that might be stale or gone." },
  { n: 3, title: "Verify", body: "Check which standards it satisfies, its compliance assessment history, and any active dispensations before you trust it." },
  { n: 4, title: "Reuse", body: "Cite the captured git_ref and content hash back to your own project — full provenance, not copy-paste with no trail." },
];

const LEARN_CARDS = [
  {
    icon: "C", title: "TOGAF Enterprise Continuum",
    body: "The classification framework that organizes architecture assets from generic to organization-specific: Foundation → Common Systems → Industry → Organization-Specific. It's a lens, not a database — Architecture Building Blocks (ABBs, the logical “what”) on one side, Solution Building Blocks (SBBs, the physical “how”) on the other.",
  },
  {
    icon: "R", title: "This Repository",
    body: "The Continuum needs somewhere to actually store what it classifies — that's the Architecture Repository. This service is that store: real artifact content, a Standards Information Base (TOGAF/DoDAF/MODAF/NAF), and a Governance Log of compliance assessments and dispensations. Continuum is the workflow; this is the content.",
  },
  {
    icon: "K9", title: "K9-AIF is built on TOGAF",
    body: "Not a metaphor bolted on afterward — K9-AIF's own component model is ABB/SBB from the ground up: BaseAgent, BaseOrchestrator, BaseSquad are Foundation ABBs; every concrete agent you build is an SBB implementing one. This repository is believed to be the first governed, searchable artifact catalog built for agentic components on TOGAF terms.",
  },
];

const ECOSYSTEM = [
  { name: "K9X Continuum", color: "#6366f1", body: "The Enterprise Continuum classification and governance workflow this Repository stores artifacts for — submit, review, publish, promote.", urlKey: "continuum" },
  { name: "K9X Studio", color: "#8b5cf6", body: "Visual builder that composes Squads, Agents, and Orchestrators from the same ABB catalog this Repository documents.", urlKey: null },
  { name: "K9X HIL", color: "#10b981", body: "Kafka-native human-in-the-loop case management for AMBER/RED-zone touchpoints your agents escalate to.", urlKey: null },
];

function pageHome() {
  app.innerHTML = `
    <div class="landing-hero">
      <div class="landing-eyebrow">TOGAF Architecture Repository</div>
      <h1 class="landing-title">K9X Enterprise Repository</h1>
      <p class="landing-tagline">
        The governed, searchable store of real ABB/SBB artifacts, standards, and
        compliance history — the agentic world's counterpart to a UDDI service
        registry or an API catalog, built directly on TOGAF's own Architecture
        Repository structure.
      </p>
      <div class="landing-cta-row">
        <button class="btn btn-primary" onclick="location.hash='#/search'">Explore the Repository</button>
        <button class="btn btn-ghost" onclick="document.getElementById('learn-section').scrollIntoView({behavior:'smooth'})">How this works</button>
      </div>
    </div>

    <div class="landing-section">
      <div class="landing-section-label">How it works</div>
      <div class="landing-section-title">Four steps from search to trusted reuse</div>
      <div class="landing-steps">
        ${HOW_IT_WORKS.map((s, idx) => `
          <div class="landing-step-wrap">
            <div class="landing-step-card">
              <div class="landing-step-head">
                <div class="landing-step-badge">${s.n}</div>
              </div>
              <div class="landing-step-title">${esc(s.title)}</div>
              <div class="landing-step-body">${esc(s.body)}</div>
            </div>
            ${idx < HOW_IT_WORKS.length - 1 ? `<span class="landing-step-chevron">›</span>` : ""}
          </div>
        `).join("")}
      </div>
    </div>

    <div class="landing-section alt" id="learn-section">
      <div class="landing-section-label">Learn</div>
      <div class="landing-section-title">ABB, SBB, Continuum, Repository — what they actually mean here</div>
      <div class="landing-learn">
        ${LEARN_CARDS.map(c => `
          <div class="landing-learn-card">
            <div class="landing-learn-icon">${esc(c.icon)}</div>
            <div class="landing-learn-title">${esc(c.title)}</div>
            <div class="landing-learn-body">${esc(c.body)}</div>
          </div>
        `).join("")}
      </div>
    </div>

    <div class="landing-section">
      <div class="landing-section-label">The Wider Ecosystem</div>
      <div class="landing-section-title">K9-AIF is a framework — K9X is a growing ecosystem</div>
      <div class="landing-ecosystem">
        ${ECOSYSTEM.map(e => {
          const url = e.urlKey === "continuum" ? CONTINUUM_URL : null;
          return `
          <div class="landing-eco-card">
            <div class="landing-eco-icon" style="background:${e.color}1a;color:${e.color}">${esc(e.name[0])}</div>
            <div class="landing-eco-name">${url ? `<a href="${esc(url)}" target="_blank">${esc(e.name)} ↗</a>` : esc(e.name)}</div>
            <div class="landing-eco-body">${esc(e.body)}</div>
          </div>
        `;
        }).join("")}
      </div>
    </div>
  `;
}

// ── Search / entity / standards pages ───────────────────────────────────

async function pageSearch(params) {
  const q = params.get("q") || "";
  const artifact_type = params.get("artifact_type") || "";
  app.innerHTML = `<h1>Search</h1><p class="muted">Searching…</p>`;
  try {
    const url = new URL("/api/v1/search", location.origin);
    url.searchParams.set("q", q);
    if (artifact_type) url.searchParams.set("artifact_type", artifact_type);
    const data = await api(url.pathname + url.search);

    const entityCards = data.entities.map(e => `
      <div class="entity-card" onclick="location.hash='#/entity/${esc(e.entity_type)}/${esc(e.entity_id)}'">
        <div class="entity-card-type">${esc(e.entity_type.toUpperCase())} · ${esc(e.artifact_count)} artifact(s)</div>
        <div class="entity-card-name">${esc(e.entity_name)}</div>
        <div class="entity-card-meta">${esc(e.artifact_type)}</div>
      </div>`).join("") || `<p class="muted">No matching artifacts.</p>`;

    const standardCards = data.standards.map(s => `
      <div class="entity-card" onclick="location.hash='#/standards/${esc(s.id)}'">
        <div class="entity-card-type">STANDARD <span class="badge framework-${esc(s.framework)}">${esc(s.framework)}</span></div>
        <div class="entity-card-name">${esc(s.name)}</div>
        <div class="entity-card-meta">${esc(s.description || "")}</div>
      </div>`).join("") || `<p class="muted">No matching standards.</p>`;

    app.innerHTML = `
      <h1>Search results${q ? `: "${esc(q)}"` : ""}</h1>
      <h3 style="margin:20px 0 10px;font-size:12px;text-transform:uppercase;color:var(--text-muted)">Artifacts / Entities</h3>
      <div class="card-grid">${entityCards}</div>
      <h3 style="margin:20px 0 10px;font-size:12px;text-transform:uppercase;color:var(--text-muted)">Standards</h3>
      <div class="card-grid">${standardCards}</div>
    `;
  } catch (e) {
    app.innerHTML = `<h1>Search</h1><p class="muted">Search failed: ${esc(e.message)}</p>`;
  }
}

async function pageEntity(entityType, entityId) {
  app.innerHTML = `<p class="muted">Loading…</p>`;
  try {
    const data = await api(`/api/v1/entities/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`);
    const title = data.entity_name || `${entityType.toUpperCase()} #${entityId}`;

    const infobox = `
      <div class="infobox">
        <div class="infobox-title">${esc(title)}</div>
        <dl>
          <dt>Type</dt><dd>${esc(entityType.toUpperCase())}</dd>
          <dt>ID</dt><dd>${esc(entityId)}</dd>
          <dt>Artifacts</dt><dd>${data.artifacts.length}</dd>
          <dt>Standards satisfied</dt><dd>${data.standards.length}</dd>
          <dt>Active dispensations</dt><dd>${data.dispensations.filter(d => d.status === "active").length}</dd>
        </dl>
      </div>`;

    const artifactBlocks = data.artifacts.length
      ? data.artifacts.map(a => `
        <div class="artifact-block">
          <div class="artifact-block-header">
            <span><strong>${esc(a.filename)}</strong> · ${esc(a.artifact_type)} · v${esc(a.version)}</span>
            <span class="muted">${fmtDate(a.created_at)} · sha256:${esc((a.content_hash || "").slice(0, 12))}…</span>
          </div>
          <pre id="artifact-content-${a.id}">loading…</pre>
        </div>`).join("")
      : `<p class="muted">No artifacts captured for this entity yet.</p>`;

    const assessmentRows = data.compliance_assessments.length
      ? `<table class="listing"><tr><th>Date</th><th>Verdict</th><th>Assessor</th><th>Criteria</th></tr>` +
        data.compliance_assessments.map(c => `
          <tr><td>${fmtDate(c.assessed_at)}</td><td>${esc(c.verdict)}</td><td>${esc(c.assessor)}</td><td>${esc(c.criteria)}</td></tr>
        `).join("") + `</table>`
      : `<p class="muted">No compliance assessments logged.</p>`;

    const categories = data.standards.length
      ? `<div class="categories">${data.standards.map(s =>
          `<a href="#/standards/${esc(s.id)}" class="badge framework-${esc(s.framework)}">${esc(s.framework)}: ${esc(s.name)}${s.mandatory ? " · mandatory" : ""}</a>`
        ).join("")}</div>`
      : "";

    const backlinks = data.backlinks.length
      ? `<div class="backlinks"><h3>What links here</h3><ul>${data.backlinks.map(b =>
          `<li><a href="#/entity/${esc(b.entity_type)}/${esc(b.entity_id)}">${esc(b.entity_name)}</a> (${esc(b.entity_type.toUpperCase())})</li>`
        ).join("")}</ul></div>`
      : "";

    app.innerHTML = `
      <div class="article-title">${esc(title)}</div>
      <div class="article-body">
        <div class="article-main">
          <h3>Artifacts</h3>
          ${artifactBlocks}
          <h3>Governance</h3>
          ${assessmentRows}
          ${backlinks}
          ${categories}
        </div>
        ${infobox}
      </div>
    `;

    data.artifacts.forEach(a => {
      const el = document.getElementById(`artifact-content-${a.id}`);
      if (!el) return;
      api(`/api/v1/artifacts/${a.id}`).then(full => {
        el.textContent = full.content_text || "(binary content — download not yet implemented in this MVP)";
      }).catch(() => { el.textContent = "(failed to load content)"; });
    });
  } catch (e) {
    app.innerHTML = `<p class="muted">Could not load this entity: ${esc(e.message)}</p>`;
  }
}

async function pageStandards(params) {
  const framework = params.get("framework") || "";
  app.innerHTML = `<h1>Standards${framework ? `: ${esc(framework)}` : ""}</h1><p class="muted">Loading…</p>`;
  try {
    const url = new URL("/api/v1/standards", location.origin);
    if (framework) url.searchParams.set("framework", framework);
    const standards = await api(url.pathname + url.search);
    app.innerHTML = `
      <h1>Standards${framework ? `: ${esc(framework)}` : ""}</h1>
      ${standards.length ? `<table class="listing"><tr><th>Name</th><th>Framework</th><th>Version</th><th>Mandatory</th></tr>` +
        standards.map(s => `
          <tr>
            <td><a href="#/standards/${esc(s.id)}">${esc(s.name)}</a></td>
            <td><span class="badge framework-${esc(s.framework)}">${esc(s.framework)}</span></td>
            <td>${esc(s.version || "—")}</td>
            <td>${s.mandatory ? "Yes" : "No"}</td>
          </tr>`).join("") + `</table>`
        : `<p class="muted">No standards registered yet. Register one via <code>POST /api/v1/standards</code>.</p>`}
    `;
  } catch (e) {
    app.innerHTML = `<h1>Standards</h1><p class="muted">Failed to load: ${esc(e.message)}</p>`;
  }
}

async function pageStandardDetail(standardId) {
  app.innerHTML = `<p class="muted">Loading…</p>`;
  try {
    const entities = await api(`/api/v1/standards/${encodeURIComponent(standardId)}/entities`);
    app.innerHTML = `
      <h1>Standard #${esc(standardId)}</h1>
      <h3 style="margin:20px 0 10px;font-size:12px;text-transform:uppercase;color:var(--text-muted)">Entities satisfying this standard</h3>
      ${entities.length
        ? `<div class="card-grid">${entities.map(e => `
            <div class="entity-card" onclick="location.hash='#/entity/${esc(e.entity_type)}/${esc(e.entity_id)}'">
              <div class="entity-card-type">${esc(e.entity_type.toUpperCase())}</div>
              <div class="entity-card-name">${esc(e.entity_name)}</div>
            </div>`).join("")}</div>`
        : `<p class="muted">No entities linked to this standard yet.</p>`}
    `;
  } catch (e) {
    app.innerHTML = `<p class="muted">Failed to load: ${esc(e.message)}</p>`;
  }
}

// ── Router ─────────────────────────────────────────────────────────────────

function route() {
  const hash = location.hash.replace(/^#/, "") || "/";
  const [pathPart, queryPart] = hash.split("?");
  const params = new URLSearchParams(queryPart || "");
  const segments = pathPart.split("/").filter(Boolean);

  if (segments.length === 0) return pageHome();
  if (segments[0] === "search") return pageSearch(params);
  if (segments[0] === "entity" && segments.length === 3) return pageEntity(segments[1], segments[2]);
  if (segments[0] === "standards" && segments.length === 1) return pageStandards(params);
  if (segments[0] === "standards" && segments.length === 2) return pageStandardDetail(segments[1]);
  app.innerHTML = `<p class="muted">Not found.</p>`;
}

document.getElementById("site-search").addEventListener("submit", (e) => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  location.hash = `#/search?q=${encodeURIComponent(q)}`;
});
document.getElementById("theme-btn").addEventListener("click", toggleTheme);

window.addEventListener("hashchange", route);
initTheme();
loadSidebar();
loadConfig().then(route);
