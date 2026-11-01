# 05 — Adaptação à máquina

← Anterior: [04 — Desfazer ajustes](04-desfazer.md) · [Funcionalidades](README.md) · Próximo: [06 — Ficha da máquina](06-ficha-da-maquina.md)

**Acesso:** automática nos níveis
**Código:** `_UNSUITABLE`, `machine_skips` e `machine_notes` em [backend/profiles.py](../../backend/profiles.py)
**Testes:** [tests/test_profiles.py](../../tests/test_profiles.py), [tests/test_undo_option.py](../../tests/test_undo_option.py)

---

## 1. Para que serve

Evita aplicar o que prejudicaria esta máquina em particular. Um ajuste bom para um desktop com SSD pode piorar um notebook ou um computador com HDD.

## 2. Regras

**Tabela 1 — O que fica de fora**

| Máquina | Fica de fora | Motivo |
| --- | --- | --- |
| Disco HDD | `sysmain` | O disco mecânico se beneficia do SysMain |
| Disco HDD | Limpeza do Prefetch | O disco se beneficia dele no boot |
| Notebook | `hibernation` | Notebooks usam hibernação |
| Notebook | `power_plan` | Gastaria mais bateria |

O briefing lista o que ficou de fora em *Fora deste nível nesta máquina*, e o mission log mostra essas linhas como `[SKIP]`.

## 3. Casos especiais

| Situação | Resultado |
| --- | --- |
| Tipo de disco ou de máquina desconhecido | Nada é excluído |
| `apply <id>` direto | Aplica mesmo assim: o pedido é explícito |
| Comando `clean` | Não usa esta adaptação |

## 4. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Desconhecido não exclui | Um dado ausente não deve mudar o nível em silêncio |
| Explicar no briefing | Quem usa precisa saber o que não foi feito |
| Regra como tabela | Acrescentar um caso é acrescentar uma linha |

---

← Anterior: [04 — Desfazer ajustes](04-desfazer.md) · [Funcionalidades](README.md) · Próximo: [06 — Ficha da máquina](06-ficha-da-maquina.md)
