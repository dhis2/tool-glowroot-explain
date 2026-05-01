# Glowroot EXPLAIN Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Flask web app that substitutes Glowroot JDBC trace parameters into SQL and generates a ready-to-paste PostgreSQL EXPLAIN statement.

**Architecture:** Pure parser logic lives in `glowroot_parser.py` (no Flask dependency, fully unit-tested TDD-first). Flask wiring and embedded HTML live in `app.py`. Tests use the five real Glowroot traces collected during design as fixture files.

**Tech Stack:** Python 3.11+, Flask, pytest — all managed via `uv` (PEP 723 inline metadata in `app.py`, tests run with `uv run --with pytest pytest tests/ -v`)

---

## File Map

| File | Responsibility |
|---|---|
| `app.py` | Flask app, `GET /` and `POST /transform` routes, embedded HTML template, PEP 723 uv metadata |
| `glowroot_parser.py` | All parsing and EXPLAIN generation logic — no Flask import |
| `tests/__init__.py` | Empty — makes `tests/` a package |
| `tests/test_parser.py` | All unit and integration tests |
| `tests/fixtures/compact_single_string.txt` | Real trace: compact format, 1 string param |
| `tests/fixtures/compact_large_integers.txt` | Real trace: compact format, 64 integer params |
| `tests/fixtures/verbose_string_integer.txt` | Real trace: verbose format, string + integer |
| `tests/fixtures/verbose_strings_booleans.txt` | Real trace: verbose format, strings + booleans |
| `tests/fixtures/verbose_with_null.txt` | Real trace: verbose format, strings + booleans + NULL |

---

## Task 1: Project scaffold and fixture files

**Files:**
- Create: `glowroot_parser.py`
- Create: `app.py`
- Create: `tests/__init__.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/compact_single_string.txt`
- Create: `tests/fixtures/compact_large_integers.txt`
- Create: `tests/fixtures/verbose_string_integer.txt`
- Create: `tests/fixtures/verbose_strings_booleans.txt`
- Create: `tests/fixtures/verbose_with_null.txt`

- [ ] **Step 1: Create `glowroot_parser.py` skeleton**

```python
class ParseError(ValueError):
    pass


def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    raise NotImplementedError


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    raise NotImplementedError
```

- [ ] **Step 2: Create `app.py` skeleton with PEP 723 metadata**

```python
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
```

- [ ] **Step 3: Create `tests/__init__.py`**

Empty file.

- [ ] **Step 4: Create `tests/test_parser.py` skeleton**

```python
import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


DEFAULT_OPTIONS = {
    "analyze": False, "verbose": False, "costs": True, "settings": False,
    "memory": False, "generic_plan": False, "buffers": False, "timing": False,
    "wal": False, "summary": False, "format": "TEXT",
}

ANALYZE_OPTIONS = {
    **DEFAULT_OPTIONS, "analyze": True, "buffers": True, "timing": True, "summary": True, "costs": False,
}
```

- [ ] **Step 5: Create fixture files**

Create `tests/fixtures/` and populate with the exact traces from the design session.

`tests/fixtures/compact_single_string.txt`:
```
jdbc query: SELECT trackedentitytypeid FROM trackedentitytype  WHERE sharing->>'public' LIKE '__r%' OR sharing->>'public' IS NULL OR sharing->'users'->?->>'access' LIKE '__r%' ['SM2asR96Qwi'] => 5 rows
```

`tests/fixtures/verbose_string_integer.txt`:
```
jdbc query:

SELECT user0_.userinfoid AS userinfo1_234_,
       user0_.uid AS uid2_234_,
       user0_.code AS code3_234_,
       user0_.lastUpdated AS lastupda4_234_,
       user0_.created AS created5_234_,
       user0_.surname AS surname6_234_,
       user0_.firstName AS firstnam7_234_,
       user0_.email AS email8_234_,
       user0_.phoneNumber AS phonenum9_234_,
       user0_.jobTitle AS jobtitl10_234_,
       user0_.introduction AS introdu11_234_,
       user0_.gender AS gender12_234_,
       user0_.birthday AS birthda13_234_,
       user0_.nationality AS nationa14_234_,
       user0_.employer AS employe15_234_,
       user0_.education AS educati16_234_,
       user0_.interests AS interes17_234_,
       user0_.languages AS languag18_234_,
       user0_.welcomeMessage AS welcome19_234_,
       user0_.lastCheckedInterpretations AS lastche20_234_,
       user0_.whatsApp AS whatsap21_234_,
       user0_.skype AS skype22_234_,
       user0_.facebookMessenger AS faceboo23_234_,
       user0_.telegram AS telegra24_234_,
       user0_.twitter AS twitter25_234_,
       user0_.lastupdatedby AS lastupd26_234_,
       user0_.avatar AS avatar27_234_,
       user0_.dataviewmaxorgunitlevel AS datavie28_234_,
       user0_.attributeValues AS attribu29_234_,
       user0_.uuid AS uuid30_234_,
       user0_.creatoruserid AS creator31_234_,
       user0_.username AS usernam32_234_,
       user0_.password AS passwor33_234_,
       user0_.secret AS secret34_234_,
       user0_.externalauth AS externa35_234_,
       user0_.openid AS openid36_234_,
       user0_.ldapid AS ldapid37_234_,
       user0_.passwordLastUpdated AS passwor38_234_,
       user0_.lastLogin AS lastlog39_234_,
       user0_.idToken AS idtoken40_234_,
       user0_.restoreToken AS restore41_234_,
       user0_.restoreExpiry AS restore42_234_,
       user0_.selfRegistered AS selfreg43_234_,
       user0_.invitation AS invitat44_234_,
       user0_.disabled AS disable45_234_,
       user0_.accountExpiry AS account46_234_
  FROM userinfo user0_
 WHERE user0_.username = ?
 LIMIT ?

parameters:

  ['130713_P6', 1]

rows:

  => 1 row
```

