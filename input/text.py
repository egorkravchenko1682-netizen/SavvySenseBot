def parse_text(text: str) -> dict:
    if not text:
        return {
            "type": "text",
            "value": "",
            "valid": False,
        }

    text = text.strip()

    return {
        "type": "text",
        "value": text,
        "valid": bool(text),
    }