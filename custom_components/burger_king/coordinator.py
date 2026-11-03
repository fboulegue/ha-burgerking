"""DataUpdateCoordinator for Burger King."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import (
    BurgerKingApiClient,
    BurgerKingApiError,
    BurgerKingConnectionError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class BurgerKingDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching Burger King coupons data from the cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BurgerKingApiClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch active coupons from Burger King."""
        try:
            coupons_list = await self.client.async_get_coupons()
            coupons_dict: Dict[str, Dict[str, Any]] = {
                c["id"]: c for c in coupons_list
            }

            return {
                "coupons": coupons_dict,
                "count": len(coupons_list),
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

        except BurgerKingConnectionError as err:
            raise UpdateFailed(
                f"Error communicating with Burger King gateway: {err}"
            ) from err
        except BurgerKingApiError as err:
            raise UpdateFailed(f"Burger King API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(
                f"Unexpected error updating Burger King data: {err}"
            ) from err
