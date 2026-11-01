# 06 — Ficha da máquina

← Anterior: [05 — Adaptação à máquina](05-adaptacao-a-maquina.md) · [Funcionalidades](README.md) · Próximo: [07 — Atualização de drivers](07-drivers.md)

**Acesso:** opção 5 do menu ou `python main.py info`
**Código:** [backend/hardware.py](../../backend/hardware.py); [machine_info.py](../../frontend/components/machine_info.py)
**Testes:** [tests/test_hardware.py](../../tests/test_hardware.py), [tests/test_machine_info.py](../../tests/test_machine_info.py), [tests/test_info_option.py](../../tests/test_info_option.py)

---

## 1. Para que serve

Mostra o básico do computador em uma tabela, sem alterar nada e sem exigir Administrador. Os mesmos dados alimentam a [adaptação à máquina](05-adaptacao-a-maquina.md).

## 2. O que aparece

**Tabela 1 — Campos da ficha**

| Campo | Fonte |
| --- | --- |
| Windows, versão e compilação | Registro |
| Processador | Registro e número de threads do sistema |
| Memória | API do Windows: RAM instalada; se falhar, RAM utilizável |
| Placa de vídeo | CIM, uma linha por GPU |
| Disco do sistema | `Get-PhysicalDisk`, do disco onde está o Windows |
| Tipo | Chassi e bateria: Notebook ou Desktop |

## 3. Regras e casos especiais

| Situação | Resultado |
| --- | --- |
| Campo ilegível | Mostra *desconhecido* |
| Compilação 22000 ou maior | Corrige o nome para Windows 11, porque o registro ainda diz Windows 10 |
| NVMe com tipo não informado | Tratado como SSD |
| Chassi portátil (8, 9, 10, 11, 14, 30, 31, 32) | Notebook |
| Outro chassi informativo | Desktop |
| Chassi outro ou desconhecido (1, 2) | A presença de bateria decide |
| Sem chassi e sem bateria | Tipo desconhecido |

## 4. Por que é assim

| Decisão | Motivo |
| --- | --- |
| `get_machine_info` nunca levanta exceção | Uma leitura ruim não pode impedir um nível de rodar |
| Uma só chamada ao PowerShell | Cada chamada custa tempo, e um `try` por bloco isola falhas |
| Leitura preguiçosa, uma vez por sessão | A consulta leva alguns segundos |
| Enums sem tradução | `MediaType` e `BusType` não mudam com o idioma do Windows |

---

← Anterior: [05 — Adaptação à máquina](05-adaptacao-a-maquina.md) · [Funcionalidades](README.md) · Próximo: [07 — Atualização de drivers](07-drivers.md)
