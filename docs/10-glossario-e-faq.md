# 10 — Glossário e FAQ

← Anterior: [09 — Contribuindo](09-contribuindo.md) · [Índice](README.md)

> Termos técnicos e perguntas frequentes. Explicações mais longas estão em [03 — Conceitos fundamentais](03-conceitos-fundamentais.md).

---

## 1. Glossário

| Termo | Significado |
| --- | --- |
| **Ajuste (tweak)** | Mudança de configuração do Windows que guarda o valor anterior |
| **Ajuste agregado** | Ajuste que trata vários itens: `startup_apps`, `third_party_services` e `third_party_tasks` |
| **Administrador** | Conta ou processo com permissão para alterar o sistema |
| **Authenticode** | Assinatura digital de executáveis no Windows |
| **Briefing** | Tela que mostra o que será feito antes da confirmação |
| **Cache** | Cópia guardada para evitar baixar ou calcular de novo |
| **CIM** | Interface do Windows para consultar dados de hardware e sistema |
| **Dry-run** | Simulação: mede sem apagar nada |
| **Driver** | Programa que faz o Windows falar com um hardware |
| **DWORD** | Tipo de número inteiro usado no registro |
| **Elevação** | Rodar um processo com poderes de Administrador |
| **Exceção** | Software que o filtro de terceiros nunca toca |
| **HDD / SSD** | Disco mecânico / disco de estado sólido |
| **Junção (junction)** | Pasta que aponta para outra; o programa nunca entra nela |
| **Mission log** | Lista ao vivo das etapas de uma execução |
| **Nível (stage)** | Conjunto predefinido de limpezas e ajustes |
| **Paleta** | Conjunto de cores da interface |
| **Ponto de restauração** | Foto do sistema feita pelo Windows |
| **Prefetch** | Dados que aceleram a abertura de programas |
| **Registro** | Banco de configurações do Windows |
| **Serviço** | Programa sem janela mantido pelo Windows |
| **Superfetch / SysMain** | Serviço que pré-carrega programas na memória |
| **Tarefa agendada** | Ação que o Windows roda em horários ou eventos |
| **Telemetria** | Dados de uso enviados à Microsoft |
| **UAC** | Aviso do Windows ao elevar um programa |
| **WHQL** | Certificação de drivers pela Microsoft |

## 2. Perguntas frequentes

### Uso

**Qual nível devo escolher?** Comece pelo **Leve**, depois suba se quiser mais. O **Extrema** desliga recursos do sistema, como a indexação de pesquisa e o SysMain.

**É seguro?** O programa protege software crítico, mostra tudo antes e permite desfazer os ajustes. Ainda assim, ele apaga arquivos e esvazia a Lixeira, e isso não tem volta. Leia o briefing.

**A Lixeira é esvaziada em qualquer nível?** Sim, a partir do Leve, em todas as unidades. Confira antes se há algo que você queira recuperar.

**O programa acelera o computador?** Ele reduz o que roda em segundo plano e libera espaço. O ganho depende da máquina, e o projeto não promete um número.

**Um programa parou de abrir com o Windows.** Provavelmente era um item de terceiros. Desfaça com `python main.py undo startup_apps`, ou reative só ele no Gerenciador de Tarefas.

**A busca do Windows ficou lenta.** O ajuste `indexing` desativa a indexação. Desfaça com `python main.py undo indexing`.

**Perdi a inicialização rápida.** Ela depende da hibernação. Desfaça com `python main.py undo hibernation`.

**O que acontece se eu rodar o mesmo nível de novo?** Ajustes comuns aparecem como já aplicados. Os agregados tratam só os itens novos.

### Problemas

**Por que alguns itens aparecem como `[SKIP]`?** Falta de Administrador, ferramenta não instalada ou ajuste inadequado à máquina. O motivo aparece ao lado.

**O ponto de restauração falhou.** Verifique se a Proteção do Sistema está ligada. A execução continua mesmo assim. Se outro ponto foi criado nas últimas 24 horas, o Windows ignora o pedido, e a mensagem cobre esse caso: *criado (ou já existe um recente)*.

**Apareceu "arquivo de ajustes está danificado".** O programa não sobrescreve o arquivo. Restaure `tweaks_state.json.bak` na pasta `%LOCALAPPDATA%\WinCleaner`, sobre o `tweaks_state.json`. Uma cópia do arquivo danificado fica em `tweaks_state.corrupt-*.json`.

**O UAC diz "Editor: Desconhecido".** O exe não está assinado. Ver [05 — Build e ambiente](05-build-e-ambiente.md#6-assinatura-e-o-editor-desconhecido).

**Onde vejo o que aconteceu em detalhe?** No [log de diagnóstico](funcionalidades/10-log-de-diagnostico.md).

### Sobre o projeto

**Por que `WinCleaner` aparece na pasta de dados?** É o nome antigo. Ver [D3](08-decisoes-de-projeto.md#d3--pasta-de-dados-com-o-nome-antigo).

**Funciona em Linux ou macOS?** Não. Ele existe para alterar o Windows.

**O programa envia dados?** Não. A rede só é usada na etapa de drivers, para consultar atualizações e baixá-las.

---

← Anterior: [09 — Contribuindo](09-contribuindo.md) · [Índice](README.md)
