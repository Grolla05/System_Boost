# Documentação do System Boost

Bem-vindo à documentação completa do **System Boost**, o utilitário de terminal que limpa arquivos temporários do Windows e aplica ajustes reversíveis. Ela foi escrita em **módulos**: cada arquivo trata de um assunto e pode ser lido sozinho, mas a ordem numérica conta a história do projeto do começo ao fim.

A documentação foi pensada para **qualquer leitor**, inclusive quem nunca programou. Sempre que um termo técnico aparece pela primeira vez, ele é explicado em linguagem do dia a dia; se esquecer algum, consulte o [Glossário e FAQ](10-glossario-e-faq.md).

> **Fonte da verdade:** o código em `backend/`, `frontend/` e `main.py`, junto com os testes em `tests/`. Se algo aqui divergir do código, o código vale, e esta documentação deve ser corrigida.

---

## Por onde começar

A Tabela 1 sugere trilhas de leitura conforme o seu objetivo.

**Tabela 1 — Trilhas de leitura**

| Quem é você | O que quer | Leia, nesta ordem |
| --- | --- | --- |
| Usuário | Instalar e usar o programa | [01](01-visao-geral.md) → [02](02-guia-do-usuario.md) → [10](10-glossario-e-faq.md) |
| Quem quer entender uma feature específica | Tudo sobre níveis, limpeza, desfazer... | [Funcionalidades](funcionalidades/README.md) → o arquivo da feature |
| Leigo curioso | Entender o que o programa muda no Windows | [01](01-visao-geral.md) → [03](03-conceitos-fundamentais.md) → [Ajustes reversíveis](funcionalidades/03-ajustes-reversiveis.md) |
| Desenvolvedor novo no projeto | Rodar, testar e alterar o código | [04](04-arquitetura.md) → [05](05-build-e-ambiente.md) → [06](06-testes.md) → [09](09-contribuindo.md) |
| Quem cuida de entregas | Gerar o exe e o instalador | [05](05-build-e-ambiente.md) → [07](07-ci-e-instalador.md) |

---

## Mapa dos módulos

### Parte I — Entender o produto

| # | Módulo | Do que trata |
| --- | --- | --- |
| 01 | [Visão geral](01-visao-geral.md) | O problema, o que o programa faz, princípios e limites |
| 02 | [Guia do usuário](02-guia-do-usuario.md) | Instalar, abrir e usar cada opção, passo a passo |
| — | [Funcionalidades](funcionalidades/README.md) | **Um documento por feature**, de ponta a ponta: uso, regras, código, porquês e testes |

As funcionalidades documentadas são:

| # | Funcionalidade | # | Funcionalidade |
| --- | --- | --- | --- |
| 00 | [Boas-vindas e menu](funcionalidades/00-boas-vindas-e-menu.md) | 06 | [Ficha da máquina](funcionalidades/06-ficha-da-maquina.md) |
| 01 | [Níveis de otimização](funcionalidades/01-niveis-de-otimizacao.md) | 07 | [Atualização de drivers](funcionalidades/07-drivers.md) |
| 02 | [Limpeza de temporários](funcionalidades/02-limpeza.md) | 08 | [Ponto de restauração](funcionalidades/08-ponto-de-restauracao.md) |
| 03 | [Ajustes reversíveis](funcionalidades/03-ajustes-reversiveis.md) | 09 | [Temas e sons](funcionalidades/09-temas-e-sons.md) |
| 04 | [Desfazer ajustes](funcionalidades/04-desfazer.md) | 10 | [Log de diagnóstico](funcionalidades/10-log-de-diagnostico.md) |
| 05 | [Adaptação à máquina](funcionalidades/05-adaptacao-a-maquina.md) | | |

### Parte II — Entender o código

| # | Módulo | Do que trata |
| --- | --- | --- |
| 03 | [Conceitos fundamentais](03-conceitos-fundamentais.md) | Temporários, registro, serviços, tarefas, UAC e drivers, explicados do zero |
| 04 | [Arquitetura](04-arquitetura.md) | Como o código está dividido, quem depende de quem e o caminho de uma execução |
| — | [Módulos do código-fonte](modulos/README.md) | Um documento por área do código: o que faz, como faz e por quê |

Os módulos do código-fonte são:

| Módulo | Arquivos | Papel |
| --- | --- | --- |
| [Main](modulos/main.md) | `main.py` | Linha de comando e orquestração de cada fluxo |
| [Cleaner](modulos/cleaner.md) | `backend/cleaner.py` | Medir e apagar com segurança |
| [Profiles](modulos/profiles.md) | `backend/profiles.py` | Os 4 níveis e a adaptação à máquina |
| [Tweaks](modulos/tweaks.md) | `backend/tweaks/` | Subsistema de ajustes reversíveis |
| [Drivers](modulos/drivers.md) | `backend/drivers.py`, `backend/nvidia_driver.py` | Windows Update e NVIDIA |
| [Hardware](modulos/hardware.md) | `backend/hardware.py` | Ficha da máquina |
| [Suporte](modulos/suporte.md) | `backend/_powershell.py`, `_system.py`, `privileges.py`, `restore_point.py`, `logger.py` | Peças pequenas usadas por todo o backend |
| [Frontend](modulos/frontend.md) | `frontend/` | Telas, temas e sons |

### Parte III — Construir, testar e entregar

| # | Módulo | Do que trata |
| --- | --- | --- |
| 05 | [Build e ambiente](05-build-e-ambiente.md) | Preparar o ambiente, rodar do código e gerar o exe e o instalador |
| 06 | [Testes](06-testes.md) | Suíte `pytest`, cobertura e como testar sem tocar no Windows |
| 07 | [CI e instalador](07-ci-e-instalador.md) | GitHub Actions, Inno Setup e versões |

### Parte IV — Contexto e manutenção

| # | Módulo | Do que trata |
| --- | --- | --- |
| 08 | [Decisões de projeto](08-decisoes-de-projeto.md) | O porquê de cada escolha importante e as alternativas descartadas |
| 09 | [Contribuindo](09-contribuindo.md) | Fluxo de trabalho, convenções e como adicionar um ajuste novo |
| 10 | [Glossário e FAQ](10-glossario-e-faq.md) | Termos técnicos e perguntas frequentes |

---

## Convenções desta documentação

- **Código e nomes de arquivo** aparecem em `fonte monoespaçada`, por exemplo `cleaner.py`.
- **Links para o código** apontam para o arquivo no repositório, por exemplo [backend/cleaner.py](../backend/cleaner.py).
- **Diagramas** usam [Mermaid](https://mermaid.js.org/), que o GitHub desenha automaticamente. Em outro visualizador, o texto do diagrama continua legível.
- **Tabelas e figuras** são numeradas dentro de cada módulo e sempre citadas no texto antes de aparecerem.
- Tudo em **português (pt-BR)**, como as mensagens do programa. O código e seus comentários estão em inglês.

## Outros documentos do repositório

| Documento | Para quê |
| --- | --- |
| [README.md](../README.md) | Cartão de boas-vindas do projeto |
| [CHANGES.md](../CHANGES.md) | Registro das mudanças, da mais recente para a mais antiga |
| [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md) | Guia de contribuição |
| [.github/COMMIT_CONVENTION.md](../.github/COMMIT_CONVENTION.md) | Padrão das mensagens de commit |
| [.github/SECURITY.md](../.github/SECURITY.md) | Como reportar problemas de segurança |
