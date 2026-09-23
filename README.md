# WinCleaner — System Boost

A high-performance Windows CLI utility that cleans temporary files and applies reversible system tweaks, with a sleek Apple-inspired terminal UI. Fully local: no login, no account, no license checks, no telemetry sent anywhere, no third-party downloads.

## Features

- **Guided optimization levels** — `python main.py` with no arguments walks you through 4 escalating levels (Leve/Mediana/Alta/Extrema), each bundling temp cleanup with a matching set of reversible tweaks, with a summary + confirmation before anything runs.
- **Temp file cleanup** — User Temp, System Temp, and Prefetch, with dry-run mode and per-folder selection.
- **Reversible Windows tweaks** — 7 built-in tweaks (power plan, hibernation, visual effects, telemetry, search indexing, SysMain, compatibility appraiser task). Every tweak reads and saves its current value before changing anything, and can be undone individually or all at once.
- **Rich terminal UI** — live progress bar during cleanup, a status table for tweaks, clear success/error panels.

## Requirements

- Windows 10/11
- Python 3.11+ (or run the prebuilt `WinCleaner.exe` from `/dist`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Guided flow (default)

```bash
python main.py          # welcome -> pick a level (1-4) -> confirm -> run -> completion
python main.py menu -y  # same flow, skips confirmations (scripted/unattended use)
```

Pick a level and the tool shows exactly what it's about to clean and which tweaks it'll apply *before* touching anything. Tweaks that need Administrator are shown as "pulados" (skipped) rather than failing the whole run when the terminal isn't elevated.

### Clean temp files directly

```bash
python main.py clean --dry-run                       # simulate, delete nothing
python main.py clean --paths "User Temp" "System Temp"
python main.py clean --yes --no-close                # unattended run, keep terminal open
```

Run the terminal as **Administrator** to also clean `C:\Windows\Temp` and `C:\Windows\Prefetch`.

### Reversible tweaks

```bash
python main.py list                # show all tweaks + current/applied state
python main.py apply <tweak_id>     # apply a tweak, saving its previous value
python main.py undo <tweak_id>      # restore that tweak's previous value
python main.py undo --all           # restore every applied tweak
```

Available `tweak_id`s: `power_plan`, `hibernation`, `visual_effects`, `telemetry`, `indexing`, `sysmain`, `compat_appraiser`. Most require an elevated (Administrator) terminal — `apply`/`undo` fail with a clear message when not elevated rather than prompting for UAC.

Tweak state is stored locally at `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` — nothing leaves your machine.

## Building the executable

```bash
pip install -r requirements.txt
python build.py
# output: dist/WinCleaner.exe
```

## Project structure

- **`backend/`** — core logic, no UI: `cleaner.py`, `privileges.py`, `tweaks/` (the reversible-tweaks subsystem), `profiles.py` (the 4 guided-flow levels).
- **`frontend/`** — `rich`-based console UI: `cli.py` + `components/`.
- **`tests/`** — pytest suite (`pytest -v`).
- **`docs/funcionamento.md`** — full architecture walkthrough in Portuguese, with diagrams.

## Design principles

- 100% local — no login, no account, no license checks, no telemetry sent out, no online verification.
- No downloads of drivers, executables, or third-party packages.
- Never touches game-specific folders.
- Every system change this tool makes is reversible.

## License

MIT — see [LICENSE](LICENSE).
