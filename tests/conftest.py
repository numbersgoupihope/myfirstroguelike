import pytest


@pytest.fixture(autouse=True)
def isolate_save_file(tmp_path, monkeypatch):
    """Every test gets its own fake $HOME so save/delete never touches the
    real player's save file (or leaves one behind)."""
    monkeypatch.setenv("HOME", str(tmp_path))
