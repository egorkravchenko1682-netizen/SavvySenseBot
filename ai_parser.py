import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedRequest:
    original_text: str

    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None

    max_price: Optional[float] = None
    currency: Optional[str] = None

    color: Optional[str] = None
    gender: Optional[str] = None

    keywords: List[str] = field(
        default_factory=list
    )

    priorities: List[str] = field(
        default_factory=list
    )

    intent: str = "search"


class AIParser:
    """
    Интеллектуальный разбор пользовательского запроса.

    На этом этапе работает локально и не требует
    API-ключей.

    Позже этот слой можно подключить к настоящей
    LLM-модели, не меняя остальную архитектуру.
    """

    def parse(
        self,
        text: str
    ) -> ParsedRequest:

        original = text.strip()

        request = ParsedRequest(
            original_text=original
        )

        if not original:
            return request

        lower = original.lower()

        request.category = self.detect_category(
            lower
        )

        request.brand = self.detect_brand(
            lower
        )

        request.model = self.detect_model(
            original,
            lower
        )

        request.color = self.detect_color(
            lower
        )

        request.gender = self.detect_gender(
            lower
        )

        (
            request.max_price,
            request.currency,
        ) = self.detect_budget(
            original
        )

        request.intent = self.detect_intent(
            lower
        )

        request.priorities = self.detect_priorities(
            lower
        )

        request.keywords = self.extract_keywords(
            original,
            request
        )

        return request

    def detect_category(
        self,
        text: str
    ) -> Optional[str]:

        categories = {

            "smartphone": [
                "iphone",
                "айфон",
                "смартфон",
                "телефон",
                "android",
                "андроид",
            ],

            "laptop": [
                "ноутбук",
                "ноут",
                "macbook",
                "макбук",
            ],

            "headphones": [
                "наушники",
                "airpods",
                "гарнитура",
                "headphones",
            ],

            "tv": [
                "телевизор",
                "телек",
                "tv",
                "телевизор",
            ],

            "clothing": [
                "футболка",
                "куртка",
                "рубашка",
                "джинсы",
                "брюки",
                "платье",
                "кофта",
                "худи",
                "свитшот",
                "одежда",
            ],

            "shoes": [
                "кроссовки",
                "кеды",
                "ботинки",
                "туфли",
                "обувь",
                "sneakers",
            ],

            "watch": [
                "часы",
                "смарт-часы",
                "apple watch",
                "watch",
            ],

            "camera": [
                "камера",
                "фотоаппарат",
                "объектив",
                "canon",
                "nikon",
                "sony alpha",
            ],

            "gaming": [
                "playstation",
                "xbox",
                "steam deck",
                "консоль",
                "игровая приставка",
            ],
        }

        for category, words in categories.items():

            for word in words:

                if word in text:
                    return category

        return None

    def detect_brand(
        self,
        text: str
    ) -> Optional[str]:

        brands = [
            "apple",
            "samsung",
            "xiaomi",
            "sony",
            "lg",
            "asus",
            "lenovo",
            "acer",
            "hp",
            "dell",
            "nike",
            "adidas",
            "puma",
            "new balance",
            "reebok",
            "jbl",
            "bose",
            "dyson",
            "canon",
            "nikon",
        ]

        for brand in brands:

            if brand in text:
                return brand

        if "айфон" in text:
            return "apple"

        if "самсунг" in text:
            return "samsung"

        return None

    def detect_model(
        self,
        original: str,
        text: str
    ) -> Optional[str]:

        patterns = [

            r"\biphone\s+\d+(?:\s+pro(?:\s+max)?)?\b",

            r"\bайфон\s+\d+(?:\s+про(?:\s+макс)?)?\b",

            r"\bgalaxy\s+s\d+(?:\s+ultra)?\b",

            r"\biphone\s+\d+\s+pro\s+max\b",

            r"\bmacbook\s+(?:air|pro)\b",

            r"\bairpods\s+(?:pro\s*)?\d*\b",

            r"\bps\s*5\b",

            r"\bps\s*5\s*pro\b",

            r"\bps\s*5\s*slim\b",

            r"\bxbox\s+series\s+[xs]\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                original,
                flags=re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    def detect_color(
        self,
        text: str
    ) -> Optional[str]:

        colors = {
            "черный": "black",
            "чёрный": "black",
            "black": "black",

            "белый": "white",
            "white": "white",

            "красный": "red",
            "red": "red",

            "синий": "blue",
            "голубой": "blue",
            "blue": "blue",

            "зеленый": "green",
            "зелёный": "green",
            "green": "green",

            "серый": "gray",
            "серебристый": "silver",

            "розовый": "pink",
            "pink": "pink",

            "фиолетовый": "purple",
        }

        for word, color in colors.items():

            if word in text:
                return color

        return None

    def detect_gender(
        self,
        text: str
    ) -> Optional[str]:

        if any(
            word in text
            for word in [
                "мужской",
                "мужская",
                "мужское",
                "для мужчины",
                "мужчин",
            ]
        ):
            return "male"

        if any(
            word in text
            for word in [
                "женский",
                "женская",
                "женское",
                "для женщины",
                "женщин",
            ]
        ):
            return "female"

        if any(
            word in text
            for word in [
                "детский",
                "детская",
                "для ребенка",
                "для ребёнка",
            ]
        ):
            return "children"

        return None

    def detect_budget(
        self,
        text: str
    ):

        patterns = [

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*\$?\s*([\d\s.,]+)\s*\$",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*\$\s*([\d\s.,]+)",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:USD|доллар(?:а|ов)?)",
                "USD",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*€?\s*([\d\s.,]+)\s*€",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*€\s*([\d\s.,]+)",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:EUR|евро)",
                "EUR",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*₽",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:RUB|руб(?:лей|ля)?)",
                "RUB",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*(?:BYN)",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*р\b",
                "BYN",
            ),

            (
                r"(?:до|не\s+дороже|максимум|не\s+более)"
                r"\s*([\d\s.,]+)\s*"
                r"(?:PLN|злотых|злот)",
                "PLN",
            ),
        ]

        for pattern, currency in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            value = (
                match.group(1)
                .replace(" ", "")
                .replace(",", ".")
            )

            try:
                return float(value), currency
            except ValueError:
                continue

        return None, None

    def detect_intent(
        self,
        text: str
    ) -> str:

        if any(
            word in text
            for word in [
                "дешевле",
                "подешевле",
                "самый дешевый",
                "самый дешёвый",
                "минимальная цена",
            ]
        ):
            return "find_cheapest"

        if any(
            word in text
            for word in [
                "сравни",
                "сравнить",
                "сравнение",
            ]
        ):
            return "compare"

        if any(
            word in text
            for word in [
                "стоит ли",
                "покупать",
                "нормальный ли",
                "хороший ли",
            ]
        ):
            return "check"

        if any(
            word in text
            for word in [
                "дешевле этого",
                "найди дешевле",
                "найти дешевле",
            ]
        ):
            return "find_cheaper"

        return "search"

    def detect_priorities(
        self,
        text: str
    ) -> List[str]:

        priorities = []

        priority_words = {

            "качество": [
                "качество",
                "качественный",
                "качественная",
                "надежный",
                "надёжный",
            ],

            "price": [
                "дешевый",
                "дешёвый",
                "дешево",
                "дёшево",
                "выгодный",
                "выгодно",
                "цена",
            ],

            "camera": [
                "камера",
                "фото",
                "фотографии",
                "снимать",
            ],

            "battery": [
                "батарея",
                "автономность",
                "заряд",
                "аккумулятор",
            ],

            "performance": [
                "мощный",
                "производительность",
                "быстрый",
                "игры",
                "игровой",
            ],

            "original": [
                "оригинал",
                "оригинальный",
                "не подделка",
                "настоящий",
            ],

            "delivery": [
                "доставка",
                "быстрая доставка",
                "бесплатная доставка",
            ],
        }

        for priority, words in priority_words.items():

            if any(
                word in text
                for word in words
            ):
                priorities.append(priority)

        return priorities

    def extract_keywords(
        self,
        original: str,
        request: ParsedRequest
    ) -> List[str]:

        text = original.lower()

        remove_words = [
            "мне",
            "нужен",
            "нужна",
            "нужно",
            "хочу",
            "хотел",
            "хотела",
            "бы",
            "купить",
            "найди",
            "найти",
            "поищи",
            "ищу",
            "подбери",
            "посоветуй",
            "покажи",
            "до",
            "не",
            "дороже",
            "максимум",
            "более",
            "самый",
            "самая",
            "лучший",
            "лучшая",
        ]

        words = re.findall(
            r"[a-zA-Zа-яА-ЯёЁ0-9-]+",
            text
        )

        result = []

        for word in words:

            if word in remove_words:
                continue

            if len(word) < 2:
                continue

            if word.isdigit():
                continue

            result.append(word)

        return list(
            dict.fromkeys(result)
        )


def parse_user_request(
    text: str
) -> ParsedRequest:

    parser = AIParser()

    return parser.parse(text)