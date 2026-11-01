# Módulo Profiles — os níveis de otimização

← Anterior: [Tweaks](tweaks.md) · [Módulos](README.md) · Próximo: [Drivers](drivers.md)

**Arquivo:** [backend/profiles.py](../../backend/profiles.py)
**Testes:** [tests/test_profiles.py](../../tests/test_profiles.py), [tests/test_preview_items.py](../../tests/test_preview_items.py)
**Funcionalidades:** [Níveis de otimização](../funcionalidades/01-niveis-de-otimizacao.md) · [Adaptação à máquina](../funcionalidades/05-adaptacao-a-maquina.md)

> **Resumo:** define os quatro níveis e decide o que cada um faz nesta máquina, com a elevação atual.

---

## 1. Explicação para leigos

É o **cardápio de combos**. Cada combo lista o que traz, e o garçom confere o que dá para servir hoje: se falta um ingrediente ou se o prato faria mal a este cliente, ele avisa e tira do pedido.

## 2. Estruturas

**Tabela 1 — Dados do módulo**

| Nome | Conteúdo |
| --- | --- |
| `LEVELS` | `id`, `label`, `description`, `clean_paths`, `clean_commands`, `tweak_ids` de cada nível |
| `LEVEL_ORDER` | `leve`, `mediana`, `alta`, `extrema` |
| `_UNSUITABLE` | Ajuste → `(regra, motivo)` |

## 3. Funções

**Tabela 2 — API do módulo**

| Função | Faz |
| --- | --- |
| `resolve_clean_paths(level_id, machine)` | Pastas do nível, filtradas por admin, existência e máquina |
| `resolve_tweak_plan(level_id, machine)` | `(aplicáveis, pulados por admin)`; os inadequados não entram em nenhuma lista |
| `machine_skips(tweak_ids, machine)` | `{id: motivo}` do que fica fora |
| `machine_notes(level_id, machine)` | Linhas para o briefing |
| `preview_tweak_items(tweak_ids)` | Itens que os agregados alterariam |
| `apply_level_tweaks(level_id, state_path, on_event, machine)` | Aplica e devolve `(id, status, nota)` |

## 4. Eventos de `apply_level_tweaks`

`on_event(tweak_id, status, note)` é chamado ao vivo: `"running"` antes de cada ajuste, depois o status final (`True`, `"already"`, `False` ou `None`) e um evento `"item"` para cada item alterado por um agregado. O `main.py` transforma esses eventos em linhas do mission log.

Erros inesperados também são capturados por ajuste, então um problema em um não impede os outros.

## 5. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| `_extend` monta o nível seguinte | Evita repetir listas |
| `machine=None` aceito | Sem ficha, nada é excluído |
| Sem chamadas de tela | O `main.py` decide como mostrar |

---

← Anterior: [Tweaks](tweaks.md) · [Módulos](README.md) · Próximo: [Drivers](drivers.md)
