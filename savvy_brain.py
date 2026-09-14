from intent_engine import understand_query


def understand(text, country="BY", currency="EUR"):
    try:
        intent = understand_query(
            text,
            preferred_currency=currency,
            destination_country=country,
        )

        return {
            "query": intent.search_query or text,
            "product": intent.product,
            "brand": intent.brand,
            "model": intent.model,
            "category": intent.category,
            "color": intent.color,
            "size": intent.size,
            "gender": intent.gender,
            "condition": intent.condition,
            "max_price": intent.max_price,
            "currency": intent.currency or currency,
            "accessory": bool(intent.accessory_requested),
            "attributes": intent.attributes or [],
            "priorities": intent.priorities or [],
            "confidence": intent.confidence,
        }

    except Exception as e:
        print("SAVVY BRAIN ERROR:", e)
        return {
            "query": text,
            "product": None,
            "brand": None,
            "model": None,
            "category": None,
            "color": None,
            "size": None,
            "gender": None,
            "condition": None,
            "max_price": None,
            "currency": currency,
            "accessory": False,
            "attributes": [],
            "priorities": [],
            "confidence": 0.0,
        }