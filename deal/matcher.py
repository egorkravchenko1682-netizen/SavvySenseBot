import re
from typing import Any


class ProductMatcher:
    """
    Строгий Product Matching Engine для SAVVY SENSE.

    Задача:
    определить, является ли найденный результат тем товаром,
    который действительно запросил пользователь.

    Результаты:

    exact
        Товар соответствует обязательным параметрам.

    similar
        Товар похож, но отличается по одному или нескольким
        параметрам, которые не являются критическими.

    rejected
        Товар не соответствует запросу и не должен попадать
        в основной результат.
    """

    ACCESSORY_WORDS = {
        "case",
        "cover",
        "cable",
        "charger",
        "adapter",
        "holder",
        "stand",
        "screen",
        "protector",
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
        "part",
        "accessory",
        "аксессуар",
        "чехол",
        "зарядка",
        "зарядное",
        "кабель",
        "переходник",
        "держатель",
        "подставка",
        "стекло",
        "защитное стекло",
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
        "экран",
        "аксессуары",
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

    def match(
        self,
        product: dict[str, Any],
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        requested = self._build_requested_attributes(
            product
        )

        offered = self._build_offered_attributes(
            offer
        )

        title = self._get_offer_title(
            offer
        )

        normalized_title = self._normalize(
            title
        )

        # ---------------------------------
        # 1. Очевидный аксессуар / запчасть
        # ---------------------------------

        accessory = self._contains_any(
            normalized_title,
            self.ACCESSORY_WORDS,
        )

        if accessory:

            return self._result(
                match_type="rejected",
                score=0,
                reason="accessory_or_spare_part",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 2. Информационная страница
        # ---------------------------------

        informational = self._contains_any(
            normalized_title,
            self.INFORMATIONAL_WORDS,
        )

        if informational:

            return self._result(
                match_type="rejected",
                score=0,
                reason="informational_page",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 3. Проверка категории
        # ---------------------------------

        category_result = (
            self._check_category(
                requested,
                offered,
                normalized_title,
            )
        )

        if category_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_product_category",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 4. Проверка бренда
        # ---------------------------------

        brand_result = self._check_brand(
            requested,
            offered,
            normalized_title,
        )

        if brand_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_brand",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 5. Проверка модели
        # ---------------------------------

        model_result = self._check_model(
            requested,
            offered,
            normalized_title,
        )

        if model_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_model",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 6. Проверка обязательных атрибутов
        # ---------------------------------

        attribute_result = (
            self._check_required_attributes(
                requested,
                offered,
                normalized_title,
            )
        )

        if attribute_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="required_attribute_mismatch",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 7. Проверка типа товара
        # ---------------------------------

        product_type_result = (
            self._check_product_type(
                requested,
                offered,
                normalized_title,
            )
        )

        if product_type_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_product_type",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 8. Проверка цвета
        # ---------------------------------

        color_result = self._check_attribute(
            requested_value=requested.get(
                "color"
            ),
            offered_value=offered.get(
                "color"
            ),
            title=normalized_title,
        )

        if color_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_color",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 9. Проверка размера
        # ---------------------------------

        size_result = self._check_attribute(
            requested_value=requested.get(
                "size"
            ),
            offered_value=offered.get(
                "size"
            ),
            title=normalized_title,
        )

        if size_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_size",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 10. Проверка памяти
        # ---------------------------------

        storage_result = self._check_storage(
            requested,
            offered,
            normalized_title,
        )

        if storage_result == "rejected":

            return self._result(
                match_type="rejected",
                score=0,
                reason="wrong_storage",
                requested=requested,
                offered=offered,
            )

        # ---------------------------------
        # 11. Итоговая оценка
        # ---------------------------------

        score = self._calculate_score(
            requested,
            offered,
            normalized_title,
        )

        if score >= 90:

            match_type = "exact"

        elif score >= 65:

            match_type = "similar"

        else:

            match_type = "rejected"

        return self._result(
            match_type=match_type,
            score=score,
            reason="matched",
            requested=requested,
            offered=offered,
        )

    # ==================================================
    # REQUESTED ATTRIBUTES
    # ==================================================

    def _build_requested_attributes(
        self,
        product: dict[str, Any],
    ) -> dict[str, Any]:

        attributes = product.get(
            "attributes",
            {},
        )

        return {
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
            "storage": attributes.get(
                "storage"
            ),
            "color": attributes.get(
                "color"
            ),
            "size": attributes.get(
                "size"
            ),
            "gender": attributes.get(
                "gender"
            ),
            "material": attributes.get(
                "material"
            ),
        }

    # ==================================================
    # OFFER ATTRIBUTES
    # ==================================================

    def _build_offered_attributes(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

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

        return {
            "name": product.get(
                "title"
            )
            or offer.get(
                "title"
            ),
            "brand": product.get(
                "brand"
            )
            or offer.get(
                "brand"
            ),
            "category": product.get(
                "category"
            )
            or offer.get(
                "category"
            ),
            "product_type": (
                product.get(
                    "product_type"
                )
                or offer.get(
                    "product_type"
                )
            ),
            "model": product.get(
                "model"
            )
            or offer.get(
                "model"
            ),
            "storage": attributes.get(
                "storage"
            )
            or offer.get(
                "storage"
            ),
            "color": attributes.get(
                "color"
            )
            or offer.get(
                "color"
            ),
            "size": attributes.get(
                "size"
            )
            or offer.get(
                "size"
            ),
            "gender": attributes.get(
                "gender"
            )
            or offer.get(
                "gender"
            ),
            "material": attributes.get(
                "material"
            )
            or offer.get(
                "material"
            ),
        }

    # ==================================================
    # TITLE
    # ==================================================

    @staticmethod
    def _get_offer_title(
        offer: dict[str, Any],
    ) -> str:

        product = offer.get(
            "product",
            {},
        )

        if isinstance(
            product,
            dict,
        ):

            title = product.get(
                "title"
            )

            if title:
                return str(title)

        return str(
            offer.get(
                "title",
                "",
            )
        )

    # ==================================================
    # CATEGORY
    # ==================================================

    def _check_category(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        requested_category = self._normalize(
            requested.get("category")
        )

        offered_category = self._normalize(
            offered.get("category")
        )

        if (
            requested_category
            and offered_category
        ):

            if not self._category_compatible(
                requested_category,
                offered_category,
            ):
                return "rejected"

        return "ok"

    def _category_compatible(
        self,
        requested: str,
        offered: str,
    ) -> bool:

        if requested == offered:
            return True

        groups = [
            {
                "smartphone",
                "phone",
                "mobile phone",
                "смартфон",
                "телефон",
            },
            {
                "clothing",
                "одежда",
            },
            {
                "shirt",
                "рубашка",
            },
            {
                "polo",
                "polo shirt",
                "поло",
            },
            {
                "tshirt",
                "t-shirt",
                "футболка",
            },
            {
                "tank top",
                "майка",
            },
        ]

        for group in groups:

            if requested in group:

                if offered in group:
                    return True

        return False

    # ==================================================
    # BRAND
    # ==================================================

    def _check_brand(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        brand = self._normalize(
            requested.get("brand")
        )

        if not brand:
            return "ok"

        offered_brand = self._normalize(
            offered.get("brand")
        )

        if offered_brand:

            if brand != offered_brand:

                return "rejected"

            return "ok"

        if brand not in title:

            return "rejected"

        return "ok"

    # ==================================================
    # MODEL
    # ==================================================

    def _check_model(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        model = self._normalize(
            requested.get("model")
        )

        name = self._normalize(
            requested.get("name")
        )

        offered_model = self._normalize(
            offered.get("model")
        )

        # Явная модель из Product Identity
        if model:

            if offered_model:

                if model not in offered_model:

                    return "rejected"

            elif model not in title:

                return "rejected"

            return "ok"

        # Если отдельной модели нет,
        # проверяем имя товара.
        if name:

            important_tokens = (
                self._important_tokens(
                    name
                )
            )

            matched = sum(
                1
                for token in important_tokens
                if token in title
            )

            if important_tokens and (
                matched
                < len(important_tokens)
            ):

                return "rejected"

        return "ok"

    # ==================================================
    # REQUIRED ATTRIBUTES
    # ==================================================

    def _check_required_attributes(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        fields = (
            "gender",
            "material",
        )

        for field in fields:

            requested_value = (
                requested.get(field)
            )

            if not requested_value:
                continue

            result = self._check_attribute(
                requested_value,
                offered.get(field),
                title,
            )

            if result == "rejected":

                return "rejected"

        return "ok"

    # ==================================================
    # PRODUCT TYPE
    # ==================================================

    def _check_product_type(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        requested_type = self._normalize(
            requested.get(
                "product_type"
            )
        )

        if not requested_type:
            return "ok"

        offered_type = self._normalize(
            offered.get(
                "product_type"
            )
        )

        if offered_type:

            if not self._type_compatible(
                requested_type,
                offered_type,
            ):

                return "rejected"

            return "ok"

        # Если extractor не определил тип,
        # проверяем title.
        type_aliases = {
            "polo": {
                "polo",
                "polo shirt",
                "майка поло",
                "поло",
            },
            "tshirt": {
                "t shirt",
                "tshirt",
                "футболка",
            },
            "tank top": {
                "tank top",
                "tank",
                "майка",
            },
            "smartphone": {
                "iphone",
                "smartphone",
                "смартфон",
                "телефон",
            },
        }

        aliases = type_aliases.get(
            requested_type,
            {
                requested_type
            },
        )

        if not self._contains_any(
            title,
            aliases,
        ):

            return "rejected"

        return "ok"

    def _type_compatible(
        self,
        requested: str,
        offered: str,
    ) -> bool:

        if requested == offered:
            return True

        aliases = {
            "polo": {
                "polo",
                "polo shirt",
            },
            "tshirt": {
                "tshirt",
                "t shirt",
            },
            "smartphone": {
                "smartphone",
                "phone",
                "mobile phone",
            },
        }

        group = aliases.get(
            requested
        )

        if group and offered in group:
            return True

        return False

    # ==================================================
    # GENERIC ATTRIBUTE
    # ==================================================

    def _check_attribute(
        self,
        requested_value,
        offered_value,
        title: str,
    ) -> str:

        if not requested_value:
            return "ok"

        requested = self._normalize(
            requested_value
        )

        if offered_value:

            offered = self._normalize(
                offered_value
            )

            if (
                requested != offered
                and requested not in offered
                and offered not in requested
            ):

                return "rejected"

            return "ok"

        if requested not in title:

            aliases = self._attribute_aliases(
                requested
            )

            if not self._contains_any(
                title,
                aliases,
            ):

                return "rejected"

        return "ok"

    # ==================================================
    # STORAGE
    # ==================================================

    def _check_storage(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> str:

        requested_storage = self._normalize(
            requested.get("storage")
        )

        if not requested_storage:
            return "ok"

        requested_gb = self._extract_storage_gb(
            requested_storage
        )

        if requested_gb is None:
            return "ok"

        offered_storage = offered.get(
            "storage"
        )

        if offered_storage:

            offered_gb = (
                self._extract_storage_gb(
                    self._normalize(
                        offered_storage
                    )
                )
            )

            if (
                offered_gb is not None
                and offered_gb
                != requested_gb
            ):

                return "rejected"

        title_storage = (
            self._extract_storage_gb(
                title
            )
        )

        # Если в названии предложения явно
        # указана другая память — reject.
        if (
            title_storage is not None
            and title_storage
            != requested_gb
        ):

            return "rejected"

        # Если память запрошена, но в предложении
        # вообще невозможно её подтвердить,
        # не считаем товар exact.
        if (
            offered_storage is None
            and title_storage is None
        ):

            return "rejected"

        return "ok"

    @staticmethod
    def _extract_storage_gb(
        text: str,
    ):

        if not text:
            return None

        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(tb|gb|гб|тб)\b",
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

    # ==================================================
    # SCORE
    # ==================================================

    def _calculate_score(
        self,
        requested: dict[str, Any],
        offered: dict[str, Any],
        title: str,
    ) -> int:

        score = 0

        if requested.get(
            "brand"
        ):

            score += 20

        if requested.get(
            "model"
        ) or requested.get(
            "name"
        ):

            score += 30

        if requested.get(
            "storage"
        ):

            score += 20

        if requested.get(
            "color"
        ):

            score += 10

        if requested.get(
            "size"
        ):

            score += 10

        if requested.get(
            "product_type"
        ):

            score += 10

        return min(
            score,
            100,
        )

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _normalize(
        value,
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
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    @staticmethod
    def _important_tokens(
        text: str,
    ) -> list[str]:

        normalized = ProductMatcher._normalize(
            text
        )

        tokens = normalized.split()

        stop_words = {
            "нужен",
            "нужна",
            "нужно",
            "найди",
            "купить",
            "куплю",
            "товар",
            "до",
            "за",
            "the",
            "a",
            "an",
            "buy",
            "find",
        }

        return [
            token
            for token in tokens
            if token not in stop_words
            and len(token) > 1
        ]

    @staticmethod
    def _contains_any(
        text: str,
        values,
    ) -> bool:

        for value in values:

            normalized = (
                ProductMatcher._normalize(
                    value
                )
            )

            if not normalized:
                continue

            if normalized in text:
                return True

        return False

    @staticmethod
    def _attribute_aliases(
        value: str,
    ) -> set[str]:

        aliases = {
            "белый": {
                "белый",
                "white",
            },
            "white": {
                "white",
                "белый",
            },
            "черный": {
                "черный",
                "чёрный",
                "black",
            },
            "black": {
                "black",
                "черный",
                "чёрный",
            },
            "синий": {
                "синий",
                "blue",
            },
            "blue": {
                "blue",
                "синий",
            },
        }

        return aliases.get(
            value,
            {
                value
            },
        )

    @staticmethod
    def _result(
        match_type: str,
        score: int,
        reason: str,
        requested: dict[str, Any],
        offered: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "match_type": match_type,
            "match_score": score,
            "match_reason": reason,
            "requested_attributes": requested,
            "offered_attributes": offered,
        }