`tests/fixtures/verbose_strings_booleans.txt`:
```
jdbc query:

SELECT programsta0_.programstageid AS programs1_179_,
       programsta0_.uid AS uid2_179_,
       programsta0_.code AS code3_179_,
       programsta0_.created AS created4_179_,
       programsta0_.lastUpdated AS lastupda5_179_,
       programsta0_.lastupdatedby AS lastupda6_179_,
       programsta0_.name AS name7_179_,
       programsta0_.description AS descript8_179_,
       programsta0_.formName AS formname9_179_,
       programsta0_.mindaysfromstart AS mindays10_179_,
       programsta0_.programid AS program11_179_,
       programsta0_.repeatable AS repeata12_179_,
       programsta0_.dataentryformid AS dataent13_179_,
       programsta0_.standardInterval AS standar14_179_,
       programsta0_.executiondatelabel AS executi15_179_,
       programsta0_.duedatelabel AS duedate16_179_,
       programsta0_.autoGenerateEvent AS autogen17_179_,
       programsta0_.validationstrategy AS validat18_179_,
       programsta0_.displayGenerateEventBox AS display19_179_,
       programsta0_.generatedByEnrollmentDate AS generat20_179_,
       programsta0_.blockEntryForm AS blocken21_179_,
       programsta0_.remindCompleted AS remindc22_179_,
       programsta0_.allowGenerateNextVisit AS allowge23_179_,
       programsta0_.openAfterEnrollment AS openaft24_179_,
       programsta0_.reportDateToUse AS reportd25_179_,
       programsta0_.preGenerateUID AS pregene26_179_,
       programsta0_.style AS style27_179_,
       programsta0_.hideDueDate AS hidedue28_179_,
       programsta0_.sort_order AS sort_or29_179_,
       programsta0_.translations AS transla30_179_,
       programsta0_.featuretype AS feature31_179_,
       programsta0_.enableuserassignment AS enableu32_179_,
       programsta0_.periodtypeid AS periodt33_179_,
       programsta0_.attributeValues AS attribu34_179_,
       programsta0_.userid AS userid35_179_,
       programsta0_.sharing AS sharing36_179_,
       programsta0_.nextscheduledateid AS nextsch37_179_,
       programsta0_.referral AS referra38_179_
  FROM programstage programsta0_
 WHERE (jsonb_extract_path_text (programsta0_.sharing, ?) LIKE ?
      OR jsonb_extract_path_text (programsta0_.sharing, ?) = ?
      OR jsonb_extract_path_text (programsta0_.sharing, ?) IS null
      OR jsonb_extract_path_text (programsta0_.sharing, ?) IS null
      OR jsonb_extract_path_text (programsta0_.sharing, ?) = ?
      OR jsonb_extract_path_text (programsta0_.sharing, ?) = ?
      OR jsonb_has_user_id (programsta0_.sharing, ?) = ?
     AND jsonb_check_user_access (programsta0_.sharing, ?, ?) = ?)
   AND programsta0_.uid = ?

parameters:

  ['public', 'r%', 'public', 'null', 'public', 'owner', 'owner', 'null', 'owner', 'qweRt000210', 'qweRt000210', true, 'qweRt000210', 'r%', true, 'in3pSeq1UNJ']

rows:

  => 0 rows
```

