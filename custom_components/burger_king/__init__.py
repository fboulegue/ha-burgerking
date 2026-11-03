"""The Burger King integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BurgerKingApiClient
from .const import CONF_COUNTRY, DEFAULT_COUNTRY, DOMAIN
from .coordinator import BurgerKingDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Burger King from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    country = entry.data.get(CONF_COUNTRY, DEFAULT_COUNTRY)
    session = async_get_clientsession(hass)
    client = BurgerKingApiClient(session=session, locale=country)

    coordinator = BurgerKingDataUpdateCoordinator(hass, client, entry)

    # Perform initial data refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
