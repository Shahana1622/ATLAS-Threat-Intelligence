const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const API_BASE_URL = "https://atlas-threat-intelligence-backend.onrender.com";

const get = (path) =>
  fetch(`${API_BASE_URL}${path}`).then((response) => response.json());

const state = {
  activeNav: "overview",
  dataset: null,
  dashboard: null,
  graph: null,
  timeline: [],
  coverage: null,
  cas: null,
  analysis: null,
  selectedEvidence: null,
  selectedActor: null,
  selectedPersona: null,
  query: "",
};

const moduleNavigation = [
  {
    id: "evidence",
    label: "A / Evidence Intelligence",
    pages: [["evidence", "Evidence"], ["sources", "Sources"], ["conflicts", "Conflicts"], ["correlations", "Correlations"]],
  },
  {
    id: "actors",
    label: "B / Attribution & Identity",
    pages: [["actors", "Actors"], ["identity-links", "Identity Links"], ["false-links", "False Links"]],
  },
  {
    id: "personas",
    label: "C / AI Persona Intelligence",
    pages: [["personas", "Personas"], ["stylometry", "Stylometry"], ["behavior", "Behavior"], ["migration", "Migration"]],
  },
  {
    id: "reliability",
    label: "D / Attribution Reliability",
    pages: [["reliability", "Reliability"], ["cas", "CAS Abstention"]],
  },
  {
    id: "graph",
    label: "E / Investigator Intelligence",
    pages: [["graph", "Evidence Graph"], ["timeline", "Timeline"], ["audit", "Audit Trail"], ["reports", "Reports"]],
  },
];

function moduleForPage(page) {
  return moduleNavigation.find((module) => module.pages.some(([id]) => id === page))?.id;
}

function updateWorkspaceStatus() {
  const status = document.getElementById("workspace-status");
  if (!status) return;

  const module = moduleNavigation.find((item) => item.id === moduleForPage(state.activeNav));
  const label = module?.label || "00 / Overview";
  const descriptions = {
    overview: "Cross-module situation overview and current evidence posture",
    evidence: "Evidence provenance, conflicts, sources, and correlation review",
    actors: "Identity resolution, infrastructure correlation, and false-link analysis",
    personas: "Stylometric, behavioral, and migration intelligence",
    reliability: "Calibration, fragility, confidence decomposition, and abstention controls",
    graph: "Evidence graph, timeline, audit trail, and local reporting",
  };

  status.innerHTML = `
    <span class="workspace-status-code">ACTIVE VIEW / ${label}</span>
    <span class="workspace-status-description">${descriptions[state.activeNav] || "Investigation workspace"}</span>
    <span class="workspace-status-signal"><i></i> LIVE ANALYSIS</span>
  `;
}

function renderModuleNavigation() {
  const activeModule = moduleForPage(state.activeNav);
  if (!activeModule) return;
  const section = document.getElementById(`${state.activeNav}-page`);
  const module = moduleNavigation.find((item) => item.id === activeModule);
  if (!section || !module) return;

  const nav = document.createElement("div");
  nav.className = "module-subnav";
  nav.innerHTML = `<span class="module-subnav-label">${module.label}</span>${module.pages.map(([id, label]) => `
    <button type="button" class="${id === state.activeNav ? "active" : ""}" data-module-page="${id}">${label}</button>
  `).join("")}`;
  section.prepend(nav);
  nav.querySelectorAll("[data-module-page]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeNav = button.dataset.modulePage;
      renderAll();
    });
  });
}

function formatLabel(value) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatNumber(value) {
  return Number(value).toLocaleString();
}

function formatPercent(value) {
  if (typeof value === "number") {
    return `${Math.round(value * 100)}%`;
  }
  return value;
}

