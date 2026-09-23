# CHANGES.md

## 2026-09-23 (2) — Fluxo guiado por menu (`python main.py`), 4 níveis de otimização

Baseado no plano de ação aprovado em `C:\Users\fegro\.claude\plans\pasted-content-id-ebf4-quero-evoluir-replicated-fairy.md` (segunda rodada de planejamento na mesma sessão — plano anterior era o sistema de ajustes reversíveis, já implementado e documentado na entrada abaixo). Motivação: rodar `python main.py` sem argumentos ainda caía direto na limpeza (`clean`), a mesma navegação de antes do sistema de tweaks existir. O usuário pediu um fluxo guiado de 4 telas: boas-vindas → menu de níveis (leve/mediana/alta/extrema) → configuração/execução → conclusão — evolução interativa da ideia original de "perfil 1 clique" (item 2 do roadmap), expandida de um único pacote pré-definido para 4 níveis escaláveis.

### 1. Novo módulo `backend/profiles.py`

Funções puras (sem classes, igual ao resto do `backend/` fora de `tweaks/`), orquestrando `cleaner` + `tweaks` juntos — por isso vive fora de `backend/tweaks/`, que continua restrito à abstração de ajuste em si.

- `LEVELS`: dict declarativo com os 4 níveis (`leve`, `mediana`, `alta`, `extrema`), cada um com `clean_paths` (quais pastas de temp) e `tweak_ids` (quais dos 7 ajustes).
- `resolve_clean_paths(level_id)`: reaproveita `cleaner.get_temp_paths()` e o mesmo filtro por status de admin que `cmd_clean` já tinha em `main.py` — nenhuma lógica nova de descoberta de pasta.
- `resolve_tweak_plan(level_id)`: separa os ajustes do nível em `applicable` (pode aplicar agora) e `skipped` (exige admin e o terminal não está elevado) — checa `tweak.requires_admin` de cada ajuste via `tweaks.catalog.get_tweak(id)`.
- `apply_level_tweaks(level_id, state_path=None)`: aplica cada ajuste `applicable` via `tweaks.manager.apply_tweak()` (reaproveitado sem alteração), capturando `TweakError` por ajuste — um ajuste já aplicado ou que falhe não aborta os demais. Retorna uma lista de `(tweak_id, status, nota)` por ajuste, com `status` em `True` (aplicado), `False` (falhou) ou `None` (pulado por falta de admin).

### 2. Mapeamento dos 4 níveis (confirmado com o usuário via pergunta em plan mode)

| Nível | Pastas limpas | Ajustes aplicados |
|---|---|---|
| Leve | User Temp | `visual_effects` |
| Mediana | + System Temp | + `power_plan` |
| Alta | + Prefetch | + `hibernation`, `indexing` |
| Extrema | (mesmas de Alta) | + `telemetry`, `sysmain`, `compat_appraiser` |

Leve e Mediana nunca exigem admin (só usam os 2 ajustes sem esse requisito); Alta e Extrema aplicam tudo que estiver disponível e **pulam graciosamente** — nunca travam a execução inteira — o que exigir admin quando o terminal não está elevado, mesma filosofia que `cmd_clean` já usava para filtrar pastas.

### 3. Refatoração: `frontend/components/_terminal.py` (novo, compartilhado)

A lógica de "aguardar uma tecla e opcionalmente fechar o terminal via `WM_CLOSE`" existia só em `completion.py`. Extraída para `wait_for_keypress_and_maybe_close(close_terminal)` em `_terminal.py`, reaproveitada por `completion.py` (`clean`) e pelo novo `level_completion.py` (`menu`) — evita duplicar a dança de `ctypes`/`msvcrt`/fallback POSIX uma segunda vez. Comportamento de `completion.py` preservado byte a byte (mesmo texto, mesma sequência), só a implementação interna mudou.

### 4. Novos componentes de frontend

