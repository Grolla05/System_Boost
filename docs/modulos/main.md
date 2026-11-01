# Módulo Main — linha de comando e orquestração

← Anterior: [Frontend](frontend.md) · [Módulos](README.md)

**Arquivo:** [main.py](../../main.py)
**Testes:** [tests/test_main.py](../../tests/test_main.py), [tests/test_info_option.py](../../tests/test_info_option.py), [tests/test_undo_option.py](../../tests/test_undo_option.py)

> **Resumo:** interpreta os argumentos, chama o fluxo certo e liga os eventos do backend às telas.

---

## 1. Explicação para leigos

É o **maestro**: não toca nenhum instrumento, mas diz quem entra e quando.

## 2. Funções

**Tabela 1 — Funções do módulo**

| Função | Faz |
| --- | --- |
| `parse_args(argv)` | Monta os subcomandos; sem argumentos, assume `menu` |
| `cmd_menu`, `cmd_clean`, `cmd_list`, `cmd_info`, `cmd_apply`, `cmd_undo` | Um fluxo por comando |
| `_clean_with_log` | Roda limpezas por comando e por pasta, com uma linha por item |
| `_wants_drivers` | Decide se a etapa de drivers roda |
| `_restore_point_step` | Cria o ponto de restauração e registra no log |
| `_run_driver_step`, `_update_drivers_logged` | Liga `update_all_drivers` ao mission log |
| `_tweak_event_handler` | Liga `apply_level_tweaks` ao mission log |
| `_run_undo_flow` | Opção 6 do menu |
| `main()` | Liga o log, aplica opções de tela e despacha |
| `run_guarded()` | Trata interrupção e erro não previsto |

## 3. Regras da linha de comando

- Sem argumentos: `menu`.
- Só `--dry-run` pode omitir o subcomando, e vira `clean`: uma simulação não apaga nada.
- `undo` exige um id ou `--all`.
- `apply`, `undo <id>` e `undo --all` com falha terminam com código 1.

## 4. Tratamento de erros

**Tabela 2 — Onde cada erro para**

| Erro | Tratamento |
| --- | --- |
| Falha de uma pasta ou de um ajuste | Linha `[FAIL]`; continua |
| `StateCorruptError` | Mensagem clara, espera uma tecla e sai com código 1 |
| `TweakError` em `apply` ou `undo` | Painel de erro e código 1 |
| `Ctrl+C` | Mensagem e saída com código 0 |
| Qualquer outro erro | Traceback, log e espera por uma tecla |

A espera por tecla existe para a janela não sumir quando o programa foi aberto com um duplo clique.

## 5. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| Tabela `_DISPATCH` | Acrescentar um comando é acrescentar uma linha |
| Ficha lida sob demanda | A consulta leva alguns segundos |
| `-y` não implica drivers | Ver [D15](../08-decisoes-de-projeto.md#d15--drivers-exigem-consentimento-próprio) |

---

← Anterior: [Frontend](frontend.md) · [Módulos](README.md)
