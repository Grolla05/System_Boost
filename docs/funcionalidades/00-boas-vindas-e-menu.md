# 00 — Boas-vindas e menu

[Funcionalidades](README.md) · Próximo: [01 — Níveis de otimização](01-niveis-de-otimizacao.md)

**Acesso:** `python main.py` ou `python main.py menu`
**Código:** `cmd_menu` em [main.py](../../main.py); [welcome.py](../../frontend/components/welcome.py); [level_menu.py](../../frontend/components/level_menu.py)
**Testes:** [tests/test_retro_ui.py](../../tests/test_retro_ui.py), [tests/test_main.py](../../tests/test_main.py), [tests/test_info_option.py](../../tests/test_info_option.py), [tests/test_undo_option.py](../../tests/test_undo_option.py)

---

## 1. Para que serve

É a porta de entrada: apresenta o programa e deixa escolher entre os quatro níveis, a ficha da máquina e o desfazer.

## 2. Como usar

1. Pressione qualquer tecla na tela de boas-vindas.
2. Navegue com `↑`/`↓` e confirme com `Enter`, ou tecle o número da opção.

```text
► [1] STAGE 1: LEVE (NORMAL)
  [2] STAGE 2: MEDIANA (BOOST)
  [3] STAGE 3: ALTA (TURBO BOOST)
  [4] STAGE 4: EXTREMA (HYPER DRIVE)
  [5] VER FICHA DA MÁQUINA
  [6] DESFAZER AJUSTES
[↑/↓] Navegar  [1-6] Direto  [P] Tema  [ENTER] Confirmar
```

## 3. Regras e casos especiais

| Situação | Resultado |
| --- | --- |
| `Esc` ou `Q` no menu | Sai sem executar nada |
| Opção 5 | Mostra a ficha e volta ao menu |
| Opção 6 | Abre o desfazer e volta ao menu |
| Recusar o briefing | Sai sem alterar nada |
| `ESC` no resumo final | Volta ao menu, sem repetir as boas-vindas |
| Outra tecla no resumo final | Encerra e fecha o terminal |
| `--level <id>` | Pula o menu naquela rodada; o briefing continua, salvo com `-y` |
| `-y` | Pula a espera de tecla e as confirmações, mas o menu abre se não houver `--level` |
| Entrada sem terminal interativo | O menu vira uma pergunta numérica |

## 4. Por dentro

1. `cmd_menu` mostra as boas-vindas e entra em um laço.
2. `display_level_menu` devolve um id de nível ou `INFO_CHOICE`, `UNDO_CHOICE`, `EXIT_CHOICE`.
3. Teclas pendentes são descartadas antes de cada leitura (`flush_input`), para que uma tecla antiga não pule uma tela.
4. A ficha é lida uma vez por sessão, porque a consulta leva alguns segundos.

## 5. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Números e setas | Quem conhece vai direto; quem explora navega |
| Sair sem executar como caminho fácil | Sair nunca deve alterar nada |
| Fechar o terminal ao final | O programa costuma ser aberto por atalho, em janela própria |
| `ESC` volta ao menu | Permite escolher outro nível na mesma sessão |

---

[Funcionalidades](README.md) · Próximo: [01 — Níveis de otimização](01-niveis-de-otimizacao.md)
