"""The band count, which huile's kernels compile in: checked when they load."""

from __future__ import annotations

from ..spectral import N_BANDS


def check_bands(file, n, compiled_bands):
    """Refuse a kernel file (``file``) written for ``n`` bands unless that is
    ``murex.spectral.N_BANDS``, and its cached kernels unless they were
    compiled for it too.

    The kernels compile the band count in as a constant, and numba remakes a
    cached kernel only when it sees the kernel's file change (numba 0.68 and
    later by its content, older ones by its time and size): so the count is
    written out in each kernel file, and changing it is an edit there. A
    cache can still keep its stamp across such an edit: bytecode older than
    the file runs the old code and caches its kernels under the new stamp,
    and older numba does not see an edit that kept the file's size when a
    copy kept its time. ``compiled_bands`` is a tiny kernel of that file
    returning its N, cached the same way: in such a cache it returns the old
    count.
    """
    if n != N_BANDS:
        raise RuntimeError(
            f"{file} has N = {n} spectral bands, spectral.py has {N_BANDS}: "
            f"set N = {N_BANDS} in _engine.py and _render.py."
        )
    compiled = compiled_bands()
    if compiled != n:
        raise RuntimeError(
            f"numba cache is stale: the cached kernels of {file} were compiled "
            f"for {compiled} spectral bands, it has N = {n}. Stop any Python "
            "process still running the old code, delete the *.nbi and *.nbc "
            f"files in {compiled_bands.stats.cache_path} and import again."
        )
