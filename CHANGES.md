# Changes

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
