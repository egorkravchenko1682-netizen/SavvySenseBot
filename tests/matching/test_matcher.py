from matching.matcher import ProductMatcher
from matching.result import MatchStatus


def build_matcher():
    return ProductMatcher()


def iphone_request():
    return {
        "name": "iPhone 15 Pro Max",
        "brand": "Apple",
        "model": "iPhone 15 Pro Max",
        "product_type": "smartphone",
        "category": "smartphone",
        "required_attributes": {
            "brand": "Apple",
            "model": "iPhone 15 Pro Max",
            "product_type": "smartphone",
            "storage": "256 GB",
            "color": "black",
        },
    }


def iphone_offer(
    storage="256 GB",
    color="black",
    model="iPhone 15 Pro Max",
):
    return {
        "source": "test",
        "url": "https://example.com/product",
        "product": {
            "title": (
                f"Apple {model} "
                f"{storage} {color}"
            ),
            "brand": "Apple",
            "model": model,
            "product_type": "smartphone",
            "category": "smartphone",
            "attributes": {
                "storage": storage,
                "color": color,
            },
        },
    }


def test_exact_match():
    matcher = build_matcher()

    result = matcher.match(
        iphone_request(),
        iphone_offer(),
    )

    assert result.status == MatchStatus.EXACT
    assert result.is_exact
    assert not result.is_rejected
    assert result.identity_match
    assert result.score > 0

    assert (
        "storage"
        in result.matched_attributes
    )

    assert (
        "color"
        in result.matched_attributes
    )


def test_required_attribute_mismatch_is_rejected():
    matcher = build_matcher()

    result = matcher.match(
        iphone_request(),
        iphone_offer(
            storage="512 GB",
        ),
    )

    assert result.status == MatchStatus.REJECTED
    assert result.is_rejected
    assert not result.is_exact

    assert (
        "storage"
        in result.mismatched_attributes
    )


def test_model_mismatch_is_rejected():
    matcher = build_matcher()

    result = matcher.match(
        iphone_request(),
        iphone_offer(
            model="iPhone 15 Pro",
        ),
    )

    assert result.status == MatchStatus.REJECTED
    assert result.is_rejected

    assert (
        "model"
        in result.mismatched_attributes
    )


def test_unknown_required_attribute_is_not_exact():
    matcher = build_matcher()

    offer = iphone_offer()

    del offer["product"]["attributes"][
        "storage"
    ]

    result = matcher.match(
        iphone_request(),
        offer,
    )

    assert result.status == MatchStatus.SIMILAR
    assert result.is_similar
    assert not result.is_exact
    assert not result.is_rejected

    assert (
        "storage"
        in result.unknown_attributes
    )


def test_unknown_attribute_is_not_mismatch():
    matcher = build_matcher()

    offer = iphone_offer()

    del offer["product"]["attributes"][
        "color"
    ]

    result = matcher.match(
        iphone_request(),
        offer,
    )

    assert (
        "color"
        in result.unknown_attributes
    )

    assert (
        "color"
        not in result.mismatched_attributes
    )


def test_accessory_is_rejected():
    matcher = build_matcher()

    offer = {
        "source": "test",
        "url": "https://example.com/case",
        "product": {
            "title": (
                "iPhone 15 Pro Max "
                "protective case"
            ),
            "brand": None,
            "model": None,
            "product_type": "case",
            "category": "accessory",
            "attributes": {},
        },
    }

    result = matcher.match(
        iphone_request(),
        offer,
    )

    assert result.status == MatchStatus.REJECTED
    assert result.is_rejected

    assert (
        "accessory_or_spare_part"
        in result.reasons
    )


def test_informational_page_is_rejected():
    matcher = build_matcher()

    offer = {
        "source": "test",
        "url": "https://example.com/review",
        "product": {
            "title": (
                "iPhone 15 Pro Max "
                "review"
            ),
            "brand": "Apple",
            "model": "iPhone 15 Pro Max",
            "product_type": "smartphone",
            "category": "smartphone",
            "attributes": {},
        },
    }

    result = matcher.match(
        iphone_request(),
        offer,
    )

    assert result.status == MatchStatus.REJECTED
    assert result.is_rejected

    assert (
        "informational_page"
        in result.reasons
    )


def test_storage_units_are_normalized():
    matcher = build_matcher()

    request = iphone_request()

    request[
        "required_attributes"
    ]["storage"] = "1 TB"

    offer = iphone_offer(
        storage="1024 GB"
    )

    result = matcher.match(
        request,
        offer,
    )

    assert result.status == MatchStatus.EXACT

    assert (
        "storage"
        in result.matched_attributes
    )


def test_color_aliases_match():
    matcher = build_matcher()

    request = iphone_request()

    request[
        "required_attributes"
    ]["color"] = "чёрный"

    offer = iphone_offer(
        color="black"
    )

    result = matcher.match(
        request,
        offer,
    )

    assert result.status == MatchStatus.EXACT

    assert (
        "color"
        in result.matched_attributes
    )


def test_score_does_not_create_exact_match():
    matcher = build_matcher()

    request = iphone_request()

    offer = iphone_offer(
        storage="512 GB",
    )

    result = matcher.match(
        request,
        offer,
    )

    assert result.status == MatchStatus.REJECTED
    assert not result.is_exact