- `frontend/components/level_menu.py`:
  - `display_level_menu(console)` — tabela `rich` com os 4 níveis, lê a escolha via `rich.prompt.IntPrompt.ask(..., choices=["1","2","3","4"])` (dependência já existente, nenhuma instalação nova).
  - `display_level_summary(console, ...)` — painel mostrando o que será limpo e quais ajustes serão aplicados vs. pulados (admin), depois `rich.prompt.Confirm.ask("Prosseguir?", default=True)`.
- `frontend/components/level_completion.py`: painel combinado (bytes liberados + contagem de aplicados/pulados/falharam), reaproveitando `wait_for_keypress_and_maybe_close` — **esta tela fecha o terminal ao final**, igual ao `clean`, porque o fluxo guiado é agora a experiência "clique e pronto" primária que o `clean` originalmente visava. `list`/`apply`/`undo` continuam sem essa cerimônia.
- `frontend/cli.py` ganhou `show_level_menu`, `show_level_summary`, `show_level_completion`, seguindo a convenção de wrapper fino já usada pelos comandos existentes.

### 5. `main.py`: novo subcomando `menu` + mudança no argv padrão

- `COMMANDS` ganhou `"menu"`.
- **Só `argv` vazio** agora mapeia para `["menu"]` em vez de `["clean"]`. O ramo existente `elif argv[0] not in COMMANDS: argv = ["clean"] + argv` foi mantido intacto — flags soltas como `--dry-run -y` (sem palavra-chave de subcomando) continuam implicando `clean`, preservando a retrocompatibilidade já testada.
- **Nome do subcomando corrigido de `boost` para `menu` durante a implementação**: a primeira tentativa usou `boost` (mesmo nome do `prog=` do argparse, que já é "boost" desde a sessão anterior), o que gerava `usage: boost boost [-h] [-y]` — confuso. Renomeado para `menu` (`usage: boost menu [-h] [-y]`, lê corretamente).
- `cmd_menu(args)`: `show_welcome` → `show_level_menu()` → `profiles.resolve_clean_paths`/`resolve_tweak_plan` → se não `--yes`, `show_level_summary(...)` (recusar aborta sem alterar nada) → `show_loading(clean_paths, clean_directory, format_size, dry_run=False)` (reaproveitado de `cmd_clean`, mesmo formato de dict) → `profiles.apply_level_tweaks(level_id)` → `show_level_completion(...)`.
- `_DISPATCH` ganhou `"menu": cmd_menu`.

### 5.1. Tela de conclusão: Enter para sair, ESC para voltar ao menu (refinamento pedido após a primeira versão)

A tela de conclusão do `menu` originalmente saía com qualquer tecla. Adicionado: **Enter (ou qualquer tecla que não seja ESC) sai**, **ESC volta ao menu de níveis** (sem reabrir a tela de boas-vindas) para escolher outro nível sem reiniciar o processo.

- `frontend/components/_terminal.py`: extraída `_read_single_key()` (leitura crua compartilhada, Windows via `msvcrt.getch()` / POSIX via `termios`) e `_close_terminal()` (a chamada `WM_CLOSE`) das duas funções públicas existentes. Nova função `wait_for_exit_or_back(close_terminal=True)`: lê uma tecla, retorna `"back"` se for ESC (`b'\x1b'`/`'\x1b'`), senão fecha o terminal (se pedido) e retorna `"exit"`. `wait_for_keypress_and_maybe_close()` (usada por `completion.py`/`clean`) manteve o comportamento idêntico, só reaproveitando os dois helpers privados internamente.
- `frontend/components/level_completion.py`: não chama mais `sys.exit(0)` internamente — retorna `"exit"` (quando `skip_wait=True`, ou depois de `wait_for_exit_or_back`) ou `"back"` para quem chamou decidir, mesmo padrão dos outros componentes que nunca finalizam o processo sozinhos.
- `frontend/components/level_menu.py`: `display_level_menu()` ganhou `console.clear()` no início, para a tela renderizar limpa quando o usuário volta do completion via ESC.
- `main.py`: `cmd_menu()` virou um laço (`while True`) em torno de menu → resumo → execução → conclusão; só sai do laço quando `show_level_completion(...)` retorna algo diferente de `"back"`. Com `-y`, `skip_wait=True` sempre retorna `"exit"` na primeira volta, então o comportamento não-interativo/scriptado não muda.
- Nenhum teste novo (mesma justificativa já registrada: componentes de teclado em `frontend/components/*` não são testados unitariamente neste repo). Verificado via `subprocess.run(["python","main.py","menu","-y"], input=b"1\n")` que o caminho `-y` continua saindo limpo após uma única volta do laço; o caminho interativo ESC/Enter foi verificado por inspeção de código pela mesma limitação de `msvcrt.getch()` com stdin pipado já documentada acima.

