/* Explain My Code — front end.
 *
 * No framework and no build step, for two reasons: the page is one screen with one
 * state object, and the interesting work already happened on the server. The client's
 * job is to render the analysis it is handed and keep the level switch instant —
 * `/v1/explain/all-levels` returns all three, so changing level never costs a request.
 */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const el = {
    code: $("code"), highlight: $("highlight").querySelector("code"), gutter: $("gutter"),
    run: $("run"), enrich: $("enrich"), language: $("language"), detected: $("detected"),
    counts: $("counts"), summary: $("summary"), summaryMeta: $("summary-meta"),
    verdict: $("verdict"), statRow: $("stat-row"), panels: $("panels"),
    levelIndicator: $("level-indicator"), hovercard: $("hovercard"), pipeline: $("pipeline"),
    badgeConcepts: $("badge-concepts"), badgeFindings: $("badge-findings"),
  };

  const state = {
    level: "beginner",
    tab: "lines",
    levels: null,      // { eli5, beginner, developer } payloads
    analysis: null,
    language: null,
    activeLine: null,
    aiByLine: new Map(),
    busy: false,
  };

  /* ---------------------------------------------------------------- syntax
   * A deliberately small highlighter. It exists so the editor reads like code,
   * not to be a language service — the server owns every semantic claim on the
   * page, and this only colours keywords, strings, numbers and comments.
   */
  const KEYWORDS = {
    python: "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield match case self",
    javascript: "async await break case catch class const continue default delete do else export extends finally for from function if import in instanceof let new of return static super switch this throw try typeof var void while yield null true false undefined",
    java: "abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for if implements import instanceof int interface long native new package private protected public return short static super switch synchronized this throw throws try void volatile while var record sealed true false null",
    cpp: "alignas auto bool break case catch char class const constexpr continue decltype default delete do double else enum explicit export extern false float for friend goto if inline int long mutable namespace new noexcept nullptr operator private protected public return short signed sizeof static struct switch template this throw true try typedef typename union unsigned using virtual void volatile while",
    sql: "select from where group by having order limit offset join left right inner outer full cross on as and or not in exists between like ilike is null distinct union all intersect except with insert into values update set delete create table view index case when then else end over partition asc desc",
  };
  const COMMENT_SOURCE = {
    python: "#[^\\n]*", sql: "--[^\\n]*", javascript: "//[^\\n]*",
    java: "//[^\\n]*", cpp: "//[^\\n]*",
  };

  const escapeHtml = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  const _regexCache = new Map();
  function tokenizer(lang) {
    if (!_regexCache.has(lang)) {
      const comment = COMMENT_SOURCE[lang] || "#[^\\n]*";
      const preproc = lang === "cpp" ? "|^\\s*#\\s*\\w+" : "";
      _regexCache.set(lang, new RegExp(
        `(${comment})` +                                            // 1 comment
        // Triple quotes first, so a Python docstring is one token rather than
        // an empty "" followed by a bare word.
        `|("""[\\s\\S]*?"""|'''[\\s\\S]*?'''` +
        `|"(?:[^"\\\\]|\\\\.)*"|'(?:[^'\\\\]|\\\\.)*'|\`[^\`]*\`)` +  // 2 string
        `|(\\b\\d[\\d_]*\\.?\\d*(?:[eE][+-]?\\d+)?\\b${preproc})` +  // 3 number / preproc
        `|([A-Za-z_$][\\w$]*)`,                                     // 4 word
        "g"
      ));
    }
    return _regexCache.get(lang);
  }

  /* Single pass, single output string. An earlier version chained .replace() calls and
     the later ones matched words inside the markup the earlier ones had emitted,
     rewriting `class="tok-fn"` as if it were source code. One pass cannot do that. */
  function highlightLine(line, lang) {
    const words = new Set((KEYWORDS[lang] || "").split(" "));
    const isKeyword = (w) => words.has(w) || (lang === "sql" && words.has(w.toLowerCase()));
    const regex = tokenizer(lang);
    regex.lastIndex = 0;
    let out = "";
    let cursor = 0;
    let match;
    while ((match = regex.exec(line)) !== null) {
      if (match.index > cursor) out += escapeHtml(line.slice(cursor, match.index));
      const [text, comment, string, number, word] = match;
      if (comment) out += `<span class="tok-com">${escapeHtml(text)}</span>`;
      else if (string) out += `<span class="tok-str">${escapeHtml(text)}</span>`;
      else if (number) out += `<span class="tok-num">${escapeHtml(text)}</span>`;
      else if (word) {
        const callish = line[match.index + text.length] === "(";
        const cls = isKeyword(word) ? "tok-kw" : callish ? "tok-fn" : null;
        out += cls ? `<span class="${cls}">${escapeHtml(text)}</span>` : escapeHtml(text);
      }
      cursor = match.index + text.length;
      if (text.length === 0) regex.lastIndex++;
    }
    return out + escapeHtml(line.slice(cursor));
  }

  function renderEditor() {
    const lang = state.language || el.language.value;
    const lines = el.code.value.split("\n");
    el.highlight.innerHTML = lines
      .map((line, i) => {
        const active = state.activeLine === i + 1 ? " is-active" : "";
        return `<span class="ln${active}">${highlightLine(line, lang) || "&nbsp;"}</span>`;
      })
      .join("");
    renderGutter(lines.length);
    el.counts.textContent = `${lines.length} line${lines.length === 1 ? "" : "s"}`;
    // The textarea must grow with content — it has no scrollbar of its own so the
    // highlight layer underneath stays pixel-aligned with the text on top.
    el.code.style.height = "auto";
    el.code.style.height = `${el.code.scrollHeight}px`;
  }

  function renderGutter(count) {
    const payload = state.levels?.[state.level];
    const byLine = new Map((payload?.lines || []).map((l) => [l.line, l]));
    const ratings = new Map(
      (state.analysis?.functions || []).map((f) => [f.line, f.rating])
    );
    let html = "";
    for (let i = 1; i <= count; i++) {
      const note = byLine.get(i);
      const rating = ratings.get(i);
      const classes = ["gutter-line"];
      if (note) classes.push("has-note");
      if (state.activeLine === i) classes.push("is-hot");
      html += `<div class="${classes.join(" ")}" data-line="${i}">`;
      if (note) {
        html += `<span class="note-dot${state.aiByLine.has(i) ? " is-ai" : ""}"></span>`;
      }
      html += `<span>${i}</span>`;
      html += rating ? `<span class="rating-pip rating-${rating}">${rating}</span>`
                     : `<span class="rating-pip" style="background:transparent"></span>`;
      html += "</div>";
    }
    el.gutter.innerHTML = html;
  }

  /* ---------------------------------------------------------------- pipeline */
  function setStage(name, on, skip = false) {
    const stage = el.pipeline.querySelector(`[data-stage="${name}"]`);
    if (!stage) return;
    stage.classList.toggle("is-on", !!on);
    stage.classList.toggle("is-skip", !!skip);
    stage.classList.toggle("is-ai", name === "enrich");
  }
  function resetStages() {
    ["parse", "analyze", "explain", "enrich"].forEach((s) => setStage(s, false, false));
  }

  /* ---------------------------------------------------------------- request */
  async function run() {
    if (state.busy) return;
    const code = el.code.value.trim();
    if (!code) return toast("Nothing to explain — paste some code first.");

    state.busy = true;
    el.run.disabled = true;
    resetStages();
    setStage("parse", true);

    const body = { code, level: state.level };
    if (el.language.value !== "auto") body.language = el.language.value;

    try {
      const response = await fetch("/v1/explain/all-levels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail.detail || `Request failed (${response.status})`);
      }
      const data = await response.json();
      setStage("analyze", true);
      setStage("explain", true);

      state.levels = { eli5: data.eli5, beginner: data.beginner, developer: data.developer };
      state.analysis = data.analysis;
      state.language = data.language;
      state.aiByLine = new Map();

      el.detected.hidden = el.language.value !== "auto";
      el.detected.textContent = `detected ${data.language}`;
      if (data.diagnostics?.length) {
        const worst = data.diagnostics.find((d) => d.severity === "error") || data.diagnostics[0];
        toast(worst.message, worst.severity === "error" ? "high" : "low");
      }

      renderAll();
      persist(code);

      if (el.enrich.checked) await enrich(code);
      else setStage("enrich", false, true);
    } catch (error) {
      toast(error.message || "Something went wrong.");
      resetStages();
    } finally {
      state.busy = false;
      el.run.disabled = false;
    }
  }

  /* SSE enrichment. The static explanation is already on screen; this only adds to it. */
  async function enrich(code) {
    setStage("enrich", true);
    const panel = $("panel-lines");
    panel.classList.add("streaming");
    let buffer = "";
    try {
      const response = await fetch("/v1/explain/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code, level: state.level, enrich: true,
          language: el.language.value === "auto" ? null : el.language.value,
        }),
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let pending = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        pending += decoder.decode(value, { stream: true });
        const frames = pending.split("\n\n");
        pending = frames.pop() || "";
        for (const frame of frames) {
          const event = /^event: (.+)$/m.exec(frame)?.[1];
          const raw = /^data: (.+)$/m.exec(frame)?.[1];
          if (!event || !raw) continue;
          const payload = JSON.parse(raw);
          if (event === "delta") buffer += payload.text;
          if (event === "error") toast(payload.detail || "The AI layer is unavailable.", "low");
        }
      }
      applyEnrichment(buffer);
    } catch {
      toast("The AI layer did not respond. The static analysis above is unaffected.", "low");
    } finally {
      panel.classList.remove("streaming");
    }
  }

  function applyEnrichment(raw) {
    let parsed;
    try {
      const start = raw.indexOf("{"), end = raw.lastIndexOf("}");
      parsed = JSON.parse(start >= 0 ? raw.slice(start, end + 1) : raw);
    } catch {
      return;
    }
    for (const item of parsed.lines || []) {
      if (typeof item.line === "number" && item.text) state.aiByLine.set(item.line, item);
    }
    if (parsed.summary) {
      el.summary.textContent = `${el.summary.textContent}\n\n${parsed.summary}`;
    }
    for (const risk of parsed.risks || []) {
      if (risk.text) state.aiByLine.set(risk.line, { text: risk.text, risk: true, confidence: 0.5 });
    }
    renderAll();
  }

  /* ---------------------------------------------------------------- render */
  function renderAll() {
    const payload = state.levels?.[state.level];
    if (!payload) return;
    const metrics = state.analysis.metrics;

    el.summary.textContent = payload.summary;
    el.verdict.textContent = metrics.rating;
    el.verdict.dataset.rating = metrics.rating;
    el.summaryMeta.innerHTML = [
      state.language,
      `${state.analysis.parser}`,
      `${metrics.codeLines} sloc`,
    ].map((t) => `<span>${escapeHtml(String(t))}</span>`).join("");

    el.statRow.innerHTML = [
      ["Cyclomatic", metrics.cyclomatic, "paths"],
      ["Cognitive", metrics.cognitive, "load"],
      ["Max nesting", metrics.maxNesting, "deep"],
      ["Maintainability", metrics.maintainability, "/100"],
    ].map(([k, v, unit]) => `
      <div class="stat">
        <div class="stat-k">${k}</div>
        <div class="stat-v">${v} <small>${unit}</small></div>
      </div>`).join("");

    el.badgeConcepts.textContent = payload.concepts.length || "";
    const findings = state.analysis.findings || [];
    el.badgeFindings.textContent = findings.length || "";
    el.badgeFindings.classList.toggle("is-alert", findings.some((f) => f.severity === "high"));

    renderWalkthrough(payload);
    renderConcepts(payload);
    renderFindings(findings);
    renderMetrics();
    renderStructure();
    renderEditor();
  }

  function renderWalkthrough(payload) {
    const panel = $("panel-lines");
    const source = el.code.value.split("\n");
    const merged = new Map();
    for (const line of payload.lines) merged.set(line.line, { ...line, ai: null });
    for (const [line, ai] of state.aiByLine) {
      const existing = merged.get(line) || { line, text: "", kind: "", source: "llm" };
      merged.set(line, { ...existing, ai });
    }
    const steps = [...merged.values()].sort((a, b) => a.line - b.line);
    if (!steps.length) return void (panel.innerHTML = `<p class="empty">Nothing to walk through.</p>`);

    panel.innerHTML = steps.map((step) => {
      const snippet = (source[step.line - 1] || "").trim().slice(0, 70);
      const tags = [];
      for (const concept of step.concepts || []) tags.push(`<span class="tag">${escapeHtml(concept)}</span>`);
      if (step.ai) tags.push(`<span class="tag is-ai">AI · ${Math.round((step.ai.confidence ?? .6) * 100)}%</span>`);
      return `
        <div class="step" data-line="${step.line}">
          <div class="step-line">${step.line}</div>
          <div class="step-body">
            ${step.text ? `<p>${markup(step.text)}</p>` : ""}
            ${step.ai ? `<p style="margin-top:5px;color:var(--ai)">${markup(step.ai.text)}</p>` : ""}
            ${step.detail ? `<div class="step-detail">${escapeHtml(step.detail)}</div>` : ""}
            ${snippet ? `<div class="step-detail" style="border-color:var(--ink-500)">${escapeHtml(snippet)}</div>` : ""}
            ${tags.length ? `<div class="step-tags">${tags.join("")}</div>` : ""}
          </div>
        </div>`;
    }).join("");
  }

  function renderConcepts(payload) {
    const panel = $("panel-concepts");
    if (!payload.concepts.length) {
      panel.innerHTML = `<p class="empty">No named concepts detected in this snippet.</p>`;
      return;
    }
    panel.innerHTML = payload.concepts.map((concept) => `
      <div class="concept">
        <div class="concept-head">
          <span class="concept-name">${escapeHtml(concept.label)}</span>
          <span class="concept-cat">${escapeHtml(concept.category)}</span>
          <span class="concept-lines">${concept.lines.map((l) =>
            `<button class="jump" data-line="${l}">${l}</button>`).join("")}</span>
        </div>
        <p>${markup(concept.text || "")}</p>
      </div>`).join("");
  }

  function renderFindings(findings) {
    const panel = $("panel-findings");
    if (!findings.length) {
      panel.innerHTML = `<p class="empty">No findings. Every rule the analyser knows came back clean.</p>`;
      return;
    }
    panel.innerHTML = findings.map((finding) => `
      <div class="finding" data-sev="${finding.severity}" data-line="${finding.line || ""}">
        <div class="sev-bar"></div>
        <div>
          <div class="finding-head">
            <span class="finding-title">${escapeHtml(finding.title)}</span>
            ${finding.line ? `<button class="jump" data-line="${finding.line}">line ${finding.line}</button>` : ""}
            <span class="finding-rule">${escapeHtml(finding.rule)}</span>
          </div>
          <p>${markup(finding.message)}</p>
          ${finding.suggestion ? `<div class="suggestion">${escapeHtml(finding.suggestion)}</div>` : ""}
        </div>
      </div>`).join("");
  }

  function renderMetrics() {
    const panel = $("panel-metrics");
    const { metrics, functions, symbols } = state.analysis;
    const rows = functions.map((f) => `
      <tr data-line="${f.line}">
        <td>${f.line}</td>
        <td class="name">${escapeHtml(f.name)}${f.isRecursive ? " ↻" : ""}</td>
        <td>${f.cyclomatic}</td>
        <td>${f.cognitive}</td>
        <td>${f.complexityClass}</td>
        <td><span class="rating-pip rating-${f.rating}">${f.rating}</span></td>
      </tr>`).join("");

    panel.innerHTML = `
      ${functions.length ? `
        <div class="section-title">Callables</div>
        <table class="metric-table">
          <thead><tr><th>Ln</th><th>Name</th><th>Cyclo</th><th>Cog</th><th>Cost</th><th>Rate</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>` : ""}

      <div class="section-title">File</div>
      <dl>
        ${kv("Lines of code", metrics.codeLines)}
        ${kv("Comment ratio", `${Math.round(metrics.commentRatio * 100)}%`)}
        ${kv("Cyclomatic complexity", metrics.cyclomatic)}
        ${kv("Cognitive complexity", metrics.cognitive)}
        ${kv("Max nesting depth", metrics.maxNesting)}
        ${kv("Loops / branches / calls", `${metrics.loopCount} / ${metrics.branchCount} / ${metrics.callCount}`)}
      </dl>

      <div class="section-title">Halstead</div>
      <dl>
        ${kv("Vocabulary", metrics.halstead.vocabulary)}
        ${kv("Volume", metrics.halstead.volume)}
        ${kv("Difficulty", metrics.halstead.difficulty)}
        ${kv("Estimated time to write", `${metrics.halstead.estimatedMinutes} min`)}
      </dl>

      <div class="section-title">Maintainability</div>
      <div class="bar"><span style="width:${metrics.maintainability}%;background:var(--rate-${metrics.rating.toLowerCase()})"></span></div>
      <p style="font-size:12px;color:var(--text-dim);margin-top:7px">
        ${metrics.maintainability}/100 — grade ${metrics.rating}. Derived from Halstead volume,
        cyclomatic complexity and length.
      </p>

      ${symbols.unused.length ? `
        <div class="section-title">Assigned but never read</div>
        <dl>${symbols.unused.map((s) => kv(s.name, s.kind)).join("")}</dl>` : ""}`;
  }

  function renderStructure() {
    const panel = $("panel-graph");
    const { functions, callGraph } = state.analysis;
    if (!functions.length) {
      panel.innerHTML = `<p class="empty">No callables — this is straight-line code.</p>`;
      return;
    }
    panel.innerHTML = `
      <div class="section-title">Call structure</div>
      <div class="tree">
        ${functions.map((f) => `
          <div class="tree-node" data-line="${f.line}">
            <span class="tree-kind">${escapeHtml(f.kind)}</span>
            <span class="tree-name">${escapeHtml(f.name)}</span>
            <span class="tree-cost">${f.complexityClass}${f.isRecursive ? " ↻" : ""}</span>
          </div>
          ${(f.calls || []).length ? `<div style="padding-left:22px;color:var(--text-faint);font-size:11px">
            → ${f.calls.map((c) => escapeHtml(c.split(".").pop())).join(", ")}</div>` : ""}
        `).join("")}
      </div>
      ${(callGraph.cycles || []).length ? `
        <div class="cycle">Mutual recursion: ${callGraph.cycles.map((c) =>
          escapeHtml(c.map((n) => n.split(".").pop()).join(" ↔ "))).join("; ")}</div>` : ""}
      ${(callGraph.external || []).length ? `
        <div class="section-title">Called but not defined here</div>
        <div class="tree" style="color:var(--text-dim)">${callGraph.external.slice(0, 24)
          .map((n) => escapeHtml(n)).join(", ")}</div>` : ""}`;
  }

  const kv = (k, v) => `<div class="kv"><dt>${escapeHtml(String(k))}</dt><dd>${escapeHtml(String(v))}</dd></div>`;
  // Explanations use `backticks` for code spans — the only markup they carry.
  const markup = (text) =>
    escapeHtml(text).replace(/`([^`]+)`/g, "<code>$1</code>");

  /* ---------------------------------------------------------------- events */
  function focusLine(line) {
    state.activeLine = line;
    renderEditor();
    const target = el.gutter.querySelector(`[data-line="${line}"]`);
    target?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  el.code.addEventListener("input", () => { state.activeLine = null; renderEditor(); });
  el.code.addEventListener("scroll", () => {
    el.highlight.parentElement.scrollTop = el.code.scrollTop;
  });
  el.code.addEventListener("keydown", (event) => {
    if (event.key === "Tab") {
      event.preventDefault();
      const { selectionStart: s, selectionEnd: e, value } = el.code;
      el.code.value = `${value.slice(0, s)}    ${value.slice(e)}`;
      el.code.selectionStart = el.code.selectionEnd = s + 4;
      renderEditor();
    }
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); run(); }
  });

  el.run.addEventListener("click", run);
  el.language.addEventListener("change", () => { el.detected.hidden = true; renderEditor(); });

  document.querySelectorAll(".level").forEach((button, index) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".level").forEach((b) => {
        b.classList.remove("is-active"); b.setAttribute("aria-selected", "false");
      });
      button.classList.add("is-active");
      button.setAttribute("aria-selected", "true");
      el.levelIndicator.style.transform = `translateX(${index * 100}%)`;
      state.level = button.dataset.level;
      if (state.levels) renderAll();
    });
  });

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => {
        t.classList.remove("is-active"); t.setAttribute("aria-selected", "false");
      });
      document.querySelectorAll(".panel").forEach((p) => p.classList.remove("is-active"));
      tab.classList.add("is-active");
      tab.setAttribute("aria-selected", "true");
      document.querySelector(`[data-panel="${tab.dataset.tab}"]`).classList.add("is-active");
      state.tab = tab.dataset.tab;
    });
  });

  document.querySelectorAll("[data-sample]").forEach((chip) => {
    chip.addEventListener("click", () => {
      const key = chip.dataset.sample;
      el.code.value = window.SAMPLES[key];
      el.language.value = key;
      state.language = key;
      renderEditor();
      run();
    });
  });

  // One delegated listener for every "jump to line" affordance on the page.
  el.panels.addEventListener("click", (event) => {
    const target = event.target.closest("[data-line]");
    if (target?.dataset.line) focusLine(Number(target.dataset.line));
  });
  el.gutter.addEventListener("click", (event) => {
    const target = event.target.closest("[data-line]");
    if (target) focusLine(Number(target.dataset.line));
  });

  el.gutter.addEventListener("mousemove", (event) => {
    const target = event.target.closest(".gutter-line");
    if (!target) return hideCard();
    const line = Number(target.dataset.line);
    const payload = state.levels?.[state.level];
    const note = payload?.lines.find((l) => l.line === line);
    const ai = state.aiByLine.get(line);
    if (!note && !ai) return hideCard();
    showCard(event, note, ai);
  });
  el.gutter.addEventListener("mouseleave", hideCard);

  function showCard(event, note, ai) {
    el.hovercard.hidden = false;
    el.hovercard.innerHTML = `
      ${note ? `<div class="hc-kind">${escapeHtml(note.kind)}</div><p>${markup(note.text)}</p>` : ""}
      ${ai ? `<div class="hc-kind is-ai" style="margin-top:${note ? "8px" : "0"}">AI layer</div>
              <p style="color:var(--ai)">${markup(ai.text)}</p>` : ""}
      ${note?.detail ? `<div class="hc-detail">${escapeHtml(note.detail)}</div>` : ""}`;
    const box = el.hovercard.getBoundingClientRect();
    const top = Math.min(event.clientY + 14, window.innerHeight - box.height - 12);
    el.hovercard.style.left = `${Math.min(event.clientX + 16, window.innerWidth - box.width - 12)}px`;
    el.hovercard.style.top = `${Math.max(12, top)}px`;
  }
  function hideCard() { el.hovercard.hidden = true; }

  $("theme-toggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("emc-theme", next);
  });

  let toastTimer;
  function toast(message, severity = "high") {
    document.querySelector(".toast")?.remove();
    const node = document.createElement("div");
    node.className = "toast";
    node.style.borderColor = `var(--sev-${severity})`;
    node.textContent = message;
    document.body.appendChild(node);
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => node.remove(), 6000);
  }

  /* Share links: the snippet rides in the URL hash so it never touches the server
     as a stored document. Base64 of UTF-8, which needs the escape dance below. */
  function persist(code) {
    try {
      const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(code)));
      history.replaceState(null, "", `#${el.language.value}/${encoded}`);
    } catch { /* oversized snippets simply do not get a share link */ }
  }
  function restore() {
    const hash = location.hash.slice(1);
    if (!hash.includes("/")) return false;
    const [language, encoded] = [hash.slice(0, hash.indexOf("/")), hash.slice(hash.indexOf("/") + 1)];
    try {
      const bytes = Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0));
      el.code.value = new TextDecoder().decode(bytes);
      if (language) el.language.value = language;
      return true;
    } catch { return false; }
  }

  /* ---------------------------------------------------------------- boot */
  document.documentElement.dataset.theme = localStorage.getItem("emc-theme") || "dark";
  if (!restore()) {
    el.code.value = window.SAMPLES.python;
    el.language.value = "python";
  }
  state.language = el.language.value === "auto" ? "python" : el.language.value;
  renderEditor();
  run();
})();
