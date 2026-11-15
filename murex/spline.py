"""Stroke paths: smooth curves resampled by arc length."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
from numba import njit

#: A value along a stroke: a number, a sequence, or a function of u in 0..1
#: (called with the array of all u, or with one u at a time if that fails).
Profile = (
    float
    | Sequence[float]
    | Callable[[np.ndarray], np.ndarray]
    | Callable[[float], float]
)


def _as_points(points, kind: str) -> np.ndarray:
    """Control points as an (n, 2) float array, checked: a clear error here
    beats an IndexError or a NaN cast deep inside the sampling."""
    try:
        P = np.asarray(points, dtype=np.float64)
    except (TypeError, ValueError):
        raise TypeError(
            f"{kind} points must be (x, y) pairs of numbers, got {points!r:.80}"
        ) from None
    if P.size % 2:
        raise ValueError(
            f"{kind} points must be (x, y) pairs, got {P.size} numbers in all"
        )
    P = P.reshape(-1, 2)
    if len(P) == 0:
        raise ValueError(f"{kind} needs at least one point (x, y), got none")
    bad = ~np.isfinite(P).all(axis=1)
    if bad.any():
        i = int(np.argmax(bad))
        raise ValueError(
            f"{kind} points must be finite numbers; point {i} is ({P[i, 0]}, {P[i, 1]})"
        )
    return P


def _is_float64(array, columns: int) -> bool:
    """Whether ``array`` is what the kernels take: a numpy array itself (not
    a subclass) of float64 in this machine's byte order, of rows of
    ``columns`` numbers (0: of numbers)."""
    if not (type(array) is np.ndarray and array.dtype == np.float64):
        return False
    return array.shape[1:] == ((columns,) if columns else ())


def _snapshot(points) -> tuple:
    """Control points as they are now, to tell later whether they have
    changed (to the bit: -0.0 is not 0.0)."""
    points = np.asarray(points)
    return points.dtype.str, points.shape, points.tobytes()


class Path:
    """Base class. Subclasses implement :meth:`_dense` returning densely sampled
    points plus, for each point, a fractional knot index (0 at the first
    control point, 1 at the second, ...).

    The dense points of a path are worked out once, by the first call to
    :meth:`sample` or :attr:`length`, and kept for the next: a stroke
    samples its path and asks its length, sometimes more than once. A path
    may still be changed (its control points moved, in place or not): the
    dense points are then worked out again. For that, a class that
    implements :meth:`_dense` also says what its dense points are worked out
    from, in :meth:`_state`; the dense points of one that does not are
    worked out at every call, as they all were before.
    """

    n_knots: int = 0
    #: Whether the class that implements _dense also implements _state.
    _keeps: bool = False
    #: The state the dense points were worked out from, and what was worked
    #: out (see _measured).
    _kept: tuple | None = None

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        # (a subclass that works out its dense points in its own way, from
        # something its parent's _state knows nothing of, must not be given
        # stale ones: the _state that counts is its own, or a child's)
        order = cls.__mro__
        dense = next(i for i, c in enumerate(order) if "_dense" in vars(c))
        state = next(i for i, c in enumerate(order) if "_state" in vars(c))
        cls._keeps = state <= dense

    def _dense(self) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError

    def _state(self) -> object:
        """What :meth:`_dense` works the dense points out from, as a value
        that compares equal to an earlier one only if the dense points would
        come out the same, to the bit (so: a copy of what may change in
        place, such as the bytes of an array); or None, for dense points
        that are not to be kept."""
        return None

    def __getstate__(self) -> dict:
        # (what is kept is not part of the path: it is not pickled or copied)
        return {k: v for k, v in vars(self).items() if k != "_kept"}

    def _measured(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """The dense points, their knots, the length of the path up to each
        and its whole length: worked out once, and again only if the path
        has changed. (The arrays are the path's own: not to be handed out.)"""
        state = self._state() if self._keeps else None
        kept = self._kept
        if state is not None and kept is not None and kept[0] == state:
            return kept[1]
        pts, knot = self._dense()
        if _is_float64(pts, 2) and len(pts) > 1:
            seg, s = _arc(np.ascontiguousarray(pts))
        else:
            seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
            s = np.concatenate([[0.0], np.cumsum(seg)])
        # (numpy's own sum, which adds in pairs: not the last of s)
        measured = (pts, knot, s, float(seg.sum()))
        if state is not None:
            self._kept = (state, measured)
        return measured

    def sample(self, spacing: float):
        """Resample at (roughly) equal arc-length ``spacing`` in pixels.

        Returns ``(points (M,2), tangents (M,2), u (M,), knot (M,))`` where
        ``u`` runs 0..1 along the arc length and ``knot`` is the fractional
        control-point index, used to interpolate per-control-point values.
        """
        pts, knot, s, _ = self._measured()
        length = s[-1]
        if length < 1e-9:
            # (copies: the dense points are the path's own)
            point, at = np.array(pts[:1]), np.array(knot[:1])
            return point, np.array([[1.0, 0.0]]), np.zeros(1), at
        n = max(2, int(np.ceil(length / max(spacing, 1e-3))) + 1)
        si = np.linspace(0.0, length, n)
        x, y = np.interp(si, s, pts[:, 0]), np.interp(si, s, pts[:, 1])
        k = np.interp(si, s, knot)
        if x.dtype == y.dtype == np.float64:
            out = np.empty((n, 2))
            out[:, 0], out[:, 1] = x, y
            return out, _tangents(out), si / length, k
        # (dense points that are complex numbers: by numpy, as it all was)
        out = np.stack([x, y], -1)
        tan = np.gradient(out, axis=0)
        tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
        return out, tan, si / length, k

    @property
    def length(self) -> float:
        return self._measured()[3]


# The kernels: plain IEEE arithmetic only (no fastmath), which numba neither
# reorders nor fuses, so each operation matches numpy's to the bit. What
# numpy may not work out the same way everywhere (a power, an interpolation,
# a sum in pairs) is left to numpy.
@njit(cache=True, error_model="numpy")
def _arc(pts):
    """The length of each segment between the points (n, 2), n > 1, and the
    length of the path up to each point: ``np.linalg.norm(np.diff(pts,
    axis=0), axis=1)`` and its ``np.cumsum`` after a 0, to the bit."""
    n = pts.shape[0]
    seg = np.empty(n - 1)
    s = np.empty(n)
    s[0] = 0.0
    for i in range(n - 1):
        dx = pts[i + 1, 0] - pts[i, 0]
        dy = pts[i + 1, 1] - pts[i, 1]
        seg[i] = np.sqrt(dx * dx + dy * dy)
        s[i + 1] = seg[i] if i == 0 else s[i] + seg[i]
    return seg, s


@njit(cache=True, error_model="numpy")
def _tangents(points):
    """The direction of the path at each of its points (n, 2), n > 1, of
    length 1: ``np.gradient(points, axis=0)`` over its norm (1e-12 at
    least), to the bit."""
    n = points.shape[0]
    tan = np.empty((n, 2))
    for i in range(n):
        if i == 0:
            dx = points[1, 0] - points[0, 0]
            dy = points[1, 1] - points[0, 1]
        elif i == n - 1:
            dx = points[i, 0] - points[i - 1, 0]
            dy = points[i, 1] - points[i - 1, 1]
        else:
            dx = (points[i + 1, 0] - points[i - 1, 0]) / 2.0
            dy = (points[i + 1, 1] - points[i - 1, 1]) / 2.0
        norm = np.sqrt(dx * dx + dy * dy)
        if norm < 1e-12:  # (np.maximum: NaN stays NaN)
            norm = 1e-12
        tan[i, 0] = dx / norm
        tan[i, 1] = dy / norm
    return tan


class CatmullRom(Path):
    """Smooth curve passing through every control point.

    ``alpha=0.5`` (centripetal) avoids loops and cusps on uneven spacing.
    """

    def __init__(self, points, alpha: float = 0.5, closed: bool = False):
        self.points = _as_points(points, "path")
        self.alpha = alpha
        self.closed = closed
        self.n_knots = len(self.points) + (1 if closed else 0)

    def _state(self) -> object:
        return _snapshot(self.points), self.alpha, self.closed

    def _dense(self):
        P = self.points
        if not _is_float64(P, 2) or len(P) == 1:
            return self._dense_general()
        P, chord = _catmull_knots(np.ascontiguousarray(P), bool(self.closed))
        # (numpy's own power, as in _catmull_segment: it gives the same for
        # a chord whether it is worked out once or for each dense point)
        step = np.maximum(chord, 1e-6) ** self.alpha
        if not _is_float64(step, 0) or step.shape != chord.shape:
            return self._dense_general()  # (an alpha that is no plain number)
        return _catmull_points(P, chord, step)

    def _dense_general(self):
        """The dense points, by numpy: for points that are not a plain array
        of float64 (they are, unless ``points`` was replaced), and what the
        compiled kernels repeat, operation for operation."""
        P = self.points
        if len(P) == 1:
            return P.copy(), np.zeros(1)
        if self.closed:
            P = np.vstack([P[-1], P, P[0], P[1]])
        else:  # reflect end points to get natural end tangents
            P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
        # all segments at once: segment i runs from P[i + 1] to P[i + 2]
        p0, p1, p2, p3 = P[:-3], P[1:-2], P[2:-1], P[3:]
        # samples per segment
        m = np.maximum(8, (np.linalg.norm(p2 - p1, axis=1) / 2).astype(int) + 1)
        seg = np.repeat(np.arange(len(m)), m)
        # 0..1 within each
        t = (np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)) * (1.0 / m[seg])
        pts = _catmull_segment(p0[seg], p1[seg], p2[seg], p3[seg], t, self.alpha)
        return np.vstack([pts, P[-2][None]]), np.concatenate(
            [seg + t, [float(len(P) - 3)]]
        )


