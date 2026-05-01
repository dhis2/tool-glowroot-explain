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


@app.post("/transform")
def transform():
    return jsonify({"error": "not implemented"}), 501


if __name__ == "__main__":
    app.run(debug=True)
