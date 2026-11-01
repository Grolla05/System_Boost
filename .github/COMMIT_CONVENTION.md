# Convenção de Commits — System Boost

Seguimos o padrão **Conventional Commits 1.0**. O histórico do projeto usa assuntos em inglês, sem escopo; o escopo é opcional.

## Formato

```
<tipo>[(escopo)]: <descrição curta>

[corpo opcional]

[rodapé(s) opcional(is)]
```

- Linha de assunto: **máx. 72 caracteres**
- Verbo no imperativo, em minúsculas: "add", não "added" nem "Add"
- Sem ponto final no assunto

---

## Tipos

| Tipo       | Quando usar |
|------------|-------------|
| `feat`     | Nova funcionalidade visível ao usuário |
| `fix`      | Correção de bug |
| `refactor` | Mudança interna sem alterar comportamento externo |
| `test`     | Adiciona ou corrige testes |
| `docs`     | Apenas documentação |
| `build`    | Build, instalador ou dependências |
| `ci`       | Pipelines em `.github/workflows/` |
| `style`    | Formatação, sem mudança de lógica |
| `chore`    | Tarefas de manutenção que não encaixam acima |
| `perf`     | Melhoria de desempenho |
| `revert`   | Reverte um commit anterior |

---

## Escopos

| Escopo     | O que cobre |
|------------|-------------|
| `cleaner`  | Limpeza (`backend/cleaner.py`) |
| `profiles` | Níveis (`backend/profiles.py`) |
| `tweaks`   | Ajustes (`backend/tweaks/`) |
| `drivers`  | Drivers (`backend/drivers.py`, `backend/nvidia_driver.py`) |
| `hardware` | Ficha da máquina (`backend/hardware.py`) |
| `ui`       | Interface (`frontend/`) |
| `main`     | Ponto de entrada (`main.py`) |
| `tests`    | Qualquer arquivo em `tests/` |
| `build`    | `build.py`, `installer.py`, `installer.iss` |
| `deps`     | Dependências externas |

---

## Exemplos

Do histórico do projeto:

```
fix: make temp cleanup stricter

fix: never lose tweak undo data

feat: adapt levels to the machine and handle new items

chore: remove dead code and tighten CI and build
```

Com escopo:

```
fix(tweaks): restore delayed-auto services on undo

docs: reorganize documentation into numbered modules
```

---

## Breaking Changes

Qualquer mudança que quebre compatibilidade de comportamento documentado:

```
feat(tweaks)!: rename the state file

BREAKING CHANGE: the old file is no longer read.
```

---

## Referências em rodapé

| Palavra-chave         | Efeito no GitHub           |
|-----------------------|----------------------------|
| `Closes #123`         | Fecha a issue ao fazer merge |
| `Fixes #123`          | Idem |
| `Refs #123`           | Vincula sem fechar |
| `Co-authored-by: ...` | Atribuição compartilhada |
