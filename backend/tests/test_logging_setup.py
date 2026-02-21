import logging

from hound_core.logging_setup import configure_logging


def test_configure_logging_writes_log_file(tmp_path) -> None:
    log_path = tmp_path / "hound.log"

    configure_logging(log_path=log_path)
    logger = logging.getLogger("hound.test")
    logger.info("hello logging")

    for handler in logging.getLogger().handlers:
        handler.flush()

    assert log_path.exists()
    assert "hello logging" in log_path.read_text(encoding="utf-8")
