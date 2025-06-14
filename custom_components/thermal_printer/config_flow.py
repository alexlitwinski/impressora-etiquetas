"""Config flow for Thermal Printer integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from bleak import BleakScanner
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from .const import CONF_MAC_ADDRESS, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_MAC_ADDRESS): str,
    vol.Required(CONF_NAME, default="Impressora Térmica"): str,
})


class ThermalPrinterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Thermal Printer."""

    VERSION = 1

    def __init__(self):
        """Initialize config flow."""
        self.discovered_devices = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac_address = user_input[CONF_MAC_ADDRESS].upper()
            name = user_input[CONF_NAME]

            # Validate MAC address format
            if not self._is_valid_mac(mac_address):
                errors[CONF_MAC_ADDRESS] = "invalid_mac"
            else:
                # Check if already configured
                await self.async_set_unique_id(mac_address)
                self._abort_if_unique_id_configured()

                # Test connection
                try:
                    from bleak import BleakClient
                    client = BleakClient(mac_address)
                    connected = await client.connect()
                    if connected:
                        await client.disconnect()
                    else:
                        errors["base"] = "cannot_connect"
                except Exception:
                    errors["base"] = "cannot_connect"

                if not errors:
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_MAC_ADDRESS: mac_address,
                            CONF_NAME: name,
                        },
                    )

        # Discover Bluetooth devices
        if not self.discovered_devices:
            self.discovered_devices = await self._discover_bluetooth_devices()

        # Allow manual MAC entry while suggesting discovered devices
        if self.discovered_devices:
            options = [
                selector.SelectOptionDict(value=addr, label=name)
                for addr, name in self.discovered_devices.items()
            ]
            schema = vol.Schema({
                vol.Required(CONF_MAC_ADDRESS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Required(CONF_NAME, default="Impressora Térmica"): str,
            })
        else:
            schema = STEP_USER_DATA_SCHEMA

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "devices_found": len(self.discovered_devices)
            }
        )

    async def _discover_bluetooth_devices(self) -> dict[str, str]:
        """Discover Bluetooth devices."""
        devices = {}
        try:
            _LOGGER.info("Scanning for Bluetooth devices...")
            scanner = BleakScanner()
            bluetooth_devices = await scanner.discover(timeout=10.0)

            printer_keywords = ['printer', 'thermal', 'pos', 'receipt', 'impressora', 'print']

            for device in bluetooth_devices:
                device_name = device.name or "Dispositivo Desconhecido"
                device_address = device.address

                # Prioritize devices that look like printers
                if device.name and any(keyword in device.name.lower() 
                                     for keyword in printer_keywords):
                    devices[device_address] = f"🖨 {device_name} ({device_address})"
                elif device.name:
                    devices[device_address] = f"📱 {device_name} ({device_address})"
                else:
                    devices[device_address] = f"❓ {device_address}"

            _LOGGER.info("Found %d Bluetooth devices", len(devices))

        except Exception as err:
            _LOGGER.error("Error discovering Bluetooth devices: %s", err)

        return devices

    def _is_valid_mac(self, mac: str) -> bool:
        """Validate MAC address format."""
        import re
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        return bool(mac_pattern.match(mac))

    async def async_step_bluetooth(self, discovery_info):
        """Handle bluetooth discovery."""
        mac_address = discovery_info.address
        name = discovery_info.name or f"Thermal Printer {mac_address}"

        await self.async_set_unique_id(mac_address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"name": name}

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Confirm bluetooth discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"],
                data={
                    CONF_MAC_ADDRESS: self.unique_id,
                    CONF_NAME: self.context["title_placeholders"]["name"],
                }
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"]
        )
