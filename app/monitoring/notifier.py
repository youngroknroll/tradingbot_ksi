from app.core.logging import get_logger

logger = get_logger(__name__)


class ConsoleNotifier:
    def notify(self, title: str, message: str) -> None:
        logger.info("notification", title=title, message=message)

    def alert(self, title: str, message: str) -> None:
        logger.warning("alert", title=title, message=message)

    def error(self, title: str, message: str) -> None:
        logger.error("error_alert", title=title, message=message)
