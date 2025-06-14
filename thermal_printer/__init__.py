"""The Thermal Printer integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import voluptuous as vol
from bleak import BleakClient, BleakScanner
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_MAC_ADDRESS,
    DOMAIN,
    SERVICE_PRINT_TEXT,
    SERVICE_PRINT_QRCODE,
    SERVICE_PRINT_BARCODE,
    SERVICE_FEED_PAPER,
    PRINTER_CHARACTERISTIC_UUID,
    ESC_INIT,
    ESC_ALIGN_LEFT,
    ESC_ALIGN_CENTER,
    ESC_ALIGN_RIGHT,
    ESC_BOLD_ON,
    ESC_BOLD_OFF,
    ESC_SIZE_NORMAL,
    ESC_SIZE_LARGE,
    ESC_LINE_FEED,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = []

PRINT_TEXT_SCHEMA = vol.Schema({
    vol.Required("text"): cv.string,
    vol.Optional("font_size", default="normal"): vol.In(["small", "normal", "large"]),
    vol.Optional("alignment", default="left"): vol.In(["left", "center", "right"]),
    vol.Optional("bold", default=False): cv.boolean,
})

PRINT_QR_SCHEMA = vol.Schema({
    vol.Required("data"): cv.string,
    vol.Optional("size", default=6): vol.Range(min=1, max=16),
})

PRINT_BARCODE_SCHEMA = vol.Schema({
    vol.Required("data"): cv.string,
    vol.Optional("barcode_type", default="CODE128"): cv.string,
})

FEED_PAPER_SCHEMA = vol.Schema({
    vol.Optional("lines", default=3): vol.Range(min=1, max=10),
})


class ThermalPrinterCoordinator(DataUpdateCoordinator):
    """Coordinator for thermal printer."""

    def __init__(self, hass: HomeAssistant, mac_address: str) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.mac_address = mac_address
        self.client: BleakClient | None = None
        self.is_connected = False

    async def _async_update_data(self):
        """Update data via library."""
        try:
            if not self.is_connected:
                await self._connect()
            return {"connected": self.is_connected, "mac_address": self.mac_address}
        except Exception as err:
            _LOGGER.error("Error updating data: %s", err)
            self.is_connected = False
            return {"connected": False, "mac_address": self.mac_address}

    async def _connect(self):
        """Connect to the thermal printer."""
        try:
            if self.client and self.client.is_connected:
                return True

            self.client = BleakClient(self.mac_address)
            await self.client.connect()
            self.is_connected = True
            _LOGGER.info("Connected to thermal printer %s", self.mac_address)
            return True

        except Exception as err:
            _LOGGER.error("Failed to connect to printer: %s", err)
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from printer."""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            self.is_connected = False

    async def print_text(
        self,
        text: str,
        font_size: str = "normal",
        alignment: str = "left",
        bold: bool = False,
    ):
        """Print text to thermal printer."""
        if not await self._connect():
            raise Exception("Cannot connect to printer")

        try:
            # Create ESC/POS commands
            commands = bytearray()
            
            # Initialize printer
            commands.extend(ESC_INIT)
            
            # Set alignment
            if alignment == "center":
                commands.extend(ESC_ALIGN_CENTER)
            elif alignment == "right":
                commands.extend(ESC_ALIGN_RIGHT)
            else:
                commands.extend(ESC_ALIGN_LEFT)
            
            # Set font size
            if font_size == "large":
                commands.extend(ESC_SIZE_LARGE)
            else:
                commands.extend(ESC_SIZE_NORMAL)
            
            # Set bold
            if bold:
                commands.extend(ESC_BOLD_ON)
            
            # Add text (handle encoding properly)
            try:
                text_bytes = text.encode('cp850')  # Code page 850 for Latin chars
            except UnicodeEncodeError:
                text_bytes = text.encode('utf-8', errors='replace')
            
            commands.extend(text_bytes)
            
            # Line feed
            commands.extend(ESC_LINE_FEED)
            
            # Reset formatting
            commands.extend(ESC_BOLD_OFF)
            commands.extend(ESC_SIZE_NORMAL)
            commands.extend(ESC_ALIGN_LEFT)
            
            # Send to printer via Bluetooth
            await self._send_to_printer(commands)
            
        except Exception as err:
            _LOGGER.error("Error printing text: %s", err)
            raise

    async def print_qr_code(self, data: str, size: int = 6):
        """Print QR code."""
        if not await self._connect():
            raise Exception("Cannot connect to printer")

        try:
            commands = bytearray()
            
            # Initialize
            commands.extend(ESC_INIT)
            
            # Center alignment for QR code
            commands.extend(ESC_ALIGN_CENTER)
            
            # QR Code commands (ESC/POS standard)
            # Set QR code model
            commands.extend(b'\x1D\x28\x6B\x04\x00\x31\x41\x32\x00')
            
            # Set QR code size
            commands.extend(b'\x1D\x28\x6B\x03\x00\x31\x43')
            commands.extend(bytes([size]))
            
            # Set error correction level
            commands.extend(b'\x1D\x28\x6B\x03\x00\x31\x45\x30')
            
            # Store QR data
            data_bytes = data.encode('utf-8')
            data_len = len(data_bytes) + 3
            commands.extend(b'\x1D\x28\x6B')
            commands.extend(data_len.to_bytes(2, 'little'))
            commands.extend(b'\x31\x50\x30')
            commands.extend(data_bytes)
            
            # Print QR code
            commands.extend(b'\x1D\x28\x6B\x03\x00\x31\x51\x30')
            
            # Reset alignment
            commands.extend(ESC_ALIGN_LEFT)
            
            await self._send_to_printer(commands)
            
        except Exception as err:
            _LOGGER.error("Error printing QR code: %s", err)
            raise

    async def print_barcode(self, data: str, barcode_type: str = "CODE128"):
        """Print barcode."""
        if not await self._connect():
            raise Exception("Cannot connect to printer")

        try:
            commands = bytearray()
            
            # Initialize
            commands.extend(ESC_INIT)
            
            # Center alignment
            commands.extend(ESC_ALIGN_CENTER)
            
            # Set barcode height
            commands.extend(b'\x1D\x68\x64')  # Height = 100 dots
            
            # Set barcode width
            commands.extend(b'\x1D\x77\x02')  # Width = 2
            
            # Set HRI position (Human Readable Interpretation)
            commands.extend(b'\x1D\x48\x02')  # Below barcode
            
            # Print barcode (CODE128 example)
            if barcode_type.upper() == "CODE128":
                commands.extend(b'\x1D\x6B\x49')  # CODE128
                commands.extend(bytes([len(data)]))  # Data length
                commands.extend(data.encode('ascii'))
            
            # Reset alignment
            commands.extend(ESC_ALIGN_LEFT)
            
            await self._send_to_printer(commands)
            
        except Exception as err:
            _LOGGER.error("Error printing barcode: %s", err)
            raise

    async def feed_paper(self, lines: int = 3):
        """Feed paper."""
        if not await self._connect():
            raise Exception("Cannot connect to printer")

        try:
            commands = bytearray()
            for _ in range(lines):
                commands.extend(ESC_LINE_FEED)
            
            await self._send_to_printer(commands)
            
        except Exception as err:
            _LOGGER.error("Error feeding paper: %s", err)
            raise

    async def _send_to_printer(self, data: bytearray):
        """Send data to printer via Bluetooth."""
        if not self.client or not self.client.is_connected:
            raise Exception("Printer not connected")

        try:
            # Split data into chunks (Bluetooth has packet size limits)
            chunk_size = 20
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                await self.client.write_gatt_char(PRINTER_CHARACTERISTIC_UUID, chunk)
                await asyncio.sleep(0.05)  # Small delay between chunks
                
        except Exception as err:
            _LOGGER.error("Error sending data to printer: %s", err)
            raise


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Thermal Printer from a config entry."""
    mac_address = entry.data[CONF_MAC_ADDRESS]
    
    coordinator = ThermalPrinterCoordinator(hass, mac_address)
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def print_text_service(call: ServiceCall):
        """Handle print text service."""
        try:
            await coordinator.print_text(
                call.data["text"],
                call.data.get("font_size", "normal"),
                call.data.get("alignment", "left"),
                call.data.get("bold", False),
            )
        except Exception as err:
            _LOGGER.error("Error in print_text service: %s", err)

    async def print_qr_service(call: ServiceCall):
        """Handle print QR code service."""
        try:
            await coordinator.print_qr_code(
                call.data["data"],
                call.data.get("size", 6),
            )
        except Exception as err:
            _LOGGER.error("Error in print_qr service: %s", err)

    async def print_barcode_service(call: ServiceCall):
        """Handle print barcode service."""
        try:
            await coordinator.print_barcode(
                call.data["data"],
                call.data.get("barcode_type", "CODE128"),
            )
        except Exception as err:
            _LOGGER.error("Error in print_barcode service: %s", err)

    async def feed_paper_service(call: ServiceCall):
        """Handle feed paper service."""
        try:
            await coordinator.feed_paper(call.data.get("lines", 3))
        except Exception as err:
            _LOGGER.error("Error in feed_paper service: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_TEXT, print_text_service, schema=PRINT_TEXT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_QRCODE, print_qr_service, schema=PRINT_QR_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PRINT_BARCODE, print_barcode_service, schema=PRINT_BARCODE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FEED_PAPER, feed_paper_service, schema=FEED_PAPER_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.disconnect()
    
    # Remove services
    hass.services.async_remove(DOMAIN, SERVICE_PRINT_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_PRINT_QRCODE)
    hass.services.async_remove(DOMAIN, SERVICE_PRINT_BARCODE)
    hass.services.async_remove(DOMAIN, SERVICE_FEED_PAPER)
    
    hass.data[DOMAIN].pop(entry.entry_id)
    
    return True
