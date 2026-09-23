from __future__ import annotations

from unittest.mock import Mock, patch

from offer.extractor import OfferExtractor


def _response(
    html: str,
    url: str = "https://example.com/product",
):
    response = Mock()

    response.text = html
    response.url = url

    response.raise_for_status.return_value = None

    return response


def test_extract_product_from_json_ld():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "Apple iPhone 15 Pro Max 256 GB",
                "brand": {
                    "@type": "Brand",
                    "name": "Apple"
                },
                "sku": "IPHONE15PM256",
                "mpn": "A3108",
                "offers": {
                    "@type": "Offer",
                    "price": "999.99",
                    "priceCurrency": "USD",
                    "availability":
                        "https://schema.org/InStock",
                    "itemCondition":
                        "https://schema.org/NewCondition",
                    "seller": {
                        "@type": "Organization",
                        "name": "Example Store"
                    }
                }
            }
            </script>
        </head>
        <body>
            Apple iPhone 15 Pro Max 256 GB
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/product"
        )

    assert result["title"] == (
        "Apple iPhone 15 Pro Max 256 GB"
    )

    assert result["brand"] == "Apple"

    assert result["price"] == 999.99

    assert result["currency"] == "USD"

    assert result["condition"] == "new"

    assert result["availability"] == "in_stock"

    assert result["seller"] == "Example Store"

    assert result["sku"] == "IPHONE15PM256"

    assert result["mpn"] == "A3108"

    assert result["extracted"] is True

    mock_get.assert_called_once()


def test_extract_refurbished_condition():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name":
                    "Refurbished iPhone 15 Pro Max 256GB",
                "brand": {
                    "@type": "Brand",
                    "name": "Apple"
                },
                "offers": {
                    "@type": "Offer",
                    "price": "849.00",
                    "priceCurrency": "USD",
                    "itemCondition":
                        "https://schema.org/RefurbishedCondition"
                }
            }
            </script>
        </head>
        <body>
            Refurbished iPhone 15 Pro Max 256GB
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/refurbished"
        )

    assert result["price"] == 849.00

    assert result["currency"] == "USD"

    assert result["condition"] == "refurbished"


def test_extract_out_of_stock():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name": "Test Product",
                "offers": {
                    "@type": "Offer",
                    "price": "100",
                    "priceCurrency": "USD",
                    "availability":
                        "https://schema.org/OutOfStock"
                }
            }
            </script>
        </head>
        <body>
            Test Product
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/out-of-stock"
        )

    assert result["availability"] == (
        "out_of_stock"
    )


def test_extract_meta_price_when_json_ld_has_no_price():
    html = """
    <html>
        <head>
            <meta
                property="og:title"
                content="Test Smartphone"
            />

            <meta
                property="product:price:amount"
                content="799.99"
            />

            <meta
                property="product:price:currency"
                content="USD"
            />
        </head>

        <body>
            Test Smartphone
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/meta-price"
        )

    assert result["title"] == (
        "Test Smartphone"
    )

    assert result["price"] == 799.99

    assert result["currency"] == "USD"


def test_unknown_price_is_not_zero():
    html = """
    <html>
        <head>
            <meta
                property="og:title"
                content="Product Without Price"
            />
        </head>

        <body>
            Product Without Price
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/no-price"
        )

    assert result["price"] is None


def test_fallback_is_used_when_request_fails():
    extractor = OfferExtractor()

    fallback = {
        "title":
            "Apple iPhone 15 Pro Max 256 GB",
        "brand":
            "Apple",
        "model":
            "iPhone 15 Pro Max",
        "product_type":
            "smartphone",
        "category":
            "smartphone",
        "attributes": {
            "storage": "256 GB",
        },
        "price": 699.99,
        "currency": "USD",
        "condition": "new",
        "availability": "in_stock",
        "seller": "Fallback Store",
    }

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.side_effect = Exception(
            "connection error"
        )

        result = extractor.extract(
            "https://example.com/failing-page",
            fallback=fallback,
        )

    assert result["title"] == (
        "Apple iPhone 15 Pro Max 256 GB"
    )

    assert result["brand"] == "Apple"

    assert result["model"] == (
        "iPhone 15 Pro Max"
    )

    assert result["price"] == 699.99

    assert result["currency"] == "USD"

    assert result["condition"] == "new"

    assert result["availability"] == "in_stock"

    assert result["seller"] == (
        "Fallback Store"
    )

    assert result["extracted"] is False


def test_meta_currency_is_normalized_to_uppercase():
    html = """
    <html>
        <head>
            <meta
                property="og:title"
                content="Test Product"
            />

            <meta
                property="product:price:amount"
                content="123.45"
            />

            <meta
                property="product:price:currency"
                content="eur"
            />
        </head>

        <body>
            Test Product
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/eur"
        )

    assert result["price"] == 123.45

    assert result["currency"] == "EUR"


def test_product_attributes_are_extracted():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "name":
                    "Apple iPhone 15 Pro Max 256 GB",
                "brand": {
                    "@type": "Brand",
                    "name": "Apple"
                },
                "offers": {
                    "@type": "Offer",
                    "price": "999",
                    "priceCurrency": "USD"
                }
            }
            </script>
        </head>

        <body>
            Apple iPhone 15 Pro Max 256 GB
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html
        )

        result = extractor.extract(
            "https://example.com/iphone"
        )

    attributes = result["attributes"]

    assert isinstance(
        attributes,
        dict,
    )

    assert attributes.get(
        "storage"
    ) == "256 GB"


def test_final_url_and_domain_are_preserved():
    html = """
    <html>
        <head>
            <meta
                property="og:title"
                content="Test Product"
            />
        </head>

        <body>
            Test Product
        </body>
    </html>
    """

    extractor = OfferExtractor()

    with patch(
        "offer.extractor.requests.get"
    ) as mock_get:

        mock_get.return_value = _response(
            html,
            url=(
                "https://www.example.com/"
                "product?id=123"
            ),
        )

        result = extractor.extract(
            "https://example.com/product"
        )

    assert result["url"] == (
        "https://www.example.com/"
        "product?id=123"
    )

    assert result["domain"] == (
        "www.example.com"
    )

    assert result["extracted"] is True