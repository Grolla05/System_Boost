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

No test suite, linter, or formatter is configured in this repo.

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

WinCleaner is a Windows CLI utility that deletes temp files. Two layers, strictly separated:

- **`backend/`** — pure logic, no UI. `cleaner.py` does path discovery, size calculation, and deletion; `privileges.py` checks admin rights via `ctypes.windll.shell32.IsUserAnAdmin`.
- **`frontend/`** — `rich`-based console UI. `cli.py` wires a monochromatic + blue-accent `Theme` and exposes `show_welcome` / `show_loading` / `show_completion`, each delegating to a component in `frontend/components/` (`welcome.py`, `loading.py`, `completion.py`).

`main.py` is the only place these two layers meet: it calls `is_admin()` to decide which paths are in scope, then passes `backend` functions into `frontend.cli.show_loading` as callbacks so the progress bar updates as deletion actually happens.

Key behavioral rules baked into `backend/cleaner.py`:
- **Privilege-gated scope**: non-admin runs only clean `User Temp` (`%TEMP%`); admin runs also clean `C:\Windows\Temp` and `C:\Windows\Prefetch`. This gating happens in `main.py`, not in `cleaner.py` itself.
- **Silent skip on lock**: `PermissionError`/`OSError`/`FileNotFoundError` during delete are swallowed per-entry so one locked file never aborts the run.
- Progress is per-entry (`progress_callback(1)` per file/dir processed), not per-byte.

`frontend/components/completion.py` has a Windows-specific quirk worth knowing before touching it: after the user presses a key, it locates the console via `ctypes.windll.kernel32.GetConsoleWindow()` and posts `WM_CLOSE` via `user32.PostMessageW()` to auto-close the hosting terminal (PowerShell/CMD/Windows Terminal). This only works when a real console window handle exists.

`WinCleaner.spec` is the PyInstaller spec `build.py` invokes; `build/` and `dist/` are build artifacts, not source.

For a deeper (Portuguese) walkthrough with sequence diagrams, see [docs/funcionamento.md](docs/funcionamento.md).
