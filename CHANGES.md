# CHANGES.md

## 2026-07-29 — Hardening: dry-run, seleção de paths, fix de I/O, testes, CI

Baseado no plano de ação aprovado em `C:\Users\fegro\.claude\plans\claude-crie-um-plano-lovely-raven.md`. Objetivo: tornar o WinCleaner mais seguro de usar (não-destrutivo por padrão em modo dry-run), testável e com build reprodutível.

### 1. CLI flags + dry-run + seleção de paths (`main.py`, `backend/cleaner.py`, `frontend/cli.py`, `frontend/components/{welcome,loading,completion}.py`)

- `main.py` ganhou `argparse` com 4 flags:
  - `-n` / `--dry-run`: simula a limpeza, não apaga nada, só reporta o que seria liberado.
  - `--paths {User Temp,System Temp,Prefetch}` (`nargs="+"`): restringe a limpeza a um subconjunto das pastas (valida via `choices`, rejeita nomes inválidos com erro claro e exit code 2).
  - `-y` / `--yes`: pula a tela de boas-vindas (keypress) e a tela final (keypress), permitindo uso automatizado/scriptado.
  - `--no-close`: desativa o fechamento automático do terminal ao final.
- `backend/cleaner.py`: `clean_directory()` ganhou parâmetro `dry_run=False`. Quando ativo, os tamanhos ainda são calculados (via `entry.stat().st_size` / `get_dir_size`) mas nenhum `os.remove`/delete acontece.
- `paths_to_clean` em `main.py` agora é filtrado tanto pelo status de admin (lógica original) quanto por `--paths` (interseção).
- `frontend/components/welcome.py`: `display_welcome_screen()` ganhou `skip_wait`, pulando a espera de tecla quando `--yes`.
- `frontend/components/loading.py`: `run_cleanup_with_loading()` propaga `dry_run` para `clean_func` e troca o texto da barra de progresso ("Analisando arquivos (dry-run)..." vs "Limpando arquivos desnecessários...").
- `frontend/components/completion.py`: `display_completion_screen()` ganhou `dry_run` (troca título/texto: "SIMULAÇÃO CONCLUÍDA" / "seriam limpos" vs "LIMPEZA CONCLUÍDA" / "foram limpos") e `skip_wait` (sai imediatamente sem esperar tecla quando `--yes`).

### 2. Aviso de limpeza do Prefetch (`main.py`)

Quando `"Prefetch" in paths_to_clean` (só ocorre em execução como admin) e `--yes` não foi passado, imprime aviso via `console` (já exposto em `frontend/cli.py`) antes de iniciar a limpeza, alertando que o Windows recria o Prefetch automaticamente mas isso pode afetar o próximo boot.

### 3. Fix de double directory walk (`backend/cleaner.py`)

Antes: para cada subpasta, `get_dir_size()` percorria a árvore inteira pra somar tamanho e depois `shutil.rmtree()` percorria de novo pra apagar — 2x I/O e risco de mismatch se arquivos mudassem entre as duas passadas.

Agora: nova função `_remove_and_measure()` faz a travessia recursiva em passada única, apagando arquivo por arquivo e somando o tamanho ao mesmo tempo, depois remove o diretório vazio com `os.rmdir()`. Import de `shutil` removido (não é mais usado). `get_dir_size()` foi mantida intacta pois ainda é usada no caminho de `dry_run`.

### 4. Suíte de testes pytest (`tests/`)

Novos arquivos: `tests/__init__.py`, `tests/test_cleaner.py`, `tests/test_privileges.py`.

Usa exclusivamente a fixture `tmp_path` do pytest — nenhum teste toca pastas reais do Windows. Cobertura:
- `get_dir_size`: soma flat e aninhada, path inexistente retorna 0.
- `clean_directory`: deleta e reporta tamanho corretamente, modo dry-run não apaga nada, path inexistente retorna 0, `PermissionError` num arquivo não aborta o resto (via `monkeypatch` em `os.remove`), `progress_callback` é chamado uma vez por entrada de topo.
- `format_size`: tabela de casos (0 B, 1023 B, 1 KB, 1.5 KB, 1 GB).
- `get_temp_paths`: filtra corretamente paths inexistentes (via `monkeypatch`).
- `is_admin` (`backend/privileges.py`): os dois branches da API do Windows (`IsUserAnAdmin` retornando 1/0) via `types.SimpleNamespace` fake de `ctypes.windll`, e o fallback para `os.getuid()` quando `windll` não existe.

**13 testes, todos passando** (`pytest -v` → `13 passed`).

### 5. Pin de versões (`requirements.txt`, `requirements-dev.txt` novo)

`requirements.txt` antes tinha `rich` e `pyinstaller` sem versão (build não-reprodutível). Verificado via `pip show` as versões instaladas no ambiente de dev e pinado com `~=` (compatible-release, permite patch mas trava major):
```
rich~=15.0
pyinstaller~=6.20
```
Novo `requirements-dev.txt` inclui `-r requirements.txt` + `pytest~=8.4`, mantendo o `requirements.txt` de runtime limpo para o build do PyInstaller (não precisa empacotar pytest no `.exe`).

### 6. LICENSE (MIT), pyproject.toml, CI (GitHub Actions)

- `LICENSE`: texto padrão MIT, copyright `Grolla05`, ano 2026 (confirmado com o usuário via pergunta em plan mode).
- `pyproject.toml`: `[project]` mínimo (name, version, description, requires-python, license) + `[tool.pytest.ini_options]` com `testpaths = ["tests"]` (substitui a necessidade de um `pytest.ini` separado). Não interfere no fluxo `build.py`/PyInstaller existente.
- `.github/workflows/ci.yml`: workflow roda em `windows-latest` (obrigatório — `ctypes.windll` e `msvcrt` são Windows-only), em todo push/PR: instala `requirements-dev.txt` e roda `pytest -v`. Escopo intencionalmente limitado a testes; build/release automatizado do `.exe` fica fora deste escopo (usuário pode pedir depois se quiser releases automáticos).

### 7. Opt-out do force-close do terminal (`frontend/components/completion.py`)

Ver item 1 acima — `close_terminal=True` por padrão (comportamento inalterado sem flags), controlável via `--no-close`. Auto-desativado quando `--dry-run` ou `--yes` são usados, para não matar o terminal do host (ex: terminal integrado de IDE) em uso scriptado/automatizado.

### 8. Fix de link morto (`docs/README.md`)

Link absoluto `file:///d:/GitHub/Limpeza_TEMP/docs/funcionamento.md` (apontava pro nome antigo do repositório) trocado por link relativo `funcionamento.md` — sobrevive a clone em outra máquina ou rename futuro do repo. Também removida uma linha em branco duplicada adjacente (lint MD012).

### Verificação executada

- `python main.py --help` — todas as flags listadas corretamente.
- `python main.py --dry-run --yes --paths "User Temp"` — roda sem travar em keypress, mostra "SIMULAÇÃO CONCLUÍDA" com tamanho correto, exit code 0, nenhum arquivo real apagado.
- `python main.py --paths BadName` — argparse rejeita com erro claro, exit code 2.
- `pytest -v` — 13/13 testes passando.
- `pip install -r requirements.txt` — resolve normalmente com as versões pinadas.

### Pendências / próximos passos sugeridos (fora do escopo deste commit)

- Release automatizado do `.exe` via CI (build+publish job) — não implementado, opcional.
- Testes de UI (`frontend/components/*`) — deliberadamente fora de escopo (mocking de keypress/console/WM_CLOSE não compensa para utilitário single-maintainer).