`tests/fixtures/verbose_with_null.txt`:
```
jdbc query:

SELECT trackedent0_.trackedentityattributeid AS trackede1_214_,
       trackedent0_.uid AS uid2_214_,
       trackedent0_.code AS code3_214_,
       trackedent0_.created AS created4_214_,
       trackedent0_.lastUpdated AS lastupda5_214_,
       trackedent0_.lastupdatedby AS lastupda6_214_,
       trackedent0_.name AS name7_214_,
       trackedent0_.shortname AS shortnam8_214_,
       trackedent0_.description AS descript9_214_,
       trackedent0_.formName AS formnam10_214_,
       trackedent0_.valuetype AS valuety11_214_,
       trackedent0_.aggregationType AS aggrega12_214_,
       trackedent0_.optionsetid AS options13_214_,
       trackedent0_.inherit AS inherit14_214_,
       trackedent0_.expression AS express15_214_,
       trackedent0_.displayOnVisitSchedule AS display16_214_,
       trackedent0_.sortOrderInVisitSchedule AS sortord17_214_,
       trackedent0_.displayInListNoProgram AS display18_214_,
       trackedent0_.sortOrderInListNoProgram AS sortord19_214_,
       trackedent0_.confidential AS confide20_214_,
       trackedent0_.uniquefield AS uniquef21_214_,
       trackedent0_.generated AS generat22_214_,
       trackedent0_.pattern AS pattern23_214_,
       trackedent0_.textpattern AS textpat24_214_,
       trackedent0_.fieldMask AS fieldma25_214_,
       trackedent0_.style AS style26_214_,
       trackedent0_.orgunitScope AS orgunit27_214_,
       trackedent0_.skipsynchronization AS skipsyn28_214_,
       trackedent0_.translations AS transla29_214_,
       trackedent0_.userid AS userid30_214_,
       trackedent0_.sharing AS sharing31_214_,
       trackedent0_.attributeValues AS attribu32_214_
  FROM trackedentityattribute trackedent0_
 WHERE (jsonb_extract_path_text (trackedent0_.sharing, ?) LIKE ?
      OR jsonb_extract_path_text (trackedent0_.sharing, ?) = ?
      OR jsonb_extract_path_text (trackedent0_.sharing, ?) IS null
      OR jsonb_extract_path_text (trackedent0_.sharing, ?) IS null
      OR jsonb_extract_path_text (trackedent0_.sharing, ?) = ?
      OR jsonb_extract_path_text (trackedent0_.sharing, ?) = ?
      OR jsonb_has_user_id (trackedent0_.sharing, ?) = ?
     AND jsonb_check_user_access (trackedent0_.sharing, ?, ?) = ?)
   AND trackedent0_.uid = ?

parameters:

  ['public', 'r%', 'public', 'null', 'public', 'owner', 'owner', 'null', 'owner', 'qweRt000210', 'qweRt000210', true, 'qweRt000210', 'r%', true, NULL]

rows:

  => 0 rows
```

`tests/fixtures/compact_large_integers.txt`:
```
jdbc query: SELECT psi.programstageinstanceid, psi.uid, psi.status, psi.executiondate, psi.duedate, psi.storedby, psi.completedby, psi.completeddate, psi.createdbyuserinfo, psi.created, psi.createdatclient, psi.lastupdated, psi.lastupdatedatclient, psi.lastupdatedbyuserinfo, psi.deleted, ST_AsBinary(psi.geometry) as geometry, tei.uid as tei_uid, pi.uid as enruid, pi.followup as enrfollowup, pi.status as enrstatus, p.uid as prguid, ps.uid as prgstguid, o.uid as ou_uid, o.name as ou_name, coc.uid as cocuid, ( SELECT string_agg(opt.uid::text, ',') FROM dataelementcategoryoption opt join categoryoptioncombos_categoryoptions ccc on opt.categoryoptionid = ccc.categoryoptionid WHERE coc.categoryoptioncomboid = ccc.categoryoptioncomboid ) as catoptions, ui.uid as userid, ui.firstname, ui.surname, ui.username from programstageinstance psi join programinstance pi on psi.programinstanceid = pi.programinstanceid join trackedentityinstance tei on pi.trackedentityinstanceid = tei.trackedentityinstanceid join program p on pi.programid = p.programid join programstage ps on psi.programstageid = ps.programstageid join organisationunit o on psi.organisationunitid = o.organisationunitid join categoryoptioncombo coc on psi.attributeoptioncomboid = coc.categoryoptioncomboid left join userinfo ui on psi.assigneduserid = ui.userinfoid where pi.programinstanceid in (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) AND CASE WHEN p.type = 'WITH_REGISTRATION' THEN p.trackedentitytypeid in (?, ?, ?, ?, ?) else true END AND psi.programstageid in (?, ?, ?, ?, ?, ?, ?, ?, ?) AND pi.programid IN (?, ?) and psi.attributeoptioncomboid not in (select distinct(cocco.categoryoptioncomboid) from categoryoptioncombos_categoryoptions as cocco where cocco.categoryoptionid not in ( select co.categoryoptionid from dataelementcategoryoption co   where  ( co.sharing->>'owner' is null or co.sharing->>'owner' = 'SM2asR96Qwi')  or co.sharing->>'public' like '__r_____' or co.sharing->>'public' is null  or (jsonb_has_user_id( co.sharing, 'SM2asR96Qwi') = true  and jsonb_check_user_access( co.sharing, 'SM2asR96Qwi', '__r_____' ) = true )  ) ) [385870, 2370770, 286604, 286590, 286613, 385556, 2092423, 2092451, 2092120, 385733, 385777, 2092069, 286737, 2370882, 385630, 385670, 2370450, 286859, 2370476, 286457, 286671, 385581, 385896, 2092404, 385603, 385827, 2370501, 285369, 385839, 286497, 286708, 385709, 385901, 286806, 385647, 385607, 2511994, 2092127, 2092413, 385686, 385720, 2092375, 385563, 2511991, 385549, 2370896, 286852, 2370736, 3565, 3977, 3228, 3373, 2281, 4158, 4164, 11008924, 4131, 4156, 4134, 4121, 4117, 4127, 4170, 11008934] => 9587 rows
```

