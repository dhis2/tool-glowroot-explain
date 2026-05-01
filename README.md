# Glowroot EXPLAIN Tool

Paste a Glowroot JDBC trace, get a ready-to-run PostgreSQL `EXPLAIN` statement.

## What it does

Glowroot records slow queries as JDBC traces with `?` placeholders and a separate parameter list. This tool substitutes the parameters and wraps the SQL in an `EXPLAIN (...)` clause so you can paste it straight into psql or your database client of choice.

Supports both Glowroot trace formats (compact single-line and verbose multi-section). When ANALYZE is enabled and the query is a DML statement (INSERT/UPDATE/DELETE/etc.), the output is automatically wrapped in `BEGIN; ... ROLLBACK;` to prevent accidental data modification.

As usual, be cautious when running generated SQL in production environments. Always review the output before executing.

## Requirements

- [uv](https://docs.astral.sh/uv/) — no other installation needed.
- [pg_format](https://github.com/darold/pgFormatter) _(optional)_ — if available in your `PATH`, the tool detects it automatically and offers a **Format SQL** checkbox to pretty-print the output.

## Installation

### Install from GitHub (recommended)

Install directly from GitHub using `uv` without cloning the repository:

```bash
# Install latest
uv tool install git+https://github.com/dhis2/tool-glowroot-explain

# Pin a specific version (see https://github.com/dhis2/tool-glowroot-explain/releases)
uv tool install git+https://github.com/dhis2/tool-glowroot-explain@<tag>

# Update to latest
uv tool install --reinstall git+https://github.com/dhis2/tool-glowroot-explain
```

Then run from anywhere:

```bash
glowroot-explain
```

### Local development

```bash
git clone https://github.com/dhis2/tool-glowroot-explain.git
cd tool-glowroot-explain
uv run app.py
```

## Usage

Open [http://localhost:5000](http://localhost:5000), paste your trace, choose EXPLAIN options, click **Generate EXPLAIN**, then **Copy**.

If `pg_format` is installed, a **Format SQL with pg_format** checkbox appears (enabled by default) and formats the output when FORMAT is TEXT.

## Example input

```
jdbc query: SELECT * FROM users WHERE username = ? LIMIT ? ['admin', 1] => 1 row
```

## Example output

```sql
EXPLAIN (COSTS, FORMAT TEXT)
SELECT * FROM users WHERE username = 'admin' LIMIT 1;
```
