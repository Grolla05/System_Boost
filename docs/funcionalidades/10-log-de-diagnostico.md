# 10 — Log de diagnóstico

← Anterior: [09 — Temas e sons](09-temas-e-sons.md) · [Funcionalidades](README.md)

**Acesso:** automático
**Código:** [backend/logger.py](../../backend/logger.py)
**Testes:** [tests/test_logger.py](../../tests/test_logger.py)

---

## 1. Para que serve

Registra em arquivo, passo a passo, o que cada execução fez, para investigar um problema depois. Ele é diferente do **mission log**, que aparece na tela e some ao sair.

## 2. Onde fica

| Execução | Arquivo |
| --- | --- |
| Executável | `%LOCALAPPDATA%\WinCleaner\logs\system_boost.log` |
| Código-fonte | `logs\system_boost.log`, na raiz do projeto |

O exe não grava ao lado de si porque `Program Files` é somente leitura.

## 3. Formato

```text
<data e hora> | INFO    | system_boost.tweaks.manager | apply 'telemetry': iniciando
```

Cada sessão começa com uma linha `SESSÃO INICIADA`, com versão do Python, sistema, Administrador, se é exe, PID e argumentos. O arquivo gira ao chegar a 1 MB, e até 5 cópias antigas ficam guardadas.

## 4. Regras e casos especiais

| Situação | Resultado |
| --- | --- |
| Pasta sem permissão de escrita | Log desligado, e o programa segue |
| `setup_logging` chamado de novo | Reaproveita o arquivo aberto |
| Erro não tratado | Traceback no log e na tela, que espera uma tecla antes de fechar |

## 5. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Nunca escreve no console | A tela é do `rich` |
| Nunca levanta exceção | Um log que falha não pode parar uma limpeza |
| Nível `DEBUG` no arquivo | Quem investiga precisa de detalhes; quem usa nem vê |

---

← Anterior: [09 — Temas e sons](09-temas-e-sons.md) · [Funcionalidades](README.md)
