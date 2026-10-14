# CHANGES

## Stages renomeados e cumulativos + gerenciador de itens de terceiros no Stage 1

### Nomes do menu (`frontend/components/level_menu.py`)
- `STAGE 1: LEVE (NORMAL)`, `STAGE 2: MEDIANA (BOOST)`, `STAGE 3: ALTA (TURBO BOOST)`, `STAGE 4: EXTREMA (HYPER DRIVE)`.
- Briefing da missão (`display_level_summary`) ganhou a linha "Preservados: itens do Windows, antivírus, drivers, VPN e OneDrive." quando o stage inclui algum dos novos ajustes de terceiros.

### Stages cumulativos (`backend/profiles.py`)
- Novo helper `_extend(previous_id, ...)`: cada stage = stage anterior + extras (união sem repetir, ordem do anterior preservada). `LEVELS` deixou de repetir tuplas à mão.
- Descrições no formato `STAGE N + [extras]` (Mediana: "STAGE 1 + ...", Alta: "STAGE 2 + ...", Extrema: "STAGE 3 + ...").
- Stage 1 agora: limpa `User Temp`, `visual_effects`, `startup_apps`, `third_party_services`, `third_party_tasks`.

### Novos ajustes reversíveis (`backend/tweaks/`)
Cada um é um tweak agregado por categoria: `previous_value` guarda a lista (JSON) de itens alterados, então `manager`, `state_store`, `undo_all` e o menu "Desfazer ajustes" funcionam sem mudanças.
- `third_party.py` — filtro compartilhado `is_third_party(name, command, display)`. Nunca toca: itens sob `%SystemRoot%` ou qualquer pasta `Microsoft*`, comando vazio/desconhecido, e a lista `EXCEPTION_NAMES` (antivírus, drivers/periféricos, VPN, OneDrive, virtualização/WSL, nomes Microsoft/Windows). Nomes só casam no início de palavra (`amd` protege `amdrsserv`, não `ramdisk`).
- `startup_apps.py` (`startup_apps`, sem admin; escopos HKLM só quando elevado) — Run (HKCU, HKLM, WOW6432Node) e pastas Startup (usuário/todos). Desativa pelo `StartupApproved` (mesmo mecanismo da aba Inicializar do Gerenciador de Tarefas): não apaga nada; undo restaura os bytes originais ou remove o registro. Atalhos de pasta são classificados pelo nome do arquivo (alvo do .lnk não é resolvido).
- `third_party_services.py` (`third_party_services`, admin) — serviços Win32 (tipo 0x10/0x20) com Start=auto e fora do Windows/Microsoft. Aplica `sc config start= demand` + `sc stop` (manual, não disabled, para o app ainda poder iniciar o serviço). Undo restaura `auto`/`delayed-auto` e dá `sc start`.
- `third_party_tasks.py` (`third_party_tasks`, admin) — tarefas fora de `\Microsoft\` e não desativadas, listadas via PowerShell (`Get-ScheduledTask`, JSON). Desativa com `schtasks /Change /Disable`; undo reativa só as que foram desativadas.
- Falha em um item é registrada em log e ignorada; os demais continuam.
- `catalog.py`: 7 → 10 tweaks.
- `frontend/components/tweak_list.py`: valor atual em lista aparece como "N item(ns)".

### Testes
- Novos: `tests/test_tweaks/test_third_party.py`, `test_startup_apps.py`, `test_third_party_services.py`, `test_third_party_tasks.py`.
- Atualizados: `tests/test_profiles.py` (stages cumulativos, novos ids no Stage 1, descrições), `tests/test_tweaks/test_catalog.py` (10 tweaks).
- `pytest -v`: 319 passed (CI `.github/workflows/ci.yml` roda apenas `pytest -v`).
- Descoberta validada em leitura real na máquina de desenvolvimento (nenhuma alteração aplicada).

### Observações
- Tarefas de atualizadores de terceiros (ex.: Google Updater, Opera Autoupdate) são desativadas no Stage 1; reversível pelo menu "Desfazer ajustes".
- Sem Administrador, `third_party_services` e `third_party_tasks` aparecem como "requer administrador" e `startup_apps` só altera itens do usuário.

## Tela de log ao vivo (MISSION LOG)

- Novo `frontend/components/live_log.py` (`MissionLog`): painel com uma linha por etapa: `[ .. ]` em andamento (spinner), `[ OK ]`, `[FAIL]` (com motivo) e `[SKIP]` (ex.: requer administrador). "Já aplicado" aparece como `[ OK ]` com a nota. Itens de terceiros afetados saem **uma linha por item** (`└ Spotify`).
- Enquanto roda, usa `rich.Live` mostrando só as últimas linhas que cabem na tela; a tela é limpa antes de começar e o painel fica centralizado (largura fixa); ao terminar o log é apagado (`keep=True` imprime o log completo) e a tela de conclusão aparece limpa e centralizada, como antes. Se o bloco `with` sair por exceção, etapas em andamento viram `[FAIL] interrompido`.
- `backend/profiles.apply_level_tweaks(..., on_event=None)`: emite `running`, o status final e um evento `item` por item alterado pelos ajustes agregados (resumo "N item(ns)" ou "nenhum item de terceiros"). Sem `on_event` o comportamento e o retorno são os mesmos.
- `backend/drivers.update_all_drivers(..., on_result=None)`: avisa o resultado de cada driver logo após a instalação.
- `main.py`: `_clean_with_log` (uma linha por pasta), `_tweak_event_handler`, `_update_drivers_logged`; `_run_driver_step(..., mlog=None)` (sem `mlog` mantém a barra de progresso antiga). `menu` e `clean` usam o log; `show_loading` deixou de ser usado por eles.
- `show_completion` / `show_level_completion` ganharam o parâmetro `clear=True` (padrão: limpa a tela e centraliza, como sempre); `menu` e `clean` usam o padrão.
- Testes: `tests/test_live_log.py` (novo), mais casos em `test_profiles.py`, `test_drivers.py` e `test_main.py`. `pytest -v`: 346 passed.
- Limitação: o estado dos ajustes agregados é gravado como "aplicado"; rodar o Stage 1 de novo antes de desfazer mostra "já aplicado" e não pega apps de terceiros instalados depois.

## Temas removidos

- Paletas `Phosphor Amber CRT` (`amber`) e `Matrix Terminal` (`matrix`) removidas de `frontend/palettes.py` (restam `dmg`, `pocket`, `arcade`); `-p/--palette` aceita só essas três. Config salva com paleta removida volta para `dmg`.
- Testes: `tests/test_palettes.py` e `tests/test_main.py` atualizados.

## Stage 2 (MEDIANA): recomendações e ofertas do Windows desligadas

- Novo tweak `recommendations_offers` (`backend/tweaks/recommendations_offers.py`, HKCU, sem admin, reversível): desliga os switches de Configurações > Privacidade e segurança > Recomendações e ofertas — Personalized offers (`TailoredExperiencesWithDiagnosticDataEnabled=0`), Allow websites to access my language list (`HttpAcceptLanguageOptOut=1`), Improve Start and search results (`Start_TrackProgs=0`), Show notifications in Settings (`SystemSettings\AccountNotifications\EnableAccountNotifications=0`, `SubscribedContent-338389Enabled=0` sozinho não desligava o switch na tela), Recommendations and offers in Settings (`SubscribedContent-338393/353694/353696Enabled=0`) e Advertising ID (`AdvertisingInfo\Enabled=0`).
- `apply()` devolve um item por switch que de fato mudou (o log mostra uma linha por switch; Advertising ID já desligado não aparece). `previous_value` guarda valor anterior de cada DWORD; undo restaura ou apaga o que não existia. Falha em um valor não aborta os outros.
- Stage 2 = Stage 1 + limpeza de System Temp + `power_plan` (Alto Desempenho, já existente, `powercfg /setactive`, persistente) + `recommendations_offers`. Descrição do menu atualizada. Catálogo: 10 → 11 tweaks.
- O Windows pode mudar entre builds qual chave controla "Show notifications in Settings" / "Recommendations and offers in Settings"; por isso todos os candidatos conhecidos são gravados. A tela de Configurações só reflete a mudança depois de fechar e reabrir o app.
- Testes: `tests/test_tweaks/test_recommendations_offers.py` (novo), `test_catalog.py` (11) e `test_profiles.py` (Stage 2 ⊃ Stage 1). `pytest -v`: 354 passed.

## Stage 2 (MEDIANA): "Enhance pointer precision" desativado

- Novo tweak `mouse_acceleration` (`backend/tweaks/mouse_acceleration.py`, HKCU, sem admin, reversível). É a mesma configuração do toggle em Configurações > Bluetooth e dispositivos > Mouse e do checkbox do diálogo clássico (Propriedades do Mouse > Opções do ponteiro).
- Grava `"0"` (REG_SZ, não DWORD) em `HKCU\Control Panel\Mouse`: `MouseSpeed`, `MouseThreshold1`, `MouseThreshold2` (padrão do Windows: `"1"`/`"6"`/`"10"`). A velocidade do ponteiro (`MouseSensitivity`) não é alterada.
- Efeito imediato, sem relogar: `user32.SystemParametersInfoW(SPI_SETMOUSE, ...)` com `{0,0,0}` (`SPIF_UPDATEINIFILE | SPIF_SENDCHANGE`). Falha nessa chamada só vai para o log (o registro já foi gravado e vale no próximo login).
- `apply()` devolve `[{"name": "Enhance pointer precision"}]` se estava ligado e `[]` se já estava desligado (log mostra "nenhum item"). `previous_value` = `{nome: string|None}`; `undo()` restaura (apaga o que não existia) e reenvia o `SPI_SETMOUSE` com os valores originais.
- `profiles.py`: Stage 2 = Stage 1 + System Temp + `power_plan` + `recommendations_offers` + `mouse_acceleration` (Stages 3 e 4 herdam). Descrição do menu atualizada. Catálogo: 11 → 12 tweaks. `CLAUDE.md` atualizado.
- Testes: `tests/test_tweaks/test_mouse_acceleration.py` (novo), `conftest.py` (`FakeWinReg.REG_SZ`), `test_catalog.py` (12) e `test_profiles.py` (Stage 2 inclui `mouse_acceleration`). `pytest -v`: 361 passed.

## Efeitos visuais movidos do Stage 1 para o Stage 3 (ALTA)

- `backend/profiles.py`: `visual_effects` saiu de `leve` e entrou em `alta` (primeiro extra do Stage 3; Stage 4 herda). Stage 1 agora: `startup_apps`, `third_party_services`, `third_party_tasks`.
- Descrições do menu: Stage 1 não menciona mais efeitos visuais; Stage 3 passou de "STAGE 2 + " para "STAGE 2 + efeitos visuais no modo melhor desempenho, hibernação e indexação de pesquisa desativadas e limpeza do Prefetch." O briefing da missão monta a lista pelos `tweak_ids`, então acompanha sozinho.
- Labels padronizados em "Tópico: ação" no briefing (`startup_apps`, `recommendations_offers`, `mouse_acceleration`).
- Quem já aplicou `visual_effects` antes continua com o ajuste registrado e reversível em "Desfazer ajustes".
- `docs/funcionamento.md`: tabela dos níveis atualizada.
- Testes: `tests/test_profiles.py` (ordem dos stages, testes que usavam `visual_effects` no Stage 1 passaram a usar `startup_apps`/`power_plan`, novo `test_visual_effects_only_from_alta_onwards`). `pytest -v`: 362 passed.

# Alterações — instalador do System Boost

## Fluxo de build e empacotamento

- Adicionado `installer.py` como comando local no Windows. Por padrão, ele localiza o compilador Inno Setup 6, executa `build.py` para instalar as dependências de build e gerar o executável standalone, então compila o instalador.
- O build chama PyInstaller pelo mesmo interpretador Python (`python -m PyInstaller`) que instalou `requirements.txt`, evitando coletar bibliotecas que existam apenas em outra instalação Python da máquina.
- Adicionado suporte a `INNO_SETUP_COMPILER` para configurar um caminho personalizado para `ISCC.exe`; também são pesquisados o `PATH`, os diretórios convencionais do Inno Setup 6 e a pasta de instalação por usuário em `%LOCALAPPDATA%`. A ausência do compilador e de arquivos de entrada produz mensagens de erro específicas.
- Adicionada a opção `python installer.py --skip-build` para empacotar um `dist/System Boost.exe` já existente.
- O comando gera `dist/System Boost Setup.exe`, usando a versão declarada em `pyproject.toml`. O instalador inclui somente o executável standalone: Python e dependências Python ficam incorporados pelo PyInstaller e não são exigidos na máquina de destino.

## Configuração do instalador

- Adicionado `installer.iss` para gerar pacote Inno Setup com instalação por usuário em `%LOCALAPPDATA%\Programs\System Boost`, atalhos no menu Iniciar, desinstalação registrada no Windows e opção para iniciar o aplicativo após a instalação.
- O Setup oferece mensagens em português brasileiro e inglês. A elevação UAC continua sendo solicitada ao iniciar o aplicativo, conforme o manifesto `requireAdministrator` já aplicado pelo PyInstaller.
- Atualizado o README com instruções de instalação para usuários finais, pré-requisitos de build, comando de geração e configuração opcional do caminho de `ISCC.exe`.

## Confiabilidade do build e testes

- `build.py` agora retorna status de sucesso/falha e o entrypoint converte esse resultado em código de saída do processo. Isso impede que o empacotador trate uma falha do PyInstaller como sucesso e continue com artefatos antigos.
- Adicionado teste para garantir que a falha de build é comunicada ao chamador.
- Adicionado `tests/test_installer.py` cobrindo a configuração de instalação, comando/versionamento do Inno Setup, compilador ausente, executável ausente e sequência de build e empacotamento.
- Validação executada: `pytest -v` — 370 testes passaram no Python 3.12.10.
- O workflow em `.github/workflows/ci.yml` instala `requirements.txt` e executa `pytest -v`; a suíte equivalente passou localmente. O workflow remoto não foi disparado.
- Inno Setup 6.7.3 foi instalado e o fluxo de build compilou `dist/System Boost Setup.exe` com sucesso. O teste automatizado de instalação real do programa não foi executado.

## Correção da falha de CI

- O teste de localização do Inno Setup por usuário falhava em runners que também tinham uma instalação global. O resolver prioriza corretamente %ProgramFiles(x86)%; o teste agora aponta esse caminho para uma pasta temporária inexistente e valida o fallback de %LOCALAPPDATA% de forma determinística.
- Validação local: pytest -v — 370 testes passaram.
