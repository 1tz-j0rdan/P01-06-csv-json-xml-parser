import json

import pytest

from data_parser.cli import main
from data_parser.core import DataError, convert, inspect_file, load_records, save_records


@pytest.fixture
def rows():
    return [{"name": "Ada", "age": "30"}, {"name": "Lin", "age": ""}]


@pytest.mark.parametrize("extension", ["csv", "json", "xml"])
def test_roundtrip(tmp_path, rows, extension):
    path = tmp_path / f"people.{extension}"
    save_records(path, rows)
    assert load_records(path) == rows


@pytest.mark.parametrize("source,target", [("csv", "json"), ("json", "xml"), ("xml", "csv")])
def test_conversion(tmp_path, rows, source, target):
    first = tmp_path / f"in.{source}"
    second = tmp_path / f"out.{target}"
    save_records(first, rows)
    assert convert(first, second) == 2
    assert load_records(second) == rows


def test_inspect(tmp_path, rows):
    path = tmp_path / "people.json"
    save_records(path, rows)
    assert inspect_file(path) == {
        "format": "json", "records": 2, "columns": ["name", "age"], "missing_values": 1
    }


def test_missing_column_count(tmp_path):
    path = tmp_path / "people.json"
    save_records(path, [{"a": "x"}, {"b": "y"}])
    assert inspect_file(path)["missing_values"] == 2


def test_overwrite_protection(tmp_path, rows):
    path = tmp_path / "people.csv"
    save_records(path, rows)
    with pytest.raises(DataError):
        save_records(path, rows)
    save_records(path, [], overwrite=True)
    assert load_records(path) == []


def test_same_path(tmp_path, rows):
    path = tmp_path / "same.json"
    save_records(path, rows)
    with pytest.raises(DataError, match="differ"):
        convert(path, path)


@pytest.mark.parametrize("extension", ["txt", "yaml", ""])
def test_bad_extension(tmp_path, extension):
    with pytest.raises(DataError, match="Unsupported"):
        load_records(tmp_path / f"file{'.' + extension if extension else ''}")


def test_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json}")
    with pytest.raises(DataError):
        load_records(path)


def test_duplicate_json_keys(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('[{"a": 1, "a": 2}]')
    with pytest.raises(DataError, match="Duplicate"):
        load_records(path)


@pytest.mark.parametrize("payload", ['{"a": 1}', '[1, 2]', '[["nested"]]'])
def test_nonrecord_json(tmp_path, payload):
    path = tmp_path / "bad.json"
    path.write_text(payload)
    with pytest.raises(DataError):
        load_records(path)


def test_nested_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('[{"a": {"nested": true}}]')
    with pytest.raises(DataError, match="nested"):
        load_records(path)


def test_duplicate_csv_headers(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("a,a\n1,2\n")
    with pytest.raises(DataError, match="unique"):
        load_records(path)


def test_extra_csv_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("a,b\n1,2,3\n")
    with pytest.raises(DataError, match="more values"):
        load_records(path)


def test_invalid_xml_root(tmp_path):
    path = tmp_path / "bad.xml"
    path.write_text("<items/>")
    with pytest.raises(DataError, match="root"):
        load_records(path)


def test_duplicate_xml_field(tmp_path):
    path = tmp_path / "bad.xml"
    path.write_text('<records><record><field name="a">1</field>'
                    '<field name="a">2</field></record></records>')
    with pytest.raises(DataError, match="duplicate"):
        load_records(path)


def test_xml_special_field_name(tmp_path):
    path = tmp_path / "test.xml"
    save_records(path, [{"first name": "A&B <C>"}])
    assert load_records(path) == [{"first name": "A&B <C>"}]


def test_empty_records(tmp_path):
    for ext in ("csv", "json", "xml"):
        path = tmp_path / f"empty.{ext}"
        save_records(path, [])
        assert load_records(path) == []


def test_json_numeric_values(tmp_path):
    path = tmp_path / "nums.json"
    path.write_text(json.dumps([{"n": 3, "active": True, "missing": None}]))
    assert load_records(path) == [{"n": "3", "active": "True", "missing": ""}]


def test_cli_inspect(tmp_path, rows, capsys):
    path = tmp_path / "data.json"
    save_records(path, rows)
    assert main(["inspect", str(path)]) == 0
    assert '"records": 2' in capsys.readouterr().out


def test_cli_validate(tmp_path, rows, capsys):
    path = tmp_path / "data.csv"
    save_records(path, rows)
    assert main(["validate", str(path)]) == 0
    assert "Valid: 2" in capsys.readouterr().out


def test_cli_preview(tmp_path, rows, capsys):
    path = tmp_path / "data.json"
    save_records(path, rows)
    assert main(["preview", str(path), "--limit", "1"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1


def test_cli_convert(tmp_path, rows, capsys):
    source = tmp_path / "data.csv"
    target = tmp_path / "data.xml"
    save_records(source, rows)
    assert main(["convert", str(source), str(target)]) == 0
    assert load_records(target) == rows
    assert "Converted 2" in capsys.readouterr().out


def test_cli_invalid_limit(tmp_path, rows, capsys):
    path = tmp_path / "data.json"
    save_records(path, rows)
    assert main(["preview", str(path), "--limit", "-1"]) == 1
    assert "nonnegative" in capsys.readouterr().err


def test_cli_missing_file(capsys):
    assert main(["inspect", "missing.json"]) == 1
    assert "Error:" in capsys.readouterr().err
