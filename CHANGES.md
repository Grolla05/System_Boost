# Changes

## Qualidade, CI e documentação

- Removidos `loading.py`, `retro_sprite.py`, `hardware_loading.py`, `typewriter.py` e o ramo de barra de progresso de drivers.
- `update_all_drivers`: um caminho só de instalação para Windows Update e NVIDIA.
- CI: `ruff`, cobertura, job de build do exe, `permissions: contents: read` e actions fixadas por SHA.
- `build.py`: falha de assinatura agora encerra com erro.
- Dependências separadas em `requirements.txt`, `requirements-dev.txt` e `requirements-build.txt`; `requires-python` alinhado em 3.11.
- Telas usam cores do tema, então `--palette` vale para todas.
- README e `docs/funcionamento.md` alinhados: 12 ajustes, downloads de drivers, limites da reversibilidade e nome System Boost.

## Bugs funcionais

- `third_party.py`: pasta do usuário fica fora do filtro (`hp` não casa `Hpereira`) e `intel` não casa `IntelliJ`.
- `services.py`: `delayed-auto` é lido do registro e restaurado no undo.
- `ScheduledTaskTweak`: `fallback_paths` cobre o nome da tarefa em outras builds; `compat_appraiser` aceita com e sem `Exp`.
- Stage 4 tem descrição; mensagens citam o exe quando empacotado (`cli_command()`).
- Mission log fica acima do resumo; briefing avisa sobre Prefetch.
- `find_product`: chassi define série de notebook, para GPUs sem "Laptop" no nome.

## Undo confiável

- `state_store.py`: arquivo danificado gera `StateCorruptError`, fica copiado em `.corrupt-*` e bloqueia escrita; cada save mantém `.bak`.
- `manager.py`: registro `pending` é gravado antes de `apply()`; queda mantém o ajuste listado para undo.
- `TweakPartialUndo`: tweaks agregados reportam o que não voltou, e só isso fica no estado.
- `undo_all` e `apply_level_tweaks` sobrevivem a erros inesperados por ajuste.

## Filtro de terceiros ampliado com prévia

- `third_party.py`: lista única para startup, serviços e tarefas. Volta a proteger VPN e soma bancos, EDR/antivírus, backup, licenciamento e updaters. `ANYWHERE_NAMES` casa `vpn`, `update` e `trendmicro` dentro da palavra. Reverte a decisão anterior de remover VPN e de manter serviços/tarefas com a lista menor.
- `profiles.preview_tweak_items()`: briefing lista cada item antes de agir (até 30).

## Consentimento e ponto de restauração

- `level_menu.py`: ESC/Q retorna `EXIT_CHOICE` e sai sem executar.
- `main.py`: só `--dry-run` pode omitir o subcomando; `clean` pede confirmação (Prefetch avisado ali, visível); drivers exigem `--drivers` ou sim na pergunta, e `-y` sozinho não instala.
- `backend/restore_point.py`: `Checkpoint-Computer` antes de stage e `clean`; falha vira aviso no mission log.

## Execução e instalação

- `backend/_system.py`: `system_exe()`/`powershell_exe()` resolvem ferramentas do Windows por caminho absoluto, usados em tweaks, PowerShell e tela.
- `drivers.py` reutiliza `run_powershell`.
- `installer.iss`: `PrivilegesRequired=admin`, `{autopf}` e remoção da instalação antiga.
- Logs do exe em `%LOCALAPPDATA%\\WinCleaner\\logs`.

## Limpeza mais estrita

- `backend/cleaner.py`: remoção não percorre links; `is_safe_clean_root()` recusa raízes sensíveis; `CLEAN_RULES` define idade mínima de 24 h em User/System Temp e preserva caches de modelos em `~/.cache`.
- npm e uv: cache limpo pela pasta, sem executar a ferramenta. Isso também corrige `npm` nunca encontrado no Windows.
- `disk_breakdown.py` reutiliza `get_dir_size`.

## Lixeira esvaziada já no Stage 1

- `backend/profiles.py`: `recycle-bin` passa de Mediana para Leve (Stage 2+ herdam). Ordem em Mediana: Lixeira, npm, uv.
- `frontend/components/level_menu.py`: briefing avisa que a Lixeira (todas as unidades) é esvaziada de vez, sem restauração.
- Testes e docs atualizados.

## Stage 2: "Lista C" de limpeza sem mover

- `backend/cleaner.py`: `get_temp_paths()` ganha `SquirrelTemp`, `Gradle Cache` (`~/.gradle/caches`), `Go Build Cache` e `User Cache` (`~/.cache`); `ADMIN_ONLY_PATHS` (System Temp, Prefetch) substitui a regra "só User Temp". Novo `COMMAND_CLEANUPS` + `run_command_cleanup()` para `npm cache clean --force`, `uv cache clean` e `Clear-RecycleBin` (pula se a ferramenta não existe; mede o ganho antes/depois; dry-run só mede).
- `backend/profiles.py`: níveis ganham `clean_commands`; Mediana inclui os itens acima e o ajuste `hibernation` (movido de Alta; Alta herda).
- `main.py`/`frontend`: `_clean_with_log(..., commands=)`, novos `--paths`, briefing lista caches/Lixeira e avisa que a hibernação off perde hibernação/inicialização rápida.
- Testes e docs atualizados.

