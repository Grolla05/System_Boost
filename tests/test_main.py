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