- [ ] **Step 6: Verify uv can run the app**

```bash
uv run app.py &
sleep 1
curl -s http://localhost:5000/ | grep "Glowroot"
kill %1
```

Expected output contains: `Glowroot EXPLAIN Tool`

- [ ] **Step 7: Verify pytest can collect (0 tests, no errors)**

```bash
uv run --with pytest pytest tests/ -v
```

Expected: `no tests ran` with exit code 0.

- [ ] **Step 8: Commit scaffold**

```bash
git add app.py glowroot_parser.py tests/
git commit -m "feat: scaffold app, parser skeleton, test fixtures"
```

---

## Task 2: Format detection

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_parser.py`:

```python
from glowroot_parser import _is_verbose


def test_verbose_detected_from_parameters_line():
    raw = "jdbc query:\nSELECT 1\n\nparameters:\n\n  [42]\n\nrows:\n\n  => 1 row"
    assert _is_verbose(raw) is True


def test_compact_has_no_parameters_line():
    raw = "jdbc query: SELECT 1 WHERE x = ? [42] => 1 row"
    assert _is_verbose(raw) is False


def test_parameters_inside_sql_string_does_not_trigger_verbose():
    # 'parameters:' appears in a SQL string literal, not on its own line
    raw = "jdbc query: SELECT * FROM t WHERE col = 'parameters: foo' [42] => 0 rows"
    assert _is_verbose(raw) is False


```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "verbose" -v
```

Expected: `ImportError` — `_is_verbose` not yet exported.

- [ ] **Step 3: Implement `_is_verbose` in `glowroot_parser.py`**

```python
import re


def _is_verbose(raw: str) -> bool:
    return bool(re.search(r'^\s*parameters:\s*$', raw, re.MULTILINE))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "verbose" -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement verbose format detection"
```

---

## Task 3: Extract SQL and param block — verbose format

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
from glowroot_parser import _split_verbose


