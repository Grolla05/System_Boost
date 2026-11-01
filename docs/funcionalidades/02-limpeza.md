# 02 — Limpeza de temporários

← Anterior: [01 — Níveis de otimização](01-niveis-de-otimizacao.md) · [Funcionalidades](README.md) · Próximo: [03 — Ajustes reversíveis](03-ajustes-reversiveis.md)

**Acesso:** níveis do menu ou `python main.py clean`
**Código:** [backend/cleaner.py](../../backend/cleaner.py); `cmd_clean` e `_clean_with_log` em [main.py](../../main.py)
**Testes:** [tests/test_cleaner.py](../../tests/test_cleaner.py), [tests/test_state_survives_cleanup.py](../../tests/test_state_survives_cleanup.py), [tests/test_disk_breakdown.py](../../tests/test_disk_breakdown.py)

---

## 1. Para que serve

Libera espaço apagando temporários e caches, sem arriscar arquivos em uso ou fora dessas pastas.

> ⚠️ **A limpeza não tem desfazer.** Ela não passa pela Lixeira. Para medir antes, use `clean --dry-run`.

## 2. Como usar

```bash
python main.py clean                 # pede confirmação e limpa
python main.py clean --dry-run       # só mede
python main.py clean --paths "User Temp" "Gradle Cache"
```

## 3. O que é limpo

**Tabela 1 — Alvos da limpeza**

| Alvo | Local | Admin? | Regra extra |
| --- | --- | --- | --- |
| User Temp | `%TEMP%` | Não | Mantém itens com menos de 24 h |
| System Temp | `C:\Windows\Temp` | Sim | Mantém itens com menos de 24 h |
| Prefetch | `C:\Windows\Prefetch` | Sim | Aviso no briefing |
| SquirrelTemp | `%LOCALAPPDATA%\SquirrelTemp` | Não | — |
| Gradle Cache | `~\.gradle\caches` | Não | Só `caches`: `~\.gradle` guarda credenciais |
| Go Build Cache | `%LOCALAPPDATA%\go-build` | Não | — |
| User Cache | `~\.cache` | Não | Preserva `huggingface`, `torch`, `lm-studio`, `ollama` |
| npm cache | `NPM_CONFIG_CACHE` ou `%LOCALAPPDATA%\npm-cache` | Não | Pulado se `npm` não estiver instalado |
| uv cache | `UV_CACHE_DIR` ou `%LOCALAPPDATA%\uv\cache` | Não | Pulado se `uv` não estiver instalado |
| Lixeira | Todas as unidades | Não | Esvaziada de vez, medida antes e depois |

Lixeira, npm e uv só rodam nos níveis. O comando `clean` trata apenas as pastas.

## 4. Regras e casos especiais

| Situação | Resultado |
| --- | --- |
| Arquivo em uso ou sem permissão | Pulado e registrado no log |
| Pasta inexistente | Ignorada |
| Link simbólico ou junção | Remove o link, nunca o destino |
| Raiz sensível (disco inteiro, Windows, perfil do usuário...) | Recusada |
| Pasta de extração do próprio exe | Protegida |
| `--dry-run` | Mede sem apagar e não cria ponto de restauração |
| Sem Administrador | System Temp e Prefetch ficam de fora |
| Subpasta alterada nas últimas 24 h (User e System Temp) | A subpasta fica, e só os itens antigos saem |

## 5. Por dentro

1. `get_temp_paths()` monta o mapa e descarta o que não existe.
2. `clean_directory()` valida a raiz com `is_safe_clean_root()`.
3. Cada entrada é tratada conforme o tipo: link, arquivo ou pasta.
4. `_is_recent()` considera a maior data entre modificação e criação, porque arquivos extraídos mantêm datas antigas.
5. `_remove_and_measure()` apaga e soma os bytes em uma só passada.
6. `run_command_cleanup()` mede, limpa e mede de novo.

## 6. Por que é assim

| Decisão | Motivo |
| --- | --- |
| Nunca seguir junções | `is_symlink()` não as reconhece, e entrar em uma limparia o destino, em qualquer lugar do disco |
| Idade mínima de 24 h | Apps abertos dependem de temporários recentes |
| Preservar modelos | Custam caro para baixar de novo |
| Não executar npm e uv | O processo pode estar elevado, e o `PATH` é do usuário |
| Recusar raízes sensíveis | Uma variável de ambiente errada não pode esvaziar uma pasta importante |

---

← Anterior: [01 — Níveis de otimização](01-niveis-de-otimizacao.md) · [Funcionalidades](README.md) · Próximo: [03 — Ajustes reversíveis](03-ajustes-reversiveis.md)
