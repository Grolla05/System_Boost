# CHANGES

## feat: "Desfazer ajustes" na opção 6 do menu e aviso de como reverter

O desfazer já existia no backend e na CLI (`python main.py undo <id>` / `undo --all`), mas não havia nada no menu guiado nem na tela de conclusão: quem usava só o menu aplicava ajustes (plano de energia, hibernação, telemetria, serviços...) sem saber que dava para voltar atrás. Agora o caminho aparece no fluxo.

### O que mudou para o usuário

- **Menu guiado, 6ª opção "DESFAZER AJUSTES"** (setas, tecla `6`, ou `6` no fallback sem terminal interativo). Fluxo: lista os ajustes aplicados → confirma → reverte todos → mostra OK/FALHA por ajuste e o total ("N de M ajuste(s) desfeito(s)") → volta ao menu.
- **Sem nada aplicado**: mostra "Nenhum ajuste aplicado: nada para desfazer." e volta ao menu.
- **Sem Administrador**: a confirmação avisa quais ajustes (os que exigem admin) não poderão ser desfeitos; no resultado eles aparecem como FALHA com o motivo, sem derrubar os demais.
- **Tela de conclusão do nível** ganhou a linha "Para reverter: opção 6 do menu ou `python main.py undo --all`" sempre que algum ajuste foi aplicado (ou já estava aplicado).
- **Briefing antes de executar** ganhou "Reversível: opção 6 do menu ou `python main.py undo --all`" quando o nível aplica ajustes.
- `-y`/`--yes`: sem confirmação e sem esperar tecla no desfazer.

### Arquivos

- `backend/tweaks/manager.py`: `list_applied(state_path=None)` devolve `[(tweak, record)]` dos ajustes aplicados, do mais recente para o mais antigo. Só lê o state file (não consulta o Windows) e ignora ids que saíram do catálogo. Exportado em `backend/tweaks/__init__.py`.
- `frontend/components/undo_menu.py` (novo): `display_undo_confirm`, `display_undo_empty`, `display_undo_results`.
- `frontend/components/level_menu.py`: `UNDO_CHOICE = "undo"`, 6 opções em `_OPTIONS`, legenda `[1-6]`, constante `REVERT_HINT`, aviso de reversibilidade no briefing. Painel com largura mínima para a legenda não ser cortada por temas de nome longo.
- `frontend/components/level_completion.py`: linha de como reverter.
- `frontend/cli.py`: reexporta `UNDO_CHOICE` e expõe `show_undo_confirm`, `show_undo_empty`, `show_undo_results`.
- `main.py`: `_run_undo_flow(args)` e o ramo `UNDO_CHOICE` no loop do `cmd_menu`. Um erro inesperado no desfazer vira painel de erro e o menu continua.
- `tests/test_undo_option.py` (novo, 28 testes) e 4 testes em `tests/test_tweaks/test_manager.py` (`list_applied`). Em `tests/test_info_option.py`, dois testes de navegação circular foram ajustados para 6 opções (o "último" do menu agora é o desfazer).

### Teste de regressão: a limpeza não apaga os dados do desfazer

- `tests/test_state_survives_cleanup.py` (novo, 6 testes): o `tweaks_state.json` e o `ui_config.json` ficam fora de toda pasta que a limpeza esvazia (ambiente real e perfil simulado no padrão Windows, com `Temp` irmã de `WinCleaner`); limpar o `User Temp` apaga o lixo mas preserva o estado; os ajustes aplicados continuam listáveis para o desfazer depois de uma limpeza (inclusive `previous_value: null`); várias limpezas seguidas não corroem o estado.
- Limite conhecido (não coberto pelo código): se alguém apontar `TEMP` para o mesmo diretório do `LOCALAPPDATA` (ou para um pai dele), a limpeza apaga a pasta `WinCleaner` e o desfazer perde os valores originais. Confirmado por simulação; não é a configuração padrão do Windows.

