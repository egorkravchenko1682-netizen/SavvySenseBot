from __future__ import annotations

from typing import Any

from .result import MatchResult


class RejectedFilter:
    """
    Фильтр неподходящих предложений SAVVY SENSE.

    Задача:
        MatchResult
            ↓
        REJECTED → исключить
        EXACT    → оставить
        SIMILAR  → оставить

    Важно:
    фильтр не принимает решение о том,
    является ли товар EXACT/SIMILAR/REJECTED.

    Это делает ProductMatcher.

    RejectedFilter только применяет
    уже полученный результат.
    """

    def filter(
        self,
        offers: list[dict[str, Any]],
        match_results: list[MatchResult],
    ) -> list[dict[str, Any]]:
        """
        Возвращает только допустимые предложения.

        Позиция offer[i] соответствует
        match_results[i].
        """

        if not offers:
            return []

        if not match_results:
            return []

        filtered = []

        for index, offer in enumerate(offers):

            if index >= len(match_results):
                continue

            result = match_results[index]

            if result.is_rejected:
                continue

            filtered.append(
                offer
            )

        return filtered

    def split(
        self,
        offers: list[dict[str, Any]],
        match_results: list[MatchResult],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Разделяет предложения на:

            exact
            similar
            rejected
        """

        result = {
            "exact": [],
            "similar": [],
            "rejected": [],
        }

        if not offers:
            return result

        if not match_results:
            return result

        for index, offer in enumerate(offers):

            if index >= len(match_results):
                continue

            match_result = match_results[index]

            if match_result.is_exact:
                result["exact"].append(
                    offer
                )

            elif match_result.is_similar:
                result["similar"].append(
                    offer
                )

            elif match_result.is_rejected:
                result["rejected"].append(
                    offer
                )

        return result

    @staticmethod
    def is_allowed(
        match_result: MatchResult,
    ) -> bool:
        """
        Проверяет, может ли предложение
        продолжать обработку.
        """

        return not match_result.is_rejected

    @staticmethod
    def is_rejected(
        match_result: MatchResult,
    ) -> bool:
        return match_result.is_rejected

    @staticmethod
    def reason(
        match_result: MatchResult,
    ) -> str:
        """
        Возвращает причину отклонения.
        """

        if not match_result.is_rejected:
            return ""

        if match_result.reasons:
            return "; ".join(
                match_result.reasons
            )

        if match_result.mismatched_attributes:
            return (
                "Несовпадение характеристик: "
                + ", ".join(
                    match_result.mismatched_attributes
                )
            )

        return "Предложение не соответствует запросу."