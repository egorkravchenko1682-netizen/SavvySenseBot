from __future__ import annotations

import re
from typing import Any

from offer.models import CanonicalOffer, ProductData
from matching.result import (
    AttributeComparison,
    AttributeStatus,
    MatchResult,
    MatchStatus,
)


class ProductMatcher:
    """
    Strict Product Matching Engine.

    Главный принцип:

    1. Сначала проверяем идентичность товара.
    2. Затем проверяем обязательные атрибуты.
    3. MISMATCH обязательного параметра = REJECTED.
    4. UNKNOWN обязательного параметра = не EXACT.
    5. Score используется только для оценки качества
       совпадения и НЕ определяет идентичность товара.
    """

    ACCESSORY_WORDS = {
        "case",
        "cover",
        "cable",
        "charger",
        "adapter",
        "holder",
        "stand",
        "screen protector",
        "glass",
        "film",
        "strap",
        "bag",
        "wallet",
        "keyboard",
        "mouse",
        "battery",
        "replacement",
        "replacement part",
        "spare part",
        "accessory",
        "аксессуар",
        "чехол",
        "зарядка",
        "зарядное",
        "кабель",
        "переходник",
        "держатель",
        "подставка",
        "защитное стекло",
        "стекло",
        "плёнка",
        "пленка",
        "ремешок",
        "сумка",
        "кошелёк",
        "клавиатура",
        "мышь",
        "аккумулятор",
        "батарея",
        "запчасть",
        "деталь",
        "дисплей",
    }

    INFORMATIONAL_WORDS = {
        "manual",
        "review",
        "reviews",
        "support",
        "specs",
        "specifications",
        "news",
        "article",
        "guide",
        "инструкция",
        "обзор",
        "отзывы",
        "поддержка",
        "характеристики",
        "новости",
        "статья",
    }

    ATTRIBUTE_ALIASES = {
        "white": {
            "white",
            "белый",
            "белая",
            "белое",
            "белые",
        },
        "белый": {
            "white",
            "белый",
            "белая",
            "белое",
            "белые",
        },
        "black": {
            "black",
            "черный",
            "чёрный",
            "черная",
            "чёрная",
            "черное",
            "чёрное",
        },
        "черный": {
            "black",
            "черный",
            "чёрный",
            "черная",
            "чёрная",
            "черное",
            "чёрное",
        },
        "blue": {
            "blue",
            "синий",
            "синяя",
            "синее",
        },
        "синий": {
            "blue",
            "синий",
            "синяя",
            "синее",
        },
    }

    PRODUCT_TYPE_ALIASES = {
        "smartphone": {
            "smartphone",
            "phone",
            "mobile phone",
            "iphone",
            "смартфон",
            "телефон",
        },
        "phone": {
            "smartphone",
            "phone",
            "mobile phone",
            "iphone",
            "смартфон",
            "телефон",
        },
        "polo": {
            "polo",
            "polo shirt",
            "поло",
        },
        "tshirt": {
            "tshirt",
            "t shirt",
            "t-shirt",
            "футболка",
        },
        "tank top": {
            "tank top",
            "tank",
            "майка",
        },
    }

    CATEGORY_ALIASES = {
        "smartphone": {
            "smartphone",
            "phone",
            "mobile phone",
            "смартфон",
            "телефон",
        },
        "clothing": {
            "clothing",
            "одежда",
        },
        "shirt": {
            "shirt",
            "рубашка",
        },
        "polo": {
            "polo",
            "polo shirt",
            "поло",
        },
        "tshirt": {
            "tshirt",
            "t-shirt",
            "t shirt",
            "футболка",
        },
        "tank top": {
            "tank top",
            "майка",
        },
    }

    def match(
        self,
        product: dict[str, Any] | dict[str, Any],
        offer: CanonicalOffer | dict[str, Any],
    ) -> MatchResult:
        """
        Основная точка входа.

        Поддерживает:
        - Product DNA как dict
        - CanonicalOffer
        - legacy offer dict
        """

        requested = self._build_requested_attributes(
            product
        )

        offered = self._build_offered_attributes(
            offer
        )

        title = self._normalize(
            offered.get("title")
        )

        result = MatchResult(
            status=MatchStatus.SIMILAR
        )

        # ---------------------------------------------
        # 1. Фильтр аксессуаров / запчастей
        # ---------------------------------------------

        if self._contains_any(
            title,
            self.ACCESSORY_WORDS,
        ):
            result.status = MatchStatus.REJECTED
            result.identity_match = False
            result.score = 0
            result.add_reason(
                "accessory_or_spare_part"
            )
            return result

        # ---------------------------------------------
        # 2. Фильтр информационных страниц
        # ---------------------------------------------

        if self._contains_any(
            title,
            self.INFORMATIONAL_WORDS,
        ):
            result.status = MatchStatus.REJECTED
            result.identity_match = False
            result.score = 0
            result.add_reason(
                "informational_page"
            )
            return result

        # ---------------------------------------------
        # 3. Проверяем identity
        # ---------------------------------------------

        identity_checks = [
            (
                "brand",
                requested.get("brand"),
                offered.get("brand"),
            ),
            (
                "model",
                requested.get("model"),
                offered.get("model"),
            ),
            (
                "product_type",
                requested.get("product_type"),
                offered.get("product_type"),
            ),
            (
                "category",
                requested.get("category"),
                offered.get("category"),
            ),
        ]

        for (
            attribute,
            requested_value,
            offered_value,
        ) in identity_checks:

            if not requested_value:
                continue

            comparison = self._compare_attribute(
                attribute=attribute,
                requested_value=requested_value,
                offered_value=offered_value,
                title=title,
            )

            result.add_comparison(
                comparison
            )

            if (
                comparison.status
                == AttributeStatus.MISMATCH
            ):
                result.status = MatchStatus.REJECTED
                result.identity_match = False
                result.score = 0

                result.add_reason(
                    f"{attribute}_mismatch"
                )

                return result

        # ---------------------------------------------
        # 4. Обязательные атрибуты из Product DNA
        # ---------------------------------------------

        required_attributes = (
            requested.get(
                "required_attributes",
                {},
            )
        )

        if not isinstance(
            required_attributes,
            dict,
        ):
            required_attributes = {}

        for (
            attribute,
            requested_value,
        ) in required_attributes.items():

            if not requested_value:
                continue

            # Identity уже проверили отдельно.
            if attribute in {
                "brand",
                "model",
                "product_type",
            }:
                continue

            offered_value = offered.get(
                attribute
            )

            comparison = self._compare_attribute(
                attribute=attribute,
                requested_value=requested_value,
                offered_value=offered_value,
                title=title,
            )

            result.add_comparison(
                comparison
            )

            if (
                comparison.status
                == AttributeStatus.MISMATCH
            ):
                result.status = MatchStatus.REJECTED
                result.identity_match = False
                result.score = 0

                result.add_reason(
                    f"{attribute}_mismatch"
                )

                return result

        # ---------------------------------------------
        # 5. Проверяем identity outcome
        # ---------------------------------------------

        identity_unknown = any(
            comparison.status
            == AttributeStatus.UNKNOWN
            for comparison in result.comparisons
            if comparison.attribute
            in {
                "brand",
                "model",
                "product_type",
                "category",
            }
        )

        identity_match = not identity_unknown

        result.identity_match = (
            identity_match
        )

        # ---------------------------------------------
        # 6. UNKNOWN обязательных атрибутов
        # ---------------------------------------------

        required_unknown = [
            comparison.attribute
            for comparison in result.comparisons
            if (
                comparison.status
                == AttributeStatus.UNKNOWN
                and comparison.attribute
                in required_attributes
            )
        ]

        # ---------------------------------------------
        # 7. Score
        #
        # Score НЕ определяет EXACT.
        # ---------------------------------------------

        result.score = self._calculate_score(
            result
        )

        # ---------------------------------------------
        # 8. Финальная классификация
        # ---------------------------------------------

        if not identity_match:
            result.status = MatchStatus.SIMILAR

            result.add_reason(
                "identity_unconfirmed"
            )

            return result

        if required_unknown:
            result.status = MatchStatus.SIMILAR

            result.add_reason(
                "required_attributes_unconfirmed"
            )

            return result

        result.status = MatchStatus.EXACT

        result.add_reason(
            "all_required_attributes_confirmed"
        )

        return result

    # =================================================
    # REQUESTED
    # =================================================

    def _build_requested_attributes(
        self,
        product: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            product,
            dict,
        ):
            return {}

        attributes = product.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        required_attributes = product.get(
            "required_attributes",
            {},
        )

        if not isinstance(
            required_attributes,
            dict,
        ):
            required_attributes = {}

        merged_attributes = dict(
            attributes
        )

        merged_attributes.update(
            required_attributes
        )

        result = {
            "name": product.get(
                "name"
            ),
            "brand": product.get(
                "brand"
            ),
            "category": product.get(
                "category"
            ),
            "product_type": product.get(
                "product_type"
            )
            or product.get(
                "type"
            ),
            "model": product.get(
                "model"
            ),
            "required_attributes":
                required_attributes,
        }

        for (
            key,
            value,
        ) in merged_attributes.items():

            if key not in result:
                result[key] = value

        return result

    # =================================================
    # OFFER
    # =================================================

    def _build_offered_attributes(
        self,
        offer: CanonicalOffer | dict[str, Any],
    ) -> dict[str, Any]:

        if isinstance(
            offer,
            CanonicalOffer,
        ):
            product = offer.product

            result = {
                "title": product.title,
                "brand": product.brand,
                "model": product.model,
                "product_type":
                    product.product_type,
                "category":
                    product.category,
            }

            result.update(
                product.attributes
            )

            return result

        if not isinstance(
            offer,
            dict,
        ):
            return {}

        product = offer.get(
            "product",
            {},
        )

        if not isinstance(
            product,
            dict,
        ):
            product = {}

        attributes = product.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        result = {
            "title": (
                product.get("title")
                or offer.get("title")
                or ""
            ),
            "brand": (
                product.get("brand")
                or offer.get("brand")
            ),
            "model": (
                product.get("model")
                or offer.get("model")
            ),
            "product_type": (
                product.get(
                    "product_type"
                )
                or offer.get(
                    "product_type"
                )
            ),
            "category": (
                product.get("category")
                or offer.get("category")
            ),
        }

        result.update(
            attributes
        )

        # Поддержка legacy-полей.
        for key in (
            "storage",
            "color",
            "size",
            "gender",
            "material",
            "capacity",
            "voltage",
            "quantity",
            "weight",
            "dimensions",
            "compatibility",
            "season",
            "condition",
        ):
            if (
                key not in result
                or result[key] is None
            ):
                result[key] = offer.get(
                    key
                )

        return result

    # =================================================
    # ATTRIBUTE COMPARISON
    # =================================================

    def _compare_attribute(
        self,
        attribute: str,
        requested_value: Any,
        offered_value: Any,
        title: str,
    ) -> AttributeComparison:

        if not requested_value:
            return AttributeComparison(
                attribute=attribute,
                requested=requested_value,
                actual=offered_value,
                status=AttributeStatus.UNKNOWN,
                reason="not_requested",
            )

        requested = self._normalize(
            requested_value
        )

        offered = self._normalize(
            offered_value
        )

        # ---------------------------------------------
        # Значение есть непосредственно в offer
        # ---------------------------------------------

        if offered:

            if self._values_match(
                attribute,
                requested,
                offered,
            ):
                return AttributeComparison(
                    attribute=attribute,
                    requested=requested_value,
                    actual=offered_value,
                    status=AttributeStatus.MATCH,
                    reason="direct_match",
                )

            return AttributeComparison(
                attribute=attribute,
                requested=requested_value,
                actual=offered_value,
                status=AttributeStatus.MISMATCH,
                reason="direct_mismatch",
            )

        # ---------------------------------------------
        # Значения нет в structured data.
        # Пробуем title.
        # ---------------------------------------------

        if self._value_in_text(
            attribute,
            requested,
            title,
        ):
            return AttributeComparison(
                attribute=attribute,
                requested=requested_value,
                actual=None,
                status=AttributeStatus.MATCH,
                reason="confirmed_by_title",
            )

        # ---------------------------------------------
        # Нет подтверждения.
        #
        # Это UNKNOWN, а не MISMATCH.
        # ---------------------------------------------

        return AttributeComparison(
            attribute=attribute,
            requested=requested_value,
            actual=None,
            status=AttributeStatus.UNKNOWN,
            reason="not_confirmed",
        )

    # =================================================
    # VALUE MATCHING
    # =================================================

    def _values_match(
        self,
        attribute: str,
        requested: str,
        offered: str,
    ) -> bool:

        if requested == offered:
            return True

        if attribute in {
            "category",
            "product_type",
        }:
            return self._semantic_match(
                requested,
                offered,
                self.PRODUCT_TYPE_ALIASES
                if attribute == "product_type"
                else self.CATEGORY_ALIASES,
            )

        if attribute == "storage":
            requested_gb = (
                self._extract_storage_gb(
                    requested
                )
            )

            offered_gb = (
                self._extract_storage_gb(
                    offered
                )
            )

            if (
                requested_gb is not None
                and offered_gb is not None
            ):
                return (
                    requested_gb
                    == offered_gb
                )

        aliases = self._attribute_aliases(
            requested
        )

        normalized_offered = self._normalize(
            offered
        )

        if normalized_offered in aliases:
            return True

        if requested in normalized_offered:
            return True

        if normalized_offered in requested:
            return True

        return False

    def _value_in_text(
        self,
        attribute: str,
        requested: str,
        title: str,
    ) -> bool:

        if not title:
            return False

        if attribute == "storage":
            requested_gb = (
                self._extract_storage_gb(
                    requested
                )
            )

            title_gb = (
                self._extract_storage_gb(
                    title
                )
            )

            if (
                requested_gb is not None
                and title_gb is not None
            ):
                return (
                    requested_gb
                    == title_gb
                )

            return False

        if attribute in {
            "product_type",
            "category",
        }:
            aliases = (
                self.PRODUCT_TYPE_ALIASES
                if attribute == "product_type"
                else self.CATEGORY_ALIASES
            )

            return self._semantic_text_match(
                requested,
                title,
                aliases,
            )

        if requested in title:
            return True

        return self._contains_any(
            title,
            self._attribute_aliases(
                requested
            ),
        )

    # =================================================
    # SEMANTIC GROUPS
    # =================================================

    def _semantic_match(
        self,
        requested: str,
        offered: str,
        groups: dict[str, set[str]],
    ) -> bool:

        requested = self._normalize(
            requested
        )

        offered = self._normalize(
            offered
        )

        if requested == offered:
            return True

        for group in groups.values():

            normalized_group = {
                self._normalize(value)
                for value in group
            }

            if (
                requested in normalized_group
                and offered in normalized_group
            ):
                return True

        return False

    def _semantic_text_match(
        self,
        requested: str,
        title: str,
        groups: dict[str, set[str]],
    ) -> bool:

        requested = self._normalize(
            requested
        )

        for group in groups.values():

            normalized_group = {
                self._normalize(value)
                for value in group
            }

            if requested not in normalized_group:
                continue

            for value in normalized_group:
                if value in title:
                    return True

        return False

    # =================================================
    # SCORE
    # =================================================

    def _calculate_score(
        self,
        result: MatchResult,
    ) -> float:

        total = len(
            result.comparisons
        )

        if total == 0:
            return 0.0

        matched = len(
            result.matched_attributes
        )

        unknown = len(
            result.unknown_attributes
        )

        mismatched = len(
            result.mismatched_attributes
        )

        if mismatched:
            return 0.0

        score = (
            matched / total
        ) * 100

        # UNKNOWN снижает уверенность,
        # но не превращается автоматически
        # в rejection.
        if unknown:
            score *= 0.75

        return round(
            min(score, 100.0),
            2,
        )

    # =================================================
    # STORAGE
    # =================================================

    @staticmethod
    def _extract_storage_gb(
        text: str | None,
    ) -> int | None:

        if not text:
            return None

        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*"
            r"(tb|gb|гб|тб)\b",
            text.lower(),
        )

        if not match:
            return None

        value = float(
            match.group(1)
        )

        unit = match.group(2)

        if unit in {
            "tb",
            "тб",
        }:
            value *= 1024

        return int(value)

    # =================================================
    # NORMALIZATION
    # =================================================

    @staticmethod
    def _normalize(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        text = str(
            value
        ).lower().strip()

        text = (
            text
            .replace("-", " ")
            .replace("_", " ")
            .replace("/", " ")
            .replace("ё", "е")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    # =================================================
    # ALIASES
    # =================================================

    def _attribute_aliases(
        self,
        value: str,
    ) -> set[str]:

        normalized = self._normalize(
            value
        )

        return self.ATTRIBUTE_ALIASES.get(
            normalized,
            {normalized},
        )

    # =================================================
    # TEXT SEARCH
    # =================================================

    def _contains_any(
        self,
        text: str,
        values: set[str],
    ) -> bool:

        normalized_text = self._normalize(
            text
        )

        for value in values:

            normalized_value = (
                self._normalize(value)
            )

            if not normalized_value:
                continue

            if normalized_value in normalized_text:
                return True

        return False