### Verificação

- `python -m pytest -q`: 270 passed (264 + os 6 acima, sem contar `tests/test_hardware_loading.py`) (sem contar `tests/test_hardware_loading.py`, de outra frente de trabalho, que importa um módulo ainda inexistente).
- Telas renderizadas com o estado real da máquina em modo somente leitura (7 ajustes lidos do state file); o desfazer em si **não foi executado no Windows real**, só com o sistema simulado nos testes.
- Navegação por teclado real (`msvcrt`) coberta por testes com `_read_menu_key` simulado.

### build.py: aborta se o `System Boost.exe` anterior ainda estiver em execução

- Causa do erro `Access is denied: ...\dist\System Boost.exe`: o PyInstaller apaga o `.exe` antigo antes de regravar, e o Windows nega enquanto ele roda (com `--uac-admin` o processo é elevado, e um terminal comum não consegue encerrá-lo).
- `build.py`: `is_exe_running()` consulta `tasklist /FI "IMAGENAME eq System Boost.exe" /FO CSV /NH` e procura o nome do exe na saída (o nome não é localizado; a mensagem de "nenhuma tarefa" é, por isso não é usada). Falha do `tasklist` (`OSError`/timeout) nunca bloqueia o build. `build()` aborta antes do `pip install`/PyInstaller com instrução de como fechar o processo.
- `tests/test_build.py`: +5 testes (exe detectado, sem correspondência, falha do tasklist, build aborta antes do PyInstaller).

### Ficha da máquina centralizada no menu (`wait=True`)

- `frontend/components/machine_info.py`: com `wait=True` a tabela e o aviso "Pressione qualquer tecla..." saem centralizados (`rich.align.Align`) com padding vertical. `wait=False` (comando `info`) não mudou.
- Fecha `tests/test_hardware_loading.py::test_display_machine_info_centered_with_wait`.

### Decisão: proteção da pasta `WinCleaner` na limpeza

- Uma tentativa de proteger `%LOCALAPPDATA%\WinCleaner` na limpeza (módulo `backend/paths.py`) foi desfeita no editor e **não** será refeita. O "Limite conhecido" acima continua valendo.

### Verificação (estado final)

- `python -m pytest -q`: 278 passed. CI (`.github/workflows/ci.yml`: `pip install -r requirements.txt` + `pytest -v`) equivale ao mesmo comando.

## feat: upgrade completo de UI retrô 8-bit — paletas, sprites animados, loot breakdown e typewriter

Expande a interface gráfica de terminal do System Boost com 4 novas funcionalidades visuais e interativas de estética retrô 8-bit:
1. **Seletor de Paletas Retrô** (5 esquemas de cores inspirados em consoles e monitores CRT clássicos, com persistência e atalho de tecla).
2. **Sprites Animados no Loading** (micro-animação contínua estilo Pac-Cleaner devorando dados temporários).
3. **Gráfico de Pré-Inspeção de Disco ("Loot Breakdown")** (barras horizontais de porcentagem e distribuição do volume antes da limpeza).
4. **Efeito Typewriter com Micro-Cliques de Áudio** (renderização estilo máquina de escrever em diálogos de briefing com cancelamento instantâneo).

```
python main.py
python main.py menu [-p {dmg,pocket,arcade,amber,matrix}] [--no-sound]
python main.py clean [--dry-run] [-p {dmg,pocket,arcade,amber,matrix}] [--no-sound]
```

### Funcionalidades implementadas

