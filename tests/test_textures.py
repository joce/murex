"""Noise, filters and PNG output: shapes, ranges, repeatability."""

import struct
import zlib

import numpy as np
import pytest

from murex import filters, noise, write_png

FIELDS = {
    "value": lambda h, w, rng: noise.value_noise_2d(h, w, 6.0, rng),
    "fractal": lambda h, w, rng: noise.fractal_noise_2d(h, w, 8.0, rng),
    "weave": lambda h, w, rng: noise.canvas_weave(h, w, 5.0, rng),
    "aniso": lambda h, w, rng: noise.aniso_noise(h, w, 20.0, 3.0, 30.0, rng),
    "woven": lambda h, w, rng: noise.woven(h, w, 5.0, rng),
    "twill": lambda h, w, rng: noise.woven(h, w, 5.0, rng, twill=True),
    "paper": lambda h, w, rng: noise.paper(h, w, 3.0, rng),
    "wood": lambda h, w, rng: noise.wood(h, w, 8.0, 20.0, rng),
    "brushmarks": lambda h, w, rng: noise.brushmarks(h, w, 15.0, rng),
}


@pytest.mark.parametrize("name", FIELDS)
def test_a_texture_is_a_finite_field_that_repeats_with_its_seed(name):
    make = FIELDS[name]
    a = make(40, 56, np.random.default_rng(7))
    assert a.shape == (40, 56)
    assert np.isfinite(a).all() and a.std() > 0
    np.testing.assert_array_equal(a, make(40, 56, np.random.default_rng(7)))
    assert not np.array_equal(a, make(40, 56, np.random.default_rng(8)))


def test_noise_along_a_line():
    a = noise.value_noise_1d(100, 9.0, np.random.default_rng(1))
    assert a.shape == (100,) and np.isfinite(a).all() and a.std() > 0


def test_box_blur_keeps_the_mean_of_a_flat_field_and_the_type():
    flat = np.full((9, 12), 3.0, np.float32)
    out = filters.box_blur(flat, 2)
    assert out.dtype == np.float32
    np.testing.assert_allclose(out, 3.0)
    assert filters.box_blur(flat, 0) is flat
    spike = np.zeros((9, 12))
    spike[4, 6] = 1.0
    np.testing.assert_allclose(filters.box_blur(spike, 1).sum(), 1.0)
    along = filters.box_blur(spike, 1, axis=1)
    np.testing.assert_allclose(along[4, 5:8], 1 / 3)
    assert along[3].sum() == 0


def test_max_filter_and_smoothing():
    spike = np.zeros((9, 12), np.float32)
    spike[4, 6] = 1.0
    grown = filters.max_filter(spike, 1)
    assert grown.sum() == 9 and grown[3:6, 5:8].all()
    soft = filters.smooth121(spike)
    np.testing.assert_allclose(soft.sum(), 1.0, rtol=1e-6)
    assert soft[4, 6] == 0.25


def test_smoothstep_and_bilinear():
    x = np.array([-1.0, 0.0, 0.5, 1.0, 2.0])
    np.testing.assert_allclose(filters.smoothstep(0.0, 1.0, x), [0, 0, 0.5, 1, 1])
    grid = np.arange(12.0).reshape(3, 4)
    y, x = np.array([0.0, 0.5, 2.0]), np.array([0.0, 1.5, 3.0])
    np.testing.assert_allclose(filters.bilinear(grid, y, x), [0.0, 3.5, 11.0])
    rgb = np.repeat(grid[:, :, None], 3, axis=2)
    np.testing.assert_allclose(filters.bilinear(rgb, y, x)[1], [3.5, 3.5, 3.5])


def _chunks(data: bytes):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    at = 8
    while at < len(data):
        (n,) = struct.unpack(">I", data[at : at + 4])
        tag, body = data[at + 4 : at + 8], data[at + 8 : at + 8 + n]
        (crc,) = struct.unpack(">I", data[at + 8 + n : at + 12 + n])
        assert crc == zlib.crc32(tag + body)
        yield tag, body
        at += 12 + n


@pytest.mark.parametrize("channels", [None, 1, 3, 4])
def test_png_holds_the_pixels_it_was_given(tmp_path, channels):
    rng = np.random.default_rng(5)
    shape = (6, 9) if channels is None else (6, 9, channels)
    img = rng.integers(0, 256, shape, dtype=np.uint8)
    path = tmp_path / "out.png"
    write_png(str(path), img)
    chunks = dict(_chunks(path.read_bytes()))
    w, h, depth, color_type = struct.unpack(">IIBB", chunks[b"IHDR"][:10])
    c = channels or 1
    assert (w, h, depth, color_type) == (9, 6, 8, {1: 0, 3: 2, 4: 6}[c])
    raw = zlib.decompress(chunks[b"IDAT"])
    rows = np.frombuffer(raw, np.uint8).reshape(6, 1 + 9 * c)
    assert (rows[:, 0] == 0).all()
    np.testing.assert_array_equal(rows[:, 1:].reshape(6, 9, c), img.reshape(6, 9, c))
