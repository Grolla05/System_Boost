# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install deps
pip install -r requirements.txt

# Run app directly
python main.py

# Build standalone .exe (PyInstaller, one-file, console)
python build.py
# output: /dist/WinCleaner.exe
```

```bash
# Run tests
pytest -v
```

Test suite (`pytest`) is configured via `pyproject.toml` (`testpaths = ["tests"]`). No linter or formatter is configured in this repo.

---

## Workflow obrigatório de funcionamento

1 -> A partir do prompt gere os testes para verificação da feature antes mesmo de começar a desenvolver, todos os testes unitários tem que ser criados dentro da pasta tests na raiz do projeto, caso a pasta não exista crie ela na raiz do repositório.
2 -> Com os testes escritos explore as opções e caminhos nos quais podem ser seguidos para o desenvolvimento
3 -> Escreva o plano de ação para implementar a feature
4 -> Desenvolva o plano proposto, dividindo a atividade do plano em task's
5 -> Após o desenvolvimento execute os testes escritos no passo 1, para validar oque foi gerado, se não passar em algum teste, identifique oque deu problema e conserte e rode o teste novamente
6 -> Após ter ocorrido tudo corretamente por favor crie, edite caso já exista, o arquivo CHANGES.md na raiz do projeto, no qual este por sua vez deve documentar tudo nos mínimos detalhes do que foi feito
7 -> Após ter ter documentado tudo no CHANGES.md prepare para gerar o commit, baseado nas alterações documentadas no CHANGES.md, ou seja deve ser feito baseado neste arquivo o commit mensage, mas espere a validação e comando do usuário
8 -> Com a validação do usuário siga o processo de commit -> push (sync changes) -> Pull Request. Não é necessário abrir uma branch nova para cada feature, apenas utilize a branch Grolla para realizar este processo

---

## Architecture

WinCleaner ("System Boost") is a Windows CLI utility for temp-file cleanup and reversible system tweaks. `main.py` uses `argparse` with subcommands (`menu`, `clean`, `list`, `apply`, `undo`); **bare `python main.py` with zero arguments now launches `menu`** (the guided level-menu flow), while bare *flags* with no subcommand keyword (e.g. `--dry-run -y`) still imply `clean` for back-compat. Two logic layers, strictly separated:

- **`backend/`** — pure logic, no UI. `cleaner.py` does path discovery, size calculation, and deletion; `privileges.py` checks admin rights via `ctypes.windll.shell32.IsUserAnAdmin`; `tweaks/` is the reversible-tweaks subsystem (see below); `profiles.py` bundles cleanup + tweaks into the 4 guided-flow levels (see below).
- **`frontend/`** — `rich`-based console UI. `cli.py` wires a monochromatic + blue-accent `Theme` and exposes `show_welcome` / `show_loading` / `show_completion` / `show_tweak_list` / `show_tweak_success` / `show_tweak_error` / `show_undo_all_results` / `show_level_menu` / `show_level_summary` / `show_level_completion`, each delegating to a component in `frontend/components/`.

`main.py` is the only place these two layers meet: each `cmd_*` function calls `backend` functions and passes results (or callbacks, for `clean`) into the matching `frontend.cli.show_*` function.

Key behavioral rules baked into `backend/cleaner.py`:
- **Privilege-gated scope**: non-admin runs only clean `User Temp` (`%TEMP%`); admin runs also clean `C:\Windows\Temp` and `C:\Windows\Prefetch`. This gating happens in `main.py`, not in `cleaner.py` itself.
- **Silent skip on lock**: `PermissionError`/`OSError`/`FileNotFoundError` during delete are swallowed per-entry so one locked file never aborts the run.
- Progress is per-entry (`progress_callback(1)` per file/dir processed), not per-byte.

The keypress-wait + `WM_CLOSE` terminal-auto-close dance (after a keypress, locate the console via `ctypes.windll.kernel32.GetConsoleWindow()` and post `WM_CLOSE` via `user32.PostMessageW()`) lives in `frontend/components/_terminal.py`'s `wait_for_keypress_and_maybe_close()`, shared by `completion.py` (`clean`) and `level_completion.py` (`menu`) — both are "run and done" double-click-style screens. `list`/`apply`/`undo` deliberately don't use it; their components just `console.print(...)` and return, since they're meant to be run in sequence from an already-open terminal. This only works when a real console window handle exists.

### `backend/profiles.py` — guided-flow optimization levels

`menu` (the new default when `main.py` is run with no arguments) bundles cleanup + tweaks into 4 escalating levels — `leve` → `mediana` → `alta` → `extrema` — defined declaratively in `profiles.LEVELS`. `resolve_clean_paths()` reuses `cleaner.get_temp_paths()` with the same admin-filter shape `cmd_clean` already had; `resolve_tweak_plan()`/`apply_level_tweaks()` reuse `tweaks.manager.apply_tweak()` per id, catching `TweakError` per-tweak so one admin-required tweak being unavailable (not elevated) or already-applied never aborts the rest of the level — it's recorded as skipped/failed and shown on the completion screen, same graceful-degradation spirit as `cmd_clean`'s path filtering. This module is intentionally separate from `backend/tweaks/` (which stays scoped to the tweak abstraction itself) since it's cross-cutting orchestration over both `cleaner` and `tweaks`.

`frontend/components/level_menu.py` reads the level choice via `rich.prompt.IntPrompt` and the run/skip confirmation via `rich.prompt.Confirm` — both stdlib-adjacent (already part of the `rich` dependency, no new installs), and both read from real stdin so they don't share `_terminal.py`'s `msvcrt.getch()` console-only limitation. Note for testing: `IntPrompt`/`Confirm` work fine when stdin is piped (e.g. `subprocess.run(..., input=b"1\n")`), but `msvcrt.getch()` (used by `show_welcome`/`show_completion`/`show_level_completion` when `skip_wait=False`) reads directly from the console and hangs forever on piped/redirected stdin — any scripted smoke test of the guided flow needs `-y` (which sets `skip_wait=True` throughout) to avoid hanging on those screens.

### `backend/tweaks/` — reversible tweaks subsystem

Each tweak is an `abc.ABC` subclass (`base.Tweak`) implementing `get_current_value()` / `apply()` / `undo(previous_value)` — the one deliberate, scoped exception to the rest of the backend's function-only style, because 7 heterogeneous mechanisms need real polymorphism and a missing method should fail loudly at class-definition time, not silently at undo time. Mechanism classes are split by *how* they talk to Windows, not one-per-tweak: `registry_value.py` (`RegistryValueTweak`, generic DWORD read/write) backs both `visual_effects` and `telemetry`; `services.py` (`ServiceStateTweak`, `sc.exe` + registry read) backs both `indexing` (WSearch) and `sysmain` (SysMain); `scheduled_tasks.py` (`ScheduledTaskTweak`, `schtasks.exe`) backs `compat_appraiser`; `power_plan.py`/`hibernation.py` are each one-off despite both shelling to `powercfg.exe`, since their read/write semantics differ. `catalog.py` instantiates all 7 by id; `state_store.py` persists applied state as JSON; `manager.py` coordinates admin checks, catalog lookup, and state read/write for `apply_tweak`/`undo_tweak`/`undo_all`/`list_status`.

Two decisions worth knowing before touching this code:
- **Reads go through `winreg`, not by parsing `.exe` stdout.** `sc.exe`/`schtasks.exe`/`powercfg.exe` stdout is localized to the OS display language (this repo's own UI is pt-BR) — regexing English labels would silently break. Writes still use the `.exe`s since their command-line switches are fixed keywords. One caveat found the hard way: `schtasks /XML` declares `encoding="UTF-16"` in its prolog, but bytes captured through a redirected pipe are actually UTF-8 — `scheduled_tasks.py` decodes as UTF-8 itself before handing text (not bytes) to `ElementTree`, since `ET.fromstring` on bytes trusts a declaration that doesn't match reality here.
- **Admin-required tweaks hard-fail, they don't self-elevate.** `manager.py` checks `is_admin()` and raises `TweakError` with a clear message ("reabra como Administrador") rather than attempting a UAC relaunch — keeps `--yes`/scripted use possible and avoids a surprise elevation prompt from a tool with no login/account/telemetry ethos.

State persists at `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` (JSON, atomic write via temp-file + `os.replace`), one record per tweak id keyed by id — re-applying an already-applied id is rejected, not overwritten, so a double-apply can't destroy the true original value. `previous_value: null` is meaningful (the value didn't exist before); `undo()` deletes the registry value in that case rather than writing `null`.

`WinCleaner.spec` is the PyInstaller spec `build.py` invokes; `build/` and `dist/` are build artifacts, not source.

For a deeper (Portuguese) walkthrough with sequence diagrams, see [docs/funcionamento.md](docs/funcionamento.md).

## Roadmap (future items, not yet built)

The "System Boost" evolution has 6 more planned items beyond the reversible-tweaks system above. No stub files exist for these yet — each gets its module the day it's actually built:

| Item | Future module | Responsibility |
|---|---|---|
| ~~1-click quick profile~~ | superseded by `backend/profiles.py` | Done — 4 levels (leve/mediana/alta/extrema) via the `menu` guided flow, not a single hardcoded bundle |
| Live resource monitor | `backend/monitor.py`, `frontend/components/monitor_dashboard.py` | `psutil` sampling + `rich` Live dashboard (CPU/RAM/disk/network) |
| Disk cleanup evolution | `backend/disk_report.py` | Before/after diff over a `cleaner.get_temp_paths()`-style categorized dict |
| Driver inventory | `backend/drivers.py` | `pnputil`/`wmic` subprocess inventory, export-only, no downloads |
| Debloat/startup manager | `backend/startup.py` | Run/RunOnce + Startup folder enumeration via `winreg`/`os.scandir` |
| Hardware detection | `backend/hardware.py` | Notebook/desktop, SSD/HDD, RAM — feeds a future `Tweak.applicable(hw)` filter |

`main.py` stays the single wiring point for CLI dispatch until it crosses roughly 5-6 `cmd_*` functions with nontrivial per-command glue — past that point, split into a `cli/` package (`cli/clean.py`, `cli/tweaks.py`, `cli/__init__.py` with `main()`), keeping "backend has zero UI imports, frontend has zero business logic" intact.
