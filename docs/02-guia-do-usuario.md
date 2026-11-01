# 02 — Guia do usuário

← Anterior: [01 — Visão geral](01-visao-geral.md) · [Índice](README.md) · Próximo: [03 — Conceitos fundamentais](03-conceitos-fundamentais.md)

> Como instalar, abrir e usar o System Boost, opção por opção. Não é preciso saber programar.

---

## 1. Instalar

### Pelo instalador

Execute `System Boost Setup.exe`. Ele pede Administrador, instala em `Program Files`, remove uma cópia antiga por usuário (se houver), cria atalhos no menu Iniciar e na área de trabalho e registra o desinstalador. Python e dependências já vêm dentro do executável.

Ainda não há versão publicada na página de Releases do GitHub. Para obter o instalador, gere-o seguindo [05 — Build e ambiente](05-build-e-ambiente.md).

### Pelo código-fonte

Com Python 3.11 ou superior:

```bash
pip install -r requirements.txt
python main.py
```

## 2. Administrador ou não?

O executável sempre pede elevação ao abrir (aviso do UAC). Pelo código-fonte, abra o terminal como Administrador por conta própria. A Tabela 1 mostra o que muda sem elevação.

**Tabela 1 — O que muda sem Administrador**

| Item | Sem Administrador |
| --- | --- |
| `C:\Windows\Temp` e Prefetch | Ficam de fora da limpeza |
| Ajustes que exigem admin | Pulados no nível; falham com mensagem em `apply` e `undo` |
| `startup_apps` | Trata só os itens do usuário atual |
| Ponto de restauração | Não é criado; o log mostra um aviso |
| Drivers | Etapa pulada |
| Ficha da máquina | Funciona normalmente |

## 3. Fluxo guiado

Rode sem argumentos:

```bash
python main.py
```

1. **Boas-vindas:** pressione qualquer tecla.
2. **Menu:** escolha uma opção. A Tabela 2 mostra as teclas.
3. **Briefing:** confira espaço identificado, pastas, ajustes e itens de terceiros, e confirme em *Iniciar missão?*.
4. **Drivers:** responda se quer atualizar drivers também. O padrão é **não**.
5. **Mission log:** acompanhe cada etapa.
6. **Resumo:** veja o espaço liberado e o resultado dos ajustes. **ESC** volta ao menu; qualquer outra tecla encerra e fecha o terminal.

**Tabela 2 — Teclas do menu**

| Tecla | Ação |
| --- | --- |
| `↑` / `↓` | Move a seleção |
| `Enter` | Confirma a opção selecionada |
| `1` a `6` | Escolhe a opção direto |
| `P` | Troca a paleta de cores |
| `Esc` ou `Q` | Sai sem executar nada |

As opções 1 a 4 são os níveis. A opção **5** mostra a ficha da máquina e a opção **6** desfaz os ajustes aplicados.

Um exemplo de mission log sem Administrador, com valores ilustrativos:

```text
MISSION LOG // STAGE: LEVE
[ !! ] Criando ponto de restauração  — requer administrador
[ OK ] Limpando Lixeira  — 120.50 MB liberados
[ OK ] Limpando User Temp  — 1.32 GB liberados
[ OK ] Apps de terceiros na inicialização: desativar  — 2 item(ns)
         └ Spotify
         └ Discord
[SKIP] Serviços de terceiros: iniciar só sob demanda  — requer administrador
[SKIP] Tarefas agendadas de terceiros: desativar  — requer administrador
```

**Tabela 3 — Marcas do mission log**

| Marca | Significado |
| --- | --- |
| `[ OK ]` | Concluído (em cor apagada: já estava aplicado) |
| `[FAIL]` | Falhou; o motivo aparece ao lado |
| `[SKIP]` | Pulado: falta de Administrador, ferramenta ausente ou inadequado à máquina |
| `[ !! ]` | Aviso; a execução continua |

## 4. Opções da linha de comando

