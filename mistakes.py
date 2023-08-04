class ConnectApiError(Exception):
    """Ошибка соединения с API."""

    pass


class InvalidResponse(Exception):
    """Ошибка в запросе API."""

    pass


class MainError(Exception):
    """Ошибка в основном теле цикла."""

    pass


class NotHomeworkName(Exception):
    """Нет homework_name в homework."""

    pass
