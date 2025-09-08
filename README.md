# Quandify Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This is a custom integration for Home Assistant to integrate with Quandify smart water devices.

This integration connects to the Quandify API over internet to provide sensor data and control for your devices.

## Installation

The easiest way to install this integration is with the Home Assistant Community Store (HACS).

1.  **HACS Installation:**

    - Go to your Home Assistant instance.
    - In the sidebar, click on **HACS**.
    - Go to **Integrations**.
    - Click the three-dot menu in the top right and select **"Custom repositories"**.
    - In the "Repository" field, paste this URL: `https://github.com/quandify/ha-quandify`
    - In the "Category" dropdown, select **"Integration"**.
    - Click **"Add"**.
    - You can now search for "Quandify" in the main HACS integration list and click **"Download"**.

2.  **Restart Home Assistant:** After downloading, you must restart Home Assistant for the integration to be loaded.

## Configuration

Once installed, the integration can be configured through the Home Assistant UI.

1.  Navigate to **Settings > Devices & Services**.
2.  Click the **+ Add Integration** button.
3.  Search for "Quandify" and select it.
4.  A dialog box will appear. Enter the email and password for your Quandify account.
5.  Click **Submit**. The integration will automatically discover and add all your registered devices and their entities.

## Supported devices

This integration provides the following entities based on your device type:

### Water Grip

- **Sensor:** Total volume
- **Sensor:** Water temperature
- **Sensor:** Water type (Hot/Cold)
- **Sensor:** WiFi signal strength
- **Binary Sensor:** Leak
- **Button:** Acknowledge leak
