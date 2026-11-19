from murex import fusain


def test_everything_exported_exists():
    for name in fusain.__all__:
        assert getattr(fusain, name) is not None, name
