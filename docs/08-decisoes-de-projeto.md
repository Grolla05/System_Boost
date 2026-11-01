# 08 — Decisões de projeto

← Anterior: [07 — CI e instalador](07-ci-e-instalador.md) · [Índice](README.md) · Próximo: [09 — Contribuindo](09-contribuindo.md)

> Este módulo reúne **o porquê** das escolhas importantes, no formato de registros de decisão: contexto, decisão, alternativas e consequências. Serve para quem quer entender o projeto e para quem precisa mudar algo sem desfazer uma escolha consciente.

---

## D1 — Backend sem interface

- **Decisão:** `backend/` não imprime nem lê teclas. Eventos chegam ao `frontend` por retornos e callbacks.
- **Consequências:** módulos testáveis isoladamente; `main.py` liga cada callback ao mission log.

## D2 — Classe abstrata, organizada por mecanismo

- **Contexto:** o resto do backend usa funções, mas os 12 ajustes falam com o Windows de formas bem diferentes.
- **Decisão:** classe abstrata `Tweak`, com uma subclasse por **mecanismo**, não por ajuste. `RegistryValueTweak` atende `visual_effects` e `telemetry`; `ServiceStateTweak` atende `indexing` e `sysmain`.
- **Por quê:** uma subclasse que esquecer `undo()` falha ao ser instanciada, e não na hora em que o usuário mais precisa do desfazer.

## D3 — Pasta de dados com o nome antigo

- **Contexto:** o projeto se chamava WinCleaner.
- **Decisão:** manter `%LOCALAPPDATA%\WinCleaner`.
- **Alternativa:** migrar para uma pasta nova, com risco de perder o histórico de desfazer.
- **Consequências:** um nome antigo fica visível, em troca de instalações existentes continuarem funcionando.

## D4 — Ler pelo registro, escrever pelas ferramentas

- **Contexto:** a saída de `sc.exe`, `schtasks.exe` e `powercfg.exe` é traduzida para o idioma do Windows, e a interface é pt-BR.
- **Decisão:** leituras via `winreg` sempre que possível; escritas pelos `.exe`, cujas opções não são traduzidas.
- **Detalhe:** `schtasks /XML` declara `UTF-16`, mas os bytes capturados pelo pipe são UTF-8. `scheduled_tasks.py` decodifica antes de passar o texto ao parser.

## D5 — Estado em JSON, à prova de queda

- **Decisão:** um registro por ajuste, com escrita atômica (arquivo temporário + `os.replace`) e cópia `.bak`. O registro nasce `pending` antes de `apply()`.
- **Regra:** arquivo danificado nunca é sobrescrito: gera `StateCorruptError`, uma cópia `.corrupt-*` e bloqueia a escrita.
- **Por quê:** perder esse arquivo significa perder os valores originais.

## D6 — Reaplicar não sobrescreve

- **Contexto:** reaplicar um ajuste sobrescreveria o valor original com o valor já alterado.
- **Decisão:** reaplicar é rejeitado com `TweakAlreadyApplied`. A exceção são os três ajustes agregados: tratam só os itens novos e os somam ao registro, gravando antes de `apply()`.
- **Consequências:** rodar um nível de novo pega o que foi instalado desde a última vez, e o `undo` cobre esses itens.

## D7 — Sem autoelevação pelo código

- **Decisão:** o `manager` falha com mensagem clara em vez de relançar o processo. Só o exe pede elevação, pelo manifesto.
- **Por quê:** mantém `--yes` e o uso automatizado viáveis, e evita um aviso de elevação inesperado no meio de uma execução.

## D8 — Caminhos absolutos e nada do `PATH`

- **Contexto:** o processo costuma rodar elevado.
- **Decisão:** `system_exe()` pede a pasta System32 ao Windows, sem confiar em `%SystemRoot%`. Os caches do npm e do uv são limpos pela pasta, sem executar essas ferramentas.
- **Por quê:** um `sc.exe` ou `npm` plantado na pasta atual ou no `PATH` herdaria a elevação.