def _catmull_segment(p0, p1, p2, p3, t, alpha):
    """Points at parameter t (0..1) on the Catmull-Rom segments from p1 to p2
    (one row of p0..p3 per value of t)."""

    def tj(ti, a, b):
        return ti + np.maximum(np.linalg.norm(b - a, axis=1), 1e-6) ** alpha

    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    tt = t1 + (t2 - t1) * t
    t1, t2, t3, tt = t1[:, None], t2[:, None], t3[:, None], tt[:, None]
    a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
    a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
    a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
    b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2
    b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3
    return (t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2


@njit(cache=True, error_model="numpy")
def _catmull_knots(points, closed):
    """The control points (n, 2), n > 1, with those a Catmull-Rom curve
    needs before the first and after the last (the path's own if it is
    closed, the end points reflected if not), and the length of the chord
    from each to the next."""
    n = points.shape[0]
    P = np.empty((n + 3 if closed else n + 2, 2))
    for c in range(2):
        for i in range(n):
            P[i + 1, c] = points[i, c]
        if closed:
            P[0, c] = points[n - 1, c]
            P[n + 1, c] = points[0, c]
            P[n + 2, c] = points[1, c]
        else:
            P[0, c] = 2.0 * points[0, c] - points[1, c]
            P[n + 1, c] = 2.0 * points[n - 1, c] - points[n - 2, c]
    chord = np.empty(P.shape[0] - 1)
    for i in range(chord.shape[0]):
        dx = P[i + 1, 0] - P[i, 0]
        dy = P[i + 1, 1] - P[i, 1]
        chord[i] = np.sqrt(dx * dx + dy * dy)
    return P, chord


@njit(cache=True, error_model="numpy")
def _catmull_points(P, chord, step):
    """The dense points and their knots of the Catmull-Rom curve through
    ``P[1:-2]`` (as :func:`_catmull_knots` gives them, with the chords):
    what :meth:`CatmullRom._dense_general` works out, to the bit. ``step``
    is the chords (1e-6 at least) to the power alpha: the knot intervals."""
    segments = P.shape[0] - 3
    total = 0
    for i in range(segments):
        total += max(8, int(chord[i + 1] / 2.0) + 1)
    pts = np.empty((total + 1, 2))
    knot = np.empty(total + 1)
    at = 0
    for i in range(segments):
        m = max(8, int(chord[i + 1] / 2.0) + 1)
        t0 = 0.0
        t1 = t0 + step[i]
        t2 = t1 + step[i + 1]
        t3 = t2 + step[i + 2]
        for j in range(m):
            t = j * (1.0 / m)
            tt = t1 + (t2 - t1) * t
            a1p0, a1p1 = (t1 - tt) / (t1 - t0), (tt - t0) / (t1 - t0)
            a2p1, a2p2 = (t2 - tt) / (t2 - t1), (tt - t1) / (t2 - t1)
            a3p2, a3p3 = (t3 - tt) / (t3 - t2), (tt - t2) / (t3 - t2)
            b1a1, b1a2 = (t2 - tt) / (t2 - t0), (tt - t0) / (t2 - t0)
            b2a2, b2a3 = (t3 - tt) / (t3 - t1), (tt - t1) / (t3 - t1)
            for c in range(2):
                a1 = a1p0 * P[i, c] + a1p1 * P[i + 1, c]
                a2 = a2p1 * P[i + 1, c] + a2p2 * P[i + 2, c]
                a3 = a3p2 * P[i + 2, c] + a3p3 * P[i + 3, c]
                b1 = b1a1 * a1 + b1a2 * a2
                b2 = b2a2 * a2 + b2a3 * a3
                pts[at, c] = a2p1 * b1 + a2p2 * b2
            knot[at] = i + t
            at += 1
    pts[total, 0] = P[segments + 1, 0]
    pts[total, 1] = P[segments + 1, 1]
    knot[total] = segments
    return pts, knot


class Bezier(Path):
    """Piecewise cubic Bezier:
    ``[anchor, handle, handle, anchor, handle, handle, anchor, ...]`` (3n + 1
    points). Knots are the anchors."""

    def __init__(self, points):
        P = _as_points(points, "Bezier")
        if (len(P) - 1) % 3 != 0 or len(P) < 4:
            raise ValueError(
                "Bezier needs 3n+1 points: anchor, handle, handle, anchor, ..."
            )
        self.points = P
        self.n_knots = (len(P) - 1) // 3 + 1

    def _state(self) -> object:
        return _snapshot(self.points), self.n_knots

    def _dense(self):
        pts, knots = [], []
        P = self.points
        for i in range(self.n_knots - 1):
            p0, p1, p2, p3 = P[3 * i : 3 * i + 4]
            approx = (
                np.linalg.norm(p1 - p0)
                + np.linalg.norm(p2 - p1)
                + np.linalg.norm(p3 - p2)
            )
            t = np.linspace(0.0, 1.0, max(8, int(approx / 2) + 1), endpoint=False)[
                :, None
            ]
            mt = 1 - t
            pts.append(
                mt**3 * p0 + 3 * mt * mt * t * p1 + 3 * mt * t * t * p2 + t**3 * p3
            )
            knots.append(i + t[:, 0])
        pts.append(P[-1][None])
        knots.append(np.array([float(self.n_knots - 1)]))
        return np.vstack(pts), np.concatenate(knots)


class Polyline(Path):
    """Straight segments between points."""

    def __init__(self, points):
        self.points = _as_points(points, "Polyline")
        self.n_knots = len(self.points)

    def _state(self) -> object:
        return _snapshot(self.points)

    def _dense(self):
        return self.points.copy(), np.arange(len(self.points), dtype=np.float64)


def as_path(path) -> Path:
    if isinstance(path, Path):
        return path
    return CatmullRom(path)


def evaluate_profile(
    profile: Profile, u: np.ndarray, knot: np.ndarray, n_knots: int
) -> np.ndarray:
    """Evaluate a per-stroke value (width, pressure, ...) along the samples.

    * scalar -> constant
    * sequence with one value per control point -> interpolated between knots
    * any other sequence -> spread evenly along the stroke length
    * callable f(u) with u in 0..1 along the stroke. It is called once with
      the whole array of u; if it only takes a single number (it raises
      TypeError or ValueError on the array, as ``30 if u < 0.5 else 10``
      does), it is called again for each u.
    """
    if callable(profile):
        f: Callable[[Any], Any] = profile
        try:
            values = f(u)
        except (TypeError, ValueError) as array_error:
            try:
                values = [f(x) for x in u.tolist()]
            except Exception as error:
                error.add_note(
                    "(raised calling the profile with each u, after calling it "
                    f"with the array of all u raised {array_error!r})"
                )
                raise error from array_error
        return _profile_values(values, u)
    arr = np.asarray(profile, dtype=np.float64)
    if arr.ndim == 0:
        return np.full_like(u, float(arr))
    if arr.size == 1:
        return np.full_like(u, float(arr[0]))
    if arr.size == n_knots:
        return np.interp(knot, np.arange(n_knots), arr)
    return np.interp(u, np.linspace(0, 1, arr.size), arr)


def _profile_values(values, u: np.ndarray) -> np.ndarray:
    """What a profile function returned, as one value per u: it must be a
    number, or numbers shaped like u (or that spread to its shape)."""
    raw = np.asarray(values)
    if raw.dtype.kind not in "biuf":
        raise TypeError(f"a profile function must return numbers, got {values!r:.80}")
    try:
        fits = np.broadcast_shapes(raw.shape, u.shape) == u.shape
    except ValueError:
        fits = False
    if not fits:
        raise ValueError(
            "a profile function must return a number, or an array of one "
            f"number per u (shape {u.shape}); got shape {raw.shape}"
        )
    return raw.astype(np.float64) * np.ones_like(u)
