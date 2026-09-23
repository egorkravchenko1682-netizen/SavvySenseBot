from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    """
    Базовый контракт для модулей извлечения данных.

    Каждый extractor:
    - получает структурированные данные;
    - при необходимости получает текст;
    - возвращает словарь извлечённых значений.

    Extractor не должен:
    - обращаться к Telegram;
    - выполнять поиск;
    - принимать решения о совпадении;
    - рассчитывать итоговую стоимость;
    - изменять исходные данные.
    """

    @abstractmethod
    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """
        Извлекает данные из источника.

        Args:
            data:
                Структурированные данные страницы,
                JSON-LD или уже подготовленный словарь.

            text:
                Текст страницы или товара.

        Returns:
            Словарь извлечённых значений.
        """

        raise NotImplementedError

    @staticmethod
    def is_valid_value(
        value: Any,
    ) -> bool:
        """
        Проверяет, является ли значение пригодным
        для дальнейшей обработки.
        """

        if value is None:
            return False

        if isinstance(
            value,
            str,
        ):
            return bool(
                value.strip()
            )

        if isinstance(
            value,
            (list, tuple, dict),
        ):
            return bool(value)

        return True

    @staticmethod
    def clean_text(
        value: Any,
    ) -> str | None:
        """
        Безопасно приводит значение к строке.
        """

        if value is None:
            return None

        text = str(
            value
        ).strip()

        return text or None