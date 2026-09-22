def parse_photo(photo) -> dict:
    if photo is None:
        return {
            "type": "photo",
            "value": None,
            "valid": False,
        }

    return {
        "type": "photo",
        "value": photo,
        "valid": True,
    }