import subprocess
import sys

import murex


def test_the_package_knows_its_version():
    assert isinstance(murex.__version__, str)
    assert murex.__version__


def test_everything_exported_exists():
    for name in murex.__all__:
        assert getattr(murex, name) is not None, name


def test_importing_murex_loads_no_medium():
    # a medium compiles an engine: nobody pays for one they do not use
    code = (
        "import sys, murex; "
        "print([n for n in sys.modules if n.startswith('murex.') and n.count('.') > 1])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    # only murex's own modules are loaded: none of a subpackage's
    assert out.stdout.strip() == "[]"
