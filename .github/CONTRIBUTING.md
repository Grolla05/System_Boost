# Guia de Contribuição — System Boost

Obrigado por considerar contribuir com o System Boost! Este guia explica como configurar o ambiente, as convenções adotadas e o fluxo de trabalho esperado.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Para que serve |
|------------|---------------|----------------|
| Windows    | 10 ou 11      | Único sistema suportado |
| Python     | 3.11+         | Rodar e testar |
| `git`      | 2.30+         | Controle de versão |
| Inno Setup | 6 (opt.)      | Gerar o instalador |

Veja os detalhes no [guia de build](../docs/05-build-e-ambiente.md).

---

## Configuração do ambiente

```sh
# 1. Fork do repositório pelo GitHub, depois clone o seu fork
git clone https://github.com/<seu-usuario>/System_Boost.git
cd System_Boost

# 2. Adicione o repositório original como upstream
git remote add upstream https://github.com/Grolla05/System_Boost.git

# 3. Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# 4. Verifique que tudo passa
pytest
ruff check .
```

---

## Fluxo de trabalho

```
main
 └── sua-branch-descritiva
       ├── commits atômicos
       └── pull request → main
```

1. **Sincronize** com o upstream antes de começar:

   ```sh
   git fetch upstream
   git rebase upstream/main
   ```

2. **Crie uma branch** com nome descritivo:

   ```sh
   git checkout -b fix/limpeza-segura
   # ou
   git checkout -b feat/ajustes-por-maquina
   ```

3. **Implemente** em commits pequenos e atômicos (um commit = uma mudança coesa).

4. **Valide** localmente antes de abrir o PR:

   ```sh
   pytest
   ruff check .
   ```

5. **Abra um Pull Request** para `main` usando o template disponível.

---

## Convenção de commits

Seguimos o padrão **Conventional Commits**. Leia o guia completo em [`.github/COMMIT_CONVENTION.md`](COMMIT_CONVENTION.md).

---

## Padrões de código

- Python 3.11+, sem avisos do `ruff`
- `backend/` não importa `frontend/` e não imprime nada
- Mensagens para o usuário em pt-BR; identificadores e comentários em inglês
- Ferramentas do Windows sempre por caminho absoluto (`system_exe`, `powershell_exe`)
- Todo ajuste novo precisa de `undo()` testado

As convenções completas estão em [docs/09-contribuindo.md](../docs/09-contribuindo.md).

---

## Testes

Todo código novo ou modificado deve ter testes correspondentes em `tests/`. Os testes **nunca** podem alterar o Windows de verdade: simule `subprocess`, `winreg`, PowerShell e rede. Veja [docs/06-testes.md](../docs/06-testes.md).

---

## Reportando bugs

Use o template [Bug Report](ISSUE_TEMPLATE/bug_report.yml) no GitHub Issues. Inclua sempre a versão do Windows, os passos para reproduzir e o trecho relevante do log.

---

## Sugerindo funcionalidades

Use o template [Feature Request](ISSUE_TEMPLATE/feature_request.yml) no GitHub Issues.

---

## Código de conduta

Este projeto adota um ambiente colaborativo e respeitoso. Seja construtivo nas revisões e receptivo ao feedback.
