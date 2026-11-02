# P01-06 — CSV / JSON / XML Parser

A dependency-free Python command-line tool for validating, inspecting, previewing, and converting **flat tabular records** between CSV, JSON, and XML. Built for Phase 1 of a software engineering portfolio.

## Features

- Parse UTF-8 CSV (including UTF-8 BOM), JSON arrays of objects, and XML records.
- Inspect record count, column names, and missing values.
- Validate input with clear errors for duplicate headers, malformed input, and nested JSON.
- Preview records without modifying files.
- Convert among CSV, JSON, and XML; refuses to overwrite output by default.
- Automated tests, Ruff linting, and GitHub Actions CI.

## Install (PowerShell / Windows)

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Try it

Create disposable input:

```powershell
New-Item -ItemType Directory -Force .\demo-files
@'
name,age,city
Ada,30,London
Lin,25,Seattle
'@ | Set-Content -Encoding utf8 .\demo-files\people.csv
```

Run:

```powershell
python -m data_parser inspect .\demo-files\people.csv
python -m data_parser validate .\demo-files\people.csv
python -m data_parser preview .\demo-files\people.csv --limit 1
python -m data_parser convert .\demo-files\people.csv .\demo-files\people.json
python -m data_parser convert .\demo-files\people.json .\demo-files\people.xml
python -m data_parser inspect .\demo-files\people.xml
```

To intentionally replace an existing destination, add `--overwrite`.

## Test and lint

```powershell
python -m pytest -v
python -m ruff check .
```

## Data model and limitations

- All fields are normalized to **strings** (null/missing values become empty strings). JSON numeric and Boolean types are not preserved across conversion.
- Only flat records are supported; nested arrays and objects are rejected.
- CSV requires a header row; all records may have different fields in JSON/XML, and CSV output takes the union of fields.
- XML uses the explicit schema below to support arbitrary field names:

```xml
<records>
  <record>
    <field name="name">Ada</field>
    <field name="age">30</field>
  </record>
</records>
```

- This is a learning-focused parser, not a streaming parser for massive files. Only process XML from trusted sources; no hardened XML security policy is implemented.

## GitHub publishing

Create a new empty public repository named `P01-06-csv-json-xml-parser` (do not initialize with a README). Then:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Initial release: CSV JSON XML Parser v0.1.0"
git remote add origin https://github.com/1tz-j0rdan/P01-06-csv-json-xml-parser.git
git push -u origin main
```

The `.gitignore` excludes `.venv/` and `demo-files/`.