### 6. Testes (`tests/test_profiles.py`, `tests/test_main.py`)

Segue o padrão `monkeypatch`-o-colaborador já estabelecido em `tests/test_tweaks/test_manager.py` (nenhum teste toca `winreg`/`subprocess` reais aqui — `profiles.py` não fala com o Windows diretamente, só orquestra `cleaner`/`tweaks`).

- `resolve_clean_paths`: cada nível retorna exatamente suas pastas declaradas; admin=False derruba System Temp/Prefetch; filtra para o que `get_temp_paths()` reporta como existente.
- `resolve_tweak_plan`: ajustes que exigem admin caem em `skipped` sem elevação e em `applicable` com elevação; Leve nunca tem ajuste pulado (só usa `visual_effects`, que não exige admin).
- `apply_level_tweaks`: chama `apply_tweak` só para ids `applicable` (nunca para os pulados), coleta `(id, True, None)` em sucesso e `(id, False, str(exc))` em `TweakError`.
- `tests/test_main.py`: `parse_args([])` agora resolve para `"menu"` (era `"clean"`); `parse_args(["menu", "-y"])` funciona; `parse_args(["--dry-run", "-y"])` continua resolvendo para `"clean"` (guarda de regressão da retrocompatibilidade).

Nenhum teste novo para `frontend/components/level_menu.py`/`level_completion.py` — mesmo precedente já estabelecido (`frontend/components/*` não é testado unitariamente neste repo).

**84 testes, todos passando** (`pytest -v` → `84 passed`; 72 pré-existentes + 12 novos).

### Verificação executada

- `pytest -v` — 84/84 passando.
- `python main.py --help` / `python main.py menu --help` — confirma que o nome do subcomando (`menu`) não colide mais com o `prog` (`boost`) depois da correção do item 5.
- Smoke test via `subprocess.run(..., input=b"1\n")` (nível Leve, `-y`): aplicou `visual_effects`, limpou `User Temp`, tela final reportou "1 ajuste(s) aplicado(s)" — confirmado inspecionando `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` antes/depois.
- Mesmo teste com nível Extrema (não-admin): "2 ajuste(s) aplicado(s)" (`visual_effects`, `power_plan`) + "5 pulado(s) (requer Administrador)" (`hibernation`, `indexing`, `telemetry`, `sysmain`, `compat_appraiser`) — confirma a degradação graciosa sem admin.
- **Limitação de teste descoberta e documentada** (em `CLAUDE.md`): `msvcrt.getch()` (usado pelas telas de boas-vindas/conclusão quando `skip_wait=False`) lê diretamente do console e trava indefinidamente com stdin redirecionado/pipado — diferente de `rich.prompt.IntPrompt`/`Confirm`, que funcionam normalmente com stdin pipado. Por isso o caminho de "usuário recusa a confirmação" (que passa pela tela de boas-vindas com keypress real) foi verificado por inspeção de código, não por execução automatizada — mesma limitação já documentada para outros componentes de frontend deste repo.
- Regressão manual: `python main.py list`, `python main.py --dry-run -y` e `python main.py clean --dry-run -y` continuam idênticos a antes da mudança (confirma que a extração de `_terminal.py` e a troca do argv padrão não quebraram nada existente).
- Máquina de desenvolvimento verificada limpa ao final (nenhum ajuste ficou aplicado depois dos testes).

