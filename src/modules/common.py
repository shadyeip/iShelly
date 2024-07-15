import psutil
import logging
import shutil
import subprocess
import platform
import os
import argparse


logger = logging.getLogger(__name__)


def prereqs_present():
    if platform.system() != "Darwin":
        logger.error("This tool is only supported on macOS.")
        return False
    if not is_installed("go"):
        logger.error("Install golang for macOS.")
        return False
    if not is_installed("xcodebuild"):
        logger.error("Install xcode via the app store.")
        return False

    return True


def get_logger(args):
    if args.debug:
        logging.basicConfig(
            format="%(asctime)-15s %(funcName)15s %(levelname)9s: %(message)s",
            level=logging.DEBUG
        )

    return logging.getLogger(__name__)


def get_parser():
    # List of valid options for the -t argument
    valid_options = [
        'installer-w-preinstall-script',
        'installer-w-postinstall-script',
        'installer-w-ld',
        'installer-plugin',
        'installer-js-embedded',
        'installer-js-script',
        'disk-image',
        'macro-vba-excel',
        'macro-vba-ppt',
        'macro-vba-word',
        'macro-sylk-excel'
    ]

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true',
                        help='for debugging only')
    parser.add_argument('-t', choices=valid_options, required=True, help="Type of initial access vector")
    parser.add_argument('-f', type=str, required=True, help="Filename of the payload")
    parser.add_argument('-u', type=str, required=False, help="URL of remote hosted payload")

    return parser


def is_installed(program):
    rc = subprocess.call(['which', program], stdout=open(os.devnull, 'wb'))
    if rc == 0:
        return True
    else:
        logger.error("Dependecy not installed: {}".format(program))
        return False


def is_running(program):
    return program in (p.name() for p in psutil.process_iter())


