from __future__ import annotations

import re
from typing import Any


class AttributeExtractor:
    """
    Извлекает характеристики товара.

    Модуль отвечает только за атрибуты:
    - storage
    - color
    - size
    - material
    - gender
    - capacity
    - voltage
    - quantity
    - weight
    - dimensions
    - compatibility

    Цена, состояние, наличие и идентичность
    товара обрабатываются отдельными модулями.
    """

    ATTRIBUTE_KEYS = {
        "storage": (
            "storage",
            "memory",
            "ram",
            "capacityStorage",
        ),
        "color": (
            "color",
            "colour",
            "colorName",
        ),
        "size": (
            "size",
            "sizeName",
        ),
        "material": (
            "material",
            "fabric",
            "composition",
        ),
        "gender": (
            "gender",
            "sex",
        ),
        "capacity": (
            "capacity",
            "volume",
            "capacityValue",
        ),
        "voltage": (
            "voltage",
            "voltageValue",
        ),
        "quantity": (
            "quantity",
            "count",
            "packQuantity",
        ),
        "weight": (
            "weight",
            "weightValue",
        ),
        "dimensions": (
            "dimensions",
            "dimension",
            "sizeDimensions",
        ),
        "compatibility": (
            "compatibility",
            "compatibleWith",
            "compatibleModels",
        ),
    }

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:

        data = data or {}

        attributes: dict[str, Any] = {}

        for attribute, keys in self.ATTRIBUTE_KEYS.items():

            value = self._extract_first_value(
                data,
                keys,
            )

            if value is not None:
                attributes[attribute] = (
                    self._normalize_attribute(
                        attribute,
                        value,
                    )
                )

        if text:
            text_attributes = (
                self._extract_from_text(
                    text
                )
            )

            for key, value in text_attributes.items():

                if (
                    key not in attributes
                    or attributes[key] is None
                ):
                    attributes[key] = value

        return {
            key: value
            for key, value in attributes.items()
            if value is not None
            and value != ""
        }

    def _extract_from_text(
        self,
        text: str,
    ) -> dict[str, Any]:

        if not text:
            return {}

        attributes: dict[str, Any] = {}

        storage = self._extract_storage(
            text
        )

        if storage:
            attributes["storage"] = storage

        color = self._extract_color(
            text
        )

        if color:
            attributes["color"] = color

        size = self._extract_size(
            text
        )

        if size:
            attributes["size"] = size

        material = self._extract_material(
            text
        )

        if material:
            attributes["material"] = material

        gender = self._extract_gender(
            text
        )

        if gender:
            attributes["gender"] = gender

        capacity = self._extract_capacity(
            text
        )

        if capacity:
            attributes["capacity"] = capacity

        voltage = self._extract_voltage(
            text
        )

        if voltage:
            attributes["voltage"] = voltage

        quantity = self._extract_quantity(
            text
        )

        if quantity:
            attributes["quantity"] = quantity

        weight = self._extract_weight(
            text
        )

        if weight:
            attributes["weight"] = weight

        dimensions = self._extract_dimensions(
            text
        )

        if dimensions:
            attributes["dimensions"] = dimensions

        compatibility = (
            self._extract_compatibility(
                text
            )
        )

        if compatibility:
            attributes["compatibility"] = compatibility

        return attributes

    def _extract_storage(
        self,
        text: str,
    ) -> str | None:

        patterns = (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(TB|GB|MB)\b",
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(ТБ|ГБ|МБ)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1)
            unit = match.group(2).upper()

            unit_map = {
                "ТБ": "TB",
                "ГБ": "GB",
                "МБ": "MB",
            }

            unit = unit_map.get(
                unit,
                unit,
            )

            return f"{value} {unit}"

        return None

    def _extract_color(
        self,
        text: str,
    ) -> str | None:

        colors = (
            "black",
            "white",
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "pink",
            "gray",
            "grey",
            "brown",
            "beige",
            "silver",
            "gold",
            "natural titanium",
            "black titanium",
            "blue titanium",
            "white titanium",
            "черный",
            "чёрный",
            "белый",
            "красный",
            "синий",
            "голубой",
            "зеленый",
            "зелёный",
            "желтый",
            "жёлтый",
            "оранжевый",
            "фиолетовый",
            "розовый",
            "серый",
            "коричневый",
            "бежевый",
            "серебристый",
            "золотой",
        )

        normalized = text.lower()

        for color in colors:

            if re.search(
                rf"\b{re.escape(color)}\b",
                normalized,
            ):
                return color

        return None

    def _extract_size(
        self,
        text: str,
    ) -> str | None:

        patterns = (
            r"\b(?:size|размер)\s*[:\-]?\s*"
            r"([A-ZА-Я]?\d{1,3}(?:[.,]\d+)?)\b",
            r"\b(XS|S|M|L|XL|XXL|XXXL)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).upper()

        return None

    def _extract_material(
        self,
        text: str,
    ) -> str | None:

        materials = (
            "leather",
            "genuine leather",
            "synthetic leather",
            "cotton",
            "wool",
            "silk",
            "linen",
            "polyester",
            "nylon",
            "denim",
            "кожа",
            "натуральная кожа",
            "экокожа",
            "хлопок",
            "шерсть",
            "шелк",
            "лен",
            "полиэстер",
            "нейлон",
            "джинсовый",
        )

        normalized = text.lower()

        # Сначала проверяем составные значения.
        materials = sorted(
            materials,
            key=len,
            reverse=True,
        )

        for material in materials:

            if re.search(
                rf"\b{re.escape(material)}\b",
                normalized,
            ):
                return material

        return None

    def _extract_gender(
        self,
        text: str,
    ) -> str | None:

        normalized = text.lower()

        male = (
            "men",
            "man's",
            "mens",
            "male",
            "мужской",
            "мужская",
            "мужское",
            "для мужчин",
        )

        female = (
            "women",
            "woman",
            "women's",
            "female",
            "женский",
            "женская",
            "женское",
            "для женщин",
        )

        unisex = (
            "unisex",
            "унисекс",
        )

        for marker in unisex:

            if re.search(
                rf"\b{re.escape(marker)}\b",
                normalized,
            ):
                return "unisex"

        for marker in male:

            if re.search(
                rf"\b{re.escape(marker)}\b",
                normalized,
            ):
                return "male"

        for marker in female:

            if re.search(
                rf"\b{re.escape(marker)}\b",
                normalized,
            ):
                return "female"

        return None

    def _extract_capacity(
        self,
        text: str,
    ) -> str | None:

        patterns = (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(L|ml|mL|литр(?:а|ов)?)\b",
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(л|мл)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = match.group(1)
            unit = match.group(2).lower()

            unit_map = {
                "л": "L",
                "литр": "L",
                "литра": "L",
                "литров": "L",
                "мл": "ml",
            }

            unit = unit_map.get(
                unit,
                unit,
            )

            return f"{value} {unit}"

        return None

    def _extract_voltage(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(V|В|volt|volts|вольт(?:а|ов)?)\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(1)

        return f"{value} V"

    def _extract_quantity(
        self,
        text: str,
    ) -> str | None:

        patterns = (
            r"\b(\d+)\s*"
            r"(?:pcs?|pieces?|шт\.?|штук|"
            r"pack|packs|упаков(?:ка|ки|ок))\b",
            r"\bpack\s+of\s+(\d+)\b",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1)

        return None

    def _extract_weight(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(kg|кг|g|г)\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        value = match.group(1)
        unit = match.group(2).lower()

        unit_map = {
            "кг": "kg",
            "г": "g",
        }

        unit = unit_map.get(
            unit,
            unit,
        )

        return f"{value} {unit}"

    def _extract_dimensions(
        self,
        text: str,
    ) -> str | None:

        match = re.search(
            r"\b(\d+(?:[.,]\d+)?)\s*[xх×]\s*"
            r"(\d+(?:[.,]\d+)?)"
            r"(?:\s*[xх×]\s*"
            r"(\d+(?:[.,]\d+)?))?"
            r"\s*(cm|мм|mm|см|m)?\b",
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        first = match.group(1)
        second = match.group(2)
        third = match.group(3)
        unit = match.group(4)

        values = [
            first,
            second,
        ]

        if third:
            values.append(third)

        result = " x ".join(values)

        if unit:
            unit_map = {
                "см": "cm",
                "мм": "mm",
            }

            unit = unit_map.get(
                unit.lower(),
                unit.lower(),
            )

            result = f"{result} {unit}"

        return result

    def _extract_compatibility(
        self,
        text: str,
    ) -> str | None:

        patterns = (
            r"(?:compatible with|совместим(?:о|а)? с)"
            r"\s+([^,.;]+)",
            r"(?:for|для)\s+"
            r"(iPhone\s+\d+[^\s,.;]*)",
            r"(?:for|для)\s+"
            r"(Galaxy\s+[A-Za-z0-9\-]+)",
        )

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

        return None

    def _extract_first_value(
        self,
        data: Any,
        keys: tuple[str, ...],
    ) -> Any:

        if isinstance(data, dict):

            for key in keys:

                if key not in data:
                    continue

                value = data.get(key)

                if self._is_valid_value(
                    value
                ):
                    return value

            for value in data.values():

                result = self._extract_first_value(
                    value,
                    keys,
                )

                if self._is_valid_value(
                    result
                ):
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._extract_first_value(
                    item,
                    keys,
                )

                if self._is_valid_value(
                    result
                ):
                    return result

        return None

    def _normalize_attribute(
        self,
        attribute: str,
        value: Any,
    ) -> Any:

        if isinstance(value, dict):

            value = (
                value.get("name")
                or value.get("@value")
                or value.get("value")
            )

        if value is None:
            return None

        if isinstance(value, list):

            return [
                self._normalize_attribute(
                    attribute,
                    item,
                )
                for item in value
            ]

        value = str(
            value
        ).strip()

        if not value:
            return None

        if attribute == "storage":
            return self._normalize_storage(
                value
            )

        if attribute == "color":
            return self._normalize_color(
                value
            )

        if attribute == "gender":
            return self._normalize_gender(
                value
            )

        if attribute == "quantity":
            return self._normalize_quantity(
                value
            )

        return value

    @staticmethod
    def _normalize_storage(
        value: str,
    ) -> str:

        value = value.strip()

        value = (
            value
            .replace("ТБ", "TB")
            .replace("тб", "TB")
            .replace("ГБ", "GB")
            .replace("гб", "GB")
            .replace("МБ", "MB")
            .replace("мб", "MB")
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    @staticmethod
    def _normalize_color(
        value: str,
    ) -> str:

        normalized = (
            value
            .lower()
            .strip()
        )

        aliases = {
            "black": "black",
            "черный": "black",
            "чёрный": "black",
            "white": "white",
            "белый": "white",
            "red": "red",
            "красный": "red",
            "blue": "blue",
            "синий": "blue",
            "green": "green",
            "зеленый": "green",
            "зелёный": "green",
            "gray": "gray",
            "grey": "gray",
            "серый": "gray",
            "silver": "silver",
            "серебристый": "silver",
            "gold": "gold",
            "золотой": "gold",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    @staticmethod
    def _normalize_gender(
        value: str,
    ) -> str:

        normalized = (
            value
            .lower()
            .strip()
        )

        aliases = {
            "men": "male",
            "man": "male",
            "male": "male",
            "мужской": "male",
            "мужская": "male",
            "мужское": "male",
            "women": "female",
            "woman": "female",
            "female": "female",
            "женский": "female",
            "женская": "female",
            "женское": "female",
            "unisex": "unisex",
            "унисекс": "unisex",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    @staticmethod
    def _normalize_quantity(
        value: str,
    ) -> str:

        match = re.search(
            r"\d+",
            value,
        )

        if match:
            return match.group(0)

        return value

    @staticmethod
    def _is_valid_value(
        value: Any,
    ) -> bool:

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, list):
            return bool(value)

        return True