### Documentação atualizada

- `docs/funcionamento.md`: nova seção "Fluxo Guiado (`menu`)" com diagrama de sequência das 4 telas, tabela dos 4 níveis, e a nota sobre degradação graciosa; diagrama de arquitetura geral atualizado para incluir `backend/profiles.py` e os novos componentes.
- `docs/README.md` e `README.md` (raiz): seção de uso reescrita para deixar claro que `python main.py` sem argumentos agora abre o fluxo guiado, com `clean` como comando explícito para o comportamento direto anterior.
- `CLAUDE.md`: nova subseção de arquitetura para `backend/profiles.py`, nota sobre a limitação de teste do `msvcrt.getch()` com stdin pipado, e a linha do roadmap "1-click quick profile" marcada como superada por este módulo (4 níveis em vez de um pacote único).

### Nota lateral: arquivo `README.md` da raiz

Durante esta sessão, `docs/README.md` (o único README rastreado no histórico do git até então) desapareceu do disco e seu conteúdo apareceu em `README.md` na raiz do projeto — um evento de sistema de arquivos fora do controle das minhas chamadas de ferramenta (nenhum comando de mover/renomear foi executado). Como consequência, e porque o `README.md` da raiz é o que o GitHub efetivamente exibe na página inicial do repositório, `docs/README.md` foi restaurado como o índice curto da pasta `docs/` (seu propósito original) e `README.md` na raiz foi escrito como o README principal e mais completo do projeto — este último agora é o arquivo git deve passar a rastrear oficialmente a partir do próximo commit.

### Pendências / próximos passos sugeridos (fora do escopo deste commit)

- Itens 3-7 do roadmap original (monitor de recursos, análise de disco por categoria, inventário de drivers, debloat/startup, detecção de hardware) — módulos futuros já nomeados em `CLAUDE.md`, nenhum código criado ainda.
- `boost quick` como comando fixo de automação (ex: `python main.py menu -y` já cobre uso não-interativo escolhendo o nível via stdin, mas não há uma forma de passar o nível direto por flag como `--level extrema` — considerar se vale a pena adicionar).

---

## 2026-09-23 — Sistema de ajustes reversíveis do Windows (item 1 do roadmap "System Boost")

Baseado no plano de ação aprovado em `C:\Users\fegro\.claude\plans\pasted-content-id-ebf4-quero-evoluir-replicated-fairy.md`. Primeira peça da evolução do WinCleaner para um "system boost" mais completo (inspirado no Dilera Boost), mantendo o princípio de ferramenta 100% local: sem login, conta, licenciamento, telemetria enviada para fora, verificação online, download de binários de terceiros, ou alteração de pastas de jogos.

### 1. Novo subpacote `backend/tweaks/`

- `base.py`: `Tweak(ABC)` com `get_current_value()`/`apply()`/`undo(previous_value)` abstratos, e `TweakError`. Única exceção deliberada e escopada ao uso de classes no backend (resto do backend é só funções) — justificada porque os 7 ajustes têm mecanismos heterogêneos e exigem polimorfismo real; uma subclasse esquecendo `undo()` falha em `TypeError` na hora de instanciar, não silenciosamente em runtime no pior momento (quando o usuário precisa desfazer algo).
- Classes de mecanismo, organizadas por **como** falam com o Windows (não uma por ajuste, pra não duplicar código entre ajustes que compartilham mecanismo):
  - `registry_value.py` → `RegistryValueTweak` (leitura/escrita genérica de um valor DWORD via `winreg`) — usada por `visual_effects` e `telemetry`.
  - `services.py` → `ServiceStateTweak` (leitura via `winreg`, escrita via `sc.exe`) — usada por `indexing` (WSearch) e `sysmain` (SysMain).
  - `scheduled_tasks.py` → `ScheduledTaskTweak` (`schtasks.exe`) — usada por `compat_appraiser`.
  - `power_plan.py` → `PowerPlanTweak`; `hibernation.py` → `HibernationTweak` — cada uma isolada apesar de ambas chamarem `powercfg.exe`, porque a semântica de leitura/escrita é genuinamente diferente entre as duas.