1. **Seletor Dinâmico de Paletas Retrô (`frontend/palettes.py`)**:
   - 5 paletas completas com tokens semânticos:
     - `dmg`: **Game Boy Classic (DMG-01)** — verde LCD autêntico de 4 tons.
     - `pocket`: **Game Boy Pocket** — monocromático cinza/prata de alto contraste.
     - `arcade`: **Cyber Arcade 80s** — neon ciano, magenta e amarelo arcade.
     - `amber`: **Phosphor Amber CRT** — âmbar clássico de terminais IBM/VT100.
     - `matrix`: **Matrix Terminal** — fundo escuro e verde código fosforescente.
   - **Tecla de atalho `[P]` no menu**: cicla instantaneamente entre as paletas com feedback sonoro `play_blip()` e atualiza a interface em tempo real.
   - **Persistência automática**: salva a escolha em `%LOCALAPPDATA%\WinCleaner\ui_config.json`.
   - **Flag CLI `--palette <nome>` / `-p <nome>`**: permite iniciar o programa diretamente no tema desejado.

2. **Sprite Pixel Art Animado no Loading (`frontend/components/retro_sprite.py` & `loading.py`)**:
   - Adicionada a coluna `RetroSpriteColumn` ao `rich.progress.Progress`.
   - Conforme os arquivos são varridos e apagados, um sprite de "Pac-Cleaner" (`[C • • •]`, `[ C• • •]`, ..., `[ ★ OK!]`) anima continuamente junto com a barra de energia retrô (Energy Gauge).

3. **Gráfico de Pré-Inspeção do Disco ("Loot Breakdown") (`frontend/components/disk_breakdown.py`)**:
   - Função `measure_paths_sizes(paths)` que mede com segurança os bytes ocupados em cada setor antes da confirmação.
   - Painel `create_disk_breakdown_panel(sizes)` com barras de porcentagem proporcionais (`[████████░░░░░░░░] XX%`) e total estimado legível em KB/MB/GB.
   - Integrado automaticamente à tela de confirmação de missão do menu (`display_level_summary`).

4. **Efeito Typewriter com Som (`frontend/typewriter.py`)**:
   - Função `typewriter_print(console, text, speed, sound, skip)`.
   - Micro-cliques suaves chiptune via `play_typewriter_click()` em `frontend/audio.py`.
   - Cancelamento instantâneo (instant skip) ao pressionar qualquer tecla (`kbhit`) ou em pipes e testes automatizados.

5. **Navegação Híbrida & Áudio Chiptune Nativo**:
   - Menu navegável por setas do teclado (`↑` e `↓` com ponteiro retrô `►` e `Enter`) ou seleção direta numérica (`1`-`5`).
   - Fanfarra triunfal de vitória de 4 notas (`play_victory()`) na tela de resultado.
   - Flag `--no-sound` disponível em todos os subcomandos interativos.

### Arquivos novos

### Arquivos novos

- `frontend/audio.py`:
  - Gerador de bipes chiptune via `winsound.Beep` no Windows.
  - Funções de áudio: `play_blip()`, `play_select()`, `play_start()`, `play_victory()`, `play_error()`, `play_typewriter_click()`.
  - Controle de ativação global: `set_sound_enabled(bool)` e `is_sound_enabled()`.
  - Tratamento defensivo de exceções e execução em thread separada.
- `frontend/palettes.py`:
  - 5 paletas retrô (`dmg`, `pocket`, `arcade`, `amber`, `matrix`), `get_theme()`, `cycle_palette()`, `save_palette()`, `load_palette()`.
- `frontend/components/retro_sprite.py`:
  - Frames de animação do Pac-Cleaner (`PAC_CLEANER_FRAMES`) e vassoura pixelada (`BROOM_FRAMES`).
- `frontend/components/disk_breakdown.py`:
  - `measure_paths_sizes()` e `create_disk_breakdown_panel()`.
- `frontend/typewriter.py`:
  - `typewriter_print()` com delay por caractere, clicks de áudio e skip instantâneo.
- `tests/test_audio.py`: 4 testes unitários de áudio.
- `tests/test_palettes.py`: 4 testes unitários de paletas e temas.
- `tests/test_disk_breakdown.py`: 3 testes unitários de medição e renderização do painel.
- `tests/test_retro_sprite.py`: 2 testes unitários de frames do sprite animado.
- `tests/test_typewriter.py`: 3 testes unitários do efeito máquina de escrever.
- `tests/test_retro_ui.py`: 7 testes unitários dos componentes, tema e navegação.

