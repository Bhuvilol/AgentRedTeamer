const config = window.ARENA_CONFIG || {};

const state = {
  persona: null,
  running: false,
  traces: [],
  filter: "all",
};

const el = {
  targetChips: document.getElementById("target-chips"),
  defenseSelect: document.getElementById("defense-select"),
  categorySelect: document.getElementById("category-select"),
  runBtn: document.getElementById("run-btn"),
  runLabel: document.getElementById("run-label"),
  transcript: document.getElementById("transcript"),
  consoleMeta: document.getElementById("console-meta"),
  verdictBadge: document.getElementById("verdict-badge"),
  verdictText: document.getElementById("verdict-text"),
  quotaText: document.getElementById("quota-text"),
  quotaPill: document.getElementById("quota-pill"),
  traceRows: document.getElementById("trace-rows"),
  traceCount: document.getElementById("trace-count"),
  verdictFilters: document.getElementById("verdict-filters"),
  modal: document.getElementById("trace-modal"),
  modalTitle: document.getElementById("modal-title"),
  modalTranscript: document.getElementById("modal-transcript"),
  modalBadge: document.getElementById("modal-badge"),
  modalReasoning: document.getElementById("modal-reasoning"),
  modalClose: document.getElementById("modal-close"),
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function outcomeOf(verdict) {
  if (verdict.leaked_secret) return "leaked";
  if (verdict.broke_character) return "broke";
  return "blocked";
}

const BADGES = {
  leaked: { cls: "badge-leaked", label: "LEAKED" },
  broke: { cls: "badge-broke", label: "BROKE CHAR" },
  blocked: { cls: "badge-blocked", label: "BLOCKED" },
};

/* ---------------- config selection ---------------- */

el.targetChips.querySelectorAll(".chip").forEach((chip) => {
  if (chip.getAttribute("aria-pressed") === "true") state.persona = chip.dataset.persona;
  chip.addEventListener("click", () => {
    if (state.running) return;
    el.targetChips.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
    chip.setAttribute("aria-pressed", "true");
    state.persona = chip.dataset.persona;
  });
});

/* ---------------- rendering a conversation ---------------- */

function clearTranscript() {
  el.transcript.innerHTML = "";
}

function appendTurn(speaker, message) {
  const row = document.createElement("div");
  row.className = speaker === "target" ? "turn turn-target" : "turn";

  const role = document.createElement("div");
  role.className = speaker === "target" ? "turn-role turn-role-target" : "turn-role turn-role-attacker";
  role.textContent = speaker === "target" ? "TARGET" : "ATTACKER";

  const bubble = document.createElement("div");
  bubble.className = speaker === "target" ? "bubble bubble-target" : "bubble bubble-attacker";
  bubble.textContent = message;

  if (speaker === "target") {
    row.append(bubble, role);
  } else {
    row.append(role, bubble);
  }
  el.transcript.append(row);
  row.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showThinking(who) {
  const row = document.createElement("div");
  row.className = "turn";
  row.id = "thinking-row";
  row.innerHTML = `<div class="turn-role"></div><div class="thinking"><span class="dot"></span>${who} is responding&hellip;</div>`;
  el.transcript.append(row);
  row.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearThinking() {
  document.getElementById("thinking-row")?.remove();
}

function setVerdict(verdict) {
  const outcome = outcomeOf(verdict);
  const badge = BADGES[outcome];
  el.verdictBadge.className = `badge ${badge.cls}`;
  el.verdictBadge.textContent = badge.label;
  el.verdictText.textContent = verdict.reasoning;
}

function resetVerdict() {
  el.verdictBadge.className = "badge";
  el.verdictBadge.style.background = "var(--border)";
  el.verdictBadge.style.color = "var(--ink-faint)";
  el.verdictBadge.textContent = "JUDGING…";
  el.verdictText.textContent = "The judge model reads the transcript once the conversation completes.";
}

/* ---------------- running an attack ---------------- */

async function playConversation(turns, meta) {
  clearTranscript();
  const attackerTurns = turns.filter((t) => t.speaker === "attacker").length;
  let shown = 0;

  for (const turn of turns) {
    if (turn.speaker === "attacker") shown += 1;
    el.consoleMeta.textContent = `turn ${shown} of ${attackerTurns} · ${meta}`;
    showThinking(turn.speaker === "attacker" ? "attacker" : "target");
    await sleep(turn.speaker === "attacker" ? 550 : 800);
    clearThinking();
    appendTurn(turn.speaker, turn.message);
    await sleep(250);
  }
}

function pickFallbackTrace(persona, defense, category) {
  const exact = state.traces.filter(
    (t) => t.persona_name === persona && t.defense_name === defense && t.attack_category === category
  );
  const pool = exact.length ? exact : state.traces.filter((t) => t.attack_category === category);
  if (!pool.length) return null;
  return pool[Math.floor(Math.random() * pool.length)];
}

function setQuota(text, ok) {
  el.quotaText.textContent = text;
  el.quotaPill.style.background = ok ? "oklch(0.93 0.07 155)" : "oklch(0.93 0.07 85)";
  el.quotaPill.style.color = ok ? "oklch(0.35 0.11 155)" : "oklch(0.42 0.11 70)";
  el.quotaPill.querySelector(".dot").style.background = ok ? "oklch(0.55 0.15 155)" : "oklch(0.65 0.14 70)";
}

async function runAttack() {
  if (state.running) return;
  state.running = true;
  el.runBtn.disabled = true;
  el.runLabel.textContent = "Running…";
  document.getElementById("transcript-empty")?.remove();
  clearTranscript();
  resetVerdict();

  const persona = state.persona;
  const defense = el.defenseSelect.value;
  const category = el.categorySelect.value;

  let result = null;
  let live = false;

  if (config.apiUrl) {
    try {
      el.consoleMeta.textContent = "contacting attacker agent…";
      const response = await fetch(config.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ persona, defense, category }),
      });
      if (response.ok) {
        result = await response.json();
        live = true;
        setQuota(
          result.remaining != null ? `Live · ${result.remaining} runs left this hour` : "Live",
          true
        );
      } else if (response.status === 429) {
        setQuota("Quota reached · replaying a logged run", false);
      } else {
        setQuota("API unavailable · replaying a logged run", false);
      }
    } catch (error) {
      setQuota("API unavailable · replaying a logged run", false);
    }
  } else {
    setQuota("Replaying logged runs", false);
  }

  if (!result) {
    const fallback = pickFallbackTrace(persona, defense, category);
    if (!fallback) {
      el.transcript.innerHTML = '<div class="empty">No logged trace available for that combination yet.</div>';
      state.running = false;
      el.runBtn.disabled = false;
      el.runLabel.textContent = "Run attack";
      return;
    }
    result = { turns: fallback.turns, verdict: fallback.verdict };
  }

  const meta = live ? "live run" : "replay of a logged run";
  await playConversation(result.turns, meta);
  el.consoleMeta.textContent = `complete · ${meta}`;
  setVerdict(result.verdict);

  state.running = false;
  el.runBtn.disabled = false;
  el.runLabel.textContent = "Run again";
}