## Blacklist ampliada para apps de inicialização

- `backend/tweaks/third_party.py`
  - Nova tupla `STARTUP_EXTRA_EXCEPTION_NAMES`: bancos de dados (mysql, postgres, mssql, mongod, redis, oracle, dbeaver, ...) e backup/cloud sync/senhas (dropbox, google drive, veeam, bitwarden, 1password, keepass, ...).
  - Helper `_compile(names)` constrói a regex de início de palavra; criadas `_EXCEPTION_RE` (base) e `_STARTUP_EXCEPTION_RE` (base + extras).
  - `is_third_party(..., *, startup=False)`: `startup=True` usa a lista ampliada. Padrão inalterado, então serviços e tarefas agendadas não mudam.
- `backend/tweaks/startup_apps.py`: `_candidates` chama `is_third_party(..., startup=True)`.
- Testes: `tests/test_tweaks/test_third_party.py` (proteção por categoria — bancos e backup/sync/senhas; a lista de web/dev infra e a de VPNs foram removidas por decisão do usuário, serviços/tarefas inalterados, apps comuns ainda desativados) e `tests/test_tweaks/test_startup_apps.py` (MySQL Workbench/Dropbox ignorados).
- `AGENTS.md`: documenta a lista extra de startup.
- `pytest`: 402 passed.

## Instalador: atalho na área de trabalho e abertura após instalar

- `installer.iss`
  - `[Icons]`: novo atalho `{autodesktop}\System Boost`, sempre criado (sem `[Tasks]` opcional).
  - `[Run]`: o app abre ao final da instalação pelo atalho da área de trabalho (`postinstall shellexec nowait skipifsilent`). O exe exige Administrador (`--uac-admin`) e o setup roda sem elevação (`PrivilegesRequired=lowest`); `CreateProcess` direto falharia com erro 740, e `shellexec` via `.lnk` dispara o UAC normalmente.
- `tests/test_installer.py`: testes do atalho de desktop e da execução pós-instalação pelo atalho.

## Atualização do driver NVIDIA junto com os drivers do Windows Update

- Novo `backend/nvidia_driver.py` (lógica pura, sem UI):
  - `get_nvidia_gpus()`: `Win32_VideoController` via PowerShell, só GPUs NVIDIA.
  - `windows_to_nvidia_version()` (`31.0.15.5123` → `551.23`) e `is_newer()`.
  - `find_product()`: resolve a GPU no catálogo público da NVIDIA (`lookupValueSearch.aspx`, séries desktop x "(Notebooks)"), sem tabela fixa.
  - `lookup_latest()`: `AjaxDriverService.php` com Game Ready, WHQL, DCH, Windows 10/11 64-bit.
  - `check_update()`: devolve `NvidiaUpdate` quando há versão mais nova; sem NVIDIA retorna `None`; falha de rede vira `NvidiaDriverError`.
  - `install_update()`: baixa o pacote oficial (~1 GB) para pasta temporária, aceita só `https` + `*.nvidia.com` + `.exe`, confere assinatura Authenticode ("NVIDIA Corporation") antes de executar, roda `-s -noreboot -noeula` (sem `-clean`, preserva configurações) e apaga o instalador no fim.
  - `FLICKER_WARNING`: aviso de que a tela pode piscar durante a instalação.
- `backend/drivers.py` `update_all_drivers`: após o Windows Update processa o driver NVIDIA com o mesmo contrato de callbacks e tuplas `(title, status, note)`. `on_scan` soma o item NVIDIA; `--dry-run` só lista; falha NVIDIA nunca aborta o resto; se o scan do Windows Update falhar, a NVIDIA ainda roda. Novo callback `on_notice(message)`, chamado com o aviso de tela piscando imediatamente antes do download/instalação.
- UI: `frontend/components/driver_progress.py` imprime o aviso acima da barra; `main.py` (`_update_drivers_logged`) mostra uma linha `[ !! ]` no log ao vivo (novo status `warn` em `live_log.py`).
- Testes: `tests/test_nvidia_driver.py`, `tests/test_driver_progress.py`, casos novos em `tests/test_drivers.py`, `tests/test_main.py`, `tests/test_live_log.py`. Rede e subprocess sempre mockados.
- Risco: a API da NVIDIA não é oficial e pode mudar; nesse caso o passo é pulado com mensagem, sem quebrar o restante.
- `pytest`: 441 passed.