### Arquivos alterados

- `frontend/cli.py`:
  - Reconfiguração para UTF-8 de `sys.stdout` e `sys.stderr` no Windows.
  - Carregamento dinâmico de paletas e integração com `palettes`.
  - Exposição de `apply_palette` e `cycle_active_palette`.
- `frontend/components/welcome.py`:
  - Banner em blocos sólidos `█ ▀ ▄` do System Boost Game Boy Edition, moldura dupla e chamada de `play_start()`.
- `frontend/components/level_menu.py`:
  - Navegação híbrida com setas `↑`/`↓` + `Enter`, teclas `1-5`, tecla `P` para alternar paletas e painel de Loot Breakdown no briefing.
- `frontend/components/loading.py`:
  - Coluna `RetroSpriteColumn` com animação contínua do Pac-Cleaner e Energy Bar retrô.
- `frontend/components/driver_progress.py`:
  - Barra de progresso estilizada com temas retrô.
- `frontend/components/completion.py` e `frontend/components/level_completion.py`:
  - Painéis com `box.DOUBLE`, pontuação retrô (`TOTAL SCORE`), preservação estrita de todos os textos originais e fanfarra de vitória (`play_victory()`).
- `frontend/components/machine_info.py`:
  - Ficha da máquina com moldura dupla `box.DOUBLE` e cabeçalho retrô.
- `frontend/components/tweak_list.py` e `frontend/components/tweak_result.py`:
  - Inventário de ajustes com molduras retrô e bordas duplas.
- `main.py`:
  - Flags `--no-sound` e `--palette` / `-p` nos subparsers `menu` e `clean`.
  - Repasse da configuração para `set_sound_enabled` e `apply_palette` em `main()`.
- `tests/test_main.py`:
  - Testes unitários para as flags `--no-sound` e `--palette`.

### Verificação

- `pytest -v`: 232 passed (100% de aprovação).
- Execução real no terminal Windows testando `menu`, `clean --dry-run`, `info`, `list` e chaveamento de paletas.
- Sem inclusão de bibliotecas externas pesadas; totalmente compatível com o build executável PyInstaller.
- Sem inclusão de bibliotecas externas pesadas; totalmente compatível com o build executável PyInstaller.


## feat: "ficha da máquina" — comando `info` e opção 5 do menu

Mostra um resumo da máquina: versão e compilação do Windows, processador, memória instalada, placa(s) de vídeo, tipo do disco do sistema (SSD/HDD) e se é notebook ou desktop. Implementa o item "Hardware detection" do roadmap do `CLAUDE.md`.

```
python main.py info
```

Saída real na máquina de desenvolvimento:

```
Windows          Windows 11 Pro 24H2 (compilação 26100.9457)
Processador      Intel(R) Core(TM) i7-4790 CPU @ 3.60GHz (8 threads)
Memória          16 GB
Placa de vídeo   Intel(R) HD Graphics 4600 / NVIDIA GeForce GTX 1650
Disco do sistema SSD SATA — KINGSTON SA400S37240G
Tipo             Desktop
```

### Arquivos novos

- `backend/_powershell.py`
  - `run_powershell(script, timeout)` e `PowerShellError`.
  - Executa `powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command`, com `stdin=DEVNULL`, e devolve stdout decodificado em `utf-8-sig`.
  - Timeout, executável ausente (`OSError`) e returncode ≠ 0 viram `PowerShellError`.
  - Cópia do padrão de `_run_powershell` em `backend/drivers.py`. `drivers.py` **não foi alterado**, porque `tests/test_drivers.py` faz patch de `drivers.subprocess.run`. Unificar os dois fica como follow-up.
  - Exporta também `PS_PRELUDE` (UTF-8 no stdout + `$ErrorActionPreference='Stop'`).
