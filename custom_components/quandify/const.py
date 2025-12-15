"""Constants for the Quandify integration."""

from typing import Final

DOMAIN: Final = "quandify"
ATTRIBUTION: Final = "Data provided by Quandify"

# API Endpoints
AUTH_BASE_URL: Final = "https://auth.prod.quandify.com"
API_BASE_URL: Final = "https://api.prod.quandify.com"

# Configuration Constants
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_ID_TOKEN: Final = "id_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_ACCOUNT_ID: Final = "account_id"
CONF_ORGANIZATION_ID: Final = "organization_id"

# Data Update Coordinator
UPDATE_INTERVAL_MINUTES: Final = 10
