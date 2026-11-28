"""Which way imports point in murex: colour imports nothing else of it, the
other shared modules import colour and each other, and a medium imports the
shared modules, never another medium. Importing murex imports no medium."""

import ast
from pathlib import Path

import murex

ROOT = Path(murex.__file__).parent
COLOUR = {"spectral", "_spectral_tables", "pigment"}
SHARED = COLOUR | {"_rounding", "spline", "noise", "filters", "reference", "png"}
SHARED |= {"paper", "papers", "surface"}  # (the supports, and the surface)
OWN = {"_about", "_version"}  # (the package's own: its version)
MEDIA = {p.name for p in ROOT.iterdir() if (p / "__init__.py").is_file()}


def _imports(path: Path, package: tuple[str, ...]) -> set[tuple[str, ...]]:
    """The modules of murex that the file at ``path`` (in ``package``)
    imports, each as the parts of its name after ``murex``."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".") for alias in node.names]
            found |= {tuple(n[1:]) for n in names if n[0] == "murex"}
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".") if node.module else []
            if node.level:
                base = [*package[: len(package) - node.level + 1], *module]
            elif module[:1] == ["murex"]:
                base = module[1:]
            else:
                continue
            if base:
                found.add(tuple(base))
            else:
                # from murex import a, B: a module of murex, or a name that
                # murex/__init__.py exports (which imports no medium)
                names = {alias.name for alias in node.names}
                found |= {(name,) for name in names if _is_module(name)}
    return found


#: What murex holds, by its exact name: its modules and its subpackages.
MODULES = {p.stem for p in ROOT.glob("*.py")} | MEDIA


def _is_module(name: str) -> bool:
    # (by name, not by asking for the file: where file names ignore case,
    # ``Pigment`` would be taken for the module ``pigment``)
    return name in MODULES


def _top(found: set[tuple[str, ...]]) -> set[str]:
    return {parts[0] for parts in found if parts}


def test_a_name_murex_exports_is_not_taken_for_the_module_named_like_it():
    assert _is_module("pigment") and not _is_module("Pigment")
    assert _is_module("fusain") and not _is_module("Fusain")


def test_the_names_this_test_goes_by_are_the_modules_there_are():
    modules = {p.stem for p in ROOT.glob("*.py")} - {"__init__"}
    assert modules - OWN == SHARED
    assert {"fusain", "huile"} <= MEDIA


def test_colour_imports_nothing_else_of_murex():
    for name in sorted(COLOUR):
        assert _top(_imports(ROOT / f"{name}.py", ())) <= COLOUR, name


def test_the_shared_modules_import_no_medium():
    for name in sorted(SHARED):
        assert _top(_imports(ROOT / f"{name}.py", ())) <= SHARED, name


def test_importing_murex_imports_no_medium():
    assert _top(_imports(ROOT / "__init__.py", ())) <= SHARED | OWN


def test_a_medium_imports_the_shared_modules_and_itself_only():
    for medium in sorted(MEDIA):
        files = sorted((ROOT / medium).glob("*.py"))
        assert files
        for path in files:
            reached = _top(_imports(path, (medium,)))
            assert reached <= SHARED | {medium}, (medium, path.name, reached)