function formatTimestamp(value) {
  if (!value) return "â€”";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function safeText(value) {
  return value ?? "â€”";
}

function renderKpis() {
  if (!state.dashboard) return;
  const kpis = [
    ["Total Actors", state.dashboard.counts.actors, "Live actor set"],
    ["Total Personas", state.dashboard.counts.personas, "Known personas"],
    ["Evidence Records", state.dashboard.counts.evidence, "Synthetic evidence"],
    ["Candidate Relationships", state.dashboard.counts.candidate_links, "Attribution hypotheses"],
    ["Conflicting Evidence", state.dashboard.counts.conflicting_evidence, "Contradictory signals"],
    ["CAS Abstentions", state.dashboard.counts.abstentions, "Review required"],
    ["Sources", state.dashboard.counts.sources, "Source families"],
  ];

  const grid = document.getElementById("overview-kpis");
  if (!grid) return;
  grid.innerHTML = kpis.map(([label, value, note]) => `
    <div class="kpi-card">
      <span class="kpi-label">${label}</span>
      <span class="kpi-value">${formatNumber(value)}</span>
      <span class="kpi-note">${note}</span>
    </div>
  `).join("");
}

function renderEvidenceAnalytics(evidence) {
  const counts = evidence.reduce((result, item) => {
    const key = formatLabel(item.evidence_type || "unknown");
    result[key] = (result[key] || 0) + 1;
    return result;
  }, {});
  const rows = Object.entries(counts).sort(([, a], [, b]) => b - a).slice(0, 6);
  const max = Math.max(...rows.map(([, value]) => value), 1);
  const width = 280;
  const bars = rows.map(([label, value], index) => {
    const y = 20 + index * 28;
    const barWidth = Math.round((value / max) * 175);
    return `<text x="0" y="${y + 10}" class="viz-label">${label}</text><rect x="92" y="${y}" width="${barWidth}" height="13" rx="2" class="viz-bar cyan"/><text x="${100 + barWidth}" y="${y + 10}" class="viz-value">${value}</text>`;
  }).join("");
  const supporting = evidence.filter((item) => item.direction === "supports").length;
  const conflicting = evidence.filter((item) => item.direction === "contradicts").length;
  return `<div class="viz-panel evidence-viz"><div class="viz-header"><h3>Evidence Analytics</h3><span>${evidence.length} records</span></div><svg class="bar-viz" viewBox="0 0 ${width} ${Math.max(180, rows.length * 28 + 24)}" role="img" aria-label="Evidence by type">${bars}</svg><div class="viz-legend"><span class="green-dot">Supporting ${supporting}</span><span class="red-dot">Conflicting ${conflicting}</span></div></div>`;
}

function renderAttributionVisualization(graph) {
  const edges = (graph?.edges ?? []).slice(0, 5);
  const nodes = edges.flatMap((edge) => [edge.source, edge.target]).filter((value, index, values) => values.indexOf(value) === index).slice(0, 6);
  const nodeMarkup = nodes.map((node, index) => {
    const x = 42 + (index % 3) * 108;
    const y = index < 3 ? 40 : 132;
    return `<g class="graph-node actor-node"><circle cx="${x}" cy="${y}" r="17"/><text x="${x}" y="${y + 31}">${node.replace("Actor_", "A_")}</text></g>`;
  }).join("");
  const edgeMarkup = edges.map((edge, index) => {
    const sourceIndex = nodes.indexOf(edge.source);
    const targetIndex = nodes.indexOf(edge.target);
    if (sourceIndex < 0 || targetIndex < 0) return "";
    const x1 = 42 + (sourceIndex % 3) * 108;
    const y1 = sourceIndex < 3 ? 40 : 132;
    const x2 = 42 + (targetIndex % 3) * 108;
    const y2 = targetIndex < 3 ? 40 : 132;
    const relationClass = edge.relationship_type.includes("false") ? "critical" : edge.strength >= 0.75 ? "positive" : "uncertain";
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="graph-link ${relationClass}"/><text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 5}" class="graph-strength">${formatPercent(edge.strength)}</text>`;
  }).join("");
  return `<div class="viz-panel graph-viz"><div class="viz-header"><h3>Attribution Graph</h3><span>${graph?.nodes?.length ?? 0} nodes / ${graph?.edges?.length ?? 0} edges</span></div><svg viewBox="0 0 300 185" role="img" aria-label="Existing attribution relationship graph">${edgeMarkup}${nodeMarkup}</svg><div class="viz-legend"><span class="cyan-dot">Actor links</span><span class="green-dot">Supported</span><span class="amber-dot">Uncertain</span></div></div>`;
}

function renderReliabilityVisualization(analysis) {
  const rows = (analysis?.reliability?.confidence_decomposition ?? []).slice(0, 5);
  const markup = rows.map((item, index) => {
    const score = Number(item.components?.overall ?? 0);
    const label = (item.candidate ?? []).join(" / ") || `Candidate ${index + 1}`;
    return `<div class="reliability-row"><span>${label}</span><div><i style="width:${Math.round(score * 100)}%"></i></div><strong>${formatPercent(score)}</strong></div>`;
  }).join("");
  return `<div class="viz-panel reliability-viz"><div class="viz-header"><h3>Attribution Reliability</h3><span>Confidence decomposition</span></div><div class="reliability-bars">${markup || '<div class="empty-state">No reliability data available.</div>'}</div><div class="viz-caption">Existing confidence components and candidate scores</div></div>`;
}

function renderPersonaVisualization(analysis) {
  const rows = (analysis?.persona?.comparisons ?? []).filter((item) => Number(item.stylometric_similarity) > 0 || Number(item.behavioral_similarity) > 0).slice(0, 5);
  const markup = rows.map((item, index) => {
    const score = Math.max(Number(item.stylometric_similarity || 0), Number(item.behavioral_similarity || 0));
    const label = `${item.persona_a} / ${item.persona_b}`;
    return `<div class="persona-row"><span>${label}</span><div><i style="width:${Math.round(score * 100)}%"></i></div><strong>${formatPercent(score)}</strong></div>`;
  }).join("");
  return `<div class="viz-panel persona-viz"><div class="viz-header"><h3>Persona Intelligence</h3><span>${analysis?.persona?.comparisons?.length ?? 0} comparisons</span></div><div class="persona-bars">${markup || '<div class="empty-state">No persona comparisons available.</div>'}</div><div class="viz-caption">Stylometric and behavioral similarity from analysis</div></div>`;
}

