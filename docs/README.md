# WinCleaner - Minimalist System Purge

A high-performance Windows utility to clean temporary files, featuring a sleek Apple-inspired CLI.

## Project Structure

- **/backend**: Core logic for file deletion, size calculation, and privilege checking.
- **/frontend**: CLI implementation using the `rich` library for an elegant user experience.
- **/docs**: General documentation and architectural overview.
  - [Funcionamento Detalhado (Arquitetura)](funcionamento.md): Explicação completa da arquitetura, fluxo e funcionamento dos módulos.

## How to Use

1. **Direct Execution:** Run `python main.py` to start the cleanup.
2. **Administrator Mode:** Run the terminal as Administrator to enable cleaning of `C:\Windows\Temp` and `C:\Windows\Prefetch`.

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
