# Glowroot EXPLAIN Tool

Paste a Glowroot JDBC trace, get a ready-to-run PostgreSQL `EXPLAIN` statement.

## What it does

Glowroot records slow queries as JDBC traces with `?` placeholders and a separate parameter list. This tool substitutes the parameters and wraps the SQL in an `EXPLAIN (...)` clause so you can paste it straight into psql.

Supports both Glowroot trace formats (compact single-line and verbose multi-section). When ANALYZE is enabled and the query is a DML statement (INSERT/UPDATE/DELETE/etc.), the output is automatically wrapped in `BEGIN; ... ROLLBACK;` to prevent accidental data modification.

## Requirements

[uv](https://docs.astral.sh/uv/) — no other installation needed.

## Usage

```bash
uv run app.py
```

Open [http://localhost:5000](http://localhost:5000), paste your trace, choose EXPLAIN options, click **Generate EXPLAIN**, then **Copy**.

## Example input

```
jdbc query: SELECT * FROM users WHERE username = ? LIMIT ? ['admin', 1] => 1 row
```

## Example output

```sql
EXPLAIN (COSTS, FORMAT TEXT)
SELECT * FROM users WHERE username = 'admin' LIMIT 1;
```
