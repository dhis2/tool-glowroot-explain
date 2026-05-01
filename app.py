# /// script
# requires-python = ">=3.11"
# dependencies = ["flask"]
# ///

from flask import Flask, render_template_string, request, jsonify
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError

app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html><body><h1>Glowroot EXPLAIN Tool</h1><p>Coming soon.</p></body></html>"""


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


if __name__ == "__main__":
    app.run(debug=True)
