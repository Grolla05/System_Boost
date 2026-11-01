# Módulo Frontend — telas, temas e sons

← Anterior: [Drivers](drivers.md) · [Módulos](README.md) · Próximo: [Main](main.md)

**Pasta:** [frontend/](../../frontend/)
**Testes:** [test_retro_ui.py](../../tests/test_retro_ui.py), [test_live_log.py](../../tests/test_live_log.py), [test_level_completion.py](../../tests/test_level_completion.py), [test_palettes.py](../../tests/test_palettes.py), [test_audio.py](../../tests/test_audio.py), [test_terminal.py](../../tests/test_terminal.py)
**Funcionalidades:** [Boas-vindas e menu](../funcionalidades/00-boas-vindas-e-menu.md) · [Temas e sons](../funcionalidades/09-temas-e-sons.md)

> **Resumo:** interface retrô 8-bit feita com `rich`. Cada tela é um componente, e `cli.py` é o único ponto de contato com o `main.py`.

---

## 1. Explicação para leigos

É o **painel do fliperama**: mostra pontuação, botões e luzes, mas quem faz o jogo funcionar está por trás dele.

## 2. Arquivos

**Tabela 1 — Componentes**

| Arquivo | Papel |
| --- | --- |
| `cli.py` | Cria o `Console` com o tema e expõe as funções `show_*` |
| `palettes.py` | Paletas, tema ativo e persistência da escolha |
| `audio.py` | Sons por `winsound.Beep`, em thread separada |
| `components/_terminal.py` | Ler tecla, limpar a tela e fechar o terminal |
| `components/welcome.py` | Tela de boas-vindas |
| `components/level_menu.py` | Menu, briefing e confirmações |
| `components/disk_breakdown.py` | Distribuição de espaço antes de limpar |
| `components/live_log.py` | `MissionLog` |
| `components/level_completion.py` | Resumo de um nível |
| `components/completion.py` | Resumo do `clean` |
| `components/driver_progress.py` | Texto do resumo de drivers |
| `components/machine_info.py` | Tabela da ficha |
| `components/tweak_list.py`, `tweak_result.py` | Saída de `list`, `apply` e `undo` |
| `components/undo_menu.py` | Confirmação e resultado do desfazer |

## 3. `MissionLog`

É um gerenciador de contexto que desenha o log ao vivo com `rich.Live`.

**Tabela 2 — API do `MissionLog`**

| Método | Faz |
| --- | --- |
| `start(key, text)` | Abre uma etapa em andamento |
| `finish(key, status, note, text)` | Define o estado final; cria a linha se ela não existir |
| `item(text, status, note)` | Acrescenta uma sublinha recuada |
| `is_running(key)` | Diz se a etapa segue em andamento |

Quando o log não cabe na tela, só as linhas mais novas aparecem, com um aviso de quantas ficaram ocultas. Ao final, o log completo é impresso acima do resumo. Se uma exceção interromper a execução, as etapas abertas viram `fail`, com a nota *interrompido*.

## 4. Fechar o terminal

Depois da última tecla, `_close_terminal` obtém a janela com `GetConsoleWindow` e envia `WM_CLOSE` por `PostMessageW`. Isso não acontece em `--dry-run`, com `--no-close` ou com `-y`.

## 5. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| `cli.py` como ponte | `main.py` não depende de cada componente |
| `clear_screen` próprio | `console.clear()` só reposiciona o cursor em alguns consoles do Windows |
| Tamanhos medidos em `try` | Uma falha na prévia não pode impedir o briefing |
| `flush_input` antes de ler | Uma tecla antiga não pula uma tela |

---

← Anterior: [Drivers](drivers.md) · [Módulos](README.md) · Próximo: [Main](main.md)
