#!/usr/bin/python3
import sys
from src.modules import modules, common

def main():
    global logger

    parser = common.get_parser()
    args = parser.parse_args()
    logger = common.get_logger(args)

    if not common.prereqs_present():
        sys.exit()

    module = common.ModulePreprocessor(args, logger)
    if args.t == 'installer-w-preinstall-script':
        modules.install_pkg(module)
    elif args.t == 'installer-w-postinstall-script':
        modules.install_pkg_postinstall(module)       
    elif args.t == 'installer-w-ld':
        modules.install_pkg_ld(module)
    elif args.t == 'installer-plugin':
        modules.install_pkg_installer_plugin(module)
    elif args.t == 'installer-js-embedded':
        modules.install_pkg_js_embedded(module)
    elif args.t == 'installer-js-script':
        modules.install_pkg_js_script(module)
    elif args.t == 'disk-image':
        modules.disk_image(module)
    elif args.t == 'macro-vba-excel':
        modules.macro_vba_excel(module)
    elif args.t == 'macro-vba-ppt':
        modules.macro_vba_ppt(module)
    elif args.t == 'macro-vba-word':
        modules.macro_vba_word(module)
    elif args.t == 'macro-sylk-excel':
        modules.macro_sylk_excel(module)

    print(
        '\n[*] Done generating package! Navigate to ./Payloads for payload.\n')
    if not args.debug:
        logger.debug(
            'Cleaning payload staging directory.')
        module.clean_payload_staging()


if __name__ == '__main__':
    main()