**Tabela 4 — Comandos e opções**

| Comando | Opção | Efeito |
| --- | --- | --- |
| `menu` | `-y`, `--yes` | Pula as confirmações |
| | `--level {leve,mediana,alta,extrema}` | Roda o nível sem abrir o menu |
| | `--drivers` / `--no-drivers` | Atualiza drivers sem perguntar / não atualiza |
| | `--no-sound` | Desliga os sons |
| | `-p`, `--palette {dmg,pocket,arcade}` | Escolhe a paleta |
| `clean` | `-n`, `--dry-run` | Simula, sem apagar nada |
| | `--paths ...` | Restringe a pastas específicas |
| | `-y`, `--yes` | Pula as confirmações |
| | `--no-close` | Não fecha o terminal ao final |
| | `--drivers` / `--no-drivers`, `--no-sound`, `-p` | Iguais aos do `menu` |
| `info` | | Mostra a ficha da máquina |
| `list` | | Lista os ajustes e o estado de cada um |
| `apply` | `<tweak_id>` | Aplica um ajuste |
| `undo` | `<tweak_id>` ou `--all` | Desfaz um ajuste ou todos |

Sem subcomando, só `--dry-run` é aceito, e equivale a `clean --dry-run`. Pelo executável, troque `python main.py` por `"System Boost.exe"`.

> **`-y` não instala drivers.** Para isso é preciso `--drivers` junto. Uma execução com `-y` não abre as confirmações, então use-a só quando já souber o que o nível faz.

## 5. Receitas

```bash
python main.py clean --dry-run                          # quanto eu recuperaria?
python main.py clean --paths "User Temp" "System Temp"  # só estas pastas
python main.py clean --dry-run -y                       # simula e lista drivers pendentes
python main.py menu -y --level mediana                  # nível sem interação
python main.py menu --no-drivers                        # fluxo guiado sem drivers
python main.py clean -y --drivers                       # limpeza e drivers sem interação
```

Os nomes aceitos em `--paths` são `User Temp`, `System Temp`, `Prefetch`, `SquirrelTemp`, `Gradle Cache`, `Go Build Cache` e `User Cache`.

> **`clean` não é igual a um nível.** Ele limpa só pastas: não esvazia a Lixeira, não limpa os caches do npm e do uv, não aplica ajustes e não adapta a limpeza à máquina. Sem `--paths`, inclui todas as pastas permitidas, até o Prefetch em HDD.

## 6. Ajustes um a um

```bash
python main.py list               # todos os ajustes e o estado de cada um
python main.py apply telemetry    # aplica, salvando o valor anterior
python main.py undo telemetry     # restaura o valor anterior
python main.py undo --all         # desfaz tudo, do mais recente ao mais antigo
```

A lista completa de ids está em [Ajustes reversíveis](funcionalidades/03-ajustes-reversiveis.md).

## 7. Desinstalar

Use **Configurações → Aplicativos** do Windows. Se houver ajustes salvos, o desinstalador pergunta se deve desfazê-los antes de remover os arquivos. Responda **sim**: depois de removido, o programa não pode mais restaurar os valores. Em desinstalação silenciosa, essa pergunta não aparece.

## 8. Onde ficam os dados

**Tabela 5 — Arquivos do programa**

| Arquivo | Para quê |
| --- | --- |
| `%LOCALAPPDATA%\WinCleaner\tweaks_state.json` | Valores salvos para o desfazer (mais uma cópia `.bak`) |
| `%LOCALAPPDATA%\WinCleaner\ui_config.json` | Paleta escolhida |
| `%LOCALAPPDATA%\WinCleaner\logs\system_boost.log` | Log de diagnóstico do executável |
| `logs\system_boost.log` | Log de diagnóstico ao rodar pelo código-fonte |

---

← Anterior: [01 — Visão geral](01-visao-geral.md) · [Índice](README.md) · Próximo: [03 — Conceitos fundamentais](03-conceitos-fundamentais.md)
