# Módulo Hardware — a ficha da máquina

← Anterior: [Suporte](suporte.md) · [Módulos](README.md) · Próximo: [Cleaner](cleaner.md)

**Arquivo:** [backend/hardware.py](../../backend/hardware.py)
**Testes:** [tests/test_hardware.py](../../tests/test_hardware.py)
**Funcionalidade:** [Ficha da máquina](../funcionalidades/06-ficha-da-maquina.md)

> **Resumo:** lê versão do Windows, CPU, RAM, GPUs, disco do sistema e tipo de máquina, sem nunca levantar exceção.

---

## 1. Explicação para leigos

É a **ficha técnica** colada no computador. Se um dado não puder ser lido, a linha fica em branco, em vez de o programa desistir.

## 2. Estrutura

`MachineInfo` é uma dataclass com `windows`, `version`, `build`, `cpu`, `threads`, `ram_gb`, `gpus`, `disk_type`, `disk_model`, `disk_bus` e `form_factor`. O que não foi lido fica `None`, ou `[]` em `gpus`.

## 3. Funções

**Tabela 1 — API do módulo**

| Função | Faz |
| --- | --- |
| `get_machine_info()` | Monta o `MachineInfo` completo |
| `is_notebook()` | `True` se chassi ou bateria indicarem portátil; `False` se desconhecido |
| `_read_cim()` | Executa a consulta única e devolve o JSON, ou `{}` se falhar |
| `_classify_disk(media, bus)` | Devolve `SSD`, `HDD` ou `None` |
| `_classify_chassis(chassis, battery)` | Devolve `Notebook`, `Desktop` ou `None` |

## 4. De onde vem cada dado

| Dado | Fonte |
| --- | --- |
| Windows | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` |
| CPU | `HKLM\HARDWARE\DESCRIPTION\System\CentralProcessor\0` |
| RAM | `GetPhysicallyInstalledSystemMemory`, com `GlobalMemoryStatusEx` de reserva |
| GPU | `Win32_VideoController` |
| Disco | `Get-Partition` e `Get-PhysicalDisk` |
| Chassi e bateria | `Win32_SystemEnclosure`, `Win32_Battery` |

## 5. Por que foi feito assim

| Decisão | Motivo |
| --- | --- |
| Registro e `ctypes` antes de PowerShell | São bem mais rápidos |
| Um `try` por bloco no script | Uma consulta ruim não derruba as outras |
| NVMe sem tipo vira SSD | O `MediaType` pode vir vazio, mas NVMe é sempre flash |

---

← Anterior: [Suporte](suporte.md) · [Módulos](README.md) · Próximo: [Cleaner](cleaner.md)
