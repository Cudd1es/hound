from hound_core.version import __version__


def test_version_prefix() -> None:
    assert __version__.startswith("0.")