el.runBtn.addEventListener("click", runAttack);

/* ---------------- trace browser ---------------- */

function renderTraces() {
  const rows = state.traces.filter((t) => state.filter === "all" || outcomeOf(t.verdict) === state.filter);
  el.traceCount.textContent = rows.length;

  if (!rows.length) {
    el.traceRows.innerHTML = '<div class="empty">No traces match that filter.</div>';
    return;
  }

  el.traceRows.innerHTML = "";
  rows.slice(0, 200).forEach((trace) => {
    const outcome = outcomeOf(trace.verdict);
    const badge = BADGES[outcome];
    const attackerTurns = trace.turns.filter((t) => t.speaker === "attacker").length;

    const row = document.createElement("div");
    row.className = "table-row";
    row.innerHTML = `
      <div class="mono" style="font-size:11px; color:var(--ink-faint);">${trace.trace_id.slice(0, 13)}</div>
      <div>
        <div style="font-weight:600;">${trace.persona_name.replace(" Assistant", "")}</div>
        <div class="table-sub mono">${trace.defense_name}</div>
      </div>
      <div class="mono table-hide-sm" style="font-size:12px;">${trace.attack_category}</div>
      <div class="table-hide-sm" style="color:var(--ink-faint);">${attackerTurns}</div>
      <div><span class="badge ${badge.cls}">${badge.label}</span></div>
    `;
    row.addEventListener("click", () => openTrace(trace));
    el.traceRows.append(row);
  });
}

function openTrace(trace) {
  const outcome = outcomeOf(trace.verdict);
  const badge = BADGES[outcome];
  el.modalTitle.textContent = `${trace.persona_name} · ${trace.defense_name} · ${trace.attack_category}`;
  el.modalBadge.className = `badge ${badge.cls}`;
  el.modalBadge.textContent = badge.label;
  el.modalReasoning.textContent = trace.verdict.reasoning;

  el.modalTranscript.innerHTML = "";
  trace.turns.forEach((turn) => {
    const row = document.createElement("div");
    row.className = turn.speaker === "target" ? "turn turn-target" : "turn";
    const role = document.createElement("div");
    role.className = turn.speaker === "target" ? "turn-role turn-role-target" : "turn-role turn-role-attacker";
    role.textContent = turn.speaker === "target" ? "TARGET" : "ATTACKER";
    const bubble = document.createElement("div");
    bubble.className = turn.speaker === "target" ? "bubble bubble-target" : "bubble bubble-attacker";
    bubble.textContent = turn.message;
    if (turn.speaker === "target") row.append(bubble, role);
    else row.append(role, bubble);
    el.modalTranscript.append(row);
  });

  el.modal.showModal();
}

el.modalClose.addEventListener("click", () => el.modal.close());

el.verdictFilters.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    el.verdictFilters.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
    chip.setAttribute("aria-pressed", "true");
    state.filter = chip.dataset.filter;
    renderTraces();
  });
});

fetch(config.tracesUrl)
  .then((response) => response.json())
  .then((traces) => {
    state.traces = traces;
    renderTraces();
    if (!config.apiUrl) setQuota("Replaying logged runs", false);
  })
  .catch(() => {
    el.traceRows.innerHTML = '<div class="empty">Could not load traces.</div>';
  });
