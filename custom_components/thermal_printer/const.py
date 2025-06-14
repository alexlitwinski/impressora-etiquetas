"""Constants for the Thermal Printer integration."""

DOMAIN = "thermal_printer"
CONF_MAC_ADDRESS = "mac_address"
CONF_DEVICE_NAME = "device_name"

# Service names
SERVICE_PRINT_TEXT = "print_text"
SERVICE_PRINT_QRCODE = "print_qr_code"
SERVICE_PRINT_BARCODE = "print_barcode"
SERVICE_FEED_PAPER = "feed_paper"

# Default values
DEFAULT_FONT_SIZE = "normal"
DEFAULT_ALIGNMENT = "left"

# Bluetooth characteristic UUID (may need adjustment for your printer)
PRINTER_CHARACTERISTIC_UUID = "0000ff02-0000-1000-8000-00805f9b34fb"

# ESC/POS Commands
ESC_INIT = b'\x1B\x40'  # Initialize printer
ESC_ALIGN_LEFT = b'\x1B\x61\x00'
ESC_ALIGN_CENTER = b'\x1B\x61\x01'
ESC_ALIGN_RIGHT = b'\x1B\x61\x02'
ESC_BOLD_ON = b'\x1B\x45\x01'
ESC_BOLD_OFF = b'\x1B\x45\x00'
ESC_SIZE_NORMAL = b'\x1D\x21\x00'
ESC_SIZE_LARGE = b'\x1D\x21\x11'
ESC_LINE_FEED = b'\x0A'
