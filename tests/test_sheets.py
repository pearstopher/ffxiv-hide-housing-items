from pathlib import Path

import pytest

from hide_housing.sheets import SheetError, read_sheet, to_bool

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_reads_fixture_keyed_by_row_id_with_conversions():
    furniture = read_sheet(
        FIXTURES / "HousingFurniture.csv",
        {"Item": int, "ModelKey": int, "HousingItemCategory": int, "Unknown5": to_bool},
    )
    assert furniture[197269] == {
        "Item": 21839,
        "ModelKey": 633,
        "HousingItemCategory": 12,
        "Unknown5": True,
    }
    assert furniture[196608]["Item"] == 0


def test_only_selected_columns_are_kept():
    items = read_sheet(FIXTURES / "Item.csv", {"Name": str})
    assert items[21839] == {"Name": "Stage Panel"}
    assert items[0] == {"Name": ""}


def test_all_columns_as_strings_by_default():
    categories = read_sheet(FIXTURES / "FurnitureCatalogCategory.csv")
    assert categories[8] == {"Category": "Walls/Pillars/Partitions", "Unknown0": "12", "Unknown1": "7"}
    assert len(categories) == 30


def test_quoted_fields_with_commas_and_newlines(tmp_path):
    sheet = tmp_path / "Item.csv"
    # write_bytes so Windows doesn't turn the embedded \n into \r\n
    sheet.write_bytes(
        b'#,Name,Description\n'
        b'1,"Table, Round","Line one\nLine two, with comma"\n'
        b'2,Chair,Plain\n'
    )
    items = read_sheet(sheet)
    assert items[1] == {"Name": "Table, Round", "Description": "Line one\nLine two, with comma"}
    assert items[2]["Name"] == "Chair"


def test_handles_utf8_bom(tmp_path):
    sheet = tmp_path / "s.csv"
    sheet.write_bytes(b"\xef\xbb\xbf#,Name\n1,\xc3\x84\n")
    assert read_sheet(sheet) == {1: {"Name": "Ä"}}


def test_missing_column_is_reported(tmp_path):
    with pytest.raises(SheetError, match="missing column.*ModelKey"):
        read_sheet(FIXTURES / "Item.csv", {"ModelKey": int})


def test_bad_value_is_reported_with_row(tmp_path):
    sheet = tmp_path / "s.csv"
    sheet.write_text("#,Count\n1,5\n2,lots\n", encoding="utf-8")
    with pytest.raises(SheetError, match="bad row 3"):
        read_sheet(sheet, {"Count": int})


def test_header_must_start_with_id_column(tmp_path):
    sheet = tmp_path / "s.csv"
    sheet.write_text("key,Name\n1,a\n", encoding="utf-8")
    with pytest.raises(SheetError, match="first column"):
        read_sheet(sheet)


def test_empty_file(tmp_path):
    sheet = tmp_path / "s.csv"
    sheet.write_text("", encoding="utf-8")
    with pytest.raises(SheetError, match="empty"):
        read_sheet(sheet)


def test_to_bool():
    assert to_bool("True") is True
    assert to_bool("False") is False
    with pytest.raises(ValueError):
        to_bool("yes")
