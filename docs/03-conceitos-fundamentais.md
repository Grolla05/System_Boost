# 03 — Conceitos fundamentais

← Anterior: [02 — Guia do usuário](02-guia-do-usuario.md) · [Índice](README.md) · Próximo: [04 — Arquitetura](04-arquitetura.md)

> O que o System Boost mexe dentro do Windows, explicado do zero. Quem nunca abriu o Editor do Registro consegue acompanhar.

---

## 1. Arquivos temporários e caches

Um **arquivo temporário** é um rascunho: um programa cria, usa e deveria apagar. Muitos ficam para trás. Um **cache** é uma cópia guardada para não baixar ou calcular de novo. Apagar um cache é seguro, mas a próxima execução da ferramenta fica mais lenta enquanto ele é refeito.

| Pasta | O que guarda |
| --- | --- |
| **User Temp** (`%TEMP%`) | Rascunhos dos programas do usuário |
| **System Temp** (`C:\Windows\Temp`) | Rascunhos do sistema; exige Administrador |
| **Prefetch** (`C:\Windows\Prefetch`) | Dados que o Windows usa para abrir programas mais rápido; recriados sozinhos; exige Administrador |
| **SquirrelTemp** | Sobras de instaladores de apps feitos com Squirrel |
| **Gradle Cache**, **Go Build Cache** | Caches de compilação |
| **User Cache** (`~/.cache`) | Caches de várias ferramentas |
| **npm cache**, **uv cache** | Pacotes baixados por essas ferramentas |

**Prefetch** merece um cuidado: apagá-lo pode deixar o próximo boot mais lento, porque o Windows precisa reconstruí-lo. Em HDD, onde ele mais ajuda, os níveis não o limpam.

## 2. O registro do Windows

O **registro** é um grande armário de configurações. Cada **chave** é uma gaveta (como uma pasta) e cada **valor** é uma ficha dentro dela, com nome e conteúdo. `HKCU` guarda o que é do usuário atual; `HKLM` guarda o que vale para a máquina inteira e exige Administrador para alterar.

Quase todo ajuste do programa se resume a mudar uma ficha. Quando a ficha não existia, o desfazer a remove, em vez de deixar um valor inventado no lugar.

## 3. Serviços

Um **serviço** é um programa sem janela que o Windows mantém rodando. O **tipo de início** diz quando ele sobe:

| Tipo | Significado |
| --- | --- |
| `auto` | Sobe com o Windows |
| `delayed-auto` | Sobe com o Windows, um pouco depois |
| `demand` | Manual: sobe só quando alguém pede |
| `disabled` | Não sobe |

Serviços de terceiros passam para `demand`, e não para `disabled`, para que o programa dono ainda consiga iniciá-los quando precisar.

## 4. Tarefas agendadas

O **Agendador de Tarefas** roda ações em horários ou eventos, como "verificar atualização a cada hora". As tarefas do próprio Windows ficam em `\Microsoft\`; as demais são consideradas candidatas a terceiros.

## 5. Inicialização de programas

Programas podem pedir para abrir com o Windows de duas formas: uma entrada em uma chave `Run` do registro ou um atalho na pasta Inicializar. O Gerenciador de Tarefas lista esses itens e guarda a escolha do usuário em `StartupApproved`, uma chave à parte. O System Boost usa esse mesmo mecanismo: marca o item como desativado, sem apagar nada.

## 6. Administrador e UAC

No Windows, até uma conta de administrador roda programas com poderes limitados. Para fazer mudanças no sistema, o programa precisa ser **elevado**, e o aviso que aparece na tela é o **UAC** (Controle de Conta de Usuário). Um executável pode declarar no seu **manifesto** que sempre precisa de elevação, que é o caso do `System Boost.exe`.

Um processo elevado merece cuidado extra: se ele chamar `sc` pelo nome curto, o Windows pode encontrar um arquivo com esse nome em outra pasta e executá-lo com poderes totais. Por isso o programa sempre usa o caminho completo das ferramentas do sistema.

## 7. Ponto de restauração

Um **ponto de restauração** é uma foto de configurações, drivers e arquivos de sistema, feita pelo próprio Windows. Ele permite voltar o sistema a um estado anterior. Não cobre documentos pessoais, depende da **Proteção do Sistema** estar ligada e o Windows ignora o pedido se outro ponto tiver sido criado nas últimas 24 horas.

## 8. Drivers

Um **driver** é o programa que ensina o Windows a falar com uma peça de hardware. O Windows Update oferece atualizações para vários deles, mas os drivers de GPU NVIDIA costumam chegar lá mais tarde, e por isso têm uma etapa própria.

Dois termos aparecem nessa etapa:

- **Game Ready WHQL:** linha de drivers da NVIDIA para jogos, certificada pela Microsoft.
- **Assinatura Authenticode:** selo criptográfico que prova quem publicou um executável e que ele não foi alterado depois.

## 9. Hibernação e `hiberfil.sys`

Ao hibernar, o Windows salva a memória no arquivo `hiberfil.sys`, que pode ocupar vários gigabytes. Desativar a hibernação remove esse arquivo, mas também desliga a **inicialização rápida**, que depende dele. Em notebook isso costuma fazer falta, e os níveis mantêm a hibernação ligada.

## 10. Reversível de verdade

Um ajuste é reversível quando três coisas acontecem nesta ordem:

1. Ler o valor atual.
2. Gravar esse valor em disco.
3. Só então alterar o Windows.

Se o programa cair entre os passos 2 e 3, o registro continua lá e o desfazer funciona. Inverter a ordem poderia perder o valor original para sempre. Essa é a ideia central do [subsistema de ajustes](modulos/tweaks.md).

---

← Anterior: [02 — Guia do usuário](02-guia-do-usuario.md) · [Índice](README.md) · Próximo: [04 — Arquitetura](04-arquitetura.md)