- `backend/hardware.py`
  - `MachineInfo` (dataclass): `windows`, `version`, `build`, `cpu`, `threads`, `ram_gb`, `gpus` (lista), `disk_type`, `disk_model`, `disk_bus`, `form_factor`.
  - `get_machine_info()` nunca levanta exceção. Cada campo falha de forma isolada: `None`, ou `[]` para GPUs.
  - Windows: `winreg` em `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` (`ProductName`, `DisplayVersion` com fallback para `ReleaseId`, `CurrentBuildNumber`, `UBR`). Compilação ≥ 22000 troca "Windows 10" por "Windows 11" no nome, porque o registro mantém o nome antigo no Windows 11. Build exibida como `CurrentBuildNumber.UBR`, ou só `CurrentBuildNumber` se o `UBR` não existir.
  - CPU: `winreg` em `HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0` (`ProcessorNameString`, espaços repetidos colapsados). Threads via `os.cpu_count()`.
  - RAM: `ctypes` `GetPhysicallyInstalledSystemMemory` (KB instalados nos pentes). Fallback `GlobalMemoryStatusEx` (total utilizável). Arredondada em 1 casa.
  - GPU, disco e tipo: **uma** chamada PowerShell/CIM (`CIM_TIMEOUT = 30s`) que devolve JSON. Cada consulta tem seu `try/catch` no script. Consultas: `Win32_VideoController`, `Get-Partition` + `Get-PhysicalDisk` (disco onde está `%SystemDrive%`), `Win32_SystemEnclosure.ChassisTypes`, `Win32_Battery`.
  - `MediaType` e `BusType` são convertidos para string no script, e os valores de enum não são traduzidos pelo idioma do Windows. A regra do repo de não parsear stdout localizado foi respeitada.
  - Disco: `SSD`/`HDD` direto de `MediaType` (aceita também `4`/`3` numéricos). `MediaType` vazio com barramento NVMe → SSD. Caso contrário `None`.
  - Notebook × Desktop: chassi 8/9/10/11/14/30/31/32 → Notebook. Outro chassi informativo → Desktop. Chassi 1/2 ("Outro"/"Desconhecido"), ou lista vazia, usa a bateria como desempate. Sem nenhuma informação → `None`.
  - GPUs duplicadas são removidas, preservando a ordem.
  - Normaliza valores escalares do PowerShell (arrays de 1 item colapsam em escalar) com `_as_list`.
  - Import de `winreg` protegido (`None` fora do Windows) para não quebrar ferramentas em outros sistemas.
- `frontend/components/machine_info.py`
  - `display_machine_info(console, info)`: tabela "A ficha da máquina", sem cabeçalho, com coluna de rótulos em `accent`.
  - Campos vazios aparecem como `[dim]desconhecido[/dim]`. Uma linha por GPU. RAM inteira sem casa decimal (`16 GB`), fracionada com uma (`15.8 GB`).
- `tests/test_powershell.py`: 4 testes (stdout decodificado e flags do comando, returncode ≠ 0, timeout, executável ausente).
- `tests/test_hardware.py`: testes de Windows 11 detectado pela build, Windows 10 abaixo de 22000, build sem UBR, fallback para `ReleaseId`, falha de registro, CPU e threads, RAM (instalada, fallback, tudo falhando), GPUs (deduplicação e escalar), classificação de disco (6 casos), disco ausente, classificação de chassi (9 casos), chassi escalar, falha/JSON inválido/saída vazia do PowerShell degradando só os campos CIM, e `get_machine_info` nunca levantando exceção.
- `tests/test_machine_info.py`: 6 testes de renderização (todos os campos, `desconhecido` sem `None` literal, RAM fracionada, várias GPUs, sem GPU, Desktop).

