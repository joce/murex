"""Nothing murex computes depends on the machine it runs on.

IEEE addition, subtraction, multiplication, division and square root are
rounded alike by every processor; numba, without ``fastmath``, neither fuses
nor reorders them. What is not:

- NumPy's elementary functions (``np.exp``, ``np.sin``, ``np.power`` and a
  power to a fraction, ...), whose SIMD routines round some values otherwise
  from one processor to another;
- the C library's (``math.exp``, ``math.atan2``, ... and so numba's, and a
  Python number raised to a fraction), which differs from one system to
  another;
- matrix and dot products (``@``, ``np.dot``, the length of a vector by
  ``np.linalg.norm``), which BLAS sums in its own order;
- NumPy's normal, log-normal and gamma draws, which take a logarithm or an
  exponential from the C library now and then.

murex has its own: ``murex._libm`` (``exp``, ``log``, ``sin``, ``atan2``,
``power``, ``hypot``, ``np_interp``, ...) and ``murex._random``. This test
reads murex's code and fails on any of the others, but in the few places
listed below, which say why they may.
"""

import ast
from pathlib import Path

import murex

ROOT = Path(murex.__file__).parent

#: Functions of NumPy and of ``math`` that round otherwise on another machine.
TRANSCENDENTAL = {
    "exp", "expm1", "exp2", "log", "log1p", "log2", "log10", "power",
    "float_power", "pow", "tanh", "sinh", "cosh", "sin", "cos", "tan",
    "arcsin", "arccos", "arctan", "arctan2", "asin", "acos", "atan", "atan2",
    "hypot", "cbrt", "sinc", "angle", "erf", "erfc", "gamma", "lgamma",
    "interp", "dot", "vdot", "inner", "matmul", "einsum", "tensordot", "dist",
}  # fmt: skip
#: The draws of a NumPy generator that take the C library's functions.
DRAWS = {
    "normal", "standard_normal", "lognormal", "gamma", "standard_gamma",
    "exponential", "standard_exponential", "beta", "chisquare", "poisson",
    "vonmises", "weibull", "standard_cauchy", "standard_t", "wald", "laplace",
}  # fmt: skip

#: Where one may be used, by file and function, and why.
ALLOWED = {
    # the derivations of the stored tables, used only for another number of
    # bands (the tables are stored because these differ by machine)
    ("spectral.py", "_build_spectrum_to_rgb"),
    ("spectral.py", "_lhtss"),
    # a power that is no plain number (an array put in its place): NumPy's,
    # as it always was
    ("spline.py", "_power"),
    # (whole numbers: an integer power)
    ("huile/palette.py", "match"),
}


def _function_of(tree: ast.AST) -> dict[ast.AST, str]:
    """The name of the function each node is in (its outermost one)."""
    owner: dict[ast.AST, str] = {}
    for top in ast.walk(tree):
        if isinstance(top, ast.FunctionDef | ast.AsyncFunctionDef):
            for node in ast.walk(top):
                owner.setdefault(node, top.name)
    return owner


def _whole(node: ast.AST) -> bool:
    """A whole number written out (or its negative): an integer power,
    which numba and NumPy work out by multiplying."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        node = node.operand
    return isinstance(node, ast.Constant) and type(node.value) is int


def _offences(source: str, name: str) -> list[tuple[str, str | None, str]]:
    """What in ``source`` (the file ``name``, relative to murex) differs by
    machine: for each, the file and the function it is in, and where and
    what it is."""
    tree = ast.parse(source)
    owner = _function_of(tree)
    found = []
    for node in ast.walk(tree):
        what = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr, of = node.func.attr, node.func.value
            module = of.id if isinstance(of, ast.Name) else None
            if module in ("np", "numpy", "math") and attr in TRANSCENDENTAL:
                what = f"{module}.{attr}"
            elif attr == "dot":
                what = ".dot"
            elif attr == "norm" and not any(k.arg == "axis" for k in node.keywords):
                what = "np.linalg.norm of a vector"
            elif attr in DRAWS and module not in ("_random", "np", "numpy"):
                what = f"a generator's {attr}"
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.MatMult):
            what = "@"
        elif (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Pow)
            and not _whole(node.right)
        ):
            what = f"** {ast.unparse(node.right)}"
        if what:
            found.append(
                (name, owner.get(node), f"{name}:{getattr(node, 'lineno', 0)} {what}")
            )
    return found


def test_murex_computes_nothing_that_differs_by_machine():
    found = []
    for path in sorted(ROOT.rglob("*.py")):
        if path.name not in ("_libm.py", "_spectral_tables.py"):
            name = path.relative_to(ROOT).as_posix()
            found += _offences(path.read_text(encoding="utf-8"), name)
    offending = [where for name, owner, where in found if (name, owner) not in ALLOWED]
    assert not offending, "\n".join(offending)
    # (and each place allowed still has something to allow)
    assert {(name, owner) for name, owner, _ in found} >= ALLOWED


def test_the_check_finds_what_it_looks_for():
    code = """
import math
import numpy as np
def f(x, y, rng, a, n):
    a = np.exp(x) + math.sin(y) + x ** 0.5 + y ** n + x @ y
    b = np.dot(x, y) + np.linalg.norm(x) + rng.normal(0.0, 1.0)
    c = x ** 2 + y ** -1 + np.linalg.norm(x, axis=1) + np.sqrt(x) + math.floor(y)
    d = _random.normal(rng, 0.0, 1.0) + _libm.exp(x) + np.interp(x, y, a)
"""
    found = [where.split(" ", 1)[1] for *_, where in _offences(code, "probe.py")]
    assert sorted(found) == sorted(
        [
            "np.exp",
            "math.sin",
            "** 0.5",
            "** n",
            "@",
            "np.dot",
            "np.linalg.norm of a vector",
            "a generator's normal",
            "np.interp",
        ]
    )
