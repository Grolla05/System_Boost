# WinCleaner — System Boost

A high-performance Windows CLI utility that cleans temporary files and applies reversible system tweaks, with a sleek Apple-inspired terminal UI. Fully local: no login, no account, no license checks, no telemetry sent anywhere, no third-party downloads.

## Features

- **Guided optimization levels** — `python main.py` with no arguments walks you through 4 escalating levels (Leve/Mediana/Alta/Extrema), each bundling temp cleanup with a matching set of reversible tweaks, with a summary + confirmation before anything runs.
- **Temp file cleanup** — User Temp, System Temp, and Prefetch, with dry-run mode and per-folder selection.
- **Reversible Windows tweaks** — 7 built-in tweaks (power plan, hibernation, visual effects, telemetry, search indexing, SysMain, compatibility appraiser task). Every tweak reads and saves its current value before changing anything, and can be undone individually or all at once.
- **Machine spec sheet** — `python main.py info` (or option 5 in the guided menu) shows Windows version/build, CPU, installed RAM, GPU(s), system-disk type (SSD/HDD) and notebook vs desktop. Read-only, no Administrator needed; anything that can't be read shows as "desconhecido".
- **Rich terminal UI** — live progress bar during cleanup, a status table for tweaks, clear success/error panels.

## Requirements

- Windows 10/11
- Python 3.11+ (or run the prebuilt `System Boost.exe` from `/dist`)

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

### Driver updates

`menu` and `clean` finish with a driver step: the tool asks Windows Update for pending driver updates and installs them one by one (Administrator required; otherwise the step is skipped). `--dry-run` only lists them; pass `--no-drivers` to skip the step. A reboot may be needed afterwards, and creating a restore point first is recommended.

```bash
python main.py clean --dry-run -y   # list pending drivers, install nothing
python main.py menu --no-drivers    # guided flow without the driver step
```

### Machine spec sheet

```bash
python main.py info     # Windows, CPU, RAM, GPU, system disk (SSD/HDD), notebook/desktop
```

### Clean temp files directly

```bash
python main.py clean --dry-run                       # simulate, delete nothing
python main.py clean --paths "User Temp" "System Temp"
python main.py clean --yes --no-close                # unattended run, keep terminal open
```

Run the terminal as **Administrator** to also clean `C:\Windows\Temp` and `C:\Windows\Prefetch`.

### Reversible tweaks

From the guided menu, option **6 — Desfazer ajustes** lists every applied tweak, asks for confirmation and restores each original value. The same is available from the command line:

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
# output: dist/System Boost.exe
```

The built exe **always asks for Administrator** (UAC prompt on every launch: the manifest is `requireAdministrator`), and carries `System Boost by Felipe Grolla` as its file description/company in Properties → Details. (`python main.py` from source is unaffected: run an elevated terminal yourself.)

**About the UAC "Publisher" line:** Windows only shows a verified publisher name when the exe is Authenticode-signed with a certificate issued to that name. Unsigned, UAC says "Publisher: Unknown" (yellow shield) no matter what the metadata says. If you have a code-signing certificate in your Windows cert store, set its SHA-1 thumbprint and `build.py` signs the exe automatically (needs `signtool` from the Windows SDK):

```powershell
$env:SYSTEM_BOOST_SIGN_THUMBPRINT = "<thumbprint>"
python build.py
```

## Project structure

- **`backend/`** — core logic, no UI: `cleaner.py`, `privileges.py`, `tweaks/` (the reversible-tweaks subsystem), `profiles.py` (the 4 guided-flow levels), `drivers.py` (Windows Update driver scan/install), `hardware.py` (machine spec sheet), `_powershell.py` (shared PowerShell runner).
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