### Arquivos alterados

- `main.py`
  - `"info"` adicionado a `COMMANDS`. Sem isso, o back-compat de flags soltas reescreveria `info` para `clean`.
  - Novo subparser `info`, `cmd_info(args)` (modelo de `cmd_list`) e entrada em `_DISPATCH`, agora em várias linhas.
  - Imports de `get_machine_info` e `show_machine_info`.
- `frontend/cli.py`: import de `display_machine_info` e wrapper `show_machine_info(info)`.
- `tests/test_main.py`: 3 testes novos (`parse_args(["info"])`, `info` em `COMMANDS`/`_DISPATCH`, `cmd_info` repassa o resultado de `get_machine_info` a `show_machine_info`).
- `README.md`: feature, seção de uso e estrutura do projeto.
- `docs/funcionamento.md`: nós no diagrama mermaid e seções de `hardware.py`, `_powershell.py` e `machine_info.py`.
- `CLAUDE.md`: linha "Hardware detection" do roadmap marcada como feita, com a descrição da implementação.

### Opção 5 no menu guiado ("Ver ficha da máquina")

A ficha também aparece dentro da navegação do `python main.py` / `menu`, como quinta opção do menu de níveis. Escolher a opção mostra a ficha e, ao apertar qualquer tecla, volta ao menu de níveis.

- `frontend/components/level_menu.py`
  - Constante `INFO_CHOICE = "info"`. `display_level_menu` devolve esse valor (em vez de um id de nível) quando a opção é escolhida.
  - Lista de opções `_OPTIONS = LEVEL_ORDER + (INFO_CHOICE,)`. Setas ↑/↓ circulam pelas 5 opções (de cima do 1 vai para o 5, de baixo do 5 vai para o 1), a tecla `5` escolhe direto, e o fallback sem terminal interativo aceita `1`–`5` no `IntPrompt`.
  - `_read_menu_key` passou a aceitar o dígito `5`, nos ramos Windows e POSIX. Legenda do painel: `[1-5] Direto`.
  - `_render_menu_panel` desenha "[5] VER FICHA DA MÁQUINA" com o mesmo ponteiro `►` dos níveis.
  - Os níveis 1–4 e o comportamento da tecla ESC (devolve a opção selecionada) não mudaram.
- `frontend/components/machine_info.py`: `display_machine_info(console, info, wait=False)`. Com `wait=True` limpa a tela, mostra a ficha, exibe "Pressione qualquer tecla para voltar ao menu..." e bloqueia em `_read_single_key()`. Sem isso o menu apagaria a ficha no redesenho seguinte. `wait=False` (padrão) mantém o comportamento do comando `info`.
- `frontend/cli.py`: `show_machine_info(info, wait=False)` repassa o `wait`, e `INFO_CHOICE` é reexportado para o `main.py`.
- `main.py` (`cmd_menu`): se `show_level_menu()` devolve `INFO_CHOICE`, lê a ficha, mostra com `wait=True` e volta ao início do loop (`continue`), sem passar pelo resumo/limpeza. A leitura do hardware (PowerShell/CIM, ~2s) roda **uma vez** por sessão, sob um spinner "Lendo hardware...", e é reaproveitada nas visualizações seguintes. Quem nunca escolhe a opção não paga custo nenhum.
- `tests/test_info_option.py` (novo, 14 testes): constante exportada e fora de `LEVEL_ORDER`; painel com 5 opções; tecla `5`; setas até a opção 5; volta circular (`up` no primeiro, 5× `down`); fallback `IntPrompt` com `"5"` entre as opções; tela de ficha espera tecla só com `wait=True`; `show_machine_info` repassa `wait`; `cmd_menu` mostra a ficha e retorna ao menu sem tratar `info` como nível; hardware lido uma única vez em várias visualizações; nenhuma leitura quando a opção não é usada.

### Build: executável sempre como Administrador + identidade do publisher

