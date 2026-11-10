import io
import urllib.error

import pytest

from hide_housing import download


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_urlopen(monkeypatch):
    calls = []

    def urlopen(request, timeout):
        calls.append(request.full_url)
        name = request.full_url.rsplit("/", 1)[1]
        return FakeResponse(f"#,data\n0,{name}\n".encode())

    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    return calls


def test_downloads_all_sheets_into_cache(tmp_path, fake_urlopen):
    paths = download.download_sheets(tmp_path)
    assert set(paths) == set(download.SHEETS)
    assert fake_urlopen == [download.sheet_url(s) for s in download.SHEETS]
    assert all(u.startswith(download.BASE_URL) for u in fake_urlopen)
    assert paths["Item"].read_text() == "#,data\n0,Item.csv\n"
    assert not list(tmp_path.glob("*.part"))


def test_reuses_cache_without_refresh(tmp_path, fake_urlopen):
    (tmp_path / "Item.csv").write_text("cached")
    paths = download.download_sheets(tmp_path, sheets=("Item",))
    assert fake_urlopen == []
    assert paths["Item"].read_text() == "cached"


def test_refresh_redownloads(tmp_path, fake_urlopen):
    (tmp_path / "Item.csv").write_text("cached")
    download.download_sheets(tmp_path, refresh=True, sheets=("Item",))
    assert len(fake_urlopen) == 1
    assert (tmp_path / "Item.csv").read_text() != "cached"


def test_creates_missing_cache_dir(tmp_path, fake_urlopen):
    download.download_sheets(tmp_path / "a" / "b", sheets=("Item",))
    assert (tmp_path / "a" / "b" / "Item.csv").is_file()


def test_http_error_gives_clear_message(tmp_path, monkeypatch):
    def urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    with pytest.raises(download.DownloadError, match=r"Item\.csv: HTTP 404 Not Found"):
        download.download_sheets(tmp_path, sheets=("Item",))
    assert not (tmp_path / "Item.csv").exists()


def test_network_error_gives_clear_message(tmp_path, monkeypatch):
    def urlopen(request, timeout):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr(download.urllib.request, "urlopen", urlopen)
    with pytest.raises(download.DownloadError, match="no route to host"):
        download.download_sheets(tmp_path, sheets=("Item",))
