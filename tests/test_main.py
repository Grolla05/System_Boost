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
