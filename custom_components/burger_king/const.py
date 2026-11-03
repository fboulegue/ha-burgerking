"""Constants for the Burger King integration."""

from datetime import timedelta

DOMAIN = "burger_king"

# API Endpoints
GRAPHQL_GATEWAY_URL = "https://euc1-prod-bk-gateway.rbictg.com/graphql"
SANITY_CDN_BASE = "https://cdn.sanity.io/images/czqk28jt/prod_bk_de"

# Default configuration values
CONF_COUNTRY = "country"
DEFAULT_COUNTRY = "de"
DEFAULT_LOCALE = "de"

# Scan interval: coupons change infrequently (every few days/weeks)
DEFAULT_SCAN_INTERVAL = timedelta(hours=2)

# Attributes
ATTR_CODE = "code"
ATTR_TITLE = "title"
ATTR_DESCRIPTION = "description"
ATTR_ITEMS = "items"
ATTR_PRICE = "price"
ATTR_VALID_UNTIL = "valid_until"
ATTR_VALID_FROM = "valid_from"
ATTR_IMAGE_URL = "image_url"
ATTR_REDEMPTION_METHOD = "redemption_method"
ATTR_COUPONS = "coupons"
