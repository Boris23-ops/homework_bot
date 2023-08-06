class ConnectApiError(Exception):
    """Ошибка соединения с API."""

    pass


class InvalidResponse(Exception):
    """Ошибка в запросе API."""

    pass
