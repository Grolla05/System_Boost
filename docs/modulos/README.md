# Módulos do código-fonte

← [Arquitetura](../04-arquitetura.md) · [Índice](../README.md)

Cada área do código tem um documento próprio. Todos seguem a mesma estrutura, para facilitar a leitura:

1. **Resumo** — o que o módulo faz, em uma frase.
2. **Explicação para leigos** — uma analogia do dia a dia.
3. **Funções** — o que cada função principal recebe, faz e devolve.
4. **Detalhes** — os passos das partes mais importantes.
5. **Por que foi feito assim** — as decisões e os motivos.
6. **Testes** — onde o módulo é testado.

A Tabela 1 sugere a ordem de leitura, das bases para cima.

**Tabela 1 — Módulos, na ordem sugerida**

| Ordem | Módulo | Arquivos | Linhas aprox. | Depende de |
| --- | --- | --- | --- | --- |
| 1 | [Suporte](suporte.md) | `_powershell.py`, `_system.py`, `privileges.py`, `restore_point.py`, `logger.py` | 170 | — |
| 2 | [Hardware](hardware.md) | `hardware.py` | 220 | suporte |
| 3 | [Cleaner](cleaner.md) | `cleaner.py` | 310 | suporte |
| 4 | [Tweaks](tweaks.md) | `tweaks/` | 1525 | suporte |
| 5 | [Profiles](profiles.md) | `profiles.py` | 210 | cleaner, tweaks |
| 6 | [Drivers](drivers.md) | `drivers.py`, `nvidia_driver.py` | 445 | suporte, hardware |
| 7 | [Frontend](frontend.md) | `frontend/` | 1230 | todos acima, só para leitura |
| 8 | [Main](main.md) | `main.py` | 415 | todos acima |
