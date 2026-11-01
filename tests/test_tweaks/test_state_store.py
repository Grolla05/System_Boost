import pytest

from backend.tweaks import state_store
from backend.tweaks.base import TweakError


def test_load_state_on_missing_file_returns_empty_structure(tmp_path):
    state = state_store.load_state(path=tmp_path / "state.json")

    assert state["tweaks"] == {}
    assert state["_schema_version"] == 1


def test_save_and_get_applied_round_trips_record(tmp_path):
    path = tmp_path / "state.json"

    state_store.save_applied("telemetry", previous_value=None, applied_value=0, requires_admin=True, path=path)
    record = state_store.get_applied("telemetry", path=path)

    assert record["tweak_id"] == "telemetry"
    assert record["previous_value"] is None
    assert record["applied_value"] == 0
    assert record["requires_admin"] is True
    assert "applied_at" in record


def test_get_applied_returns_none_when_not_applied(tmp_path):
    assert state_store.get_applied("telemetry", path=tmp_path / "state.json") is None


def test_second_save_overwrites_without_duplicating(tmp_path):
    path = tmp_path / "state.json"

    state_store.save_applied("telemetry", previous_value=None, applied_value=0, requires_admin=True, path=path)
    state_store.save_applied("telemetry", previous_value=None, applied_value=0, requires_admin=True, path=path)

    assert len(state_store.list_applied(path=path)) == 1


def test_clear_applied_removes_record(tmp_path):
    path = tmp_path / "state.json"
    state_store.save_applied("telemetry", previous_value=None, applied_value=0, requires_admin=True, path=path)

    state_store.clear_applied("telemetry", path=path)

    assert state_store.get_applied("telemetry", path=path) is None


def test_clear_applied_on_unknown_id_does_not_raise(tmp_path):
    state_store.clear_applied("nonexistent", path=tmp_path / "state.json")  # must not raise


def test_list_applied_sorted_most_recent_first(tmp_path):
    path = tmp_path / "state.json"

    state_store.save_applied("power_plan", None, "guid-a", False, path=path)
    state_store.save_applied("hibernation", 1, 0, True, path=path)

    records = state_store.list_applied(path=path)

    assert [r["tweak_id"] for r in records] == ["hibernation", "power_plan"]


@pytest.mark.parametrize("content", ['{"tweaks": {"a"', "[]", '{"tweaks": []}', b"\xff\xfe"])
def test_damaged_state_is_kept_and_blocks_writes(tmp_path, content):
    path = tmp_path / "state.json"
    raw = content if isinstance(content, bytes) else content.encode()
    path.write_bytes(raw)

    with pytest.raises(state_store.StateCorruptError):
        state_store.load_state(path)
    with pytest.raises(state_store.StateCorruptError):
        state_store.save_applied("b", 1, 0, False, path=path)

    assert path.read_bytes() == raw
    assert [p.read_bytes() for p in tmp_path.glob("state.corrupt-*.json")] == [raw]


def test_state_corrupt_error_is_a_tweak_error():
    assert issubclass(state_store.StateCorruptError, TweakError)


def test_save_keeps_previous_version_as_bak(tmp_path):
    path = tmp_path / "state.json"
    state_store.save_applied("a", 1, 0, False, path=path)
    first = path.read_bytes()

    state_store.save_applied("b", 1, 0, False, path=path)

    assert (tmp_path / "state.json.bak").read_bytes() == first


def test_update_previous_keeps_the_rest_of_the_record(tmp_path):
    path = tmp_path / "state.json"
    state_store.save_applied("a", ["x", "y"], ["x", "y"], True, path=path)

    state_store.update_previous("a", ["y"], path=path)

    record = state_store.get_applied("a", path=path)
    assert record["previous_value"] == ["y"]
    assert record["applied_value"] == ["x", "y"]