- `catalog.py`: instancia os 7 ajustes concretos (`_build_catalog()`, chamada sob demanda, não cacheada), expõe `list_tweaks()` (ordenado por id) e `get_tweak(id)` (levanta `TweakError` em id desconhecido).
- `state_store.py`: persistência em JSON, funções puras (`load_state`, `save_applied`, `get_applied`, `clear_applied`, `list_applied`), todas aceitando `path=None` (default `%LOCALAPPDATA%\WinCleaner\tweaks_state.json`) para testabilidade sem depender de variável de ambiente real.
- `manager.py`: `apply_tweak`, `undo_tweak`, `undo_all`, `list_status` — coordena checagem de admin, lookup no catálogo e leitura/escrita de estado.
- `__init__.py`: reexporta a API pública do subpacote.

### 2. Decisões de design importantes

- **Leituras via `winreg`, não parsing de stdout de `.exe`**: a saída de `sc.exe`/`schtasks.exe`/`powercfg.exe` é localizada no idioma de exibição do Windows (esta UI já é pt-BR, então o risco de quebrar com regex de string em inglês é real, não hipotético). Escritas continuam usando os `.exe`s, já que as flags de linha de comando são fixas (não traduzidas).
- **Bug descoberto e corrigido durante verificação manual**: `schtasks /Query /XML ONE` declara `encoding="UTF-16"` no prólogo do XML, mas os bytes capturados via pipe do `subprocess` são, na prática, UTF-8 — `ET.fromstring(bytes)` confiava na declaração errada e falhava o parse silenciosamente (o ajuste `compat_appraiser` aparecia como valor `None` no `boost list`). Corrigido decodificando `result.stdout` como UTF-8 para `str` antes de entregar ao `ElementTree` (string não carrega declaração de encoding, então o parser não tenta reinterpretar os bytes).
- **Nome real da tarefa agendada confirmado na máquina de dev**: `schtasks /Query /FO CSV` mostrou que a tarefa se chama `Microsoft Compatibility Appraiser Exp` nesta build do Windows 11 (sufixo "Exp" que não existe em builds mais antigas) — `catalog.py` usa o nome confirmado, com comentário explicando a origem.
- **Admin: falha clara, sem auto-elevação via UAC.** `manager.py` verifica `is_admin()` (reutilizando `backend/privileges.py` sem modificá-lo) e levanta `TweakError` pedindo para reabrir como Administrador, em vez de relançar o processo elevado. Mantém `--yes`/uso automatizado possível e evita prompt de elevação surpresa — coerente com o princípio "sem login/conta/telemetria" do projeto. Leituras (`get_current_value`, usado por `boost list`) nunca exigem admin — todas passam por `HKLM` (legível por qualquer usuário) ou consulta de tarefa.
- **Estado em JSON, não SQLite**: no máximo ~10-20 registros previstos no roadmap inteiro, escritor único, sem necessidade de joins/queries — um dict indexado por `tweak_id`, sem dependência nova. Escrita atômica (arquivo temporário + `os.replace`) evita corromper o estado numa queda no meio da escrita.
- **Reaplicar um ajuste já aplicado é rejeitado, nunca sobrescrito** — sobrescrever destruiria o `previous_value` original verdadeiro, tornando o undo inútil.
- **`previous_value: null` é significativo** (chave/valor não existia antes do `apply`) — `undo()` apaga o valor do registro nesse caso, em vez de escrever `null`.
- **Ordenação de `undo --all` via contador `_seq` interno**, não por `applied_at` (timestamp) — evita flakiness em caso de resolução de relógio baixa/empates; `_seq` incrementa a cada `save_applied` e é sempre monotônico dentro do processo.

### 3. Os 7 ajustes (`backend/tweaks/catalog.py`)

