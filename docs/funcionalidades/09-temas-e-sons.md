# 09 — Temas e sons

← Anterior: [08 — Ponto de restauração](08-ponto-de-restauracao.md) · [Funcionalidades](README.md) · Próximo: [10 — Log de diagnóstico](10-log-de-diagnostico.md)

**Acesso:** tecla `P` no menu, `--palette` e `--no-sound`
**Código:** [frontend/palettes.py](../../frontend/palettes.py), [frontend/audio.py](../../frontend/audio.py)
**Testes:** [tests/test_palettes.py](../../tests/test_palettes.py), [tests/test_audio.py](../../tests/test_audio.py), [tests/test_retro_ui.py](../../tests/test_retro_ui.py)

---

## 1. Para que serve

Dá ao programa a cara de um jogo de cartucho. É só aparência: nada aqui muda o que é feito no Windows.

## 2. Paletas

**Tabela 1 — Paletas disponíveis**

| Id | Nome | Estilo |
| --- | --- | --- |
| `dmg` | Game Boy Classic (DMG-01) | Verdes; é o padrão |
| `pocket` | Game Boy Pocket (Monochrome) | Tons de cinza |
| `arcade` | Cyber Arcade 80s (Neon) | Neon em ciano, rosa e amarelo |

A escolha fica salva em `%LOCALAPPDATA%\WinCleaner\ui_config.json` e vale nas próximas execuções.

```bash
python main.py menu --palette arcade
```

## 3. Sons

**Tabela 2 — Efeitos sonoros**

| Momento | Efeito |
| --- | --- |
| Boas-vindas | Som de início |
| Mover no menu | Blip curto |
| Selecionar | Dois tons |
| Fim da execução | Fanfarra |

Os tons usam `winsound.Beep` em uma thread separada, para nunca atrasar a interface. Para desligar:

```bash
python main.py menu --no-sound
```

A opção vale só para aquela execução.

## 4. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Cores só pelo tema | `--palette` vale para todas as telas |
| Falha de som ou de config é ignorada | Aparência nunca pode derrubar o programa |
| Sem arquivos de áudio | Tons gerados não pesam no exe |

---

← Anterior: [08 — Ponto de restauração](08-ponto-de-restauracao.md) · [Funcionalidades](README.md) · Próximo: [10 — Log de diagnóstico](10-log-de-diagnostico.md)
