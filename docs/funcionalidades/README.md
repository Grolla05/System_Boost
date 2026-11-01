# Funcionalidades

← [Índice](../README.md)

Cada funcionalidade tem um documento próprio, de ponta a ponta. Todos seguem a mesma estrutura, para facilitar a leitura:

1. **Para que serve** — o objetivo, em linguagem simples.
2. **Como usar** — o caminho de quem usa.
3. **Regras e casos especiais** — o que acontece em cada situação.
4. **Por dentro** — os passos no código.
5. **Por que é assim** — as decisões e os motivos.
6. **Testes** — onde a funcionalidade é verificada.

**Tabela 1 — Funcionalidades**

| # | Funcionalidade | Onde acessar | Código principal |
| --- | --- | --- | --- |
| 00 | [Boas-vindas e menu](00-boas-vindas-e-menu.md) | `python main.py` | `level_menu.py`, `welcome.py` |
| 01 | [Níveis de otimização](01-niveis-de-otimizacao.md) | Opções 1 a 4, `--level` | `profiles.py` |
| 02 | [Limpeza de temporários](02-limpeza.md) | Níveis, `clean` | `cleaner.py` |
| 03 | [Ajustes reversíveis](03-ajustes-reversiveis.md) | Níveis, `list`, `apply` | `backend/tweaks/` |
| 04 | [Desfazer ajustes](04-desfazer.md) | Opção 6, `undo` | `tweaks/manager.py` |
| 05 | [Adaptação à máquina](05-adaptacao-a-maquina.md) | Automática nos níveis | `profiles.py` |
| 06 | [Ficha da máquina](06-ficha-da-maquina.md) | Opção 5, `info` | `hardware.py` |
| 07 | [Atualização de drivers](07-drivers.md) | Pergunta final, `--drivers` | `drivers.py`, `nvidia_driver.py` |
| 08 | [Ponto de restauração](08-ponto-de-restauracao.md) | Automático | `restore_point.py` |
| 09 | [Temas e sons](09-temas-e-sons.md) | Tecla `P`, `--palette`, `--no-sound` | `palettes.py`, `audio.py` |
| 10 | [Log de diagnóstico](10-log-de-diagnostico.md) | Automático | `logger.py` |
