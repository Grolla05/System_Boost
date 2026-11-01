# Política de Segurança — System Boost

## Versões suportadas

| Branch / Tag | Suportada |
|--------------|-----------|
| `main`       | ✅ Sim    |
| Outras       | ❌ Não    |

## Reportando uma vulnerabilidade

O System Boost roda com privilégios de Administrador, apaga arquivos e altera configurações do Windows. O escopo de segurança relevante inclui:

- Execução de código com elevação (arquivo plantado no `PATH` ou na pasta atual, por exemplo)
- Exclusão de arquivos fora das pastas previstas, inclusive por links ou variáveis de ambiente
- Injeção em comandos PowerShell ou `schtasks`/`sc`
- Burla da verificação do download ou da assinatura do driver NVIDIA
- Perda ou adulteração do estado de desfazer

**Não reporte via issue pública** se a vulnerabilidade puder ser explorada antes da correção.

### Como reportar

Envie um e-mail para **fegrolla0210@gmail.com** com:

1. Descrição clara da vulnerabilidade
2. Passos para reproduzir (comando, versão do Windows, Administrador ou não)
3. Impacto potencial
4. Sugestão de correção (se houver)

Resposta esperada em até **7 dias úteis**.

## Processo de divulgação responsável

1. Você reporta em privado
2. Confirmamos o recebimento em até 48 h
3. Investigamos e desenvolvemos a correção
4. Publicamos a correção com crédito ao relator (salvo solicitação de anonimato)
5. Após o merge, a issue pública pode ser aberta
