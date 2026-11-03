"""Config flow for Burger King integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    BurgerKingApiClient,
    BurgerKingApiError,
    BurgerKingConnectionError,
)
from .const import CONF_COUNTRY, DEFAULT_COUNTRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COUNTRY, default=DEFAULT_COUNTRY): vol.In(
            {
                "de": "Deutschland (DE)",
                "at": "Österreich (AT)",
                "ch": "Schweiz (CH)",
            }
        ),
    }
)


class BurgerKingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Burger King."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            country = user_input[CONF_COUNTRY].strip().lower()
            await self.async_set_unique_id(f"burger_king_{country}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = BurgerKingApiClient(session=session, locale=country)

            try:
                # Test connection by querying active coupons
                coupons = await client.async_get_coupons()
                _LOGGER.info(
                    "Connected to Burger King API, found %d active coupons",
                    len(coupons),
                )

                country_label = country.upper()
                return self.async_create_entry(
                    title=f"Burger King ({country_label})",
                    data={
                        CONF_COUNTRY: country,
                    },
                )

            except (BurgerKingConnectionError, BurgerKingApiError) as err:
                _LOGGER.error("Cannot connect to Burger King gateway: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during Burger King setup: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
