# System Boost

A high-performance Windows CLI utility that cleans temporary files and applies reversible system tweaks, with a retro 8-bit terminal UI. No login, no account, no license checks, no telemetry. The network is only used for the optional driver step (see [Network and downloads](#network-and-downloads)).

## Features

- **Guided optimization levels** — `python main.py` with no arguments walks you through 4 escalating levels (Leve/Mediana/Alta/Extrema), each bundling temp cleanup with a matching set of reversible tweaks, with a summary + confirmation before anything runs.
- **Temp file cleanup** — User Temp, System Temp, Prefetch, SquirrelTemp, Gradle/Go/user caches, plus npm/uv cache clean and Recycle Bin (Stage 2 "Lista C"), with dry-run mode and per-folder selection.
- **Reversible Windows tweaks** — 12 built-in tweaks (power plan, hibernation, visual effects, telemetry, search indexing, SysMain, compatibility appraiser task, startup apps, third-party services and tasks, recommendations & offers, mouse acceleration). Every tweak reads and saves its current value before changing anything, and can be undone individually or all at once.
- **Machine spec sheet** — `python main.py info` (or option 5 in the guided menu) shows Windows version/build, CPU, installed RAM, GPU(s), system-disk type (SSD/HDD) and notebook vs desktop. Read-only, no Administrator needed; anything that can't be read shows as "desconhecido".
- **Rich terminal UI** — live mission log with one line per step, a status table for tweaks, clear success/error panels.

## Requirements

- Windows 10/11
- Python 3.11+ (or run the prebuilt `System Boost.exe` from `/dist`)

## Installation

### Para usar o programa

Baixe e execute `System Boost Setup.exe`. O instalador pede Administrador, instala em Program Files (removendo a cópia antiga por usuário, se houver), cria atalhos e registra o desinstalador. Python e dependências do projeto não são necessários na máquina de destino; eles já estão incorporados no executável. Ao iniciar o aplicativo, o Windows ainda solicitará elevação pelo UAC.

### Para gerar o instalador (Windows)

Instale o [Python 3.11 ou superior](https://www.python.org/downloads/windows/) e o [Inno Setup 6](https://jrsoftware.org/isinfo.php). Em seguida, na raiz do repositório, execute:

```bash
python installer.py
```

O script instala as dependências listadas em `requirements-build.txt`, executa o build existente do PyInstaller e gera `dist/System Boost Setup.exe` (além de `dist/System Boost.exe`). Para empacotar um executável já construído, use `python installer.py --skip-build`.

Se `ISCC.exe` não estiver no `PATH` nem no local padrão do Inno Setup, configure `INNO_SETUP_COMPILER` com o caminho completo do compilador, por exemplo:

```powershell
$env:INNO_SETUP_COMPILER = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
python installer.py
```

## Usage

### Guided flow (default)

```bash
python main.py          # welcome -> pick a level (1-4) -> confirm -> run -> completion
python main.py menu -y  # same flow, skips confirmations (scripted/unattended use)
```

Pick a level and the tool shows exactly what it's about to clean and which tweaks it'll apply *before* touching anything. Tweaks that need Administrator are shown as "pulados" (skipped) rather than failing the whole run when the terminal isn't elevated.

### Driver updates

`menu` and `clean` ask before the driver step, which installs pending updates from Windows Update and NVIDIA one by one (Administrator required). `--drivers` answers yes, `--no-drivers` skips it, and `-y` alone never installs drivers. `--dry-run` only lists them. A reboot may be needed afterwards. A restore point is created before a run changes anything; if Windows refuses, the run continues with a warning.

```bash
python main.py clean --dry-run -y   # list pending drivers, install nothing
python main.py menu --no-drivers    # guided flow without the driver step
python main.py clean -y --drivers   # unattended run that also installs drivers
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

Available `tweak_id`s: `power_plan`, `hibernation`, `visual_effects`, `telemetry`, `indexing`, `sysmain`, `compat_appraiser`, `startup_apps`, `third_party_services`, `third_party_tasks`, `recommendations_offers`, `mouse_acceleration`. Most require an elevated (Administrator) terminal — `apply`/`undo` fail with a clear message when not elevated rather than prompting for UAC.

Tweak state is stored locally at `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` — nothing leaves your machine.

## Building the executable

```bash
python build.py
# output: dist/System Boost.exe
```

`build.py` installs `requirements-build.txt`. If signing is configured and fails, the build exits with an error.

Para gerar também o instalador Windows, use `python installer.py` conforme as instruções acima.

The built exe **always asks for Administrator** (UAC prompt on every launch: the manifest is `requireAdministrator`), and carries `System Boost by Felipe Grolla` as its file description/company in Properties → Details. (`python main.py` from source is unaffected: run an elevated terminal yourself.)

**About the UAC "Publisher" line:** Windows only shows a verified publisher name when the exe is Authenticode-signed with a certificate issued to that name. Unsigned, UAC says "Publisher: Unknown" (yellow shield) no matter what the metadata says. If you have a code-signing certificate in your Windows cert store, set its SHA-1 thumbprint and `build.py` signs the exe automatically (needs `signtool` from the Windows SDK):

```powershell
$env:SYSTEM_BOOST_SIGN_THUMBPRINT = "<thumbprint>"
python build.py
```

## Project structure

- **`backend/`** — core logic, no UI: `cleaner.py`, `privileges.py`, `tweaks/` (the reversible-tweaks subsystem), `profiles.py` (the 4 guided-flow levels), `drivers.py` (Windows Update and NVIDIA driver updates), `nvidia_driver.py`, `restore_point.py`, `hardware.py` (machine spec sheet), `_powershell.py` (shared PowerShell runner), `_system.py` (absolute paths to Windows tools).
- **`frontend/`** — `rich`-based console UI: `cli.py` + `components/`.
- **`tests/`** — pytest suite. `pip install -r requirements-dev.txt`, then `pytest` and `ruff check .`.
- **`docs/funcionamento.md`** — full architecture walkthrough in Portuguese, with diagrams.

## Design principles

- No login, no account, no license checks, no telemetry sent out.
- Never touches game-specific folders.
- Every tweak is reversible. Deleted files and installed drivers are not: file cleanup can't be undone, and drivers rely on the restore point taken before a run.

## Network and downloads

Cleanup and tweaks work offline. Only the driver step, which needs your consent, uses the network: Windows Update through the Windows Update Agent, and NVIDIA's lookup service plus its official driver package (about 1 GB, checked for a valid NVIDIA signature before it runs).

## License

MIT — see [LICENSE](LICENSE).
