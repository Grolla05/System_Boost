# 06 — Testes

← Anterior: [05 — Build e ambiente](05-build-e-ambiente.md) · [Índice](README.md) · Próximo: [07 — CI e instalador](07-ci-e-instalador.md)

> Um programa que altera o Windows precisa ser testado sem alterar o Windows. A suíte simula o sistema e roda em poucos segundos em qualquer máquina de desenvolvimento.

---

## 1. Como rodar

```bash
pytest                                             # toda a suíte
pytest tests/test_cleaner.py                       # um arquivo
pytest --cov=backend --cov=frontend --cov-report=term   # com cobertura, como no CI
ruff check .                                       # lint
```

## 2. O que é simulado

Os testes **nunca** mudam o registro, serviços, tarefas ou drivers de verdade, e nunca usam a rede.

**Tabela 1 — Como cada dependência externa é substituída**

| Dependência | Substituição | Exemplo |
| --- | --- | --- |
| `subprocess` (`sc`, `schtasks`, `powercfg`) | `unittest.mock` | Confere os argumentos e simula o código de saída |
| `winreg` | `FakeWinReg`, um registro em memória | Simula valores presentes e ausentes |
| PowerShell | Mock de `run_powershell` | Devolve o JSON esperado |
| Rede | Mock | Respostas prontas do catálogo da NVIDIA |
| Disco | `tmp_path` do pytest | Pastas temporárias reais, apagadas ao final |
| Estado dos ajustes | Parâmetro `state_path` | Arquivo próprio de cada teste |

## 3. Suítes

Na data desta revisão, a suíte tem **537 testes**. A Tabela 2 mostra a distribuição.

**Tabela 2 — Testes por área**

| Área | Arquivos | Testes |
| --- | --- | --- |
| Limpeza | `test_cleaner.py`, `test_state_survives_cleanup.py`, `test_disk_breakdown.py` | 46 |
| Níveis | `test_profiles.py`, `test_preview_items.py` | 39 |
| Ajustes: filtro de terceiros | `test_tweaks/test_third_party*.py` | 56 |
| Ajustes: mecanismos | `test_tweaks/` (`registry_value`, `services`, `scheduled_tasks`, `power_plan`, `hibernation`, `startup_apps`, `recommendations_offers`, `mouse_acceleration`) | 57 |
| Ajustes: núcleo | `test_tweaks/` (`base`, `catalog`, `manager`, `state_store`, `partial_undo`) | 42 |
| Desfazer | `test_undo_option.py` | 33 |
| Drivers | `test_drivers.py`, `test_nvidia_driver.py` | 76 |
| Hardware | `test_hardware.py`, `test_machine_info.py`, `test_machine_info_screen.py`, `test_info_option.py` | 54 |
| Linha de comando | `test_main.py` | 43 |
| Interface | `test_live_log.py`, `test_level_completion.py`, `test_retro_ui.py`, `test_palettes.py`, `test_audio.py`, `test_terminal.py` | 39 |
| Suporte | `test_powershell.py`, `test_system.py`, `test_privileges.py`, `test_restore_point.py`, `test_logger.py` | 21 |
| Empacotamento | `test_build.py`, `test_installer.py` | 31 |

## 4. Fixtures compartilhadas

[tests/test_tweaks/conftest.py](../tests/test_tweaks/conftest.py) reúne as fixtures dos testes de ajustes: o `FakeWinReg` e um `subprocess.run` simulado. Prefira reaproveitá-las a recriar um ambiente simulado em cada arquivo.

## 5. O que os testes não cobrem

Por escolha, não há teste automático que:

- altere um Windows de verdade, nem em uma máquina virtual;
- execute o `System Boost.exe` gerado ou o instalador;
- consulte os serviços reais da NVIDIA ou do Windows Update.

O CI confirma que o exe é **gerado**, mas não o executa. Antes de uma entrega, faça uma passada manual em uma máquina de teste: rode um nível, confira o log e desfaça tudo.

## 6. Como escrever um teste novo

1. Coloque o teste em `tests/test_<módulo>.py`, ou em `tests/test_tweaks/` se for de ajustes.
2. Simule tudo o que tocaria o sistema. Se um teste passar sem mock, confirme que ele não alterou nada.
3. Teste o caminho de falha, não só o sucesso: valor ausente, permissão negada, saída inválida.
4. Em um ajuste, verifique sempre o par **aplicar → desfazer**.
5. Mude uma regra só depois de ter um teste que falha sem a mudança.

## 7. Mantendo as contagens

A Tabela 2 envelhece. Para gerar os números atuais:

```bash
pytest --collect-only -q
```

---

← Anterior: [05 — Build e ambiente](05-build-e-ambiente.md) · [Índice](README.md) · Próximo: [07 — CI e instalador](07-ci-e-instalador.md)
