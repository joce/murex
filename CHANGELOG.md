# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-11-12

The first release. There is no 0.1.0: an unrelated project that once had this
name on PyPI used that version number in 2017, and PyPI never lets a file name
be used twice.

### Added

- The modules oilpaint and fusain share, taken from oilpaint as they are:
  `spectral` (colour science and Kubelka-Munk mixing), `spline` (stroke paths
  and profiles), `noise` (textures), `reference` (reference images), `png`
  and `filters` (oilpaint's `_filters`, with public names).
- `Pigment`: oilpaint's `Paint` without what is particular to oil paint
  (its body).

[Unreleased]: https://github.com/joce/murex/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/joce/murex/releases/tag/v0.1.1