function renderTimelineVisualization(timeline) {
  const events = (timeline ?? []).slice(0, 6);
  return `<div class="viz-panel timeline-viz"><div class="viz-header"><h3>Investigation Timeline</h3><span>${timeline?.length ?? 0} events</span></div><div class="viz-timeline">${events.map((event) => `<div class="viz-event"><i></i><div><strong>${event.event_type}</strong><span>${event.description}</span></div><time>${formatTimestamp(event.timestamp)}</time></div>`).join("") || '<div class="empty-state">No timeline events available.</div>'}</div></div>`;
}

function renderOverview() {
  const section = document.getElementById("overview-page");
  if (!section || !state.dashboard) return;

  const graphNodes = state.graph?.nodes?.length ?? 0;
  const graphEdges = state.graph?.edges?.length ?? 0;
  const evidence = state.dataset?.evidence ?? [];
  const independentGroups = new Set(evidence.map((item) => item.independence_group)).size;
  const supporting = evidence.filter((item) => item.direction === "supports").length;
  const conflicting = evidence.filter((item) => item.direction === "contradicts").length;
  const averageReliability = evidence.length ? (evidence.reduce((sum, item) => sum + Number(item.reliability), 0) / evidence.length).toFixed(2) : "0.00";
  const warnings = [
    ...(state.dashboard.limitations || []),
    state.analysis?.reliability?.calibration?.instability_warning ? "Calibration indicates instability across the synthetic evidence fixture." : "",
    state.cas?.status === "ABSTAIN" ? "The current CAS result requires investigator review." : "",
  ].filter(Boolean);

  const candidateSummary = (state.analysis?.attribution?.candidates ?? []).slice(0, 4).map((candidate) => {
    const score = Number(candidate.confidence ?? candidate.overall ?? 0);
    const candidateLabel = candidate.candidate
      || candidate.actor_id
      || [candidate.candidate_a, candidate.candidate_b].filter(Boolean).join(" / ")
      || "Candidate";
    return `
      <div class="entity-row">
        <div>
          <strong>${candidateLabel}</strong><br />
          <span>${candidate.reason ?? "Confidence estimate based on evidence and persona alignment"}</span>
        </div>
        <div>
          <span>${formatPercent(score)}</span>
        </div>
      </div>
    `;
  }).join("") || "<div class=\"empty-state\">No candidate relationships are available.</div>";

  section.innerHTML = `
    <div class="kpi-grid" id="overview-kpis"></div>

    <div class="visualization-grid">
      ${renderEvidenceAnalytics(evidence)}
      ${renderAttributionVisualization(state.graph)}
      ${renderReliabilityVisualization(state.analysis)}
      ${renderPersonaVisualization(state.analysis)}
      ${renderTimelineVisualization(state.timeline)}
    </div>

    <div class="layout-grid">
      <div class="panel">
        <div class="panel-header">
          <h2>Evidence Correlation Graph</h2>
          <span class="panel-subtle">${graphNodes} nodes / ${graphEdges} edges</span>
        </div>
        <div class="entity-list">
          ${(state.graph?.edges ?? []).slice(0, 8).map((edge) => `
            <div class="graph-edge-row">
              <div>
                <strong>${edge.source}</strong>
                <small> â†’ ${edge.target}</small><br />
                <span>${edge.relationship_type}</span>
              </div>
              <div>
                <span>${formatPercent(edge.strength)}</span>
              </div>
            </div>
          `).join("") || "<div class=\"empty-state\">No graph edges are available.</div>"}
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2>Attribution Overview</h2>
          <span class="panel-subtle">Candidate set</span>
        </div>
        <div class="list-stack">
          ${candidateSummary}
        </div>
      </div>
    </div>

    <div class="overview-stack">
      <div class="panel">
        <div class="panel-header">
          <h2>Investigation Timeline</h2>
          <span class="panel-subtle">Recent activity</span>
        </div>
        <div class="timeline-list">
          ${(state.timeline ?? []).slice(0, 6).map((event) => `
            <div class="timeline-item">
              <div>
                <strong>${event.event_type}</strong><br />
                <small>${event.description}</small>
              </div>
              <time>${formatTimestamp(event.timestamp)}</time>
            </div>
          `).join("") || "<div class=\"empty-state\">No investigation events match the current filters.</div>"}
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2>Evidence Quality</h2>
          <span class="panel-subtle">Synthetic independence review</span>
        </div>
        <div class="metric-list">
          <div class="metric-row">
            <div>
              <strong>Independent Evidence</strong><br />
              <span>Independent groups retained</span>
            </div>
            <div><strong>${independentGroups}</strong></div>
          </div>
          <div class="metric-row">
            <div>
              <strong>Redundant Evidence</strong><br />
              <span>Repeated or dependent signals</span>
            </div>
            <div><strong>${Math.max(0, evidence.length - independentGroups)}</strong></div>
          </div>
          <div class="metric-row">
            <div>
              <strong>Conflicting Evidence</strong><br />
              <span>Contradictory support</span>
            </div>
            <div><strong>${conflicting}</strong></div>
          </div>
          <div class="metric-row">
            <div>
              <strong>Source Reliability</strong><br />
              <span>Average evidence reliability</span>
            </div>
            <div><strong>${averageReliability}</strong></div>
          </div>
          <div class="metric-row">
            <div>
              <strong>Supporting Evidence</strong><br />
              <span>Directional support count</span>
            </div>
            <div><strong>${supporting}</strong></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <h2>Important Warnings</h2>
          <span class="badge warning">Review</span>
        </div>
        <div class="list-stack">
          ${warnings.length ? warnings.map((warning) => `<div class="callout"><strong>Notice:</strong> ${warning}</div>`).join("") : '<div class="empty-state">No warnings were returned by the current analysis.</div>'}
        </div>
      </div>
    </div>
  `;

  renderKpis();
}

