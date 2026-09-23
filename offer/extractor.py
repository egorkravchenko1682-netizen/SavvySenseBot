import json
import re
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class OfferExtractor:
    """
    Универсальный extractor товарных страниц SAVVY SENSE.

    Извлекает:

    Identity:
    - title
    - brand
    - model
    - product_type
    - category

    Attributes:
    - storage
    - color
    - size
    - material
    - gender
    - condition
    - quantity
    - capacity
    - voltage
    - compatibility

    Commerce:
    - price
    - currency
    - seller
    - availability

    Additional:
    - description
    - image
    - sku
    - mpn
    - gtin
    - url
    - domain
    """

    name = "offer_extractor"

    def __init__(
        self,
        timeout: int = 15,
    ):
        self.timeout = timeout

    # =========================================================
    # PUBLIC API
    # =========================================================

    def extract(
        self,
        url: str,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        fallback = fallback or {}

        if not url:
            return self._fallback_result(
                fallback
            )

        try:

            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
                allow_redirects=True,
            )

            response.raise_for_status()

            final_url = response.url

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            json_ld = self._extract_json_ld(
                soup
            )

            product_data = self._find_product(
                json_ld
            )

            offer_data = self._find_offer(
                product_data
            )

            # =================================================
            # BASIC IDENTITY
            # =================================================

            title = (
                self._clean(
                    product_data.get("name")
                )
                or self._meta(
                    soup,
                    "og:title",
                )
                or self._meta(
                    soup,
                    "twitter:title",
                )
                or self._clean(
                    fallback.get("title")
                )
            )

            brand = (
                self._extract_brand(
                    product_data
                )
                or self._clean(
                    fallback.get("brand")
                )
                or self._infer_brand(
                    title
                )
            )

            model = (
                self._extract_model(
                    product_data
                )
                or self._clean(
                    fallback.get("model")
                )
                or self._infer_model(
                    title
                )
            )

            description = (
                self._clean(
                    product_data.get(
                        "description"
                    )
                )
                or self._meta(
                    soup,
                    "og:description",
                )
                or self._clean(
                    fallback.get(
                        "description"
                    )
                )
            )

            # =================================================
            # PRODUCT TYPE / CATEGORY
            # =================================================

            product_type = (
                self._extract_product_type(
                    product_data
                )
                or self._clean(
                    fallback.get(
                        "product_type"
                    )
                )
            )

            category = (
                self._extract_category(
                    product_data
                )
                or self._clean(
                    fallback.get(
                        "category"
                    )
                )
            )

            # =================================================
            # PRICE
            # =================================================

            price = (
                self._extract_price(
                    offer_data
                )
            )

            if price is None:
                price = self._extract_meta_price(
                    soup
                )

            if price is None:
                price = self._clean_numeric_price(
                    fallback.get(
                        "price"
                    )
                )

            # =================================================
            # CURRENCY
            # =================================================

            currency = (
                self._clean(
                    offer_data.get(
                        "priceCurrency"
                    )
                )
                or self._extract_meta_currency(
                    soup
                )
                or self._clean(
                    fallback.get(
                        "currency"
                    )
                )
            )

            if currency:
                currency = str(
                    currency
                ).upper()

            # =================================================
            # SELLER
            # =================================================

            seller = (
                self._extract_seller(
                    offer_data
                )
                or self._clean(
                    fallback.get(
                        "seller"
                    )
                )
                or self._domain_as_seller(
                    final_url
                )
            )

            # =================================================
            # AVAILABILITY
            # =================================================

            availability = (
                self._extract_availability(
                    offer_data
                )
                or self._clean(
                    fallback.get(
                        "availability"
                    )
                )
                or "unknown"
            )

            # =================================================
            # CONDITION
            # =================================================

            condition = (
                self._extract_condition(
                    product_data,
                    offer_data,
                )
                or self._clean(
                    fallback.get(
                        "condition"
                    )
                )
                or "unknown"
            )

            # =================================================
            # ATTRIBUTES
            # =================================================

            attributes = self._extract_attributes(
                product_data=product_data,
                title=title,
                description=description,
                fallback=fallback,
            )

            # Condition belongs to attributes too.
            if condition:
                attributes["condition"] = condition

            # =================================================
            # IDENTIFIERS
            # =================================================

            sku = (
                self._clean(
                    product_data.get(
                        "sku"
                    )
                )
                or self._clean(
                    fallback.get(
                        "sku"
                    )
                )
            )

            mpn = (
                self._clean(
                    product_data.get(
                        "mpn"
                    )
                )
                or self._clean(
                    fallback.get(
                        "mpn"
                    )
                )
            )

            gtin = (
                self._extract_gtin(
                    product_data
                )
                or self._clean(
                    fallback.get(
                        "gtin"
                    )
                )
            )

            # =================================================
            # IMAGE
            # =================================================

            image = self._extract_image(
                product_data
            )

            if not image:
                image = self._meta(
                    soup,
                    "og:image",
                )

            if not image:
                image = self._clean(
                    fallback.get(
                        "image"
                    )
                )

            # =================================================
            # DOMAIN
            # =================================================

            domain = urlparse(
                final_url
            ).netloc

            # =================================================
            # RESULT
            # =================================================

            return {
                "title": title,
                "brand": brand,
                "model": model,
                "product_type": product_type,
                "category": category,

                "attributes": attributes,

                "storage": attributes.get(
                    "storage"
                ),
                "color": attributes.get(
                    "color"
                ),
                "size": attributes.get(
                    "size"
                ),
                "material": attributes.get(
                    "material"
                ),
                "gender": attributes.get(
                    "gender"
                ),
                "condition": condition,

                "price": price,
                "currency": currency,

                "description": description,
                "image": image,

                "seller": seller,
                "availability": availability,

                "sku": sku,
                "mpn": mpn,
                "gtin": gtin,

                "url": final_url,
                "domain": domain,

                "extracted": True,
            }

        except Exception as error:

            print(
                f"Offer extraction failed "
                f"for {url}: {error}"
            )

            return self._fallback_result(
                fallback,
                url=url,
            )

    # =========================================================
    # HTTP
    # =========================================================

    @staticmethod
    def _headers():

        return {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept-Language":
                "en-US,en;q=0.9",
            "Accept":
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8",
            "Cache-Control":
                "no-cache",
        }

    # =========================================================
    # JSON-LD
    # =========================================================

    def _extract_json_ld(
        self,
        soup: BeautifulSoup,
    ) -> list[Any]:

        results = []

        scripts = soup.find_all(
            "script",
            type="application/ld+json",
        )

        for script in scripts:

            raw = script.string

            if not raw:
                raw = script.get_text(
                    strip=True
                )

            if not raw:
                continue

            try:

                data = json.loads(
                    raw
                )

            except Exception:

                continue

            if isinstance(
                data,
                list,
            ):

                results.extend(
                    data
                )

            else:

                results.append(
                    data
                )

        return results

    # =========================================================
    # PRODUCT FINDER
    # =========================================================

    def _find_product(
        self,
        data: list[Any],
    ) -> dict[str, Any]:

        for item in data:

            found = (
                self._find_product_recursive(
                    item
                )
            )

            if found:
                return found

        return {}

    def _find_product_recursive(
        self,
        item: Any,
    ) -> dict[str, Any]:

        if isinstance(
            item,
            dict,
        ):

            item_type = item.get(
                "@type"
            )

            if isinstance(
                item_type,
                list,
            ):

                types = [
                    str(value).lower()
                    for value in item_type
                ]

            else:

                types = [
                    str(
                        item_type
                    ).lower()
                ]

            if (
                "product" in types
                or "productgroup" in types
            ):
                return item

            graph = item.get(
                "@graph"
            )

            if isinstance(
                graph,
                list,
            ):

                for child in graph:

                    found = (
                        self._find_product_recursive(
                            child
                        )
                    )

                    if found:
                        return found

            # Некоторые сайты помещают Product
            # внутрь mainEntity.
            for key in (
                "mainEntity",
                "mainEntityOfPage",
                "item",
                "subjectOf",
            ):

                nested = item.get(
                    key
                )

                if nested is not None:

                    found = (
                        self._find_product_recursive(
                            nested
                        )
                    )

                    if found:
                        return found

            # Общий recursive fallback.
            for value in item.values():

                if isinstance(
                    value,
                    (
                        dict,
                        list,
                    ),
                ):

                    found = (
                        self._find_product_recursive(
                            value
                        )
                    )

                    if found:
                        return found

        elif isinstance(
            item,
            list,
        ):

            for child in item:

                found = (
                    self._find_product_recursive(
                        child
                    )
                )

                if found:
                    return found

        return {}

    # =========================================================
    # OFFER
    # =========================================================

    def _find_offer(
        self,
        product: dict[str, Any],
    ) -> dict[str, Any]:

        offers = product.get(
            "offers"
        )

        if isinstance(
            offers,
            dict,
        ):
            return offers

        if isinstance(
            offers,
            list,
        ):

            # Предпочитаем offer,
            # в котором есть цена.
            for offer in offers:

                if not isinstance(
                    offer,
                    dict,
                ):
                    continue

                if (
                    offer.get("price")
                    is not None
                    or offer.get("lowPrice")
                    is not None
                ):
                    return offer

            for offer in offers:

                if isinstance(
                    offer,
                    dict,
                ):
                    return offer

        return {}

    # =========================================================
    # PRICE
    # =========================================================

    def _extract_price(
        self,
        offer: dict[str, Any],
    ):

        if not offer:
            return None

        candidates = [
            offer.get("price"),
            offer.get("lowPrice"),
            offer.get("highPrice"),
        ]

        for value in candidates:

            price = self._clean_numeric_price(
                value
            )

            if price is not None:
                return price

        return None

    def _extract_meta_price(
        self,
        soup: BeautifulSoup,
    ):

        candidates = [
            "product:price:amount",
            "og:price:amount",
            "product:price",
            "price",
        ]

        for candidate in candidates:

            value = self._meta(
                soup,
                candidate,
            )

            price = self._clean_numeric_price(
                value
            )

            if price is not None:
                return price

        # Часто ecommerce-сайты используют
        # itemprop="price".
        element = soup.find(
            attrs={
                "itemprop": "price"
            }
        )

        if element:

            value = (
                element.get("content")
                or element.get_text(
                    strip=True
                )
            )

            price = self._clean_numeric_price(
                value
            )

            if price is not None:
                return price

        return None

    @staticmethod
    def _clean_numeric_price(
        value,
    ):

        if value is None:
            return None

        if isinstance(
            value,
            (
                int,
                float,
            ),
        ):

            return float(
                value
            )

        text = str(
            value
        ).strip()

        if not text:
            return None

        # Убираем валютные символы,
        # пробелы и текст вокруг числа.
        text = (
            text
            .replace("\xa0", " ")
            .replace(" ", "")
        )

        # Если формат:
        # 1,299.99
        if (
            "," in text
            and "." in text
        ):

            if text.rfind(",") < text.rfind("."):
                text = text.replace(
                    ",",
                    "",
                )
            else:
                text = (
                    text
                    .replace(".", "")
                    .replace(",", ".")
                )

        elif "," in text:

            parts = text.split(",")

            if (
                len(parts) == 2
                and len(parts[1]) <= 2
            ):

                text = (
                    parts[0]
                    + "."
                    + parts[1]
                )

            else:

                text = text.replace(
                    ",",
                    "",
                )

        match = re.search(
            r"-?\d+(?:\.\d+)?",
            text,
        )

        if not match:
            return None

        try:

            return float(
                match.group(0)
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # =========================================================
    # BRAND
    # =========================================================

    def _extract_brand(
        self,
        product: dict[str, Any],
    ):

        brand = product.get(
            "brand"
        )

        if isinstance(
            brand,
            dict,
        ):

            return self._clean(
                brand.get("name")
            )

        return self._clean(
            brand
        )

    def _infer_brand(
        self,
        title: str | None,
    ):

        if not title:
            return None

        normalized = title.lower()

        known_brands = {
            "apple": "Apple",
            "samsung": "Samsung",
            "google": "Google",
            "xiaomi": "Xiaomi",
            "oneplus": "OnePlus",
            "huawei": "Huawei",
            "sony": "Sony",
            "lg": "LG",
            "nike": "Nike",
            "adidas": "Adidas",
            "puma": "Puma",
            "reebok": "Reebok",
            "dell": "Dell",
            "hp": "HP",
            "lenovo": "Lenovo",
            "asus": "ASUS",
            "acer": "Acer",
            "microsoft": "Microsoft",
            "nintendo": "Nintendo",
            "dyson": "Dyson",
        }

        for key, brand in known_brands.items():

            if re.search(
                rf"\b{re.escape(key)}\b",
                normalized,
            ):
                return brand

        return None

    # =========================================================
    # MODEL
    # =========================================================

    def _extract_model(
        self,
        product: dict[str, Any],
    ):

        for key in (
            "model",
            "modelNumber",
            "model_number",
        ):

            value = self._clean(
                product.get(key)
            )

            if value:
                return value

        return None

    def _infer_model(
        self,
        title: str | None,
    ):

        if not title:
            return None

        normalized = " ".join(
            str(title).split()
        )

        # Apple iPhone.
        match = re.search(
            r"\biphone\s+"
            r"(?:\d+(?:\s+pro)?"
            r"(?:\s+max)?"
            r"(?:\s+plus)?"
            r"(?:\s+mini)?"
            r"(?:\s+pro\s+max)?)",
            normalized,
            re.IGNORECASE,
        )

        if match:
            return match.group(
                0
            ).strip()

        # Samsung Galaxy.
        match = re.search(
            r"\bgalaxy\s+"
            r"[A-Za-z0-9]+"
            r"(?:\s+[A-Za-z0-9]+){0,3}",
            normalized,
            re.IGNORECASE,
        )

        if match:
            return match.group(
                0
            ).strip()

        return None

    # =========================================================
    # PRODUCT TYPE
    # =========================================================

    def _extract_product_type(
        self,
        product: dict[str, Any],
    ):

        value = product.get(
            "category"
        )

        if isinstance(
            value,
            str,
        ):

            return value.strip() or None

        return None

    # =========================================================
    # CATEGORY
    # =========================================================

    def _extract_category(
        self,
        product: dict[str, Any],
    ):

        value = product.get(
            "category"
        )

        return self._clean(
            value
        )

    # =========================================================
    # ATTRIBUTES
    # =========================================================

    def _extract_attributes(
        self,
        product_data: dict[str, Any],
        title: str | None,
        description: str | None,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:

        attributes = {}

        text_parts = [
            title or "",
            description or "",
        ]

        text = " ".join(
            text_parts
        )

        # -----------------------------------------------------
        # Storage
        # -----------------------------------------------------

        storage = (
            fallback.get("storage")
        )

        if not storage:
            storage = self._extract_storage(
                product_data,
                text,
            )

        if storage:
            attributes["storage"] = storage

        # -----------------------------------------------------
        # Color
        # -----------------------------------------------------

        color = (
            fallback.get("color")
        )

        if not color:
            color = self._extract_color(
                product_data,
                text,
            )

        if color:
            attributes["color"] = color

        # -----------------------------------------------------
        # Size
        # -----------------------------------------------------

        size = (
            fallback.get("size")
        )

        if not size:
            size = self._extract_property(
                product_data,
                "size",
            )

        if size:
            attributes["size"] = size

        # -----------------------------------------------------
        # Material
        # -----------------------------------------------------

        material = (
            fallback.get("material")
        )

        if not material:
            material = self._extract_property(
                product_data,
                "material",
            )

        if material:
            attributes["material"] = material

        # -----------------------------------------------------
        # Gender
        # -----------------------------------------------------

        gender = (
            fallback.get("gender")
        )

        if not gender:
            gender = self._extract_gender(
                product_data,
                text,
            )

        if gender:
            attributes["gender"] = gender

        # -----------------------------------------------------
        # Quantity
        # -----------------------------------------------------

        quantity = (
            fallback.get("quantity")
        )

        if not quantity:
            quantity = self._extract_property(
                product_data,
                "quantity",
            )

        if quantity:
            attributes["quantity"] = quantity

        # -----------------------------------------------------
        # Capacity
        # -----------------------------------------------------

        capacity = (
            fallback.get("capacity")
        )

        if not capacity:
            capacity = self._extract_property(
                product_data,
                "capacity",
            )

        if capacity:
            attributes["capacity"] = capacity

        # -----------------------------------------------------
        # Voltage
        # -----------------------------------------------------

        voltage = (
            fallback.get("voltage")
        )

        if not voltage:
            voltage = self._extract_property(
                product_data,
                "voltage",
            )

        if voltage:
            attributes["voltage"] = voltage

        # -----------------------------------------------------
        # Compatibility
        # -----------------------------------------------------

        compatibility = (
            fallback.get("compatibility")
        )

        if not compatibility:
            compatibility = self._extract_property(
                product_data,
                "isCompatibleWith",
            )

        if compatibility:
            attributes["compatibility"] = compatibility

        return attributes

    def _extract_storage(
        self,
        product: dict[str, Any],
        text: str,
    ):

        for key in (
            "storage",
            "capacity",
            "memory",
        ):

            value = self._extract_property(
                product,
                key,
            )

            if value:
                normalized = self._normalize_storage(
                    value
                )

                if normalized:
                    return normalized

        match = re.search(
            r"\b"
            r"(\d+(?:\.\d+)?)"
            r"\s*"
            r"(TB|GB|ГБ|ТБ)"
            r"\b",
            text,
            re.IGNORECASE,
        )

        if match:

            value = match.group(1)
            unit = match.group(2)

            return (
                f"{value} "
                f"{unit.upper()}"
            )

        return None

    @staticmethod
    def _normalize_storage(
        value,
    ):

        if value is None:
            return None

        text = str(
            value
        ).strip()

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*"
            r"(TB|GB|ГБ|ТБ)",
            text,
            re.IGNORECASE,
        )

        if not match:
            return text or None

        number = match.group(1)
        unit = match.group(2).upper()

        return (
            f"{number} "
            f"{unit}"
        )

    def _extract_color(
        self,
        product: dict[str, Any],
        text: str,
    ):

        value = self._extract_property(
            product,
            "color",
        )

        if value:
            return value

        colors = [
            "black",
            "white",
            "blue",
            "red",
            "green",
            "yellow",
            "purple",
            "pink",
            "orange",
            "gray",
            "grey",
            "silver",
            "gold",
            "titanium",
            "черный",
            "чёрный",
            "белый",
            "синий",
            "красный",
            "зеленый",
            "зелёный",
            "желтый",
            "жёлтый",
            "фиолетовый",
            "розовый",
        ]

        normalized_text = text.lower()

        for color in colors:

            if re.search(
                rf"\b{re.escape(color)}\b",
                normalized_text,
            ):
                return color

        return None

    def _extract_gender(
        self,
        product: dict[str, Any],
        text: str,
    ):

        value = self._extract_property(
            product,
            "gender",
        )

        if value:
            return value

        normalized = text.lower()

        if re.search(
            r"\bmen'?s\b|\bmale\b|\bмуж",
            normalized,
        ):
            return "men"

        if re.search(
            r"\bwomen'?s\b|\bfemale\b|\bжен",
            normalized,
        ):
            return "women"

        if re.search(
            r"\bunisex\b|\bунисекс\b",
            normalized,
        ):
            return "unisex"

        return None

    def _extract_property(
        self,
        product: dict[str, Any],
        key: str,
    ):

        value = product.get(
            key
        )

        if value is None:
            return None

        if isinstance(
            value,
            dict,
        ):

            for nested_key in (
                "value",
                "name",
                "valueReference",
            ):

                nested = value.get(
                    nested_key
                )

                if nested is not None:

                    return self._clean(
                        nested
                    )

            return None

        return self._clean(
            value
        )

    # =========================================================
    # CONDITION
    # =========================================================

    def _extract_condition(
        self,
        product: dict[str, Any],
        offer: dict[str, Any],
    ):

        value = (
            offer.get(
                "itemCondition"
            )
            or product.get(
                "itemCondition"
            )
        )

        if not value:
            return None

        text = str(
            value
        ).lower()

        if "new" in text:
            return "new"

        if (
            "used" in text
            or "preowned" in text
            or "pre-owned" in text
        ):
            return "used"

        if "refurbished" in text:
            return "refurbished"

        if "renewed" in text:
            return "renewed"

        return self._clean(
            value
        )

    # =========================================================
    # AVAILABILITY
    # =========================================================

    def _extract_availability(
        self,
        offer: dict[str, Any],
    ):

        value = offer.get(
            "availability"
        )

        if not value:
            return None

        text = str(
            value
        ).lower()

        if "instock" in text:
            return "in_stock"

        if "outofstock" in text:
            return "out_of_stock"

        if "preorder" in text:
            return "preorder"

        if "limited" in text:
            return "limited"

        return self._clean(
            value
        )

    # =========================================================
    # SELLER
    # =========================================================

    def _extract_seller(
        self,
        offer: dict[str, Any],
    ):

        seller = offer.get(
            "seller"
        )

        if isinstance(
            seller,
            dict,
        ):

            return self._clean(
                seller.get("name")
            )

        return self._clean(
            seller
        )

    @staticmethod
    def _domain_as_seller(
        url: str,
    ):

        domain = urlparse(
            url
        ).netloc.lower()

        if domain.startswith(
            "www."
        ):
            domain = domain[4:]

        return domain or None

    # =========================================================
    # IDENTIFIERS
    # =========================================================

    def _extract_gtin(
        self,
        product: dict[str, Any],
    ):

        for key in (
            "gtin",
            "gtin8",
            "gtin12",
            "gtin13",
            "gtin14",
        ):

            value = self._clean(
                product.get(
                    key
                )
            )

            if value:
                return value

        return None

    # =========================================================
    # IMAGE
    # =========================================================

    def _extract_image(
        self,
        product: dict[str, Any],
    ):

        image = product.get(
            "image"
        )

        if isinstance(
            image,
            list,
        ):

            if image:

                first = image[0]

                if isinstance(
                    first,
                    dict,
                ):

                    return (
                        first.get("url")
                        or first.get(
                            "contentUrl"
                        )
                    )

                return first

            return None

        if isinstance(
            image,
            dict,
        ):

            return (
                image.get("url")
                or image.get(
                    "contentUrl"
                )
            )

        return self._clean(
            image
        )

    # =========================================================
    # META
    # =========================================================

    @staticmethod
    def _meta(
        soup: BeautifulSoup,
        property_name: str,
    ):

        element = soup.find(
            "meta",
            attrs={
                "property":
                    property_name
            },
        )

        if not element:

            element = soup.find(
                "meta",
                attrs={
                    "name":
                        property_name
                },
            )

        if not element:
            return None

        return element.get(
            "content"
        )

    def _extract_meta_currency(
        self,
        soup: BeautifulSoup,
    ):

        candidates = [
            "product:price:currency",
            "og:price:currency",
            "priceCurrency",
        ]

        for candidate in candidates:

            value = self._meta(
                soup,
                candidate,
            )

            if value:
                return value.strip().upper()

        element = soup.find(
            attrs={
                "itemprop":
                    "priceCurrency"
            }
        )

        if element:

            value = (
                element.get(
                    "content"
                )
                or element.get_text(
                    strip=True
                )
            )

            if value:
                return str(
                    value
                ).strip().upper()

        return None

    # =========================================================
    # CLEAN
    # =========================================================

    @staticmethod
    def _clean(
        value,
    ):

        if value is None:
            return None

        if isinstance(
            value,
            str,
        ):

            value = (
                value
                .replace(
                    "\xa0",
                    " ",
                )
                .strip()
            )

            return value or None

        return str(
            value
        ).strip() or None

    # =========================================================
    # FALLBACK
    # =========================================================

    @staticmethod
    def _fallback_result(
        fallback: dict[str, Any],
        url: str | None = None,
    ):

        attributes = fallback.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        condition = (
            fallback.get(
                "condition"
            )
            or attributes.get(
                "condition"
            )
            or "unknown"
        )

        return {
            "title":
                fallback.get(
                    "title"
                ),

            "brand":
                fallback.get(
                    "brand"
                ),

            "model":
                fallback.get(
                    "model"
                ),

            "product_type":
                fallback.get(
                    "product_type"
                ),

            "category":
                fallback.get(
                    "category"
                ),

            "attributes":
                attributes,

            "storage":
                fallback.get(
                    "storage"
                )
                or attributes.get(
                    "storage"
                ),

            "color":
                fallback.get(
                    "color"
                )
                or attributes.get(
                    "color"
                ),

            "size":
                fallback.get(
                    "size"
                )
                or attributes.get(
                    "size"
                ),

            "material":
                fallback.get(
                    "material"
                )
                or attributes.get(
                    "material"
                ),

            "gender":
                fallback.get(
                    "gender"
                )
                or attributes.get(
                    "gender"
                ),

            "condition":
                condition,

            "price":
                fallback.get(
                    "price"
                ),

            "currency":
                fallback.get(
                    "currency"
                ),

            "description":
                fallback.get(
                    "description"
                ),

            "image":
                fallback.get(
                    "image"
                ),

            "seller":
                fallback.get(
                    "seller"
                ),

            "availability":
                fallback.get(
                    "availability",
                    "unknown",
                ),

            "sku":
                fallback.get(
                    "sku"
                ),

            "mpn":
                fallback.get(
                    "mpn"
                ),

            "gtin":
                fallback.get(
                    "gtin"
                ),

            "url":
                url
                or fallback.get(
                    "url"
                ),

            "domain":
                fallback.get(
                    "domain"
                ),

            "extracted":
                False,
        }