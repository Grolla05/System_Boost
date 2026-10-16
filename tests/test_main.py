import pytest

from main import parse_args


def test_no_args_defaults_to_menu():
    args = parse_args([])
    assert args.command == "menu"


def test_menu_subcommand():
    args = parse_args(["menu", "-y"])
    assert args.command == "menu"
    assert args.yes is True


def test_bare_flags_imply_clean_for_back_compat():
    args = parse_args(["--dry-run", "-y"])
    assert args.command == "clean"
    assert args.dry_run is True
    assert args.yes is True


def test_no_drivers_flag_defaults_false():
    assert parse_args(["menu"]).no_drivers is False
    assert parse_args(["clean"]).no_drivers is False


def test_no_drivers_flag_on_menu_and_clean():
    assert parse_args(["menu", "--no-drivers"]).no_drivers is True
    assert parse_args(["clean", "--no-drivers"]).no_drivers is True


def test_no_sound_flag_defaults_false():
    assert parse_args(["menu"]).no_sound is False
    assert parse_args(["clean"]).no_sound is False


def test_no_sound_flag_on_menu_and_clean():
    assert parse_args(["menu", "--no-sound"]).no_sound is True
    assert parse_args(["clean", "--no-sound"]).no_sound is True


def test_palette_flag_on_menu_and_clean():
    assert parse_args(["menu", "-p", "arcade"]).palette == "arcade"
    assert parse_args(["clean", "--palette", "arcade"]).palette == "arcade"
    assert parse_args(["menu"]).palette is None


def test_list_subcommand():
    args = parse_args(["list"])
    assert args.command == "list"


def test_apply_subcommand_requires_tweak_id():
    args = parse_args(["apply", "telemetry"])
    assert args.command == "apply"
    assert args.tweak_id == "telemetry"


def test_undo_subcommand_with_id():
    args = parse_args(["undo", "telemetry"])
    assert args.command == "undo"
    assert args.tweak_id == "telemetry"
    assert args.all is False


def test_undo_subcommand_with_all_flag():
    args = parse_args(["undo", "--all"])
    assert args.command == "undo"
    assert args.all is True


def test_undo_without_id_or_all_errors():
    with pytest.raises(SystemExit):
        parse_args(["undo"])


def test_info_subcommand():
    args = parse_args(["info"])
    assert args.command == "info"


def test_info_is_not_rerouted_to_clean():
    import main

    assert "info" in main.COMMANDS
    assert "info" in main._DISPATCH


def test_cmd_info_renders_machine_info(monkeypatch):
    import main

    sentinel = object()
    shown = []
    monkeypatch.setattr(main, "get_machine_info", lambda: sentinel)
    monkeypatch.setattr(main, "show_machine_info", lambda info: shown.append(info))

    main.cmd_info(main.parse_args(["info"]))

    assert shown == [sentinel]


def test_driver_step_survives_unexpected_error(monkeypatch):
    import main

    def boom(*a, **k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(main, "show_driver_update", boom)
    args = main.parse_args(["menu"])

    summary = main._run_driver_step(args)

    assert "kaboom" in summary


def test_run_guarded_waits_for_key_on_crash(monkeypatch, capsys):
    import main

    waited = []

    def crash():
        raise RuntimeError("kaboom")

    monkeypatch.setattr(main, "main", crash)
    monkeypatch.setattr(main, "_wait_key_after_crash", lambda: waited.append(True))

    with pytest.raises(SystemExit) as exc:
        main.run_guarded()

    assert exc.value.code == 1
    assert waited == [True]
    assert "kaboom" in capsys.readouterr().err


class _FakeLog:
    def __init__(self):
        self.calls = []
        self.texts = {}

    def start(self, key, text):
        self.calls.append(("start", key, text))

    def finish(self, key, status, note=None, text=None):
        self.calls.append(("finish", key, status, note))
        if text:
            self.texts[key] = text

    def item(self, text, status="ok", note=None):
        self.calls.append(("item", text, status))

    def is_running(self, key):
        return any(c[0] == "start" and c[1] == key for c in self.calls) and not any(
            c[0] == "finish" and c[1] == key for c in self.calls)


def test_driver_step_with_log_reports_each_driver(monkeypatch):
    import main

    def fake_update(progress_callback=None, on_scan=None, dry_run=False, on_result=None, on_notice=None):
        on_scan(2)
        progress_callback("Driver A")
        on_result("Driver A", True, None)
        progress_callback("Driver B")
        on_result("Driver B", False, "falhou")
        return [("Driver A", True, None), ("Driver B", False, "falhou")], False

    monkeypatch.setattr(main, "update_all_drivers", fake_update)
    mlog = _FakeLog()

    summary = main._run_driver_step(main.parse_args(["menu"]), mlog=mlog)

    finished = {c[1]: c[2] for c in mlog.calls if c[0] == "finish"}
    assert finished["driver:Driver A"] == "ok"
    assert finished["driver:Driver B"] == "fail"
    assert finished["drivers"] == "ok"
    assert "1 driver(s) atualizado(s)" in summary


def test_driver_step_with_log_closes_scan_line_when_skipped(monkeypatch):
    import main

    monkeypatch.setattr(main, "update_all_drivers",
                        lambda **k: ([("Drivers", None, "requer administrador")], False))
    mlog = _FakeLog()

    main._run_driver_step(main.parse_args(["menu"]), mlog=mlog)

    assert ("finish", "drivers", "skip", "requer administrador") in mlog.calls


def test_driver_step_with_log_marks_scan_line_failed_on_crash(monkeypatch):
    import main

    def boom(**k):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(main, "update_all_drivers", boom)
    mlog = _FakeLog()

    summary = main._run_driver_step(main.parse_args(["menu"]), mlog=mlog)

    assert "kaboom" in summary
    assert any(c[:3] == ("finish", "drivers", "fail") for c in mlog.calls)


def test_clean_with_log_reports_each_folder(monkeypatch, tmp_path):
    import main

    mlog = _FakeLog()
    sizes = {"User Temp": 1024, "System Temp": 2048}
    monkeypatch.setattr(main, "clean_directory", lambda path, cb, dry_run=False: sizes[path])

    total_formatted, total_bytes = main._clean_with_log(mlog, {"User Temp": "User Temp", "System Temp": "System Temp"}, dry_run=False)

    assert total_bytes == 3072
    assert total_formatted == main.format_size(3072)
    assert [c[:3] for c in mlog.calls if c[0] == "finish"] == [
        ("finish", "clean:User Temp", "ok"), ("finish", "clean:System Temp", "ok")]


def test_driver_step_with_log_shows_notice_as_warning_line(monkeypatch):
    import main

    def fake_update(progress_callback=None, on_scan=None, dry_run=False, on_result=None, on_notice=None):
        on_scan(1)
        on_notice("a tela pode piscar")
        progress_callback("NVIDIA GeForce RTX 4070 → 617.42")
        on_result("NVIDIA GeForce RTX 4070 → 617.42", True, "instalado")
        return [("NVIDIA GeForce RTX 4070 → 617.42", True, "instalado")], False

    monkeypatch.setattr(main, "update_all_drivers", fake_update)
    mlog = _FakeLog()

    main._run_driver_step(main.parse_args(["menu"]), mlog=mlog)

    warn_keys = [c[1] for c in mlog.calls if c[0] == "finish" and c[2] == "warn"]
    assert len(warn_keys) == 1
    assert mlog.texts[warn_keys[0]] == "a tela pode piscar"
