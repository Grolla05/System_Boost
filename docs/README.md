# WinCleaner - Minimalist System Purge

A high-performance Windows utility to clean temporary files and apply reversible system tweaks, featuring a sleek Apple-inspired CLI.

## Project Structure

- **/backend**: Core logic for file deletion, size calculation, privilege checking, and reversible tweaks (`backend/tweaks/`).
- **/frontend**: CLI implementation using the `rich` library for an elegant user experience.
- **/docs**: General documentation and architectural overview.
  - [Funcionamento Detalhado (Arquitetura)](funcionamento.md): Explicação completa da arquitetura, fluxo e funcionamento dos módulos, incluindo o subsistema de ajustes reversíveis.

## How to Use

1. **Guided flow (default):** Run `python main.py` with no arguments to walk through welcome → level menu (Leve/Mediana/Alta/Extrema) → confirmation → execution → completion.
2. **Direct cleanup:** Run `python main.py clean` for the old direct behavior (no menu).
3. **Administrator Mode:** Run the terminal as Administrator to enable cleaning of `C:\Windows\Temp` and `C:\Windows\Prefetch`, and to apply admin-required tweaks.
4. **Reversible tweaks (granular):**
   - `python main.py list` — shows all available tweaks and their current/applied state.
   - `python main.py apply <tweak_id>` — applies a tweak, saving its previous value.
   - `python main.py undo <tweak_id>` — restores a single tweak's previous value.
   - `python main.py undo --all` — restores every applied tweak.

## Building the Executable

To generate a standalone `.exe`:

1. Install requirements: `pip install -r requirements.txt`
2. Run the build script: `python build.py`
3. Find your executable in the `/dist` folder.

## Features

- **Safe Deletion:** Automatically skips files currently in use by other applications.
- **Progress Tracking:** Real-time feedback on cleaning status.
- **Monochromatic UI:** Clean, distraction-free interface with clear typography.
- **Lightweight:** Minimal resource usage during execution.
