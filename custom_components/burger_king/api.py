"""Async API client for Burger King (RBI Gateway & Sanity CDN)."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import aiohttp

from .const import DEFAULT_LOCALE, GRAPHQL_GATEWAY_URL

_LOGGER = logging.getLogger(__name__)


class BurgerKingApiError(Exception):
    """Base exception for Burger King API errors."""


class BurgerKingConnectionError(BurgerKingApiError):
    """Exception raised for network or connection failure."""


class BurgerKingApiClient:
    """Client for querying Burger King GraphQL gateway."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        locale: str = DEFAULT_LOCALE,
    ) -> None:
        """Initialize the client."""
        self.session = session
        self.locale = locale

    def _build_headers(self) -> Dict[str, str]:
        """Construct required gateway headers."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {
            "Content-Type": "application/json",
            "x-ui-language": self.locale,
            "x-ui-region": self.locale.upper(),
            "x-ui-platform": "android",
            "x-native-os": "Android",
            "x-user-datetime": now_str,
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; Mobile; rv:120.0)",
        }

    async def async_get_coupons(self) -> List[Dict[str, Any]]:
        """Fetch and parse all active coupons from Burger King."""
        query = """
        query LoyaltyOffersEvaluation($locale: String) {
          loyaltyOffersEvaluation(locale: $locale) {
            sanityOffersMap
            engineOffersMap
          }
        }
        """
        payload = {
            "query": query,
            "variables": {
                "locale": self.locale,
            },
        }

        try:
            async with self.session.post(
                GRAPHQL_GATEWAY_URL,
                json=payload,
                headers=self._build_headers(),
                timeout=aiohttp.ClientTimeout(total=20),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise BurgerKingConnectionError(
                        f"Burger King API HTTP {response.status}: {text}"
                    )

                data = await response.json(content_type=None)
                if "errors" in data and data["errors"]:
                    raise BurgerKingApiError(
                        f"GraphQL Error: {data['errors'][0].get('message')}"
                    )

                eval_data = (
                    data.get("data", {})
                    .get("loyaltyOffersEvaluation", {})
                )
                sanity_map: Dict[str, Any] = eval_data.get("sanityOffersMap", {})
                engine_map: Dict[str, Any] = eval_data.get("engineOffersMap", {})

                coupons: List[Dict[str, Any]] = []

                for engine_id, offer in sanity_map.items():
                    # Parse localized title
                    title = ""
                    name_obj = offer.get("name", {})
                    raw_title = name_obj.get("localeRaw") or name_obj.get("de")
                    if isinstance(raw_title, list):
                        for b in raw_title:
                            if isinstance(b, dict):
                                for ch in b.get("children", []):
                                    title += ch.get("text", "")
                    elif isinstance(raw_title, str):
                        title = raw_title

                    # Parse description
                    desc = ""
                    desc_obj = offer.get("description", {})
                    raw_desc = desc_obj.get("localeRaw") or desc_obj.get("de")
                    if isinstance(raw_desc, list):
                        for b in raw_desc:
                            if isinstance(b, dict):
                                for ch in b.get("children", []):
                                    desc += ch.get("text", "")
                    elif isinstance(raw_desc, str):
                        desc = raw_desc

                    # Detailed item listing from image description
                    items_desc = (
                        offer.get("localizedImage", {})
                        .get("locale", {})
                        .get("imageDescription", "")
                    )

                    short_code = offer.get("shortCode") or "APP"

                    # Pricing
                    offer_price_cents = offer.get("offerPrice")
                    if offer_price_cents is not None:
                        try:
                            euros = float(offer_price_cents) / 100.0
                            formatted_price = f"{euros:.2f} €".replace(".", ",")
                        except (ValueError, TypeError):
                            formatted_price = str(offer_price_cents)
                    else:
                        formatted_price = "Menü-Rabatt / Coupon"

                    # Timing / Expiration
                    eng = engine_map.get(engine_id, {})
                    end_date = eng.get("endDate")
                    start_date = eng.get("startDate")

                    if not end_date:
                        rules = offer.get("rules", [])
                        for r in rules:
                            if isinstance(r, dict) and "endDate" in r:
                                end_date = r["endDate"]
                                start_date = r.get("startDate")

                    # High resolution CDN image URL
                    img_url = (
                        offer.get("localizedImage", {})
                        .get("locale", {})
                        .get("app", {})
                        .get("asset", {})
                        .get("url", "")
                    )
                    if not img_url:
                        # Fallback from asset ref HASH
                        img_ref = (
                            offer.get("localizedImage", {})
                            .get("localeRaw", {})
                            .get("app", {})
                            .get("asset", {})
                            .get("_ref", "")
                        )
                        if img_ref and img_ref.startswith("image-"):
                            parts = img_ref.split("-")
                            if len(parts) >= 4:
                                img_url = f"https://cdn.sanity.io/images/czqk28jt/prod_bk_de/{parts[1]}-{parts[2]}.{parts[3]}"

                    clean_title = (
                        title.strip()
                        or offer.get("internalName", "Burger King Coupon")
                    )

                    coupons.append(
                        {
                            "id": offer.get("_id") or engine_id,
                            "engine_id": engine_id,
                            "code": str(short_code),
                            "title": clean_title,
                            "description": desc.strip(),
                            "items": items_desc.strip() if items_desc else clean_title,
                            "price": formatted_price,
                            "valid_from": start_date[:10] if start_date else None,
                            "valid_until": end_date[:10] if end_date else None,
                            "image_url": img_url,
                            "redemption_method": offer.get("redemptionMethod") or "restaurant",
                        }
                    )

                _LOGGER.debug(
                    "Fetched %d active Burger King coupons", len(coupons)
                )
                return coupons

        except aiohttp.ClientError as err:
            raise BurgerKingConnectionError(
                f"Error connecting to Burger King gateway: {err}"
            ) from err
