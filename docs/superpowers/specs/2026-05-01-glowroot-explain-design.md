# Glowroot EXPLAIN Tool — Design Spec

**Date:** 2026-05-01  
**Status:** Draft

---

## Problem

When investigating performance issues in DHIS2, developers copy JDBC traces from the Glowroot profiler UI. These traces contain SQL with `?` placeholders and a separate parameter list. To run `EXPLAIN ANALYZE` the developer must manually substitute all parameters — tedious, error-prone, and repetitive enough to ask an AI to do it every time.

## Goal

A local Python web app that accepts a Glowroot JDBC trace, substitutes parameters, and produces a ready-to-paste `EXPLAIN` statement. The developer pastes the trace, picks options, copies the output, and runs it in psql or any other DB tool.

**Non-goal:** The tool never executes SQL. It only produces it.

---

## Architecture

- **Single file:** `app.py` with HTML template embedded via `render_template_string`
- **Runtime:** `uv run app.py` — no virtualenv, no pip install, no separate files
- **Dependency:** `flask` only, declared via PEP 723 inline metadata
- **Server:** Flask dev server on `localhost:5000`
- **Routes:**
  - `GET /` — serve UI
  - `POST /transform` — parse trace, substitute params, return SQL

---

## Input Formats

Glowroot produces two trace formats that must both be handled.

### Compact (single line)
```
jdbc query: SELECT ... WHERE x = ? ['val1', 42] => 5 rows
```

### Verbose (multi-line with section headers)
```
jdbc query:

SELECT ...
WHERE x = ?

parameters:

  ['val1', 42]

rows:

  => 5 rows
```

**Detection:** presence of `parameters:` as a standalone word in the input distinguishes verbose from compact.

---

## Parser

### Step 1 — Strip prefix
Remove leading `jdbc query:` (case-insensitive, optional).

### Step 2 — Split SQL from parameters
- **Compact:** SQL is everything before the final `[...]` block; params are inside that block.
- **Verbose:** SQL is everything between the prefix and `parameters:`; params are between `parameters:` and `rows:`.

### Step 3 — Parse parameter list
Parse the comma-separated values inside `[...]`, respecting single-quoted strings (commas inside quotes are not delimiters). Recognised types:

| Glowroot form | Substituted as | Notes |
|---|---|---|
| `'SM2asR96Qwi'` | `'SM2asR96Qwi'` | String — used as-is, already quoted |
| `385870` | `385870` | Integer — used as-is |
| `3.14` | `3.14` | Float — used as-is |
| `true` / `false` | `TRUE` / `FALSE` | Boolean — uppercased for PostgreSQL |
| `'null'` | `'null'` | String literal "null" (used in JSONB path contexts) |
| `NULL` | `NULL` | SQL NULL — unquoted uppercase |

### Step 4 — Validate
Count `?` placeholders in the SQL and compare to parameter count. On mismatch, return a clear error: `"SQL has N placeholders but M parameters were found."` Do not attempt partial substitution.

### Step 5 — Substitute
Replace each `?` left-to-right with its corresponding parameter value.

---

## EXPLAIN Options

Options are presented as checkboxes and a format dropdown. Dependency rules are enforced client-side via JavaScript.

### Always available
| Option | Default | Notes |
|---|---|---|
| ANALYZE | off | Executes the statement; enables ANALYZE-dependent options |
| VERBOSE | off | |
| COSTS | on | PostgreSQL default |
| SETTINGS | off | |
| MEMORY | off | |
| GENERIC_PLAN | off | Disabled when ANALYZE is checked (mutually exclusive) |
| FORMAT | TEXT | Dropdown: TEXT / XML / JSON / YAML |

### Enabled only when ANALYZE is checked
| Option | Default (when ANALYZE on) |
|---|---|
| BUFFERS | on |
| TIMING | on |
| WAL | off |
| SUMMARY | on |

When ANALYZE is unchecked, all ANALYZE-dependent options are greyed out and unchecked.

---

## DML Safety Wrapping

When ANALYZE is checked and the query (after trimming whitespace, case-insensitive) starts with `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `CREATE TABLE AS`, or `EXECUTE`, the output is wrapped in a transaction:

```sql
-- DML detected: wrapped in transaction for safety
BEGIN;
EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)
DELETE FROM foo WHERE id = 42;
ROLLBACK;
```

This allows the developer to paste the whole block into psql safely — the ROLLBACK prevents any data modification even if they forget to check first.

For `SELECT` statements, no wrapping is applied.

---

## Output Format

```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)
SELECT psi.programstageinstanceid, ...
FROM programstageinstance psi
WHERE pi.programinstanceid IN (385870, 2370770, ...)
  AND psi.programstageid IN (4158, 4164, ...);
```

Presented in a read-only textarea with a **Copy** button. No execution.

---

## UI Layout

```
┌─────────────────────────────────────────┐
│  Glowroot EXPLAIN Tool                  │
│                                         │
│  [Paste Glowroot trace here...        ] │
│  [                                    ] │
│                                         │
│  EXPLAIN options:                       │
│  [x] ANALYZE  [ ] VERBOSE  [x] COSTS   │
│  [ ] SETTINGS [ ] MEMORY  [ ] GENERIC  │
│  -- when ANALYZE on: --                 │
│  [x] BUFFERS  [x] TIMING  [ ] WAL      │
│  [x] SUMMARY                           │
│  FORMAT: [TEXT ▾]                       │
│                                         │
│  [Generate EXPLAIN]                     │
│                                         │
│  ⚠ ANALYZE executes the statement —    │
│    review the query before running.     │
│  (shown only when ANALYZE is checked)   │
│                                         │
│  [Output SQL here (read-only)         ] │
│  [Copy]                                 │
└─────────────────────────────────────────┘
```

---

## Error States

| Condition | User-facing message |
|---|---|
| Empty input | "Paste a Glowroot JDBC trace above." |
| No parameter block found | "Could not find a parameter list `[...]` in the trace." |
| Placeholder/parameter count mismatch | "SQL has N `?` placeholders but M parameters were found." |
| Empty parameter list with placeholders present | "SQL has N `?` placeholders but the parameter list is empty." |

Errors are shown inline between the button and the output area. Output area is cleared on error.

---

## Out of Scope (for this POC)

- Executing SQL against a database
- Chrome extension (identified as a follow-on)
- SERIALIZE option (niche, easy to add later)
- Authentication or multi-user support
- Persistent history of transforms
