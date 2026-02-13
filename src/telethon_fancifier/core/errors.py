from __future__ import annotations


class AppError(Exception):
    """Исключение с безопасным пользовательским сообщением."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message
