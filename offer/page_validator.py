from __future__ import annotations

import re


class PageValidator:
    """Проверяет, можно ли использовать страницу как источник товара."""

    REJECT_PATTERNS = {
        "captcha": [
            "captcha",
            "robot or human",
            "verify you are human",
            "activate and hold",
        ],
        "blocked": [
            "access denied",
            "access blocked",
            "page blocked",
            "you have been blocked",
            "/blocked",
        ],
        "login_required": [
            "sign in to continue",
            "login to continue",
            "please log in",
        ],
        "error": [
            "something went wrong",
            "page not found",
            "internal server error",
        ],
    }

    def validate(
        self,
        text: str | None,
        url: str | None = None,
    ) -> dict:

        if not text and not url:
            return {
                "page_valid": False,
                "rejection_reason": "empty_page",
                "validation_source": "validator",
            }

        content = f"{text or ''} {url or ''}".lower()

        for reason, patterns in self.REJECT_PATTERNS.items():
            for pattern in patterns:
                if re.search(re.escape(pattern), content):
                    return {
                        "page_valid": False,
                        "rejection_reason": reason,
                        "validation_source": "validator",
                    }

        return {
            "page_valid": True,
            "rejection_reason": None,
            "validation_source": "validator",
        }