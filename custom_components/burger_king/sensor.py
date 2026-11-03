"""Support for Burger King coupon sensors."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Set

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CODE,
    ATTR_COUPONS,
    ATTR_DESCRIPTION,
    ATTR_IMAGE_URL,
    ATTR_ITEMS,
    ATTR_PRICE,
    ATTR_REDEMPTION_METHOD,
    ATTR_TITLE,
    ATTR_VALID_FROM,
    ATTR_VALID_UNTIL,
    DOMAIN,
)
from .coordinator import BurgerKingDataUpdateCoordinator
from .entity import BurgerKingEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Burger King sensor entities."""
    coordinator: BurgerKingDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    entities: list[SensorEntity] = [BurgerKingOverviewSensor(coordinator)]
    current_coupon_ids: Set[str] = set()

    coupons = coordinator.data.get("coupons", {})
    for cid in coupons:
        current_coupon_ids.add(cid)
        entities.append(BurgerKingCouponSensor(coordinator, cid))

    async_add_entities(entities)

    @callback
    def _async_update_entities() -> None:
        """Dynamically add new coupon entities when fresh data arrives."""
        new_entities: list[SensorEntity] = []
        latest_coupons = coordinator.data.get("coupons", {})
        for cid in latest_coupons:
            if cid not in current_coupon_ids:
                current_coupon_ids.add(cid)
                new_entities.append(BurgerKingCouponSensor(coordinator, cid))

        if new_entities:
            _LOGGER.debug(
                "Discovered %d new Burger King coupons", len(new_entities)
            )
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_async_update_entities))


class BurgerKingOverviewSensor(BurgerKingEntity, SensorEntity):
    """Overview sensor reporting the total count of active Burger King coupons."""

    _attr_translation_key = "active_coupons"
    _attr_icon = "mdi:ticket-percent"

    def __init__(
        self,
        coordinator: BurgerKingDataUpdateCoordinator,
    ) -> None:
        """Initialize overview sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = "burger_king_active_coupons_overview"

    @property
    def native_value(self) -> int:
        """Return the number of currently active coupons."""
        return self.coordinator.data.get("count", 0)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return all active coupons as an attribute list for easy dashboard cards."""
        coupons = list(self.coordinator.data.get("coupons", {}).values())
        return {
            ATTR_COUPONS: coupons,
            "last_synced": self.coordinator.data.get("last_update"),
        }


class BurgerKingCouponSensor(BurgerKingEntity, SensorEntity):
    """Individual entity for a specific Burger King coupon."""

    _attr_icon = "mdi:food-burger"

    def __init__(
        self,
        coordinator: BurgerKingDataUpdateCoordinator,
        coupon_id: str,
    ) -> None:
        """Initialize individual coupon sensor."""
        super().__init__(coordinator)
        self.coupon_id = coupon_id
        self._attr_unique_id = f"burger_king_coupon_{coupon_id}"

    @property
    def coupon_data(self) -> Dict[str, Any]:
        """Return coupon dictionary from coordinator."""
        return self.coordinator.data.get("coupons", {}).get(
            self.coupon_id, {}
        )

    @property
    def available(self) -> bool:
        """Return True if coupon is still active in latest fetch."""
        return (
            super().available
            and self.coupon_id in self.coordinator.data.get("coupons", {})
        )

    @property
    def name(self) -> str:
        """Return title of the coupon as entity name."""
        return self.coupon_data.get("title") or f"Burger King Coupon {self.coupon_id}"

    @property
    def native_value(self) -> str:
        """Return coupon code as main state."""
        return self.coupon_data.get("code") or "APP"

    @property
    def entity_picture(self) -> Optional[str]:
        """Return the official burger/meal image URL for display in HA UI."""
        return self.coupon_data.get("image_url") or None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return all coupon attributes."""
        data = self.coupon_data
        return {
            ATTR_CODE: data.get("code"),
            ATTR_TITLE: data.get("title"),
            ATTR_ITEMS: data.get("items"),
            ATTR_PRICE: data.get("price"),
            ATTR_DESCRIPTION: data.get("description"),
            ATTR_VALID_UNTIL: data.get("valid_until"),
            ATTR_VALID_FROM: data.get("valid_from"),
            ATTR_IMAGE_URL: data.get("image_url"),
            ATTR_REDEMPTION_METHOD: data.get("redemption_method"),
            "engine_id": data.get("engine_id"),
        }
