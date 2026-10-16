from io import StringIO

from rich.console import Console

from frontend.cli import custom_theme
from frontend.components.live_log import MissionLog


def _console(height=40):
    return Console(file=StringIO(), width=100, height=height, force_terminal=False, theme=custom_theme)


def _render(mlog, console=None):
    console = console or _console()
    console.print(mlog.render(console.height))
    return console.file.getvalue()


def test_running_step_shows_running_tag():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.start("a", "Limpando User Temp")

    out = _render(mlog)

    assert "Limpando User Temp" in out
    assert "OK" not in out and "FAIL" not in out


def test_finish_ok_fail_skip_and_already_tags():
    mlog = MissionLog(_console(), "STAGE 1")
    for key, status, note in [("a", "ok", "312 MB"), ("b", "fail", "boom"), ("c", "skip", "requer administrador"), ("d", "already", "já aplicado")]:
        mlog.start(key, f"step {key}")
        mlog.finish(key, status, note)

    out = _render(mlog)

    assert "OK" in out and "312 MB" in out
    assert "FAIL" in out and "boom" in out
    assert "SKIP" in out and "requer administrador" in out
    assert "já aplicado" in out


def test_finish_updates_the_same_line_not_a_new_one():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.start("a", "Limpando")
    mlog.finish("a", "ok")

    assert len(mlog.lines) == 1
    assert mlog.lines[0].status == "ok"


def test_finish_unknown_key_creates_the_line():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.finish("x", "skip", "requer administrador", text="Telemetria")

    assert len(mlog.lines) == 1
    assert mlog.lines[0].text == "Telemetria"


def test_items_are_listed_one_per_line_indented_below_step():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.start("startup", "Apps de terceiros na inicialização")
    mlog.finish("startup", "ok", "2 item(ns)")
    mlog.item("Spotify")
    mlog.item("Opera GX Browser Assistant")

    out = _render(mlog)
    lines = [l for l in out.splitlines() if "Spotify" in l or "Opera GX" in l]

    assert len(lines) == 2
    assert all(l.lstrip(" │║").startswith(" ") or "└" in l or "↳" in l or "-" in l for l in lines)
    assert out.index("Apps de terceiros") < out.index("Spotify") < out.index("Opera GX")


def test_is_running_reflects_state():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.start("a", "x")
    assert mlog.is_running("a")
    mlog.finish("a", "ok")
    assert not mlog.is_running("a")
    assert not mlog.is_running("never")


def test_render_crops_to_last_lines_when_taller_than_screen():
    mlog = MissionLog(_console(height=12), "STAGE 1")
    for i in range(40):
        mlog.start(f"k{i}", f"passo-{i:02d}")
        mlog.finish(f"k{i}", "ok")

    out = _render(mlog, _console(height=12))

    assert "passo-39" in out
    assert "passo-00" not in out


def test_full_render_keeps_every_line():
    mlog = MissionLog(_console(height=12), "STAGE 1")
    for i in range(40):
        mlog.start(f"k{i}", f"passo-{i:02d}")
        mlog.finish(f"k{i}", "ok")

    console = _console(height=12)
    console.print(mlog.render(None))
    out = console.file.getvalue()

    assert "passo-00" in out and "passo-39" in out


def test_context_manager_prints_full_log_on_exit():
    console = _console(height=12)
    with MissionLog(console, "STAGE 1", keep=True) as mlog:
        for i in range(30):
            mlog.start(f"k{i}", f"passo-{i:02d}")
            mlog.finish(f"k{i}", "ok")

    out = console.file.getvalue()
    assert "passo-00" in out and "passo-29" in out


def test_context_manager_marks_unfinished_steps_as_fail_on_exception():
    console = _console()
    try:
        with MissionLog(console, "STAGE 1") as mlog:
            mlog.start("a", "Limpando")
            raise RuntimeError("quebrou")
    except RuntimeError:
        pass

    assert mlog.lines[0].status == "fail"


def test_log_is_not_reprinted_by_default_so_the_completion_screen_starts_clean():
    console = _console()
    with MissionLog(console, "STAGE 1") as mlog:
        mlog.start("a", "passo-unico")
        mlog.finish("a", "ok")

    assert "passo-unico" not in console.file.getvalue()


def test_panel_has_fixed_width_so_centering_does_not_jitter():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.start("a", "x")
    first = mlog.render(40).width
    for i in range(10):
        mlog.start(f"k{i}", "uma linha bem mais longa do que a primeira " * 1)
    assert mlog.render(40).width == first


def test_warn_status_renders_a_visible_tag_and_text():
    mlog = MissionLog(_console(), "STAGE 1")
    mlog.finish("n", "warn", text="a tela pode piscar durante a instalação")

    out = _render(mlog)

    assert "!!" in out and "a tela pode piscar" in out
