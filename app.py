# /// script
# requires-python = ">=3.11"
# dependencies = ["flask"]
# ///

from flask import Flask, render_template_string, request, jsonify
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Glowroot EXPLAIN Tool</title>
  <style>
    body { font-family: sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }
    h1 { font-size: 1.4rem; margin-bottom: 1rem; }
    textarea { width: 100%; font-family: monospace; font-size: 0.85rem; box-sizing: border-box; }
    #trace { height: 220px; }
    #output { height: 220px; background: #f5f5f5; }
    .options { margin: 1rem 0; display: flex; flex-wrap: wrap; gap: 0.75rem 1.5rem; align-items: center; }
    .options label { display: flex; align-items: center; gap: 0.3rem; cursor: pointer; }
    .analyze-group { border-left: 3px solid #d1d5db; padding-left: 1rem;
                     display: flex; flex-wrap: wrap; gap: 0.75rem 1.5rem; }
    .analyze-group.disabled label { color: #9ca3af; }
    #warning { color: #92400e; background: #fef3c7; border: 1px solid #fcd34d;
               padding: 0.5rem 0.75rem; border-radius: 4px; display: none; margin: 0.5rem 0; font-size: 0.9rem; }
    #error-msg { color: #dc2626; margin: 0.5rem 0; display: none; font-size: 0.9rem; }
    button { padding: 0.4rem 1.1rem; cursor: pointer; }
    #copy-btn { margin-top: 0.4rem; }
    select { padding: 0.15rem 0.3rem; }
  </style>
</head>
<body>
  <h1>Glowroot EXPLAIN Tool</h1>

  <textarea id="trace" placeholder="Paste Glowroot JDBC trace here..."></textarea>

  <div class="options">
    <label><input type="checkbox" id="opt-analyze"> ANALYZE</label>
    <label><input type="checkbox" id="opt-verbose"> VERBOSE</label>
    <label><input type="checkbox" id="opt-costs" checked> COSTS</label>
    <label><input type="checkbox" id="opt-settings"> SETTINGS</label>
    <label><input type="checkbox" id="opt-memory"> MEMORY</label>
    <label><input type="checkbox" id="opt-generic_plan"> GENERIC_PLAN</label>
    <label>FORMAT:
      <select id="opt-format">
        <option>TEXT</option><option>JSON</option><option>XML</option><option>YAML</option>
      </select>
    </label>
  </div>

  <div class="analyze-group disabled" id="analyze-group">
    <label><input type="checkbox" id="opt-buffers" disabled> BUFFERS</label>
    <label><input type="checkbox" id="opt-timing" disabled> TIMING</label>
    <label><input type="checkbox" id="opt-wal" disabled> WAL</label>
    <label><input type="checkbox" id="opt-summary" disabled> SUMMARY</label>
  </div>

  <div style="margin: 1rem 0;">
    <button id="go-btn">Generate EXPLAIN</button>
  </div>

  <div id="warning">WARNING: ANALYZE executes the statement — review the query before running.</div>
  <div id="error-msg"></div>

  <textarea id="output" readonly placeholder="Output will appear here..."></textarea>
  <div><button id="copy-btn">Copy</button></div>

  <script>
    const analyzeEl   = document.getElementById('opt-analyze');
    const genericEl   = document.getElementById('opt-generic_plan');
    const analyzeGroup = document.getElementById('analyze-group');
    const depIds      = ['opt-buffers', 'opt-timing', 'opt-wal', 'opt-summary'];
    const warning     = document.getElementById('warning');

    function syncAnalyze() {
      const on = analyzeEl.checked;
      analyzeGroup.classList.toggle('disabled', !on);
      depIds.forEach(id => {
        const el = document.getElementById(id);
        el.disabled = !on;
        if (!on) el.checked = false;
      });
      if (on) {
        document.getElementById('opt-buffers').checked = true;
        document.getElementById('opt-timing').checked  = true;
        document.getElementById('opt-summary').checked = true;
        genericEl.checked  = false;
        genericEl.disabled = true;
      } else {
        genericEl.disabled = false;
      }
      warning.style.display = on ? 'block' : 'none';
    }

    function syncGeneric() {
      if (genericEl.checked) {
        analyzeEl.checked  = false;
        analyzeEl.disabled = true;
        syncAnalyze();
        analyzeEl.disabled = true;
      } else {
        analyzeEl.disabled = false;
      }
    }

    analyzeEl.addEventListener('change', syncAnalyze);
    genericEl.addEventListener('change', syncGeneric);

    document.getElementById('go-btn').addEventListener('click', async () => {
      const errorEl  = document.getElementById('error-msg');
      const outputEl = document.getElementById('output');
      errorEl.style.display = 'none';
      outputEl.value = '';

      const resp = await fetch('/transform', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          trace:        document.getElementById('trace').value,
          analyze:      analyzeEl.checked,
          verbose:      document.getElementById('opt-verbose').checked,
          costs:        document.getElementById('opt-costs').checked,
          settings:     document.getElementById('opt-settings').checked,
          memory:       document.getElementById('opt-memory').checked,
          generic_plan: genericEl.checked,
          buffers:      document.getElementById('opt-buffers').checked,
          timing:       document.getElementById('opt-timing').checked,
          wal:          document.getElementById('opt-wal').checked,
          summary:      document.getElementById('opt-summary').checked,
          format:       document.getElementById('opt-format').value,
        }),
      });
      const data = await resp.json();
      if (data.error) {
        errorEl.textContent = data.error;
        errorEl.style.display = 'block';
      } else {
        outputEl.value = data.sql;
      }
    });

    document.getElementById('copy-btn').addEventListener('click', () => {
      const val = document.getElementById('output').value;
      if (val) navigator.clipboard.writeText(val);
    });
  </script>
</body>
</html>"""


@app.get("/")
def index():
    return render_template_string(HTML)


_VALID_FORMATS = {"TEXT", "JSON", "XML", "YAML"}


@app.post("/transform")
def transform():
    data = request.get_json(force=True) or {}
    fmt = str(data.get("format", "TEXT")).upper()
    if fmt not in _VALID_FORMATS:
        return jsonify({"error": f"Invalid format '{fmt}'. Must be one of: TEXT, JSON, XML, YAML."}), 400
    raw = data.get("trace", "")
    options = {
        "analyze":      bool(data.get("analyze")),
        "verbose":      bool(data.get("verbose")),
        "costs":        bool(data.get("costs")),
        "settings":     bool(data.get("settings")),
        "memory":       bool(data.get("memory")),
        "generic_plan": bool(data.get("generic_plan")),
        "buffers":      bool(data.get("buffers")),
        "timing":       bool(data.get("timing")),
        "wal":          bool(data.get("wal")),
        "summary":      bool(data.get("summary")),
        "format":       fmt,
    }
    try:
        sql, params = parse_glowroot_trace(raw)
        result = generate_explain_sql(sql, params, options)
        return jsonify({"sql": result})
    except ParseError as e:
        return jsonify({"error": str(e)}), 400


def main():
    app.run(debug=False)


if __name__ == "__main__":
    main()
