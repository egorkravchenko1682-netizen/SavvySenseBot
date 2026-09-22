from typing import Any
from urllib.parse import (
    parse_qs,
    unquote,
    urlparse,
)

import requests
from bs4 import BeautifulSoup


class DuckDuckGoAdapter:
    """
    Веб-поиск SAVVY SENSE через DuckDuckGo HTML.

    Задача адаптера:
    - найти потенциальные товарные страницы;
    - вернуть URL;
    - определить продавца по домену;
    - передать страницу дальше в OfferExtractor.

    Важное правило:
    DuckDuckGo только находит кандидатов.
    Решение о соответствии товара принимает ProductMatcher.
    """

    name = "duckduckgo"

    SEARCH_URL = (
        "https://html.duckduckgo.com/html/"
    )

    def __init__(
        self,
        max_results: int = 5,
        timeout: int = 15,
    ):
        self.max_results = max_results
        self.timeout = timeout

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        all_results = []

        seen_urls = set()

        if not queries:
            return []

        for query in queries:

            try:

                results = self._search_query(
                    query=query,
                    region=region,
                    currency=currency,
                )

            except Exception as error:

                print(
                    f"DuckDuckGo query failed: "
                    f"{query} | {error}"
                )

                continue

            for result in results:

                url = result.get(
                    "url"
                )

                if not url:
                    continue

                normalized_url = (
                    url.lower().strip()
                )

                if normalized_url in seen_urls:
                    continue

                seen_urls.add(
                    normalized_url
                )

                all_results.append(
                    result
                )

                if len(all_results) >= (
                    self.max_results
                ):
                    return all_results

        return all_results

    def _search_query(
        self,
        query: str,
        region: str,
        currency: str,
    ) -> list[dict[str, Any]]:

        params = {
            "q": query,
            "kl": self._region_code(
                region
            ),
        }

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        results = []

        result_blocks = soup.select(
            ".result"
        )

        for block in result_blocks:

            link = block.select_one(
                ".result__a"
            )

            if not link:
                continue

            raw_url = link.get(
                "href"
            )

            title = link.get_text(
                " ",
                strip=True,
            )

            if not raw_url:
                continue

            direct_url = (
                self._decode_url(
                    raw_url
                )
            )

            if not direct_url:
                continue

            if not self._is_http_url(
                direct_url
            ):
                continue

            if self._is_blocked_domain(
                direct_url
            ):
                continue

            description_element = (
                block.select_one(
                    ".result__snippet"
                )
            )

            description = None

            if description_element:

                description = (
                    description_element
                    .get_text(
                        " ",
                        strip=True,
                    )
                )

            seller = (
                self._extract_domain(
                    direct_url
                )
            )

            results.append(
                {
                    "source":
                        self.name,

                    "title":
                        title,

                    "brand":
                        None,

                    "category":
                        None,

                    "product_type":
                        None,

                    "model":
                        None,

                    "attributes":
                        {},

                    "price":
                        None,

                    "currency":
                        currency,

                    "delivery":
                        None,

                    "taxes":
                        None,

                    "duties":
                        None,

                    "fees":
                        None,

                    "url":
                        direct_url,

                    "seller":
                        seller,

                    "condition":
                        "unknown",

                    "availability":
                        "unknown",

                    "region":
                        region,

                    "description":
                        description,

                    "extracted":
                        False,
                }
            )

        return results

    @staticmethod
    def _decode_url(
        url: str,
    ) -> str | None:

        if not url:
            return None

        url = url.strip()

        # Обычная прямая ссылка.
        if url.startswith(
            "http://"
        ) or url.startswith(
            "https://"
        ):

            parsed = urlparse(
                url
            )

            # DuckDuckGo redirect.
            if (
                parsed.netloc
                and "duckduckgo.com"
                in parsed.netloc.lower()
            ):

                query = parse_qs(
                    parsed.query
                )

                uddg = query.get(
                    "uddg"
                )

                if uddg:

                    return unquote(
                        uddg[0]
                    )

            return url

        # Иногда DDG отдаёт ссылки
        # без стандартного протокола.
        if url.startswith(
            "//"
        ):

            return (
                "https:"
                + url
            )

        return None

    @staticmethod
    def _extract_domain(
        url: str,
    ) -> str | None:

        try:

            hostname = urlparse(
                url
            ).netloc.lower()

            if hostname.startswith(
                "www."
            ):
                hostname = hostname[
                    4:
                ]

            return hostname or None

        except Exception:

            return None

    @staticmethod
    def _is_http_url(
        url: str,
    ) -> bool:

        try:

            parsed = urlparse(
                url
            )

            return (
                parsed.scheme
                in (
                    "http",
                    "https",
                )
                and bool(
                    parsed.netloc
                )
            )

        except Exception:

            return False

    @staticmethod
    def _is_blocked_domain(
        url: str,
    ) -> bool:

        try:

            domain = urlparse(
                url
            ).netloc.lower()

        except Exception:

            return True

        blocked = {
            "duckduckgo.com",
            "www.duckduckgo.com",
        }

        return domain in blocked

    @staticmethod
    def _region_code(
        region: str,
    ) -> str:

        region = (
            str(
                region or "US"
            )
            .upper()
            .strip()
        )

        mapping = {
            "BY": "by-ru",
            "RU": "ru-ru",
            "PL": "pl-pl",
            "FR": "fr-fr",
            "DE": "de-de",
            "US": "us-en",
            "GB": "uk-en",
        }

        return mapping.get(
            region,
            "wt-wt",
        )

    @staticmethod
    def _headers():

        return {
            "User-Agent": (
                "Mozilla/5.0 "
                "(iPhone; CPU iPhone OS 18_0 "
                "like Mac OS X) "
                "AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) "
                "Version/18.0 Mobile/15E148 "
                "Safari/604.1"
            ),
            "Accept-Language":
                "en-US,en;q=0.9",
            "Accept":
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8",
        }