- `build.py` (refatorado em funções testáveis; `build()` continua sendo o ponto de entrada)
  - `build_command(version_file)`: comando do PyInstaller, agora com `--uac-admin` (manifesto `requestedExecutionLevel=requireAdministrator`: o Windows mostra o UAC em toda abertura do `.exe`) e `--version-file=...`.
  - `write_version_file(path, version)` / `version_tuple` / `project_version()`: gera o recurso de versão do exe com `CompanyName=Felipe Grolla`, `FileDescription=System Boost by Felipe Grolla`, `ProductName=System Boost`, `OriginalFilename=System Boost.exe` e a versão lida do `pyproject.toml` (fonte única; sufixos como `rc1` viram `.0` para caber nos 4 inteiros do Windows). O arquivo é gerado numa pasta temporária, porque `--clean` apaga `./build` antes de lê-lo.
  - `sign_command` / `sign_if_configured`: se a variável `SYSTEM_BOOST_SIGN_THUMBPRINT` existir, roda `signtool sign /sha1 <thumbprint> /fd SHA256 /tr ... /td SHA256 /d "System Boost by Felipe Grolla"` no exe. Sem a variável, só avisa que não assinou.
- `tests/test_build.py` (novo, 14 testes): flag `--uac-admin`, flags antigas preservadas, `--version-file`, versão igual à do `pyproject.toml`, `version_tuple`, conteúdo do recurso de versão (publisher/produto/versões), recurso válido para o PyInstaller (executado com as classes reais), comando do `signtool` e assinatura só quando há thumbprint.
- Verificado com um build real (`python build.py`): manifesto `requireAdministrator` presente no exe; Properties → Detalhes mostra empresa "Felipe Grolla" e descrição "System Boost by Felipe Grolla"; assinatura `NotSigned`.
- **Limite importante:** a linha "Editor verificado / Publisher" do UAC só mostra um nome quando o exe é assinado (Authenticode) com certificado emitido para esse nome. Sem assinatura o UAC mostra "Editor desconhecido" (escudo amarelo), mesmo com os metadados acima. Certificado de código (OV/EV, ou Azure Trusted Signing / SignPath) é compra/cadastro externo ao repositório; o `build.py` já assina sozinho quando houver um.
- Efeito colateral do "sempre admin": o `.exe` abre o UAC e roda numa janela de console elevada própria, que fecha ao terminar. `info`/`list`/`apply`/`undo` chamados pelo `.exe` a partir de um terminal comum piscam e fecham. Para esses comandos, prefira `python main.py ...`. Rodando do código-fonte nada muda.
- O `System Boost.spec` é ignorado pelo git (`*.spec`) e regravado pelo PyInstaller a cada build; não faz parte da mudança.

### Decisões

- **Sem dependência nova.** `psutil` não está no `requirements.txt` e não foi adicionado. `winreg`, `ctypes` e PowerShell cobrem tudo.
- **Sem Administrador.** Todas as leituras funcionam em terminal comum.
- **Dois pontos de entrada**: `python main.py info` (comando direto, sem espera) e a opção 5 do `menu` (sob demanda, volta ao menu). A ficha **não** aparece automaticamente antes do menu, então o fluxo normal e o `-y` não ficam mais lentos.
- **`-y`/`--yes` não é afetado**: ele já pula o menu interativo, e a opção só existe quando alguém navega nele.

### Verificação

- `python -m pytest -q`: 206 passed.
- Painel do menu renderizado com a opção 5 selecionada (conferido visualmente). A navegação por teclado real (`msvcrt`) está coberta por testes com `_read_menu_key` simulado, não por execução interativa.
- `python main.py info` na máquina real: os 6 campos preenchidos e coerentes (tabela acima).
- CI (`.github/workflows/ci.yml`): `pip install -r requirements.txt` + `pytest -v`. Os mesmos testes rodados localmente. Sem passo de lint.
