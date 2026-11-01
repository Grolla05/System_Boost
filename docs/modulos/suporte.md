# Módulo Suporte — as peças pequenas do backend

[Módulos](README.md) · Próximo: [Hardware](hardware.md)

**Arquivos:** [_powershell.py](../../backend/_powershell.py) · [_system.py](../../backend/_system.py) · [privileges.py](../../backend/privileges.py) · [restore_point.py](../../backend/restore_point.py) · [logger.py](../../backend/logger.py)
**Testes:** [test_powershell.py](../../tests/test_powershell.py) · [test_system.py](../../tests/test_system.py) · [test_privileges.py](../../tests/test_privileges.py) · [test_restore_point.py](../../tests/test_restore_point.py) · [test_logger.py](../../tests/test_logger.py)

> **Resumo:** utilitários usados por todo o backend: executar PowerShell, achar ferramentas do Windows, detectar Administrador, criar ponto de restauração e registrar logs.

---

## 1. Explicação para leigos

É a **caixa de ferramentas** da oficina. Cada peça faz uma coisa só e é usada por vários módulos, que assim não precisam saber os detalhes.

## 2. Funções

**Tabela 1 — API do módulo**

| Função | Arquivo | Faz |
| --- | --- | --- |
| `run_powershell(script, timeout)` | `_powershell.py` | Roda o script e devolve a saída em texto; levanta `PowerShellError` |
| `system_exe(name)` | `_system.py` | Caminho completo de uma ferramenta em System32 |
| `powershell_exe()` | `_system.py` | Caminho completo do Windows PowerShell |
| `cli_command()` | `_system.py` | Como chamar o programa, para citar em mensagens |
| `is_admin()` | `privileges.py` | `True` se o processo está elevado |
| `create_restore_point()` | `restore_point.py` | Devolve `(ok, nota)`, sem levantar exceção |
| `setup_logging(log_dir, argv)` | `logger.py` | Liga o log em arquivo; devolve o caminho ou `None` |
| `get_logger(name)` | `logger.py` | Logger filho de `system_boost` |
| `default_log_dir()` | `logger.py` | Pasta de logs conforme código ou exe |

## 3. Detalhes

**`run_powershell`** roda sem perfil, sem interação, sem stdin e com timeout. `PS_PRELUDE` força UTF-8 e faz qualquer erro interromper o script. A saída é decodificada como `utf-8-sig`, que ignora a marca de início de arquivo.

**`system_exe`** chama `GetSystemDirectoryW`, em vez de confiar em `%SystemRoot%`, que o ambiente pode alterar.

**`is_admin`** usa `shell32.IsUserAnAdmin`. Fora do Windows, cai em `os.getuid() == 0`, só para o código importar em outros sistemas.

## 4. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| Um único executor de PowerShell | Mesmo timeout, codificação e tratamento de erro em todo lugar |
| Caminhos absolutos | Um processo elevado não pode executar um arquivo plantado no `PATH` |
| `_` no nome dos arquivos | Marca utilitários internos do backend |

---

[Módulos](README.md) · Próximo: [Hardware](hardware.md)
