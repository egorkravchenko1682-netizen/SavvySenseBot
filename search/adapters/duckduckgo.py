from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


class DuckDuckGoAdapter:
    """
    Бесплатный web-search adapter для SAVVY SENSE.

    Использует HTML-версию DuckDuckGo.
    API key не требуется.

    Важно:
    этот адаптер ищет реальные страницы товаров,
    но не гарантирует наличие цены на каждой странице.
    """

    name = "duckduckgo"

    SEARCH_URL = (
        "https://html.duckduckgo.com/html/"
    )

    def __init__(
        self,
        timeout: int = 15,
        max_results: int = 5,
    ):

        self.timeout = timeout
        self.max_results = max_results

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        budget = budget or {}

        all_results = []

        seen_urls = set()

        for query in queries:

            try:

                results = self._search_query(
                    query=query,
                    region=region,
                )

                for result in results:

                    url = result.get(
                        "url"
                    )

                    if not url:
                        continue

                    if url in seen_urls:
                        continue

                    seen_urls.add(url)

                    all_results.append(
                        {
                            "source":
                                self.name,

                            "title":
                                result.get(
                                    "title"
                                ),

                            "brand":
                                None,

                            "category":
                                None,

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
                                url,

                            "seller":
                                result.get(
                                    "domain"
                                ),

                            "condition":
                                "unknown",

                            "availability":
                                "unknown",

                            "region":
                                region,

                            "description":
                                result.get(
                                    "description"
                                ),
                        }
                    )

                    if len(all_results) >= (
                        self.max_results
                    ):

                        return all_results[
                            :self.max_results
                        ]

            except Exception as error:

                print(
                    "DuckDuckGo search failed:",
                    error,
                )

        return all_results[
            :self.max_results
        ]

    # =========================
    # SEARCH QUERY
    # =========================

    def _search_query(
        self,
        query: str,
        region: str,
    ) -> list[dict[str, Any]]:

        params = {
            "q": query,
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(compatible; "
                "SavvySense/1.0)"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
        }

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=headers,
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

            title = (
                link.get_text(
                    " ",
                    strip=True,
                )
            )

            url = (
                link.get(
                    "href"
                )
            )

            description_element = (
                block.select_one(
                    ".result__snippet"
                )
            )

            description = ""

            if description_element:

                description = (
                    description_element
                    .get_text(
                        " ",
                        strip=True,
                    )
                )

            domain = ""

            if url:

                try:

                    from urllib.parse import (
                        urlparse,
                    )

                    domain = (
                        urlparse(
                            url
                        ).netloc
                    )

                except Exception:

                    domain = ""

            results.append(
                {
                    "title": title,
                    "url": url,
                    "description":
                        description,
                    "domain":
                        domain,
                }
            )

            if len(results) >= (
                self.max_results
            ):

                break

        return results