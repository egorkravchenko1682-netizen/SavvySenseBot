import re
from typing import Any


class AttributeExtractor:
    """
    Универсальный движок извлечения атрибутов товара.

    Не привязан к конкретной категории.

    Извлекает только то, что можно определить
    из текста достаточно уверенно.

    Неизвестные значения -> None.
    """

    def extract(
        self,
        text: str | None,
    ) -> dict[str, Any]:

        if not text:

            return {
                "brand": None,
                "model": None,
                "category": None,
                "product_type": None,
                "color": None,
                "size": None,
                "material": None,
                "storage": None,
                "capacity": None,
                "dimensions": None,
                "voltage": None,
                "quantity": None,
                "weight": None,
                "compatibility": None,
                "condition": None,
                "gender": None,
                "season": None,
                "keywords": [],
            }

        normalized = self._normalize(
            text
        )

        return {
            "brand":
                self._extract_brand(
                    normalized
                ),

            "model":
                self._extract_model(
                    normalized
                ),

            "category":
                self._extract_category(
                    normalized
                ),

            "product_type":
                self._extract_product_type(
                    normalized
                ),

            "color":
                self._extract_color(
                    normalized
                ),

            "size":
                self._extract_size(
                    normalized
                ),

            "material":
                self._extract_material(
                    normalized
                ),

            "storage":
                self._extract_storage(
                    normalized
                ),

            "capacity":
                self._extract_capacity(
                    normalized
                ),

            "dimensions":
                self._extract_dimensions(
                    normalized
                ),

            "voltage":
                self._extract_voltage(
                    normalized
                ),

            "quantity":
                self._extract_quantity(
                    normalized
                ),

            "weight":
                self._extract_weight(
                    normalized
                ),

            "compatibility":
                self._extract_compatibility(
                    normalized
                ),

            "condition":
                self._extract_condition(
                    normalized
                ),

            "gender":
                self._extract_gender(
                    normalized
                ),

            "season":
                self._extract_season(
                    normalized
                ),

            "keywords":
                self._extract_keywords(
                    normalized
                ),
        }

    # ==================================================
    # BRAND
    # ==================================================

    def _extract_brand(
        self,
        text: str,
    ) -> str | None:

        brands = [
            "apple",
            "samsung",
            "xiaomi",
            "google",
            "oneplus",
            "huawei",
            "honor",
            "sony",
            "lg",
            "lenovo",
            "asus",
            "acer",
            "hp",
            "dell",
            "msi",
            "nike",
            "adidas",
            "puma",
            "reebok",
            "new balance",
            "under armour",
            "zara",
            "uniqlo",
            "h&m",
            "bosch",
            "philips",
            "dyson",
            "makita",
            "dewalt",
            "milwaukee",
            "stanley",
            "ikea",
            "lego",
            "logitech",
            "jbl",
            "canon",
            "nikon",
            "fujifilm",
            "gopro",
            "dji",
            "roborock",
            "dreame",
            "ecovacs",
            "beko",
            "electrolux",
            "whirlpool",
            "bosch",
        ]

        for brand in brands:

            if self._contains_phrase(
                text,
                brand,
            ):

                return brand

        return None

    # ==================================================
    # MODEL
    # ==================================================

    def _extract_model(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            # iPhone 15 / Galaxy S24 / Pixel 9
            r"\b(?:iphone|ipad)\s+\d+(?:\s+(?:pro|max|plus|mini|air|ultra))?(?:\s+[a-z]+)?",

            r"\bgalaxy\s+[a-z]\d+(?:\s+(?:ultra|plus|fe))?",

            r"\bpixel\s+\d+(?:\s+(?:pro|xl|a))?",

            # Generic model codes
            r"\b[a-z]{1,5}[- ]?\d{2,6}[a-z0-9-]*\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                return match.group(
                    0
                ).strip()

        return None

    # ==================================================
    # CATEGORY
    # ==================================================

    def _extract_category(
        self,
        text: str,
    ) -> str | None:

        categories = {

            "smartphone": [
                "iphone",
                "смартфон",
                "smartphone",
                "телефон",
            ],

            "laptop": [
                "ноутбук",
                "laptop",
                "notebook",
            ],

            "tablet": [
                "планшет",
                "tablet",
                "ipad",
            ],

            "television": [
                "телевизор",
                "tv",
                "телек",
            ],

            "headphones": [
                "наушники",
                "headphones",
                "earbuds",
            ],

            "camera": [
                "камера",
                "фотоаппарат",
                "camera",
            ],

            "clothing": [
                "одежда",
                "куртка",
                "пальто",
                "футболка",
                "майка",
                "рубашка",
                "джинсы",
                "брюки",
                "платье",
                "свитер",
                "худи",
            ],

            "shoes": [
                "обувь",
                "кроссовки",
                "ботинки",
                "туфли",
                "shoes",
                "sneakers",
                "boots",
            ],

            "furniture": [
                "диван",
                "кресло",
                "стол",
                "стул",
                "шкаф",
                "кровать",
                "мебель",
            ],

            "appliance": [
                "холодильник",
                "стиральная машина",
                "пылесос",
                "посудомоечная машина",
                "микроволновка",
                "микроволновая печь",
            ],

            "tool": [
                "дрель",
                "шуруповерт",
                "перфоратор",
                "болгарка",
                "пила",
                "инструмент",
                "drill",
                "saw",
            ],

            "automotive": [
                "автозапчасть",
                "аккумулятор",
                "масло",
                "фильтр",
                "тормозные колодки",
                "автомобильная запчасть",
            ],
        }

        for category, words in categories.items():

            if self._contains_any(
                text,
                words,
            ):

                return category

        return None

    # ==================================================
    # PRODUCT TYPE
    # ==================================================

    def _extract_product_type(
        self,
        text: str,
    ) -> str | None:

        types = {

            "polo": [
                "поло",
                "polo",
                "polo shirt",
            ],

            "tshirt": [
                "футболка",
                "t-shirt",
                "tshirt",
            ],

            "tank top": [
                "майка",
                "tank top",
            ],

            "jacket": [
                "куртка",
                "jacket",
            ],

            "coat": [
                "пальто",
                "coat",
            ],

            "dress": [
                "платье",
                "dress",
            ],

            "sneakers": [
                "кроссовки",
                "sneakers",
            ],

            "boots": [
                "ботинки",
                "boots",
            ],

            "smartphone": [
                "смартфон",
                "smartphone",
                "iphone",
                "телефон",
            ],

            "laptop": [
                "ноутбук",
                "laptop",
            ],

            "vacuum_cleaner": [
                "пылесос",
                "vacuum cleaner",
            ],

            "refrigerator": [
                "холодильник",
                "refrigerator",
            ],

            "drill": [
                "дрель",
                "drill",
            ],
        }

        for product_type, words in types.items():

            if self._contains_any(
                text,
                words,
            ):

                return product_type

        return None

    # ==================================================
    # COLOR
    # ==================================================

    def _extract_color(
        self,
        text: str,
    ) -> str | None:

        colors = {

            "белый": [
                "белый",
                "белая",
                "белое",
                "white",
            ],

            "черный": [
                "черный",
                "чёрный",
                "черная",
                "чёрная",
                "black",
            ],

            "красный": [
                "красный",
                "красная",
                "red",
            ],

            "синий": [
                "синий",
                "синяя",
                "blue",
            ],

            "зеленый": [
                "зеленый",
                "зелёный",
                "зеленая",
                "green",
            ],

            "желтый": [
                "желтый",
                "жёлтый",
                "желтая",
                "yellow",
            ],

            "серый": [
                "серый",
                "серая",
                "grey",
                "gray",
            ],

            "розовый": [
                "розовый",
                "розовая",
                "pink",
            ],

            "фиолетовый": [
                "фиолетовый",
                "purple",
            ],

            "коричневый": [
                "коричневый",
                "brown",
            ],

            "бежевый": [
                "бежевый",
                "beige",
            ],
        }

        for color, words in colors.items():

            if self._contains_any(
                text,
                words,
            ):

                return color

        return None

    # ==================================================
    # SIZE
    # ==================================================

    def _extract_size(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            r"\b(?:size|размер)\s*[:\-]?\s*(xxs|xs|s|m|l|xl|xxl|xxxl)\b",

            r"\b(xxxl|xxl|xxxl|xxs|xs|xl|l|m|s)\b",

            r"\b(?:eu|us|uk)\s*(\d{2}(?:\.\d)?)\b",

            r"\bразмер\s*(\d{2})\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                value = (
                    match.group(
                        1
                    )
                    or match.group(0)
                )

                return value.strip()

        return None

    # ==================================================
    # MATERIAL
    # ==================================================

    def _extract_material(
        self,
        text: str,
    ) -> str | None:

        materials = [

            "кожа",
            "натуральная кожа",
            "экокожа",
            "хлопок",
            "cotton",
            "linen",
            "лён",
            "шерсть",
            "wool",
            "полиэстер",
            "polyester",
            "нейлон",
            "nylon",
            "шелк",
            "шёлк",
            "silk",
            "дерево",
            "wood",
            "металл",
            "metal",
            "алюминий",
            "aluminum",
            "сталь",
            "steel",
            "пластик",
            "plastic",
        ]

        for material in materials:

            if self._contains_phrase(
                text,
                material,
            ):

                return material

        return None

    # ==================================================
    # STORAGE
    # ==================================================

    def _extract_storage(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(tb|gb|гб|тб)\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(
            1
        )

        unit = match.group(
            2
        ).lower()

        return f"{value} {unit.upper()}"

    # ==================================================
    # CAPACITY
    # ==================================================

    def _extract_capacity(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            r"\b(\d+(?:\.\d+)?)\s*(mah)\b",

            r"\b(\d+(?:\.\d+)?)\s*(ml|l|л|мл)\b",

            r"\b(\d+(?:\.\d+)?)\s*(ah)\b",

            r"\b(\d+(?:\.\d+)?)\s*(kg|кг)\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                return (
                    f"{match.group(1)} "
                    f"{match.group(2)}"
                )

        return None

    # ==================================================
    # DIMENSIONS
    # ==================================================

    def _extract_dimensions(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            r"\b\d+(?:[.,]\d+)?\s*[xх×]\s*\d+(?:[.,]\d+)?(?:\s*[xх×]\s*\d+(?:[.,]\d+)?)?\s*(?:cm|мм|м|см)?\b",

            r"\b\d+(?:[.,]\d+)?\s*(?:cm|мм|м|см)\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                return match.group(
                    0
                ).strip()

        return None

    # ==================================================
    # VOLTAGE
    # ==================================================

    def _extract_voltage(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:\.\d+)?)\s*v\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return (
            f"{match.group(1)} V"
        )

    # ==================================================
    # QUANTITY
    # ==================================================

    def _extract_quantity(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            r"\b(\d+)\s*(?:шт|штук|pcs|pieces)\b",

            r"\b(?:набор|комплект)\s*(?:из|на)?\s*(\d+)\b",

            r"\bpack\s+of\s+(\d+)\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                return (
                    f"{match.group(1)} шт."
                )

        return None

    # ==================================================
    # WEIGHT
    # ==================================================

    def _extract_weight(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*(kg|кг|g|г)\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        return (
            f"{match.group(1)} "
            f"{match.group(2)}"
        )

    # ==================================================
    # COMPATIBILITY
    # ==================================================

    def _extract_compatibility(
        self,
        text: str,
    ) -> str | None:

        patterns = [

            r"\b(?:для|for)\s+([a-z0-9][a-z0-9 .+\-]{1,50})",

            r"\bcompatible with\s+([a-z0-9][a-z0-9 .+\-]{1,50})",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:

                value = match.group(
                    1
                ).strip()

                # Не захватываем слишком длинный
                # остаток запроса.
                value = value.split(
                    " до "
                )[0]

                value = value.split(
                    " цена"
                )[0]

                return value.strip()

        return None

    # ==================================================
    # CONDITION
    # ==================================================

    def _extract_condition(
        self,
        text: str,
    ) -> str | None:

        conditions = {

            "new": [
                "новый",
                "новая",
                "новое",
                "new",
            ],

            "used": [
                "б/у",
                "бу",
                "used",
                "second hand",
            ],

            "refurbished": [
                "refurbished",
                "восстановленный",
                "восстановленная",
            ],
        }

        for condition, words in conditions.items():

            if self._contains_any(
                text,
                words,
            ):

                return condition

        return None

    # ==================================================
    # GENDER
    # ==================================================

    def _extract_gender(
        self,
        text: str,
    ) -> str | None:

        if self._contains_any(
            text,
            [
                "мужской",
                "мужская",
                "мужское",
                "мужчин",
                "men",
                "mens",
                "men's",
                "male",
            ],
        ):

            return "male"

        if self._contains_any(
            text,
            [
                "женский",
                "женская",
                "женское",
                "женщин",
                "women",
                "womens",
                "women's",
                "female",
            ],
        ):

            return "female"

        if self._contains_any(
            text,
            [
                "детский",
                "детская",
                "детское",
                "kids",
                "children",
            ],
        ):

            return "kids"

        return None

    # ==================================================
    # SEASON
    # ==================================================

    def _extract_season(
        self,
        text: str,
    ) -> str | None:

        seasons = {

            "winter": [
                "зимний",
                "зимняя",
                "зимнее",
                "winter",
            ],

            "summer": [
                "летний",
                "летняя",
                "летнее",
                "summer",
            ],

            "demi-season": [
                "демисезон",
                "демисезонный",
                "демисезонная",
                "mid season",
            ],
        }

        for season, words in seasons.items():

            if self._contains_any(
                text,
                words,
            ):

                return season

        return None

    # ==================================================
    # KEYWORDS
    # ==================================================

    def _extract_keywords(
        self,
        text: str,
    ) -> list[str]:

        stop_words = {
            "найди",
            "нужен",
            "нужна",
            "нужно",
            "мне",
            "хочу",
            "купить",
            "пожалуйста",
            "товар",
            "до",
            "за",
            "цена",
            "где",
            "самый",
            "самая",
            "самое",
        }

        tokens = re.findall(
            r"[a-zа-яё0-9]+",
            text.lower(),
        )

        result = []

        for token in tokens:

            if token in stop_words:
                continue

            if len(token) < 2:
                continue

            if token not in result:

                result.append(
                    token
                )

        return result[:30]

    # ==================================================
    # HELPERS
    # ==================================================

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        text = str(
            text
        ).lower().strip()

        text = (
            text
            .replace("ё", "е")
            .replace("—", "-")
            .replace("–", "-")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    @staticmethod
    def _contains_any(
        text: str,
        values: list[str],
    ) -> bool:

        for value in values:

            if AttributeExtractor._contains_phrase(
                text,
                value,
            ):

                return True

        return False

    @staticmethod
    def _contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:

        phrase = (
            str(phrase)
            .lower()
            .strip()
        )

        if not phrase:
            return False

        escaped = re.escape(
            phrase
        )

        pattern = (
            rf"(?<![a-zа-яё0-9])"
            rf"{escaped}"
            rf"(?![a-zа-яё0-9])"
        )

        return bool(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )