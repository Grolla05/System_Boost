# 08 — Ponto de restauração

← Anterior: [07 — Atualização de drivers](07-drivers.md) · [Funcionalidades](README.md) · Próximo: [09 — Temas e sons](09-temas-e-sons.md)

**Acesso:** automático antes de um nível ou de um `clean` real
**Código:** [backend/restore_point.py](../../backend/restore_point.py); `_restore_point_step` em [main.py](../../main.py)
**Testes:** [tests/test_restore_point.py](../../tests/test_restore_point.py)

---

## 1. Para que serve

Pede ao Windows uma foto do sistema antes de a execução mudar qualquer coisa. É a rede de segurança para o que não tem desfazer próprio, como drivers.

## 2. Regras e casos especiais

| Situação | Mission log | Execução |
| --- | --- | --- |
| Ponto criado | `[ OK ]` *criado (ou já existe um recente)* | Continua |
| Outro ponto nas últimas 24 h | `[ OK ]`, igual: o Windows ignora o pedido em silêncio | Continua |
| Sem Administrador | `[ !! ]` *requer administrador* | Continua |
| Proteção do Sistema desligada ou erro | `[ !! ]` *não criado; verifique a Proteção do Sistema* | Continua |
| `--dry-run` | Etapa não aparece | Nada é alterado |
| `apply` e `undo` | Etapa não existe | Têm desfazer próprio |

## 3. Por dentro

`create_restore_point()` executa `Checkpoint-Computer` por PowerShell, com tipo `MODIFY_SETTINGS` e limite de 300 segundos, e devolve `(ok, nota)` sem nunca levantar exceção.

## 4. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Falha não para a execução | A proteção pode estar desligada, e os ajustes têm desfazer próprio |
| Aviso visível | Quem usa precisa saber que está sem essa rede |
| Mensagem cobre o caso das 24 h | O Windows não informa se criou de fato |

---

← Anterior: [07 — Atualização de drivers](07-drivers.md) · [Funcionalidades](README.md) · Próximo: [09 — Temas e sons](09-temas-e-sons.md)
