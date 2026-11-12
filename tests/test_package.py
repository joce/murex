import murex


def test_the_package_knows_its_version():
    assert isinstance(murex.__version__, str)
    assert murex.__version__


def test_everything_exported_exists():
    for name in murex.__all__:
        assert getattr(murex, name) is not None, name