def test_split_verbose_extracts_sql():
    raw = "jdbc query:\n\nSELECT 1 WHERE x = ?\n\nparameters:\n\n  ['hello']\n\nrows:\n\n  => 1 row"
    sql, param_block = _split_verbose(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_verbose_extracts_param_block():
    raw = "jdbc query:\n\nSELECT 1 WHERE x = ?\n\nparameters:\n\n  ['hello']\n\nrows:\n\n  => 1 row"
    _, param_block = _split_verbose(raw)
    assert param_block == "['hello']"


def test_split_verbose_strips_jdbc_prefix_case_insensitive():
    raw = "JDBC QUERY:\n\nSELECT 1\n\nparameters:\n\n  [42]\n\nrows:\n\n  => 1 row"
    sql, _ = _split_verbose(raw)
    assert sql == "SELECT 1"


def test_split_verbose_preserves_multiline_sql():
    raw = "jdbc query:\n\nSELECT a,\n       b\n  FROM t\n WHERE x = ?\n\nparameters:\n\n  [1]\n\nrows:\n\n  => 0 rows"
    sql, _ = _split_verbose(raw)
    assert "SELECT a," in sql
    assert "WHERE x = ?" in sql


def test_split_verbose_not_confused_by_parameters_alias_in_sql_body():
    # 'parameters:' appears as a column alias inside the SQL but the real
    # section marker is still correctly found and split on
    raw = "jdbc query:\n\nSELECT col AS \"parameters:\", x\n  FROM t\n WHERE y = ?\n\nparameters:\n\n  [1]\n\nrows:\n\n  => 0 rows"
    sql, param_block = _split_verbose(raw)
    assert param_block == "[1]"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "split_verbose" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `_split_verbose` in `glowroot_parser.py`**

```python
def _split_verbose(raw: str) -> tuple[str, str]:
    text = re.sub(r'(?i)^\s*jdbc\s+query:\s*', '', raw.strip(), count=1)
    parts = re.split(r'^\s*parameters:\s*$', text, maxsplit=1, flags=re.MULTILINE)
    sql = parts[0].strip()
    rest = parts[1] if len(parts) > 1 else ''
    rows_split = re.split(r'^\s*rows:\s*$', rest, maxsplit=1, flags=re.MULTILINE)
    param_block = rows_split[0].strip()
    return sql, param_block
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "split_verbose" -v
```

Expected: 5 passed.

- [ ] **Step 4b: Add edge-case test for missing `rows:` section**

```python
def test_split_verbose_works_without_rows_section():
    raw = "jdbc query:\n\nSELECT 1\n\nparameters:\n\n  [42]\n"
    sql, param_block = _split_verbose(raw)
    assert sql == "SELECT 1"
    assert param_block == "[42]"
```

Run: `uv run --with pytest pytest tests/test_parser.py -k "split_verbose" -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement verbose format SQL/param extraction"
```

---

## Task 4: Extract SQL and param block — compact format

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
from glowroot_parser import _split_compact


def test_split_compact_extracts_sql():
    raw = "jdbc query: SELECT 1 WHERE x = ? ['hello'] => 5 rows"
    sql, _ = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_compact_extracts_param_block():
    raw = "jdbc query: SELECT 1 WHERE x = ? ['hello'] => 5 rows"
    _, param_block = _split_compact(raw)
    assert param_block == "['hello']"


def test_split_compact_strips_jdbc_prefix_case_insensitive():
    raw = "JDBC QUERY: SELECT 1 WHERE x = ? [42] => 1 row"
    sql, _ = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_compact_handles_multiple_params():
    raw = "jdbc query: SELECT 1 WHERE x = ? AND y = ? [42, 'abc'] => 0 rows"
    sql, param_block = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ? AND y = ?"
    assert param_block == "[42, 'abc']"


def test_split_compact_raises_when_no_bracket():
    with pytest.raises(ParseError, match="Could not find a parameter list"):
        _split_compact("jdbc query: SELECT 1 WHERE x = 1")


def test_split_compact_works_without_row_count_suffix():
    # '=> N rows' at the end is optional
    raw = "jdbc query: SELECT 1 WHERE x = ? [42]"
    sql, param_block = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"
    assert param_block == "[42]"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "split_compact" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `_split_compact` in `glowroot_parser.py`**

```python
def _split_compact(raw: str) -> tuple[str, str]:
    text = re.sub(r'(?i)^\s*jdbc\s+query:\s*', '', raw.strip(), count=1)
    text = re.sub(r'=>\s*\d+\s+rows?\s*$', '', text).strip()
    bracket_start = text.rfind('[')
    if bracket_start == -1:
        raise ParseError("Could not find a parameter list '[...]' in the trace.")
    bracket_end = text.find(']', bracket_start)
    if bracket_end == -1:
        raise ParseError("Could not find a parameter list '[...]' in the trace.")
    sql = text[:bracket_start].strip()
    param_block = text[bracket_start:bracket_end + 1]
    return sql, param_block
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "split_compact" -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement compact format SQL/param extraction"
```

---

## Task 5: Parse the parameter list — all types

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
from glowroot_parser import _parse_param_list


def test_parse_single_string():
    assert _parse_param_list("['SM2asR96Qwi']") == ["'SM2asR96Qwi'"]


def test_parse_single_integer():
    assert _parse_param_list("[42]") == ["42"]


def test_parse_single_float():
    assert _parse_param_list("[3.14]") == ["3.14"]


def test_parse_true():
    assert _parse_param_list("[true]") == ["TRUE"]


def test_parse_false():
    assert _parse_param_list("[false]") == ["FALSE"]


def test_parse_unquoted_null_uppercase():
    assert _parse_param_list("[NULL]") == ["NULL"]


def test_parse_unquoted_null_lowercase():
    assert _parse_param_list("[null]") == ["NULL"]


def test_parse_quoted_null_is_a_string():
    assert _parse_param_list("['null']") == ["'null'"]


def test_parse_mixed_string_and_integer():
    assert _parse_param_list("['130713_P6', 1]") == ["'130713_P6'", "1"]


def test_parse_string_with_comma_inside_does_not_split():
    assert _parse_param_list("['hello, world', 42]") == ["'hello, world'", "42"]


def test_parse_strings_booleans_null():
    result = _parse_param_list("['public', 'r%', true, NULL]")
    assert result == ["'public'", "'r%'", "TRUE", "NULL"]


def test_parse_empty_list():
    assert _parse_param_list("[]") == []


def test_parse_large_integer_list():
    result = _parse_param_list("[1, 2, 3, 4, 5]")
    assert result == ["1", "2", "3", "4", "5"]


def test_parse_string_with_escaped_single_quote():
    # SQL uses '' to escape a single quote inside a string
    result = _parse_param_list("['it''s a test', 42]")
    assert result == ["'it''s a test'", "42"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "parse_" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `_parse_param_list` in `glowroot_parser.py`**

```python
def _parse_param_list(param_block: str) -> list[str]:
    content = param_block.strip()
    if content.startswith('['):
        content = content[1:]
    if content.endswith(']'):
        content = content[:-1]
    content = content.strip()
    if not content:
        return []

    params: list[str] = []
    i = 0
    while i < len(content):
        if content[i] in ' \t':
            i += 1
        elif content[i] == ',':
            i += 1
        elif content[i] == "'":
            j = i + 1
            while j < len(content):
                if content[j] == "'":
                    if j + 1 < len(content) and content[j + 1] == "'":
                        j += 2  # '' is an escaped single quote — skip both chars
                        continue
                    break
                j += 1
            params.append(content[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < len(content) and content[j] != ',':
                j += 1
            val = content[i:j].strip()
            if val.lower() == 'true':
                params.append('TRUE')
            elif val.lower() == 'false':
                params.append('FALSE')
            elif val.lower() == 'null':
                params.append('NULL')
            else:
                params.append(val)
            i = j
    return params
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "parse_" -v
```

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement parameter list parser with all Glowroot types"
```

---

## Task 6: Validate and substitute parameters

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
from glowroot_parser import _substitute


def test_substitute_single_string():
    assert _substitute("WHERE x = ?", ["'hello'"]) == "WHERE x = 'hello'"


def test_substitute_multiple_params_left_to_right():
    assert _substitute("WHERE a = ? AND b = ?", ["1", "'two'"]) == "WHERE a = 1 AND b = 'two'"


def test_substitute_null():
    assert _substitute("WHERE x = ?", ["NULL"]) == "WHERE x = NULL"


def test_substitute_boolean():
    assert _substitute("WHERE active = ?", ["TRUE"]) == "WHERE active = TRUE"


def test_substitute_raises_too_few_params():
    with pytest.raises(ParseError, match=r"SQL has 2 '\?' placeholders but only 1 parameters were found"):
        _substitute("WHERE a = ? AND b = ?", ["1"])


def test_substitute_raises_too_many_params():
    with pytest.raises(ParseError, match=r"Found 2 parameters but SQL only has 1 '\?' placeholders"):
        _substitute("WHERE a = ?", ["1", "2"])


def test_substitute_raises_empty_params_with_placeholders():
    with pytest.raises(ParseError, match=r"SQL has 1 '\?' placeholders but the parameter list is empty"):
        _substitute("WHERE a = ?", [])


def test_substitute_no_placeholders_no_params_is_valid():
    assert _substitute("SELECT 1", []) == "SELECT 1"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "substitute" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `_substitute` in `glowroot_parser.py`**

```python
def _substitute(sql: str, params: list[str]) -> str:
    count = sql.count('?')
    if count > 0 and len(params) == 0:
        raise ParseError(f"SQL has {count} '?' placeholders but the parameter list is empty.")
    if count > len(params):
        raise ParseError(f"SQL has {count} '?' placeholders but only {len(params)} parameters were found.")
    if len(params) > count:
        raise ParseError(f"Found {len(params)} parameters but SQL only has {count} '?' placeholders.")
    result = sql
    for param in params:
        result = result.replace('?', param, 1)
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "substitute" -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement parameter substitution with count validation"
```

---

## Task 7: Build the EXPLAIN clause

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

> **Note on option order:** The spec's inline example (`§EXPLAIN Options`) places BUFFERS before COSTS, but this is a typo — the spec's own option tables are authoritative and define the canonical order used here. Follow the table order, not the example.

```python
from glowroot_parser import _build_explain_clause

_ALL_OFF = {k: False for k in ["analyze","verbose","costs","settings","memory","generic_plan","buffers","timing","wal","summary"]}


def test_explain_clause_no_boolean_options():
    opts = {**_ALL_OFF, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (FORMAT TEXT)"


def test_explain_clause_costs_only():
    opts = {**_ALL_OFF, "costs": True, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (COSTS, FORMAT TEXT)"


def test_explain_clause_analyze_buffers_timing():
    opts = {**_ALL_OFF, "analyze": True, "buffers": True, "timing": True, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)"


def test_explain_clause_canonical_order():
    # All boolean options on except GENERIC_PLAN — verify table order from spec
    opts = {**_ALL_OFF, "analyze": True, "verbose": True, "costs": True, "settings": True,
            "memory": True, "buffers": True, "timing": True, "wal": True, "summary": True, "format": "JSON"}
    assert _build_explain_clause(opts) == "EXPLAIN (ANALYZE, VERBOSE, COSTS, SETTINGS, MEMORY, BUFFERS, TIMING, WAL, SUMMARY, FORMAT JSON)"


def test_explain_clause_format_json():
    opts = {**_ALL_OFF, "format": "JSON"}
    assert _build_explain_clause(opts) == "EXPLAIN (FORMAT JSON)"


def test_explain_clause_format_always_last():
    opts = {**_ALL_OFF, "verbose": True, "format": "YAML"}
    assert _build_explain_clause(opts).endswith("FORMAT YAML)")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "explain_clause" -v
```

Expected: `ImportError`.

- [ ] **Step 3: Implement `_build_explain_clause` in `glowroot_parser.py`**

```python
_OPTION_ORDER = [
    "analyze", "verbose", "costs", "settings", "memory", "generic_plan",
    "buffers", "timing", "wal", "summary",
]


def _build_explain_clause(options: dict) -> str:
    parts = [k.upper() for k in _OPTION_ORDER if options.get(k)]
    parts.append(f"FORMAT {options.get('format', 'TEXT')}")
    return f"EXPLAIN ({', '.join(parts)})"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "explain_clause" -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement EXPLAIN clause builder with canonical option ordering"
```

---

## Task 8: DML detection and transaction safety wrapping

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing tests**

```python
from glowroot_parser import _is_dml


def test_select_is_not_dml():
    assert _is_dml("SELECT 1") is False


def test_delete_is_dml():
    assert _is_dml("DELETE FROM foo WHERE id = 1") is True


def test_insert_is_dml():
    assert _is_dml("INSERT INTO foo VALUES (1)") is True


def test_update_is_dml():
    assert _is_dml("UPDATE foo SET x = 1") is True


def test_merge_is_dml():
    assert _is_dml("MERGE INTO foo USING bar ON foo.id = bar.id") is True


def test_truncate_is_dml():
    assert _is_dml("TRUNCATE TABLE foo") is True


def test_execute_is_dml():
    assert _is_dml("EXECUTE my_prepared_plan") is True


def test_create_table_as_is_dml():
    assert _is_dml("CREATE TABLE foo AS SELECT 1") is True


def test_plain_create_table_is_not_dml():
    # CREATE TABLE without AS is plain DDL — should not be wrapped
    assert _is_dml("CREATE TABLE foo (id int)") is False


def test_dml_detection_is_case_insensitive():
    assert _is_dml("delete from foo") is True


def test_dml_detection_ignores_leading_whitespace():
    assert _is_dml("  \n  DELETE FROM foo") is True


def test_delete_with_analyze_wraps_in_transaction():
    result = generate_explain_sql(
        "DELETE FROM foo WHERE id = 1",
        [],
        {**ANALYZE_OPTIONS, "costs": False},
    )
    assert result == (
        "-- Statement type may modify data: wrapped in transaction for safety\n"
        "BEGIN;\n"
        "EXPLAIN (ANALYZE, BUFFERS, TIMING, SUMMARY, FORMAT TEXT)\n"
        "DELETE FROM foo WHERE id = 1;\n"
        "ROLLBACK;"
    )


def test_select_with_analyze_is_not_wrapped():
    result = generate_explain_sql(
        "SELECT 1 WHERE x = ?",
        ["42"],
        {**ANALYZE_OPTIONS, "costs": False},
    )
    assert "BEGIN;" not in result
    assert "ROLLBACK;" not in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "dml or delete or wrapped or truncate or insert or update or merge or execute or create_table" -v
```

Expected: `ImportError` for `_is_dml`; other failures.

- [ ] **Step 3: Implement `_is_dml` and complete `generate_explain_sql` in `glowroot_parser.py`**

```python
_DML_FIRST_WORDS = {"insert", "update", "delete", "merge", "truncate", "execute"}


def _is_dml(sql: str) -> bool:
    words = sql.strip().lower().split()
    if not words:
        return False
    if words[0] in _DML_FIRST_WORDS:
        return True
    # Only "CREATE TABLE ... AS (SELECT ...)" is DML — plain DDL "CREATE TABLE foo (...)" is not
    if len(words) >= 3 and words[0] == "create" and words[1] == "table" and "as" in words:
        return True
    return False


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    if not sql.strip():
        raise ParseError("No SQL found in the trace.")
    substituted = _substitute(sql, params)
    clause = _build_explain_clause(options)
    explain = f"{clause}\n{substituted};"
    if options.get("analyze") and _is_dml(substituted):
        explain = (
            "-- Statement type may modify data: wrapped in transaction for safety\n"
            f"BEGIN;\n{explain}\nROLLBACK;"
        )
    return explain
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_parser.py -k "dml or delete or wrapped or truncate or insert or update or merge or execute or create_table" -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: implement DML detection and transaction safety wrapping"
```

---

## Task 9: Wire up `parse_glowroot_trace` and integration tests

**Files:**
- Modify: `glowroot_parser.py`
- Modify: `tests/test_parser.py`

- [ ] **Step 1: Write failing integration tests**

```python
def test_integration_compact_single_string():
    raw = load("compact_single_string.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params == ["'SM2asR96Qwi'"]
    assert sql.count('?') == 1
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert "'SM2asR96Qwi'" in result
    assert '?' not in result


def test_integration_verbose_string_and_integer():
    raw = load("verbose_string_integer.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params == ["'130713_P6'", "1"]
    assert sql.count('?') == 2
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert "'130713_P6'" in result
    assert '?' not in result


def test_integration_verbose_strings_and_booleans():
    raw = load("verbose_strings_booleans.txt")
    sql, params = parse_glowroot_trace(raw)
    assert "TRUE" in params
    assert "'in3pSeq1UNJ'" == params[-1]
    assert sql.count('?') == len(params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    assert "TRUE" in result


def test_integration_verbose_with_null():
    raw = load("verbose_with_null.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params[-1] == "NULL"
    assert sql.count('?') == len(params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    # last substituted value is NULL, followed by ;
    assert result.rstrip().endswith("NULL;")


def test_integration_compact_64_integer_params():
    raw = load("compact_large_integers.txt")
    sql, params = parse_glowroot_trace(raw)
    assert len(params) == 64
    assert all(p.isdigit() for p in params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    assert "385870" in result


def test_integration_empty_input_raises():
    with pytest.raises(ParseError, match="Paste a Glowroot JDBC trace above"):
        parse_glowroot_trace("")


def test_integration_no_param_block_raises():
    with pytest.raises(ParseError, match="Could not find a parameter list"):
        parse_glowroot_trace("jdbc query: SELECT 1 WHERE x = 1")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_parser.py -k "integration" -v
```

Expected: failures because `parse_glowroot_trace` raises `NotImplementedError`.

- [ ] **Step 3: Implement `parse_glowroot_trace` in `glowroot_parser.py`**

```python
def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    if not raw.strip():
        raise ParseError("Paste a Glowroot JDBC trace above.")
    if _is_verbose(raw):
        sql, param_block = _split_verbose(raw)
    else:
        sql, param_block = _split_compact(raw)
    if not sql.strip():
        raise ParseError("No SQL found in the trace.")
    params = _parse_param_list(param_block)
    return sql, params
```

- [ ] **Step 4: Run the full test suite**

```bash
uv run --with pytest pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add glowroot_parser.py tests/test_parser.py
git commit -m "feat: wire up parse_glowroot_trace and pass all integration tests"
```

---

## Task 10: Flask route — `POST /transform`

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the stub `transform` function**

```python
@app.post("/transform")
def transform():
    data = request.get_json(force=True)
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
        "format":       data.get("format", "TEXT"),
    }
    try:
        sql, params = parse_glowroot_trace(raw)
        result = generate_explain_sql(sql, params, options)
        return jsonify({"sql": result})
    except ParseError as e:
        return jsonify({"error": str(e)}), 400
```

- [ ] **Step 2: Smoke-test with curl**

```bash
uv run app.py &
sleep 1
curl -s -X POST http://localhost:5000/transform \
  -H "Content-Type: application/json" \
  -d '{"trace":"jdbc query: SELECT 1 WHERE x = ? [42]","costs":true,"format":"TEXT"}' \
  | python3 -m json.tool
kill %1
```

Expected JSON: `{"sql": "EXPLAIN (COSTS, FORMAT TEXT)\nSELECT 1 WHERE x = 42;"}`

- [ ] **Step 3: Test error response**

```bash
uv run app.py &
sleep 1
curl -s -X POST http://localhost:5000/transform \
  -H "Content-Type: application/json" \
  -d '{"trace":"","format":"TEXT"}' \
  | python3 -m json.tool
kill %1
```

Expected JSON: `{"error": "Paste a Glowroot JDBC trace above."}`

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: implement POST /transform route"
```

---

## Task 11: Flask UI template

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the `HTML` placeholder with the full template**

Replace `HTML = """..."""` in `app.py` with:

```python
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
```

- [ ] **Step 2: Manual browser test checklist**

```bash
uv run app.py
```

Open http://localhost:5000 and verify:
1. Paste `compact_single_string.txt` content, click Generate EXPLAIN — output contains `'SM2asR96Qwi'`, no `?`
2. Paste `verbose_with_null.txt` content — output ends with `NULL;`
3. Check ANALYZE — BUFFERS/TIMING/SUMMARY auto-enable, GENERIC_PLAN greys out, warning banner appears
4. Uncheck ANALYZE — dependent options grey out and uncheck, warning disappears
5. Check GENERIC_PLAN — ANALYZE unchecks and greys out
6. Check ANALYZE while GENERIC_PLAN is on — GENERIC_PLAN unchecks and greys out
7. Paste empty string, click Generate EXPLAIN — error message "Paste a Glowroot JDBC trace above." appears, output clears
8. Click Copy — clipboard contents match output textarea (paste into text editor to verify)

- [ ] **Step 3: Final full test suite run**

```bash
uv run --with pytest pytest tests/ -v
```

Expected: all tests pass, zero failures.

- [ ] **Step 4: Final commit**

```bash
git add app.py
git commit -m "feat: complete Flask UI with EXPLAIN options, dependency logic, and copy button"
```
