<div align="center">

# System Boost

**Limpeza de temporários e ajustes reversíveis para o Windows — direto no terminal, com visual retrô 8-bit.**

[![CI](https://github.com/Grolla05/System_Boost/actions/workflows/ci.yml/badge.svg)](https://github.com/Grolla05/System_Boost/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Windows](https://img.shields.io/badge/plataforma-Windows%2010%2F11-blue)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

[**📖 Documentação**](docs/README.md) · [**🧭 Guia do usuário**](docs/02-guia-do-usuario.md) · [**🛠️ Como contribuir**](docs/09-contribuindo.md)

</div>

---

## 👋 Bem-vindo

O **System Boost** libera espaço em disco e reduz o que roda em segundo plano no Windows. Você escolhe um de quatro níveis, vê exatamente o que será feito e confirma. Todo ajuste guarda o valor anterior antes de mudar qualquer coisa e pode ser desfeito depois. Sem login, sem conta, sem licença e sem telemetria.

## ✨ Destaques

- **4 níveis guiados:** Leve, Mediana, Alta e Extrema, cada um somando limpeza e ajustes ao anterior
- **12 ajustes reversíveis:** desfaça um a um ou todos de uma vez, pelo menu ou pela linha de comando
- **Adaptação à máquina:** em HDD mantém SysMain e Prefetch; em notebook mantém hibernação e plano de energia
- **Prévia antes de agir:** o briefing lista cada app, serviço e tarefa que será alterado
- **Proteção de software crítico:** antivírus, drivers, VPN, bancos de dados, backup e licenças ficam de fora
- **Drivers com consentimento:** Windows Update e NVIDIA, um por um, só quando você autoriza
- **Ponto de restauração:** criado antes de uma execução alterar o sistema
- **Ficha da máquina:** Windows, CPU, RAM, GPU, disco e tipo, sem precisar de Administrador

> ⚠️ **Nem tudo volta.** Arquivos apagados e a Lixeira esvaziada não têm desfazer, e drivers instalados dependem do ponto de restauração. Veja [o que é e o que não é reversível](docs/01-visao-geral.md#6-o-que-o-programa-não-faz-limites-conhecidos).

## 🚀 Começar

**Usar a partir do código** (Windows 10/11 e Python 3.11+), em um terminal aberto como Administrador:

```bash
pip install -r requirements.txt
python main.py
```

**Gerar o instalador:** com o [Inno Setup 6](https://jrsoftware.org/isinfo.php) instalado, rode `python installer.py`. O resultado é `dist/System Boost Setup.exe`, que não exige Python na máquina de destino. O passo a passo está em [docs/05-build-e-ambiente.md](docs/05-build-e-ambiente.md).

## ⌨️ Comandos

| Comando | O que faz |
| --- | --- |
| `python main.py` | Abre o fluxo guiado |
| `python main.py menu -y --level mediana` | Roda um nível sem interação |
| `python main.py clean --dry-run` | Simula a limpeza, sem apagar nada |
| `python main.py info` | Mostra a ficha da máquina |
| `python main.py list` | Lista os ajustes e o estado de cada um |
| `python main.py apply <id>` | Aplica um ajuste |
| `python main.py undo <id>` | Desfaz um ajuste |
| `python main.py undo --all` | Desfaz todos os ajustes aplicados |

Todas as opções estão no [Guia do usuário](docs/02-guia-do-usuario.md).

## 🌐 Rede e privacidade

Limpeza e ajustes funcionam offline. Só a etapa de drivers, que precisa do seu consentimento, usa a rede: o Windows Update pelo Windows Update Agent e o serviço de consulta da NVIDIA com o pacote oficial do driver (cerca de 1 GB, com assinatura conferida antes de executar). O estado dos ajustes e os logs ficam em `%LOCALAPPDATA%\WinCleaner`, na sua máquina.

## 📚 Documentação

Toda a parte técnica está em [**docs/**](docs/README.md), escrita para qualquer leitor: [visão geral](docs/01-visao-geral.md), [funcionalidades](docs/funcionalidades/README.md), [arquitetura](docs/04-arquitetura.md), [módulos do código](docs/modulos/README.md), [testes](docs/06-testes.md) e [como contribuir](docs/09-contribuindo.md).

<div align="center">

Feito por [Felipe Grolla](https://github.com/Grolla05) · [Licença MIT](LICENSE)

</div>