## D9 — Serviços de terceiros em manual

- **Decisão:** `demand`, não `disabled`.
- **Por quê:** o programa dono ainda consegue iniciar o serviço quando precisar. Serviços em `delayed-auto` voltam a esse modo no desfazer.

## D10 — Inicialização pelo `StartupApproved`

- **Decisão:** usar o mesmo mecanismo da aba Inicializar do Gerenciador de Tarefas.
- **Alternativa:** apagar as entradas `Run` e os atalhos.
- **Consequências:** nada é apagado; o desfazer restaura os bytes exatos. O item continua visível para o usuário reativar no Windows.

## D11 — Filtro por exceções, em lista única

- **Decisão:** um item só é tocado se for claramente de terceiros e não casar com a lista de exceções. Comando vazio significa dono desconhecido, e o item fica intacto. Startup, serviços e tarefas usam a mesma lista.
- **Regra de casamento:** o nome só casa no início de uma palavra (`amd` protege `amdrsserv`, não `ramdisk`); `vpn`, `update` e `trendmicro` casam em qualquer ponto. A pasta do usuário fica fora da busca (`hp` não casa `Hpereira`).
- **Consequências:** na dúvida, preserva. Alguns itens de terceiros sobrevivem, o que é melhor que desligar um antivírus.

## D12 — Limpeza conservadora

- **Decisão:** não seguir links (junções incluídas), recusar raízes sensíveis, manter itens com menos de 24 h em User e System Temp, preservar caches de modelos (`huggingface`, `torch`, `lm-studio`, `ollama`) em `~/.cache` e limpar só `~/.gradle/caches`.
- **Por quê:** apps em execução dependem de temporários recentes; modelos custam caro para baixar; `~/.gradle` guarda credenciais; a pasta de extração do próprio exe também está dentro de Temp.

## D13 — Níveis acumulativos e declarativos

- **Decisão:** `_extend()` monta cada nível como o anterior mais extras.
- **Consequências:** mudar um nível mexe em poucas linhas e os superiores herdam a mudança.

## D14 — Adaptar à máquina, sem chutar

- **Decisão:** em HDD, ficam fora `sysmain` e Prefetch; em notebook, `hibernation` e `power_plan`. Hardware desconhecido não exclui nada.
- **Consequências:** o briefing explica o que ficou de fora, e `apply <id>` continua aplicando sob pedido explícito.

## D15 — Drivers exigem consentimento próprio

- **Contexto:** um driver não tem desfazer simples, e o da NVIDIA baixa cerca de 1 GB.
- **Decisão:** só com `--drivers` ou um sim na pergunta, cujo padrão é não. `-y` sozinho nunca instala.

## D16 — Confirmar o driver NVIDIA pela versão

- **Contexto:** a NVIDIA não documenta os códigos de saída do instalador.
- **Decisão:** a versão relida do Windows decide o resultado. Driver novo presente é sucesso com qualquer código; código 0 com driver antigo pede reinício.
- **Segurança:** só `https`, só `nvidia.com`, só `.exe`, e assinatura válida da NVIDIA Corporation antes de executar.

## D17 — Ponto de restauração não bloqueia

- **Decisão:** falha vira aviso no log e a execução continua.
- **Por quê:** a Proteção do Sistema pode estar desligada, e os ajustes têm desfazer próprio.
- **Consequências:** a tela avisa antes e o log mostra o resultado. A proteção dos drivers depende dele.

## D18 — Somente Windows

- **Decisão:** suporte a Windows 10/11. Os ramos para outros sistemas existem só para o código importar e os testes rodarem.

## D19 — Interface em português, código em inglês

- **Decisão:** mensagens para o usuário, logs e documentação em pt-BR; identificadores e comentários do código em inglês.
- **Por quê:** o público é brasileiro, e o código segue a convenção da linguagem.

---

← Anterior: [07 — CI e instalador](07-ci-e-instalador.md) · [Índice](README.md) · Próximo: [09 — Contribuindo](09-contribuindo.md)
