# Módulo Drivers — Windows Update e NVIDIA

← Anterior: [Profiles](profiles.md) · [Módulos](README.md) · Próximo: [Frontend](frontend.md)

**Arquivos:** [backend/drivers.py](../../backend/drivers.py) · [backend/nvidia_driver.py](../../backend/nvidia_driver.py)
**Testes:** [tests/test_drivers.py](../../tests/test_drivers.py), [tests/test_nvidia_driver.py](../../tests/test_nvidia_driver.py)
**Funcionalidade:** [Atualização de drivers](../funcionalidades/07-drivers.md)

> **Resumo:** procura drivers pendentes e os instala um a um, com o Windows Update primeiro e a NVIDIA depois, reportando cada resultado por callbacks.

---

## 1. Explicação para leigos

É o **técnico que troca peças uma por vez**: confere o que está disponível, troca uma, anota o resultado e passa para a próxima. Se uma peça falhar, ele não abandona o serviço.

## 2. Funções

**Tabela 1 — `drivers.py`**

| Função | Faz |
| --- | --- |
| `scan_drivers()` | Lista os drivers pendentes pelo Windows Update Agent |
| `install_driver(update_id)` | Valida o GUID, baixa e instala; devolve `(ok, reinício, nota)` |
| `update_all_drivers(progress_callback, on_scan, dry_run, on_result, on_notice)` | Orquestra tudo; devolve `(resultados, reinício)` |

**Tabela 2 — `nvidia_driver.py`**

| Função | Faz |
| --- | --- |
| `get_nvidia_gpus()` | GPUs NVIDIA e versão do driver, por CIM |
| `windows_to_nvidia_version(v)` | Converte `31.0.15.5123` em `551.23` |
| `is_newer(latest, installed)` | Compara versões NVIDIA |
| `find_product(gpu_name, notebook)` | Acha a GPU no catálogo público |
| `lookup_latest(psid, pfid)` | Versão e URL do driver Game Ready WHQL mais novo |
| `validate_download_url(url)` | Aceita só `https`, `nvidia.com` e `.exe` |
| `check_update()` | Devolve `NvidiaUpdate` ou `None` |
| `install_update(update, workdir)` | Baixa, confere a assinatura, instala e limpa |

**Tabela 3 — Callbacks de `update_all_drivers`**

| Callback | Quando |
| --- | --- |
| `on_scan(total)` | Terminou a busca |
| `progress_callback(title)` | Vai começar um driver |
| `on_result(title, status, note)` | Terminou um driver |
| `on_notice(message)` | Aviso antes de um passo longo, como a tela que pisca |

`status` é `True` (atualizado), `False` (falhou) ou `None` (pulado ou `--dry-run`).

## 3. Serviços usados

**Tabela 4 — Comunicação externa**

| Destino | Para quê |
| --- | --- |
| Windows Update Agent (COM, por PowerShell) | Buscar e instalar |
| `nvidia.com/Download/API/lookupValueSearch.aspx` | Séries e produtos |
| `gfwsl.geforce.com/.../AjaxDriverService.php` | Driver mais novo do produto |
| URL devolvida pela NVIDIA, validada | Baixar o pacote oficial |

Os serviços da NVIDIA não têm contrato oficial. Qualquer erro vira `NvidiaDriverError`, e o passo é pulado.

## 4. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| Callbacks em vez de impressão | O backend não conhece o mission log |
| Um caminho só de instalação | Windows Update e NVIDIA têm o mesmo contrato de resultado |
| Sem tabela fixa de GPUs | O catálogo da NVIDIA se atualiza sozinho |
| Confirmar pela versão relida | Os códigos de saída não são documentados |
| Sem `-clean` | Preserva as configurações do painel NVIDIA |

---

← Anterior: [Profiles](profiles.md) · [Módulos](README.md) · Próximo: [Frontend](frontend.md)