function renderEvidencePage() {
  const section = document.getElementById("evidence-page");
  if (!section || !state.dataset) return;

  const evidence = state.dataset.evidence.filter((item) => {
    if (!state.query) return true;
    const match = [item.evidence_id, item.evidence_type, item.source_id, item.direction, item.actor_id, item.candidate_actor_id].join(" ").toLowerCase();
    return match.includes(state.query.toLowerCase());
  });

  section.innerHTML = `
    <div class="section-header">
      <h2>Evidence Intelligence</h2>
      <span class="badge">${evidence.length} records</span>
    </div>
    ${evidence.length ? `
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Source</th>
            <th>Reliability</th>
            <th>Group</th>
            <th>Direction</th>
            <th>Strength</th>
            <th>Timestamp</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${evidence.map((item) => `
            <tr>
              <td>${item.evidence_id}</td>
              <td>${item.evidence_type}</td>
              <td>${item.source_id}</td>
              <td>${item.reliability}</td>
              <td>${item.independence_group}</td>
              <td>${item.direction}</td>
              <td>${item.strength}</td>
              <td>${formatTimestamp(item.timestamp)}</td>
              <td><button data-evidence-id="${item.evidence_id}">Open</button></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
      <div class="detail-panel">
        <h3>${state.selectedEvidence ? state.selectedEvidence.evidence_id : evidence[0].evidence_id}</h3>
        <p>${state.selectedEvidence ? state.selectedEvidence.description : evidence[0].description}</p>
        <div class="detail-grid">
          <div><span>Source</span> ${safeText(state.selectedEvidence ? state.selectedEvidence.source_id : evidence[0].source_id)}</div>
          <div><span>Provenance</span> ${safeText(state.selectedEvidence ? state.selectedEvidence.independence_group : evidence[0].independence_group)}</div>
          <div><span>Reliability</span> ${safeText(state.selectedEvidence ? state.selectedEvidence.reliability : evidence[0].reliability)}</div>
          <div><span>Independence</span> ${safeText(state.selectedEvidence ? state.selectedEvidence.independence_group : evidence[0].independence_group)}</div>
          <div><span>Supporting relationships</span> ${safeText((state.selectedEvidence ? state.selectedEvidence.actor_id : evidence[0].actor_id) || "â€”")}</div>
          <div><span>Conflicting relationships</span> ${safeText((state.selectedEvidence ? state.selectedEvidence.candidate_actor_id : evidence[0].candidate_actor_id) || "â€”")}</div>
        </div>
      </div>
    ` : '<div class="empty-state">No evidence records match the selected filters.</div>'}
  `;

  const buttons = section.querySelectorAll("[data-evidence-id]");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const evidenceItem = state.dataset.evidence.find((item) => item.evidence_id === button.dataset.evidenceId);
      state.selectedEvidence = evidenceItem || null;
      renderEvidencePage();
    });
  });
}

function renderActorsPage() {
  const section = document.getElementById("actors-page");
  if (!section || !state.dataset) return;

  const actors = state.dataset.actors.filter((actor) => {
    if (!state.query) return true;
    const searchable = [actor.actor_id, actor.name, actor.aliases ?? "", actor.occupation ?? ""].join(" ").toLowerCase();
    return searchable.includes(state.query.toLowerCase());
  });

  section.innerHTML = `
    <div class="section-header">
      <h2>Actor / Attribution Page</h2>
      <span class="badge">${actors.length} actors</span>
    </div>
    ${actors.length ? `
      <div class="list-stack">
        ${actors.map((actor) => `
          <div class="entity-row">
            <div>
              <strong>${actor.actor_id}</strong><br />
              <span>${actor.name}</span>
            </div>
            <button class="inline-button" data-actor-id="${actor.actor_id}">Inspect</button>
          </div>
        `).join("")}
      </div>
    ` : '<div class="empty-state">No actors match the current search.</div>'}
  `;

  section.querySelectorAll("[data-actor-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedActor = button.dataset.actorId;
      state.activeNav = "actors";
      renderActorDetails();
    });
  });
}

function renderActorDetails() {
  const section = document.getElementById("identity-links-page");
  if (!section || !state.dataset) return;

  const actor = state.dataset.actors.find((item) => item.actor_id === state.selectedActor) ?? state.dataset.actors[0];
  if (!actor) {
    section.innerHTML = '<div class="empty-state">No matching investigation data.</div>';
    return;
  }

  const evidence = state.dataset.evidence.filter((item) => item.actor_id === actor.actor_id || item.candidate_actor_id === actor.actor_id);
  const personaLinks = state.dataset.personas.filter((item) => item.actor_id === actor.actor_id);
  const summary = [
    ["Confidence", state.analysis?.attribution?.candidates?.find((candidate) => candidate.actor_id === actor.actor_id)?.confidence ?? "0.00"],
    ["Evidence", evidence.length],
    ["Personas", personaLinks.length],
  ];

  section.innerHTML = `
    <div class="section-header">
      <h2>${actor.actor_id}</h2>
      <span class="badge">${actor.name}</span>
    </div>
    <div class="detail-grid">
      ${summary.map(([label, value]) => `<div><span>${label}</span> ${value}</div>`).join("")}
    </div>
    <div class="callout"><strong>Attribution note:</strong> Candidate relationships are analytical hypotheses and synthetic-only evidence. </div>
    <div class="panel" style="margin-top: 16px;">
      <h3>Evidence supporting relationship</h3>
      <ul>
        ${evidence.slice(0, 6).map((item) => `<li>${item.evidence_id} Â· ${item.evidence_type} Â· ${item.direction} Â· ${item.source_id}</li>`).join("")}
      </ul>
    </div>
  `;
}

function renderPersonasPage() {
  const section = document.getElementById("personas-page");
  if (!section || !state.dataset) return;

  const personas = state.dataset.personas.filter((persona) => {
    if (!state.query) return true;
    const searchable = [persona.persona_id, persona.actor_id, persona.handles.join(" "), persona.platforms.join(" ")].join(" ").toLowerCase();
    return searchable.includes(state.query.toLowerCase());
  });

  section.innerHTML = `
    <div class="section-header">
      <h2>Persona Intelligence</h2>
      <span class="badge">${personas.length} personas</span>
    </div>
    ${personas.length ? `
      <div class="list-stack">
        ${personas.map((persona) => `
          <div class="entity-row">
            <div>
              <strong>${persona.persona_id}</strong><br />
              <span>Actor: ${persona.actor_id} Â· Platforms: ${persona.platforms.join(", ") || "â€”"}</span>
            </div>
            <span class="badge">${persona.handles.length} handles</span>
          </div>
        `).join("")}
      </div>
    ` : '<div class="empty-state">No personas match the current search.</div>'}
  `;
}

function renderReliabilityPage() {
  const section = document.getElementById("reliability-page");
  if (!section || !state.analysis) return;

  const confidenceRows = (state.analysis.reliability?.confidence_decomposition ?? []).slice(0, 6).map((item) => {
    const components = item.components ?? {};
    return `
      <div class="entity-row">
        <div>
          <strong>${(item.candidate ?? []).join(" / ")}</strong><br />
          <span>Confidence decomposition</span>
        </div>
        <div>
          <span>${formatPercent(components.overall ?? 0)}</span>
        </div>
      </div>
    `;
  }).join("");

  const fragility = state.analysis.reliability?.fragility ?? [];
  const fragilityRows = fragility.length ? fragility.map((item) => `
    <div class="metric-row">
      <div>
        <strong>${item.label ?? item.signal ?? "Signal"}</strong><br />
        <span>${item.description ?? "Impact of leaving the signal out"}</span>
      </div>
      <div><strong>${formatPercent(item.delta ?? 0)}</strong></div>
    </div>
  `).join("") : '<div class="empty-state">No fragility data is available.</div>';

  section.innerHTML = `
    <div class="section-header">
      <h2>Attribution Reliability</h2>
      <span class="badge">Calibration</span>
    </div>
    <div class="layout-grid">
      <div class="panel">
        <h3>Confidence decomposition</h3>
        <div class="list-stack">${confidenceRows || '<div class="empty-state">No confidence decomposition is available.</div>'}</div>
      </div>
      <div class="panel">
        <h3>Fragility analysis</h3>
        <div class="metric-list">${fragilityRows}</div>
      </div>
    </div>
  `;
}

function renderCasPage() {
  const section = document.getElementById("cas-page");
  if (!section) return;

  const cas = state.cas ?? { status: "ABSTAIN", reasons: ["No additional evidence available."], explanation: "No CAS explanation was returned." };

  section.innerHTML = `
    <div class="section-header">
      <h2>CAS Abstention</h2>
      <span class="badge ${cas.status === "ABSTAIN" ? "warning" : "success"}">${cas.status}</span>
    </div>
    <div class="panel">
      <h3>Why did the system abstain?</h3>
      <ul>
        ${(cas.reasons ?? []).map((reason) => `<li>${reason}</li>`).join("") || "<li>No specific abstention reasons were returned.</li>"}
      </ul>
      <p>${cas.explanation || "No explanation was returned."}</p>
    </div>
  `;
}

function renderGraphPage() {
  const section = document.getElementById("graph-page");
  if (!section || !state.graph) return;

  const nodes = state.graph.nodes.slice(0, 12);
  const edges = state.graph.edges.slice(0, 12);

  section.innerHTML = `
    <div class="section-header">
      <h2>Evidence Graph</h2>
      <span class="badge">${state.graph.nodes.length} nodes</span>
    </div>
    <div class="layout-grid">
      <div class="panel">
        <h3>Nodes</h3>
        <div class="list-stack">
          ${nodes.map((node) => `
            <div class="entity-row">
              <div>
                <strong>${node.id}</strong><br />
                <span>${node.type}</span>
              </div>
              <span class="badge">${node.label}</span>
            </div>
          `).join("") || '<div class="empty-state">No graph nodes are available.</div>'}
        </div>
      </div>
      <div class="panel">
        <h3>Edges</h3>
        <div class="list-stack">
          ${edges.map((edge) => `
            <div class="graph-edge-row">
              <div>
                <strong>${edge.source}</strong><br />
                <span>${edge.relationship_type}</span>
              </div>
              <div>
                <span>${edge.target}</span><br />
                <small>${formatPercent(edge.strength)}</small>
              </div>
            </div>
          `).join("") || '<div class="empty-state">No graph edges are available.</div>'}
        </div>
      </div>
    </div>
  `;
}

function renderTimelinePage() {
  const section = document.getElementById("timeline-page");
  if (!section) return;

  const rows = (state.timeline ?? []).filter((item) => {
    if (!state.query) return true;
    const searchable = [item.event_type, item.description, (item.entity_ids || []).join(" ")].join(" ").toLowerCase();
    return searchable.includes(state.query.toLowerCase());
  });

  section.innerHTML = `
    <div class="section-header">
      <h2>Timeline</h2>
      <span class="badge">${rows.length} events</span>
    </div>
    ${rows.length ? `
      <div class="timeline-list">
        ${rows.map((item) => `
          <div class="timeline-item">
            <div>
              <strong>${item.event_type}</strong><br />
              <small>${item.description}</small>
            </div>
            <time>${formatTimestamp(item.timestamp)}</time>
          </div>
        `).join("")}
      </div>
    ` : '<div class="empty-state">No matching investigation data.</div>'}
  `;
}

function renderAuditPage() {
  const section = document.getElementById("audit-page");
  if (!section) return;

  const auditRows = (state.timeline ?? []).map((item) => ({
    timestamp: item.timestamp,
    action: item.event_type,
    entity: (item.entity_ids || []).join(", "),
    evidence: item.description,
    result: "Recorded",
  }));

  section.innerHTML = `
    <div class="section-header">
      <h2>Audit Trail</h2>
      <span class="badge">${auditRows.length} entries</span>
    </div>
    ${auditRows.length ? `
      <div class="audit-list">
        ${auditRows.map((item) => `
          <div class="audit-item">
            <div>
              <strong>${item.action}</strong><br />
              <small>${item.entity}</small>
            </div>
            <div>
              <small>${item.evidence}</small><br />
              <span>${item.result}</span>
            </div>
            <time>${formatTimestamp(item.timestamp)}</time>
          </div>
        `).join("")}
      </div>
    ` : '<div class="empty-state">No audit trail entries are available.</div>'}
  `;
}

function renderReportsPage() {
  const section = document.getElementById("reports-page");
  if (!section) return;

  const summary = [
    ["Actors examined", state.dashboard?.counts?.actors ?? 0],
    ["Evidence summary", state.dashboard?.counts?.evidence ?? 0],
    ["Attribution results", state.dashboard?.counts?.candidate_links ?? 0],
    ["Conflicting evidence", state.dashboard?.counts?.conflicting_evidence ?? 0],
    ["CAS results", state.dashboard?.counts?.abstentions ?? 0],
    ["Reliability analysis", state.analysis?.reliability?.confidence_decomposition?.length ?? 0],
  ];

  section.innerHTML = `
    <div class="section-header">
      <h2>Reports</h2>
      <span class="badge">Investigation summary</span>
    </div>
    <div class="panel">
      <div class="detail-grid">
        ${summary.map(([label, value]) => `<div><span>${label}</span> ${value}</div>`).join("")}
      </div>
      <div class="report-actions">
        <a class="link-button" href="/v1/investigator/export.json" target="_blank" rel="noopener noreferrer">Export JSON</a>
        <a class="link-button" href="/v1/investigator/export.csv" target="_blank" rel="noopener noreferrer">Export CSV</a>
        <a class="link-button" href="/v1/investigator/export.pdf" target="_blank" rel="noopener noreferrer">Export PDF</a>
      </div>
    </div>
  `;
}

function renderSearchPage() {
  const section = document.getElementById("search-page");
  if (!section) return;

  const query = state.query.trim();
  const results = [];
  if (query) {
    state.dataset.actors.forEach((actor) => {
      const haystack = [actor.actor_id, actor.name].join(" ").toLowerCase();
      if (haystack.includes(query.toLowerCase())) {
        results.push({ kind: "Actor", label: actor.actor_id, page: "actors", target: actor.actor_id });
      }
    });

    state.dataset.personas.forEach((persona) => {
      const haystack = [persona.persona_id, persona.actor_id, persona.handles.join(" ")].join(" ").toLowerCase();
      if (haystack.includes(query.toLowerCase())) {
        results.push({ kind: "Persona", label: persona.persona_id, page: "personas", target: persona.persona_id });
      }
    });

    state.dataset.evidence.forEach((item) => {
      const haystack = [item.evidence_id, item.evidence_type, item.source_id, item.actor_id, item.candidate_actor_id].join(" ").toLowerCase();
      if (haystack.includes(query.toLowerCase())) {
        results.push({ kind: "Evidence", label: item.evidence_id, page: "evidence", target: item.evidence_id });
      }
    });
  }

  section.innerHTML = query
    ? (results.length ? `
      <div class="section-header">
        <h2>Search Results</h2>
        <span class="badge">${results.length} results</span>
      </div>
      <div class="list-stack">
        ${results.map((result) => `
          <div class="entity-row">
            <div>
              <strong>${result.kind}</strong><br />
              <span>${result.label}</span>
            </div>
            <button class="inline-button" data-go-page="${result.page}" data-go-target="${result.target}">Open</button>
          </div>
        `).join("")}
      </div>
    ` : '<div class="empty-state">No matching investigation data.</div>')
    : '<div class="empty-state">Enter a search phrase to locate actors, personas, evidence, and related identifiers.</div>';

  section.querySelectorAll("[data-go-page]").forEach((button) => {
    button.addEventListener("click", () => {
      const page = button.dataset.goPage;
      state.activeNav = page;
      document.querySelector(`[data-nav="${page}"]`)?.classList.add("active");
      if (page === "actors") {
        state.selectedActor = button.dataset.goTarget;
      }
      renderAll();
    });
  });
}

function renderAuxiliaryPage(page) {
  const section = document.getElementById(`${page}-page`);
  if (!section || !state.dataset || !state.analysis) return;

  const evidence = state.dataset.evidence;
  const sources = state.dataset.sources;
  const personaResults = state.analysis.persona || {};
  let title = formatLabel(page);
  let content = "";

  if (page === "sources") {
    const rows = sources.map((source) => {
      const sourceEvidence = evidence.filter((item) => item.source_id === source.source_id);
      const independent = new Set(sourceEvidence.map((item) => item.independence_group)).size;
      const conflicts = sourceEvidence.filter((item) => item.direction === "contradicts").length;
      return `<tr><td>${source.source_id}</td><td>${source.source_type}</td><td>${source.reliability}</td><td>${sourceEvidence.length}</td><td>${independent}</td><td>${conflicts}</td></tr>`;
    }).join("");
    title = "Source Intelligence";
    content = `<table class="data-table"><thead><tr><th>Source ID</th><th>Type</th><th>Reliability</th><th>Evidence</th><th>Independent</th><th>Conflicts</th></tr></thead><tbody>${rows}</tbody></table>`;
  } else if (page === "conflicts") {
    const conflicts = evidence.filter((item) => item.direction === "contradicts");
    title = "Conflict Analysis";
    content = conflicts.length ? `<div class="list-stack">${conflicts.map((item) => `<div class="entity-row"><div><strong>${item.evidence_id}</strong><br /><span>${item.description}</span><br /><small>${item.source_id} · ${item.actor_id} → ${item.candidate_actor_id}</small></div><span class="badge danger">${item.direction}</span></div>`).join("")}</div>` : '<div class="empty-state">No conflicting evidence records are present.</div>';
  } else if (page === "correlations") {
    const correlations = state.analysis.evidence?.redundancy || [];
    title = "Evidence Correlations";
    content = correlations.length ? `<div class="list-stack">${correlations.map((item) => `<div class="entity-row"><div><strong>${item.source_family}</strong><br /><span>${item.evidence_ids.join(", ")}</span></div><span class="badge warning">${item.dependent_count} records</span></div>`).join("")}</div>` : '<div class="empty-state">No redundant or common-source correlations were returned.</div>';
  } else if (page === "false-links") {
    const candidates = (state.analysis.attribution?.candidates || []).filter((item) => item.relationship_type === "POSSIBLE_FALSE_LINK");
    title = "False-Link Assessment";
    content = candidates.length ? `<div class="list-stack">${candidates.map((item) => `<div class="entity-row"><div><strong>${item.candidate_a} → ${item.candidate_b}</strong><br /><span>${item.explanation}</span><br /><small>Conflicts: ${item.conflicting_evidence_ids.join(", ") || "none"}</small></div><span class="badge danger">${formatPercent(item.confidence)}</span></div>`).join("")}</div>` : '<div class="empty-state">No possible false links were returned.</div>';
  } else if (page === "stylometry") {
    const rows = (personaResults.comparisons || []).filter((item) => item.stylometric_similarity > 0).slice(0, 30);
    title = "Stylometric Analysis";
    content = rows.length ? `<table class="data-table"><thead><tr><th>Persona A</th><th>Persona B</th><th>Stylometric similarity</th><th>Rebranding candidate</th></tr></thead><tbody>${rows.map((item) => `<tr><td>${item.persona_a}</td><td>${item.persona_b}</td><td>${formatPercent(item.stylometric_similarity)}</td><td>${item.candidate_rebranding ? "Yes" : "No"}</td></tr>`).join("")}</tbody></table>` : '<div class="empty-state">No stylometric comparisons were returned.</div>';
  } else if (page === "behavior") {
    const rows = (personaResults.comparisons || []).filter((item) => item.behavioral_similarity > 0).slice(0, 30);
    title = "Behavioral Analysis";
    content = rows.length ? `<table class="data-table"><thead><tr><th>Persona A</th><th>Persona B</th><th>Behavior similarity</th><th>Stylometry</th></tr></thead><tbody>${rows.map((item) => `<tr><td>${item.persona_a}</td><td>${item.persona_b}</td><td>${formatPercent(item.behavioral_similarity)}</td><td>${formatPercent(item.stylometric_similarity)}</td></tr>`).join("")}</tbody></table>` : '<div class="empty-state">No behavioral comparisons were returned.</div>';
  } else if (page === "migration") {
    const migrations = personaResults.migration || [];
    title = "Persona Migration";
    content = migrations.length ? `<div class="list-stack">${migrations.map((item) => `<div class="entity-row"><div><strong>${item.persona_id}</strong><br /><span>${item.path.join(" → ")}</span><br /><small>${item.evidence_ids.join(", ")}</small></div><span class="badge">${item.timestamps.length} observations</span></div>`).join("")}</div>` : '<div class="empty-state">No persona migration paths were returned.</div>';
  }

  section.innerHTML = `<div class="section-header"><h2>${title}</h2><span class="badge">Backend-derived view</span></div><div class="panel">${content}</div>`;
}

function renderAll() {
  const activeModule = moduleForPage(state.activeNav);
  updateWorkspaceStatus();
  $$('[data-nav]').forEach((button) => {
    button.classList.toggle('active', button.dataset.nav === state.activeNav || button.dataset.nav === activeModule);
  });

  $$('.page-section').forEach((section) => {
    section.classList.toggle('active', section.id === `${state.activeNav}-page` || (state.activeNav === "overview" && section.id === "overview-page"));
  });

  renderOverview();
  renderEvidencePage();
  ["sources", "conflicts", "correlations", "false-links", "stylometry", "behavior", "migration"].forEach(renderAuxiliaryPage);
  renderActorsPage();
  renderActorDetails();
  renderPersonasPage();
  renderReliabilityPage();
  renderCasPage();
  renderGraphPage();
  renderTimelinePage();
  renderAuditPage();
  renderReportsPage();
  renderSearchPage();
  renderModuleNavigation();
}

async function loadApplication() {
  try {
    const [dashboard, graph, dataset, timeline, cas, coverage, analysis] = await Promise.all([
      get("/v1/investigator/dashboard"),
      get("/v1/investigator/graph"),
      get("/dataset"),
      get("/v1/investigator/timeline"),
      get("/v1/investigator/cas"),
      get("/v1/investigator/coverage"),
      get("/v1/analysis")
    ]);

    state.dashboard = dashboard;
    state.graph = graph;
    state.dataset = dataset;
    state.timeline = timeline;
    state.cas = cas;
    state.coverage = coverage;
    state.analysis = analysis;
    state.selectedEvidence = dataset.evidence[0] ?? null;
    state.selectedActor = dataset.actors[0]?.actor_id ?? null;
    renderAll();
  } catch (error) {
    const section = document.getElementById("overview-page");
    if (section) {
      section.innerHTML = `<div class="empty-state">Unable to load the investigation data. ${error.message}</div>`;
    }
  }
}

function bindNavigation() {
  $$('.nav-item').forEach((button) => {
    button.addEventListener("click", () => {
      state.activeNav = button.dataset.nav;
      renderAll();
    });
  });

  const searchInput = document.getElementById("global-search");
  searchInput.addEventListener("input", (event) => {
    state.query = event.target.value.trim();
    state.activeNav = state.query ? "search" : "overview";
    renderAll();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  loadApplication();
});
