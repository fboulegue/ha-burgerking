"""Base entity for Burger King integration."""

from __future__ import annotations

from typing import Any, Dict

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BurgerKingDataUpdateCoordinator


class BurgerKingEntity(CoordinatorEntity[BurgerKingDataUpdateCoordinator]):
    """Defines a base Burger King entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BurgerKingDataUpdateCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "burger_king_de")},
            name="Burger King Deutschland",
            manufacturer="Burger King / RBI",
            model="MyBK Coupons & Deals",
            entry_type=None,
            configuration_url="https://www.burgerking.de",
        )