`power_plan` (Alto Desempenho, sem admin), `hibernation` (desativa hibernação, admin), `visual_effects` (melhor desempenho, sem admin), `telemetry` (minimiza telemetria, admin), `indexing` (desativa WSearch, admin), `sysmain` (desativa SysMain/Superfetch, admin), `compat_appraiser` (desativa tarefa de verificação de compatibilidade, admin). Tabela completa com mecanismo de leitura/escrita e valor capturado em [docs/funcionamento.md](docs/funcionamento.md).

### 4. `main.py`: `argparse` com subcomandos

- `boost clean [--dry-run] [--paths ...] [--yes] [--no-close]` — comportamento idêntico ao anterior, sem mudanças de UX.
- `boost list` — tabela com todos os ajustes, requisito de admin, valor atual e status (aplicado ou não).
- `boost apply <tweak_id>` / `boost undo <tweak_id>` / `boost undo --all`.
- **Retrocompatibilidade preservada**: `python main.py --dry-run -y` (sem palavra-chave de subcomando) continua funcionando exatamente como antes — `parse_args()` detecta que o primeiro argumento não é um subcomando conhecido e insere `clean` implicitamente.
- `main.py` continua sendo o único ponto de wiring entre `backend` e `frontend` (nenhuma mudança nesse princípio); a divisão em um pacote `cli/` fica adiada até haver 5-6+ `cmd_*` com lógica própria relevante (documentado em `CLAUDE.md`).

### 5. Novos componentes de frontend

- `frontend/components/tweak_list.py`: tabela `rich` para `boost list`.
- `frontend/components/tweak_result.py`: painéis de sucesso/erro para `apply`/`undo`, e listagem linha-a-linha para `undo --all`.
- Deliberadamente **não** reusam a cerimônia de `display_completion_screen` (espera de tecla + `WM_CLOSE` do terminal) — essa cerimônia foi desenhada para `clean` (clique duplo e fecha), enquanto `list`/`apply`/`undo` são pensados para rodar em sequência num terminal já aberto.
- `frontend/cli.py` ganhou `show_tweak_list`, `show_tweak_success`, `show_tweak_error`, `show_undo_all_results`, seguindo a mesma convenção de wrapper fino dos comandos existentes.

### 6. Nenhuma dependência nova

Todo o subsistema usa só biblioteca padrão: `subprocess`, `winreg`, `json`, `datetime`, `xml.etree.ElementTree`, `abc`, `os`, `tempfile`, `pathlib`. `requirements.txt`/`requirements-dev.txt` inalterados.

### 7. Testes (`tests/test_tweaks/`, `tests/test_main.py`)

Segue a convenção já estabelecida em `tests/test_cleaner.py`/`test_privileges.py`: funções pytest puras, `tmp_path` para estado em disco, `monkeypatch` para simular `winreg`/`subprocess.run` sem tocar o Windows real.

- `conftest.py`: `FakeWinReg` (registro em memória, chaveado por `(hive, path)`, com helpers `seed`/`has_value` para os testes) e `FakeSubprocessRun` (grava todas as chamadas, resposta scriptável via `returncode`/`stdout`).
- `test_base.py`: ABC não instanciável diretamente; subclasse incompleta não instanciável.
- `test_registry_value.py`, `test_services.py`, `test_scheduled_tasks.py`, `test_power_plan.py`, `test_hibernation.py`: leitura com chave/valor ausente, leitura com valor presente, `apply` escreve o valor alvo, `undo` restaura o valor anterior (incluindo o caso de apagar quando `previous_value is None`), falha limpa (`TweakError`) em `returncode != 0`.
- `test_catalog.py`: exatamente 7 ajustes, ids únicos, `get_tweak` de id desconhecido levanta `TweakError`.
- `test_state_store.py`: round-trip de `save_applied`/`get_applied`, segunda gravação sobrescreve sem duplicar, `clear_applied` remove, ordenação de `list_applied` mais-recente-primeiro.
- `test_manager.py`: usa um `StubTweak` (dublê, não os mecanismos reais) para isolar a lógica de coordenação — confirma que `get_current_value` é chamado antes de `apply` (a ordem que garante que o valor salvo é o original, não o já modificado), que o gate de admin bloqueia `apply`/`undo` **antes** de tocar no `Tweak` real, que reaplicar um id já aplicado é rejeitado sem alterar o registro original, que `undo` de um ajuste que requer admin sem elevação **mantém o registro** (permite retry), e que `undo_all` sobrevive a uma falha no meio do lote, na ordem mais-recente-primeiro.
- `test_main.py`: subcomando implícito `clean` quando não há palavra-chave, flags antigas continuam mapeando pra `clean`, cada subcomando novo resolve corretamente, `undo` sem id nem `--all` sai com erro via `parser.error`.

