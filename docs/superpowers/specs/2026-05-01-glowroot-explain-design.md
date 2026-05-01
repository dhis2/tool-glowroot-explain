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

## Testing Approach

The parser is the only logic worth unit testing — the Flask wiring is thin and covered by manual browser testing.

Tests are written **test-first**: failing tests are written against the real Glowroot traces collected during design, then the parser is implemented until they pass.

**Test fixtures** are the actual traces provided during design:
1. Compact format, single string param: `sharing->'users'->?->>'access'` with `['SM2asR96Qwi']`
2. Verbose format, mixed string + integer params: `username = ?` with `['130713_P6', 1]`
3. Verbose format, strings + booleans: the `programstage` sharing query with `true` values
4. Verbose format, strings + booleans + NULL: the `trackedentityattribute` query ending with `NULL`
5. Compact format, large integer param list: the `programstageinstance` query with 64 integer params

Each test asserts: given this raw trace input + these EXPLAIN options, the output SQL equals the expected string exactly.

Additional parser behaviour tests (not tied to a specific fixture):
- A trace whose SQL starts with `DELETE` and ANALYZE enabled produces output wrapped in `BEGIN;` / `ROLLBACK;` including the safety comment line `-- Statement type may modify data: wrapped in transaction for safety` — the full comment text is part of the exact-string assertion
- A trace with a placeholder/parameter count mismatch returns the correct error message
- A trace with no `[...]` block returns the correct error message

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

**Detection:** if the input contains a line where `parameters:` is the entire non-whitespace content (regex `^\s*parameters:\s*$`), it is treated as verbose format. This avoids false positives from SQL that contains the word `parameters:` inside a string literal or column alias.

---

## Parser

### Step 1 — Strip prefix
Remove leading `jdbc query:` (case-insensitive, optional).

### Step 2 — Split SQL from parameters
- **Verbose:** SQL is everything between the prefix and the `parameters:` line; params are between `parameters:` and `rows:`.
- **Compact:** SQL is everything before the final `[...]` block; params are inside that block. Note: PostgreSQL SQL can contain `[...]` in array subscripts, but in Glowroot compact traces the parameter block always appears after the complete SQL text — finding the last `[...]` in the string is sufficient for the traces seen in practice. This heuristic is acceptable for the POC.

### Step 3 — Parse parameter list
Parse the comma-separated values inside `[...]`, respecting single-quoted strings (commas inside quotes are not delimiters). Unquoted `null` (case-insensitive) is treated as SQL `NULL`; quoted `'null'` is passed through as a string literal. Recognised types:

| Glowroot form | Substituted as | Notes |
|---|---|---|
| `'SM2asR96Qwi'` | `'SM2asR96Qwi'` | String — used as-is, already quoted |
| `385870` | `385870` | Integer — used as-is |
| `3.14` | `3.14` | Float — used as-is |
| `true` / `false` | `TRUE` / `FALSE` | Boolean — uppercased for PostgreSQL |
| `'null'` | `'null'` | String literal "null" (used in JSONB path contexts) |
| `null` / `NULL` | `NULL` | SQL NULL — unquoted, any case |

### Step 4 — Validate
Count `?` placeholders in the SQL and compare to parameter count. On mismatch, return a clear error. Do not attempt partial substitution.

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
| GENERIC_PLAN | off | Mutually exclusive with ANALYZE (see below) |
| FORMAT | TEXT | Dropdown: TEXT / XML / JSON / YAML — always available regardless of ANALYZE state |

### Enabled only when ANALYZE is checked
| Option | Default (when ANALYZE on) |
|---|---|
| BUFFERS | on |
| TIMING | on |
| WAL | off |
| SUMMARY | on |

When ANALYZE is unchecked, all ANALYZE-dependent options are greyed out and unchecked.

**EXPLAIN clause rendering:** only checked options are emitted, as bare keywords (e.g. `ANALYZE`, not `ANALYZE TRUE`). Unchecked options are omitted entirely — including COSTS, even though it is PostgreSQL's default. Options appear in the order listed in the tables above, with FORMAT always last. Example with ANALYZE + BUFFERS + TIMING + COSTS + FORMAT TEXT: `EXPLAIN (ANALYZE, BUFFERS, TIMING, COSTS, FORMAT TEXT)`.

**GENERIC_PLAN / ANALYZE mutual exclusion:** these two options cannot be active simultaneously.
- If ANALYZE is checked while GENERIC_PLAN is on: uncheck and disable GENERIC_PLAN.
- If GENERIC_PLAN is checked while ANALYZE is on: uncheck and disable ANALYZE (and consequently grey out all ANALYZE-dependent options).

---

## DML Safety Wrapping

When ANALYZE is checked and the query (after trimming whitespace, case-insensitive) starts with `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `TRUNCATE`, `CREATE TABLE AS`, or `EXECUTE`, the output is wrapped in a transaction. (`EXECUTE` runs a prepared statement which may itself be DML; `TRUNCATE` causes irreversible data loss; `CREATE TABLE AS` creates a new table.)

```sql
-- Statement type may modify data: wrapped in transaction for safety
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
│  FORMAT: [TEXT v]  (always enabled)     │
│  -- when ANALYZE on: --                 │
│  [x] BUFFERS  [x] TIMING  [ ] WAL      │
│  [x] SUMMARY                           │
│                                         │
│  [Generate EXPLAIN]                     │
│                                         │
│  WARNING: ANALYZE executes the          │
│  statement - review before running.     │
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
| Placeholder count > parameter count | "SQL has N `?` placeholders but only M parameters were found." |
| Parameter count > placeholder count | "Found M parameters but SQL only has N `?` placeholders." |
| Empty parameter list with placeholders present | "SQL has N `?` placeholders but the parameter list is empty." |
| Substituted SQL is empty after trimming | "No SQL found in the trace." |

Errors are shown inline between the button and the output area. Output area is cleared on error.

---

## Out of Scope (for this POC)

- Executing SQL against a database
- Chrome extension (identified as a follow-on)
- SERIALIZE option (niche, easy to add later)
- Authentication or multi-user support
- Persistent history of transforms
- UI tests (manual browser testing is sufficient for the thin Flask layer)
