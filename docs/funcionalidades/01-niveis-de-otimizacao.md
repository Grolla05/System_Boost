# 01 — Níveis de otimização

← Anterior: [00 — Boas-vindas e menu](00-boas-vindas-e-menu.md) · [Funcionalidades](README.md) · Próximo: [02 — Limpeza de temporários](02-limpeza.md)

**Acesso:** opções 1 a 4 do menu ou `menu --level {leve,mediana,alta,extrema}`
**Código:** `LEVELS` em [backend/profiles.py](../../backend/profiles.py); `cmd_menu` em [main.py](../../main.py)
**Testes:** [tests/test_profiles.py](../../tests/test_profiles.py), [tests/test_preview_items.py](../../tests/test_preview_items.py)

---

## 1. Para que serve

Reúne limpeza e ajustes em quatro pacotes prontos, do mais leve ao mais agressivo, para ninguém precisar escolher item por item.

## 2. Como usar

Escolha o nível, leia o briefing e confirme. O briefing mostra:

- a distribuição de espaço por pasta;
- as pastas, caches e Lixeira que serão limpos;
- cada ajuste e, nos agregados, até 30 itens que serão alterados;
- o que será pulado por falta de Administrador;
- o que ficou fora nesta máquina, e por quê.

A execução segue esta ordem: ponto de restauração, limpeza, ajustes e, se autorizado, drivers.

## 3. O que cada nível faz

Cada nível inclui tudo o que os anteriores fazem. A Tabela 1 mostra só o que cada um acrescenta.

**Tabela 1 — Acréscimos por nível**

| Nível | Pastas | Caches e Lixeira | Ajustes |
| --- | --- | --- | --- |
| **Leve** | User Temp | Lixeira | `startup_apps`, `third_party_services`, `third_party_tasks` |
| **Mediana** | System Temp, SquirrelTemp, Gradle Cache, Go Build Cache, User Cache | npm, uv | `power_plan`, `recommendations_offers`, `mouse_acceleration`, `hibernation` |
| **Alta** | Prefetch | — | `visual_effects`, `indexing` |
| **Extrema** | — | — | `telemetry`, `sysmain`, `compat_appraiser` |

## 4. Regras e casos especiais

| Situação | Resultado |
| --- | --- |
| Sem Administrador | Pastas e ajustes que exigem admin são pulados; o resto roda |
| Ajuste já aplicado | Aparece como já aplicado, sem contar como falha |
| Ajuste agregado já aplicado | Trata só os itens novos |
| Um ajuste falha | Vira `[FAIL]` e os demais continuam |
| Ferramenta não instalada | npm ou uv aparece como `[SKIP]` |
| Máquina HDD ou notebook | Ver [Adaptação à máquina](05-adaptacao-a-maquina.md) |

## 5. Por dentro

1. `_extend()` constrói cada nível a partir do anterior, sem repetir itens.
2. `resolve_clean_paths()` filtra as pastas por Administrador, existência e máquina.
3. `resolve_tweak_plan()` separa o que será aplicado do que será pulado.
4. `preview_tweak_items()` monta a prévia dos agregados.
5. `apply_level_tweaks()` aplica ajuste por ajuste e emite eventos ao vivo para o mission log.

**Tabela 2 — Estados de um ajuste no nível**

| Estado | Significado | No log |
| --- | --- | --- |
| `True` | Aplicado | `[ OK ]` |
| `"already"` | Já estava aplicado | `[ OK ]` apagado |
| `False` | Falhou | `[FAIL]` |
| `None` | Pulado | `[SKIP]` |

## 6. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Níveis acumulativos | Fáceis de entender e de manter |
| Definição declarativa | Mudar um nível é mudar uma lista |
| Briefing obrigatório sem `-y` | Nada muda sem ser mostrado |

---

← Anterior: [00 — Boas-vindas e menu](00-boas-vindas-e-menu.md) · [Funcionalidades](README.md) · Próximo: [02 — Limpeza de temporários](02-limpeza.md)
