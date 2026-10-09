import argparse
import sys

from backend.privileges import is_admin
from backend.cleaner import get_temp_paths, clean_directory, format_size
from backend.tweaks import list_status, apply_tweak, undo_tweak, undo_all, TweakError
from backend import profiles
from backend.logger import get_logger, setup_logging
from backend.drivers import update_all_drivers
from backend.hardware import get_machine_info
from frontend.cli import (
    INFO_CHOICE,
    show_machine_info,
    show_driver_update,
    format_driver_summary,
    console,
    show_welcome,
    show_loading,
    show_completion,
    show_tweak_list,
    show_tweak_success,
    show_tweak_error,
    show_undo_all_results,
    show_level_menu,
    show_level_summary,
    show_level_completion,
    set_sound_enabled,
    apply_palette,
)

log = get_logger("main")

PATH_CHOICES = ("User Temp", "System Temp", "Prefetch")
COMMANDS = ("menu", "clean", "list", "apply", "undo", "info")


def parse_args(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        argv = ["menu"]
    elif argv[0] not in COMMANDS and argv[0] not in ("-h", "--help"):
        argv = ["clean"] + argv

    parser = argparse.ArgumentParser(prog="boost", description="WinCleaner / System Boost")
    subparsers = parser.add_subparsers(dest="command", required=True)

    menu_parser = subparsers.add_parser("menu", help="Fluxo guiado: escolha um nível de otimização")
    menu_parser.add_argument("-y", "--yes", action="store_true", help="Pula confirmações (uso automatizado)")
    menu_parser.add_argument("--no-drivers", action="store_true", help="Não atualiza drivers ao final")
    menu_parser.add_argument("--no-sound", action="store_true", help="Desativa efeitos sonoros retrô 8-bit")
    menu_parser.add_argument("-p", "--palette", choices=("dmg", "pocket", "arcade", "amber", "matrix"), help="Escolhe a paleta de cores retrô")

    clean_parser = subparsers.add_parser("clean", help="Limpa arquivos temporários do Windows")
    clean_parser.add_argument("-n", "--dry-run", action="store_true", help="Simula a limpeza sem apagar nada")
    clean_parser.add_argument("--paths", nargs="+", choices=PATH_CHOICES, help="Restringe a limpeza a pastas específicas")
    clean_parser.add_argument("-y", "--yes", action="store_true", help="Pula telas de confirmação (uso automatizado)")
    clean_parser.add_argument("--no-close", action="store_true", help="Não fecha o terminal ao final")
    clean_parser.add_argument("--no-drivers", action="store_true", help="Não atualiza drivers ao final")
    clean_parser.add_argument("--no-sound", action="store_true", help="Desativa efeitos sonoros retrô 8-bit")
    clean_parser.add_argument("-p", "--palette", choices=("dmg", "pocket", "arcade", "amber", "matrix"), help="Escolhe a paleta de cores retrô")

    subparsers.add_parser("info", help="Mostra a ficha da máquina (Windows, CPU, RAM, GPU, disco, tipo)")

    subparsers.add_parser("list", help="Lista os ajustes reversíveis disponíveis e seu estado atual")

    apply_parser = subparsers.add_parser("apply", help="Aplica um ajuste reversível")
    apply_parser.add_argument("tweak_id")

    undo_parser = subparsers.add_parser("undo", help="Desfaz um ajuste aplicado")
    undo_parser.add_argument("tweak_id", nargs="?")
    undo_parser.add_argument("--all", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "undo" and not args.all and not args.tweak_id:
        parser.error("undo requer um tweak_id ou --all")
    return args


def _run_driver_step(args, dry_run=False):
    """Final step of menu/clean: scan devices and update drivers via Windows Update."""
    if args.no_drivers:
        log.info("etapa drivers: ignorada (--no-drivers)")
        return None
    log.info("etapa drivers: iniciando")
    try:
        results, reboot_required = show_driver_update(update_all_drivers, dry_run=dry_run)
    except Exception as exc:
        log.exception("etapa drivers: erro inesperado")
        return f"[danger]Drivers: erro inesperado: {exc}[/danger]"
    return format_driver_summary(results, reboot_required)


def cmd_menu(args):
    """Runs the guided flow: welcome -> level menu -> confirm -> execute -> completion.

    The menu's last option shows the machine spec sheet and returns to the menu.
    ESC on the completion screen loops back to the level menu; Enter (or -y) exits.
    """
    show_welcome(skip_wait=args.yes)

    machine_info = None  # read lazily, once: the PowerShell/CIM query takes a couple of seconds

    while True:
        level_id = show_level_menu()
        if level_id == INFO_CHOICE:
            if machine_info is None:
                log.info("menu: lendo ficha da máquina")
                with console.status("[accent]Lendo hardware...[/accent]"):
                    machine_info = get_machine_info()
            show_machine_info(machine_info, wait=True)
            continue
        log.info("menu: nível escolhido='%s'", level_id)
        clean_paths = profiles.resolve_clean_paths(level_id)
        applicable_ids, skipped_ids = profiles.resolve_tweak_plan(level_id)

        if not args.yes:
            proceed = show_level_summary(level_id, clean_paths, applicable_ids, skipped_ids)
            if not proceed:
                log.info("menu: usuário cancelou na confirmação")
                return

        log.info("etapa limpeza: iniciando")
        results, total_formatted, total_bytes = show_loading(
            clean_paths, clean_directory, format_size, dry_run=False
        )
        log.info("etapa limpeza: concluída, total liberado=%s", total_formatted)
        log.info("etapa ajustes: iniciando")
        tweak_results = profiles.apply_level_tweaks(level_id)
        log.info("etapa ajustes: resultados=%s", tweak_results)
        driver_summary = _run_driver_step(args)

        level_label = profiles.LEVELS[level_id]["label"]
        outcome = show_level_completion(
            level_label, total_formatted, tweak_results,
            close_terminal=not args.yes, skip_wait=args.yes, driver_summary=driver_summary,
        )
        if outcome != "back":
            return


def cmd_clean(args):
    """Runs the existing temp-cleaning flow (welcome -> loading -> completion)."""
    show_welcome(skip_wait=args.yes)

    admin_status = is_admin()
    all_paths = get_temp_paths()

    if not admin_status:
        paths_to_clean = {k: v for k, v in all_paths.items() if k == "User Temp"}
    else:
        paths_to_clean = all_paths

    if args.paths:
        paths_to_clean = {k: v for k, v in paths_to_clean.items() if k in args.paths}

    if "Prefetch" in paths_to_clean and not args.yes:
        console.print(
            "[warning]Prefetch será limpo — o Windows recria automaticamente, "
            "mas isso pode afetar o próximo boot.[/warning]"
        )

    results, total_formatted, total_bytes = show_loading(
        paths_to_clean, clean_directory, format_size, dry_run=args.dry_run
    )

    driver_summary = _run_driver_step(args, dry_run=args.dry_run)

    close_terminal = not (args.no_close or args.dry_run or args.yes)
    show_completion(
        total_formatted, dry_run=args.dry_run, close_terminal=close_terminal,
        skip_wait=args.yes, driver_summary=driver_summary,
    )


def cmd_list(args):
    """Shows all available tweaks with their current/applied state."""
    show_tweak_list(list_status())


def cmd_info(args):
    """Shows the machine spec sheet (Windows, CPU, RAM, GPU, disk type, notebook/desktop)."""
    show_machine_info(get_machine_info())


def cmd_apply(args):
    """Applies a single tweak by id, reporting success or failure."""
    try:
        apply_tweak(args.tweak_id)
        show_tweak_success(f"'{args.tweak_id}' aplicado com sucesso.")
    except TweakError as exc:
        show_tweak_error(str(exc))
        sys.exit(1)


def cmd_undo(args):
    """Undoes a single tweak by id, or all applied tweaks with --all."""
    if args.all:
        results = undo_all()
        show_undo_all_results(results)
        if any(not success for _, success, _ in results):
            sys.exit(1)
        return
    try:
        undo_tweak(args.tweak_id)
        show_tweak_success(f"'{args.tweak_id}' desfeito com sucesso.")
    except TweakError as exc:
        show_tweak_error(str(exc))
        sys.exit(1)


_DISPATCH = {
    "menu": cmd_menu, "clean": cmd_clean, "list": cmd_list,
    "apply": cmd_apply, "undo": cmd_undo, "info": cmd_info,
}


def main():
    setup_logging()
    args = parse_args()
    if getattr(args, "palette", None):
        apply_palette(args.palette)
    if getattr(args, "no_sound", False):
        set_sound_enabled(False)
    log.info("comando='%s' args=%s", args.command, vars(args))
    _DISPATCH[args.command](args)


def _wait_key_after_crash():
    from frontend.components._terminal import _read_single_key
    print("\nPressione qualquer tecla para sair...", file=sys.stderr)
    _read_single_key()


def run_guarded():
    """Runs main(); on an unexpected crash prints the traceback and waits, so a double-clicked window doesn't vanish."""
    try:
        main()
    except KeyboardInterrupt:
        print("\nCleanup cancelled by user.")
        sys.exit(0)
    except Exception:
        import traceback
        log.exception("erro não tratado")
        traceback.print_exc()
        _wait_key_after_crash()
        sys.exit(1)


if __name__ == "__main__":
    run_guarded()