class ModulePreprocessor:
    def __init__(self, args, logger):
        self.implant_path = args.f
        self.payload_hosting_url = args.u
        self.module_root_path = os.path.join(
            os.getcwd(), "Payloads/tmp/ModuleGenerator")
        logger.debug("ModuleGenerator class created. Root Path set to: {}".format(
            self.module_root_path))
        self.appdir = os.getcwd()
        self.payloads_dir = 'Payloads'
        self.full_payloads_dir = os.path.join(self.appdir,
                                              self.payloads_dir)
        self.payload_name = self.implant_path.split("/")[-1]

        self.payload_destination = os.path.join(
            self.full_payloads_dir, self.payload_name)

        self.payload_staging_dir = os.path.join(self.payloads_dir, 'tmp')
        self.full_payload_staging_dir = os.path.join(self.appdir,
                                                     self.payload_staging_dir)

    def set_scripts_dir(self, dst):
        self.scripts_dir = os.path.join(self.module_root_path, dst)
        logger.debug("Set scripts dir to: {}".format(self.scripts_dir))

    def copy_filedir(self, src, dst):
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        else:
            try:
                shutil.copytree(src, dst)
                logger.debug("Copied Template Folder to '{}'".format(dst))
            except OSError:
                shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logger.debug("Overwrote files '{}'".format(dst))

    def make_executable(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.chmod(path, 0o755)
        logger.debug("Made file executable: {}".format(path))

    def update_template(self, src_string, dst_string, filepath):
        with open(os.path.join(self.module_root_path, filepath), 'r') as fh:
            contents = fh.read()
            contents = contents.replace(src_string, dst_string)
        with open(os.path.join(self.module_root_path, filepath), 'w') as fh:
            fh.write(contents)
        logger.debug("Updated file: {}".format(filepath))
        logger.debug("with contents: {}".format(contents))

    def create_dir(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.makedirs(path, exist_ok=True)
        logger.debug("Made directory: {}".format(path))

    def generate_payload(self, type, identifier, output, has_scripts=True):
        if type == 'pkgbuild':
            self.run_pkgbuild(identifier, output, has_scripts)
        elif type == 'productbuild-plugin':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js-script':
            self.run_productbuild(type, identifier, output)

    def run_pkgbuild(self, identifier, output, has_scripts):
        if has_scripts:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                '--scripts',
                self.scripts_dir,
                os.path.join(self.full_payloads_dir, output)
            ]
        else:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                os.path.join(self.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def generate_cleanup(self, instructions):
        print("\n[*] Removal Instructions:")
        for instruction in instructions:
            print("\t{}".format(instruction))

    def generate_instructions(self, instructions):
        print("\n[*] Instructions for payload:")
        for instruction in instructions:
            print("\t{}".format(instruction))

    def clean_payload_staging(self):
        logger.debug("Deleting directory {}".format(
            self.payload_staging_dir))
        shutil.rmtree(self.full_payload_staging_dir)
        files = [
            'pneumaEX.zip'
        ]
        for file in files:
            full_path = os.path.join(self.full_payloads_dir, file)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.debug("Deleting file: {}".format(full_path))

    def run_xcodebuild(self):
        cmd = [
            'xcodebuild',
            '-project',
            os.path.join(self.module_root_path, 'SpecialDelivery.xcodeproj')
        ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def run_productbuild(self, type, identifier, output):
        if type == 'productbuild-plugin':
            cmd = [
                'productbuild',
                '--identifier',
                identifier,
                '--version',
                '1',
                '--package',
                os.path.join(self.module_root_path, 'plugins', output),
                '--plugins',
                os.path.join(self.module_root_path, 'plugins'),
                os.path.join(self.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--package-path',
                os.path.join(self.full_payloads_dir, 'install.pkg'),
                os.path.join(self.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js-script':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--scripts',
                self.scripts_dir,
                '--package-path',
                os.path.join(self.full_payloads_dir, 'install.pkg'),
                os.path.join(self.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

class ModuleGenerator:
    def __init__(self, agent):
        self.scripts_dir = None
        self.agent = agent

        self.module_root_path = os.path.join(
            os.getcwd(), "Payloads/tmp/ModuleGenerator")
        logger.debug("ModuleGenerator class created. Root Path set to: {}".format(
            self.module_root_path))

    def set_scripts_dir(self, dst):
        self.scripts_dir = os.path.join(self.module_root_path, dst)
        logger.debug("Set scripts dir to: {}".format(self.scripts_dir))

    def create_dir(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.makedirs(path, exist_ok=True)
        logger.debug("Made directory: {}".format(path))

    def create_file(self, dst, content):
        path = os.path.join(self.module_root_path, dst)
        with open(path, 'w') as fh:
            if isinstance(content, list):
                for line in content:
                    fh.write("%s\n" % line)
            elif isinstance(content, str):
                fh.write(content)
        logger.debug("Created file: {}".format(path))

    def make_executable(self, dst):
        path = os.path.join(self.module_root_path, dst)
        os.chmod(path, 0o755)
        logger.debug("Made file executable: {}".format(path))

    def run_pkgbuild(self, identifier, output, has_scripts):
        if has_scripts:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                '--scripts',
                self.scripts_dir,
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        else:
            cmd = [
                'pkgbuild',
                '--identifier',
                identifier,
                '--nopayload',
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def generate_payload(self, type, identifier, output, has_scripts=True):
        if type == 'pkgbuild':
            self.run_pkgbuild(identifier, output, has_scripts)
        elif type == 'productbuild-plugin':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js':
            self.run_productbuild(type, identifier, output)
        elif type == 'productbuild-js-script':
            self.run_productbuild(type, identifier, output)

    def move_files(self, src, dst):
        dst_path = os.path.join(self.module_root_path, dst)
        os.rename(src, dst_path)
        logger.debug("Moved file to {}".format(dst_path))

    def generate_cleanup(self, instructions):
        print("\n[*] Removal Instructions:")
        for instruction in instructions:
            print("\t{}".format(instruction))

    def clean_payload_staging(self):
        logger.debug("Deleting directory {}".format(
            self.payload_staging_dir))
        shutil.rmtree(self.full_payload_staging_dir)
        files = [
            'pneumaEX.zip'
        ]
        for file in files:
            full_path = os.path.join(self.full_payloads_dir, file)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.debug("Deleting file: {}".format(full_path))

    def copy_filedir(self, src, dst):
        import pdb
        pdb.set_trace()
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        else:
            try:
                shutil.copytree(src, dst)
                logger.debug("Copied Template Folder to '{}'".format(dst))
            except OSError:
                shutil.rmtree(dst)
                shutil.copytree(src, dst)
                logger.debug("Overwrote files '{}'".format(dst))

    def update_template(self, src_string, dst_string, filepath):

        with open(os.path.join(self.module_root_path, filepath), 'r') as fh:
            contents = fh.read()
            contents = contents.replace(src_string, dst_string)
        with open(os.path.join(self.module_root_path, filepath), 'w') as fh:
            fh.write(contents)
        logger.debug("Updated file: {}".format(filepath))
        logger.debug("with contents: {}".format(contents))

    def run_xcodebuild(self):
        cmd = [
            'xcodebuild',
            '-project',
            os.path.join(self.module_root_path, 'SpecialDelivery.xcodeproj')
        ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def run_productbuild(self, type, identifier, output):
        if type == 'productbuild-plugin':
            cmd = [
                'productbuild',
                '--identifier',
                identifier,
                '--version',
                '1',
                '--package',
                os.path.join(self.module_root_path, 'plugins', output),
                '--plugins',
                os.path.join(self.module_root_path, 'plugins'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--package-path',
                os.path.join(self.agent.c2.full_payloads_dir, 'install.pkg'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        elif type == 'productbuild-js-script':
            cmd = [
                'productbuild',
                '--distribution',
                os.path.join(self.module_root_path, 'distribution.xml'),
                '--scripts',
                self.scripts_dir,
                '--package-path',
                os.path.join(self.agent.c2.full_payloads_dir, 'install.pkg'),
                os.path.join(self.agent.c2.full_payloads_dir, output)
            ]
        subprocess.call(cmd, stdout=open(os.devnull, 'wb'))

    def generate_instructions(self, instructions):
        print("\n[*] Instructions for payload:")
        for instruction in instructions:
            print("\t{}".format(instruction))
