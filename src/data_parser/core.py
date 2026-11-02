"""Safe CSV, JSON, and XML handling for flat tabular records.

All values are represented as strings. Missing values become empty strings.
XML uses <records><record><field name="...">value</field></record></records>
to preserve arbitrary field names and avoid invalid XML element names.
"""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


class DataError(ValueError):
    """Invalid input, schema, or supported file format."""


FORMATS = {".csv", ".json", ".xml"}


def _format(path):
    ext = Path(path).suffix.lower()
    if ext not in FORMATS:
        raise DataError(f"Unsupported file extension: {ext or '(none)'}")
    return ext


def _normalize(records):
    if not isinstance(records, list):
        raise DataError("Dataset must be a list of records")
    normalized = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise DataError(f"Record {index} must be an object")
        if not all(isinstance(key, str) and key for key in record):
            raise DataError(f"Record {index} contains an invalid field name")
        if not all(value is None or isinstance(value, (str, int, float, bool)) for value in record.values()):
            raise DataError(f"Record {index} contains a nested or unsupported value")
        normalized.append({key: "" if value is None else str(value) for key, value in record.items()})
    return normalized


def load_records(path):
    """Load flat records; reject duplicate field names and malformed structures."""
    path = Path(path)
    ext = _format(path)
    try:
        if ext == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                if reader.fieldnames is None:
                    return []
                fields = reader.fieldnames
                if any(not field for field in fields) or len(fields) != len(set(fields)):
                    raise DataError("CSV headers must be unique and nonempty")
                records = list(reader)
                if any(None in row for row in records):
                    raise DataError("CSV row has more values than headers")
                return _normalize(records)
        if ext == ".json":
            with path.open("r", encoding="utf-8-sig") as stream:
                return _normalize(json.load(stream, object_pairs_hook=_unique_object))
        root = ET.parse(path).getroot()
        if root.tag != "records" or root.attrib:
            raise DataError("XML root must be <records> without attributes")
        records = []
        for record in root:
            if record.tag != "record" or record.attrib:
                raise DataError("XML records must use <record> without attributes")
            if (record.text or "").strip():
                raise DataError("Unexpected XML text in record")
            row = {}
            for field in record:
                if field.tag != "field" or set(field.attrib) != {"name"}:
                    raise DataError("XML fields must use <field name=...>")
                name = field.attrib["name"]
                if not name or name in row or len(field):
                    raise DataError("Invalid or duplicate XML field")
                row[name] = field.text or ""
                if (field.tail or "").strip():
                    raise DataError("Unexpected XML text after field")
            records.append(row)
        return _normalize(records)
    except (OSError, UnicodeError, csv.Error, json.JSONDecodeError, ET.ParseError) as exc:
        raise DataError(str(exc)) from exc


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DataError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def _columns(records):
    return list(dict.fromkeys(key for row in records for key in row))


def save_records(path, records, *, overwrite=False):
    """Write normalized records, refusing to overwrite unless requested."""
    path = Path(path)
    ext = _format(path)
    rows = _normalize(records)
    columns = _columns(rows)
    mode = "w" if overwrite else "x"
    try:
        with path.open(mode, encoding="utf-8", newline="") as stream:
            if ext == ".csv":
                writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
                if columns:
                    writer.writeheader()
                writer.writerows(rows)
            elif ext == ".json":
                json.dump(rows, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            else:
                root = ET.Element("records")
                for row in rows:
                    item = ET.SubElement(root, "record")
                    for key, value in row.items():
                        field = ET.SubElement(item, "field", {"name": key})
                        field.text = value
                ET.indent(root, space="  ")
                stream.write(ET.tostring(root, encoding="unicode", xml_declaration=False))
                stream.write("\n")
    except (OSError, UnicodeError, csv.Error) as exc:
        raise DataError(str(exc)) from exc


def inspect_file(path):
    rows = load_records(path)
    columns = _columns(rows)
    return {"format": _format(path)[1:], "records": len(rows), "columns": columns,
            "missing_values": sum(not row.get(column, "") for row in rows for column in columns)}


def convert(source, destination, *, overwrite=False):
    if Path(source).resolve() == Path(destination).resolve():
        raise DataError("Source and destination must differ")
    rows = load_records(source)
    save_records(destination, rows, overwrite=overwrite)
    return len(rows)
