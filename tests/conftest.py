import sys
from pathlib import Path
from shutil import copyfile

ROOT_DIR = Path.cwd()

# Since we don't have the project's code inside a module, e.g. rastreiobot/,
# in order to let the tests import .py files, it's needed to add the root
# directory to the system's path.
sys.path.insert(0, str(ROOT_DIR))

# Most of the files rely on the presence of "bot.conf" file. While we don't
# enable environment variables as configs, we create an empty "bot.conf"
# file based on "bot.conf_sample". This is a hack just for simple tests.
config_file = ROOT_DIR / "bot.conf"
if not config_file.exists():
    sample_config_file = ROOT_DIR / "bot.conf_sample"
    # Cast to str can be removed when running Rastrebiobot with Python 3.7
    copyfile(str(sample_config_file), str(config_file))