**72 testes, todos passando** (`pytest -v` → `72 passed`, incluindo os 13 testes pré-existentes de `test_cleaner.py`/`test_privileges.py`, inalterados).

### Verificação executada

- `pytest -v` — 72/72 passando.
- Verificação prévia ao código (read-only, na máquina real): `powercfg /list`, `reg query` nas 4 chaves de registro usadas, `schtasks /Query /FO CSV` para achar o nome real da tarefa de compatibilidade — revelou o sufixo "Exp" e evitou codar contra um caminho inexistente.
- `python main.py list` (não-admin) — mostra os 7 ajustes com valor atual correto (incluindo o bug do encoding UTF-16/UTF-8 do `compat_appraiser`, encontrado e corrigido nesta etapa).
- `python main.py apply visual_effects` → estado salvo em `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` com `previous_value: null`, `applied_value: 2`.
- `python main.py undo visual_effects` → registro do `winreg` (`VisualFXSetting`) apagado (confirmado via `reg query` retornando erro de "não encontrado", como esperado), registro de estado removido do JSON.
- `python main.py apply visual_effects` duas vezes seguidas → segunda chamada rejeitada com mensagem clara, sem sobrescrever `previous_value`.
- `python main.py apply hibernation` sem terminal elevado → falha limpa com mensagem pedindo Administrador, nenhum estado gravado.
- `python main.py undo --all` → desfez o único ajuste pendente (`visual_effects`), reportou `OK visual_effects`.
- `python main.py --dry-run -y` (sem subcomando) → confirma retrocompatibilidade, comportamento idêntico ao pré-existente.
- Máquina de desenvolvimento verificada limpa ao final: nenhum ajuste ficou aplicado, nenhuma chave de registro criada permaneceu.

### Documentação atualizada

- `docs/funcionamento.md`: nova seção "Ajustes Reversíveis" com diagrama de classes (`Tweak` e mecanismos), tabela dos 7 ajustes, schema do JSON de estado, diagrama de sequência de `apply`/`undo`, e a decisão de falha-clara para admin. Diagrama de arquitetura geral atualizado para incluir `backend/tweaks/`.
- `docs/README.md`: seção "How to Use" ganhou os novos subcomandos (`list`/`apply`/`undo`).
- `CLAUDE.md`: seção Architecture estendida com `backend/tweaks/` (abstração `Tweak`, decisões de locale-safety e admin hard-fail); nova seção "Roadmap" listando os 6 itens restantes do "System Boost" e seus módulos futuros (sem stubs criados); correção da linha desatualizada "No test suite... configured" (já não era verdade desde a suíte de testes anterior).

### Pendências / próximos passos sugeridos (fora do escopo deste commit)

- Itens 2-7 do roadmap (perfil "1 clique", monitor de recursos, análise de disco por categoria, inventário de drivers, debloat/startup, detecção de hardware) — módulos futuros já nomeados em `CLAUDE.md`, nenhum código criado ainda.
- Testes de UI dos novos componentes (`tweak_list.py`/`tweak_result.py`) — deliberadamente fora de escopo, seguindo o precedente já estabelecido para `frontend/components/*`.

---

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
