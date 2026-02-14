# Wiener Netze Smartmeter Integration for Home Assistant

[![codecov](https://codecov.io/gh/DarwinsBuddy/WienerNetzeSmartmeter/branch/main/graph/badge.svg?token=ACYNOG1WFW)](https://codecov.io/gh/DarwinsBuddy/WienerNetzeSmartmeter)
![Tests](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/test.yml/badge.svg)

![Hassfest](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/hassfest.yml/badge.svg)
![Validate](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/validate.yml/badge.svg)
![Release](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/release.yml/badge.svg)

## About 

## Version

2.0

This repo contains a custom component for [Home Assistant](https://www.home-assistant.io) for exposing a sensor
providing information about a registered [WienerNetze Smartmeter](https://www.wienernetze.at/smartmeter).

## Sensors

The integration exposes one main energy sensor per Zählpunkt (total increasing meter reading), a daily
consumption sensor that reports the latest DAY value, a companion DAY reading-date timestamp sensor,
and a companion METER_READ reading-date timestamp sensor for clean UI display of effective dates.

Configuration options in the UI include scan interval (minutes) and an optional advanced DAY statistics import mode.

| Sensor | Wertetyp source | State | Date context |
|---|---|---|---|
| `<zaehlpunkt>` | `METER_READ` | latest total meter reading (kWh) | `reading_date`, `yesterday`, `day_before_yesterday` attributes |
| `<zaehlpunkt> Day` | `DAY` | latest daily value (kWh) | `reading_date` attribute from latest DAY record |
| `<zaehlpunkt> Day Reading Date` | `DAY` | timestamp of selected DAY value | same date attributes as companion metadata |
| `<zaehlpunkt> Meter Read Reading Date` | `METER_READ` | timestamp of selected meter-read value | same date attributes as companion metadata |

## FAQs
[FAQs](https://github.com/DarwinsBuddy/WienerNetzeSmartmeter/discussions/19)

## Installation

### Manual

Copy `<project-dir>/custom_components/wnsm` into `<home-assistant-root>/config/custom_components`

### HACS
1. Search for `Wiener Netze Smart Meter` or `wnsm` in HACS
2. Install
3. ...
4. Profit!

## Configure

Configure the integration via the Home Assistant UI.
After successful configuration you can add sensors to your favourite dashboard, or even to your energy dashboard to track your total consumption.

### UI
<img src="./doc/wnsm1.png" alt="Settings" width="500"/>
<img src="./doc/wnsm2.png" alt="Integrations" width="500"/>
<img src="./doc/wnsm3.png" alt="Add Integration" width="500"/>
<img src="./doc/wnsm4.png" alt="Search for WienerNetze" width="500"/>
<img src="./doc/wnsm5.png" alt="Authenticate with your credentials" width="500"/>
<img src="./doc/wnsm6.png" alt="Observe that all your smartmeters got imported" width="500"/>

## Copyright

This integration uses the API of https://www.wienernetze.at/smartmeter
All rights regarding the API are reserved by [Wiener Netze](https://www.wienernetze.at/impressum)

Special thanks to [platrysma](https://github.com/platysma)
for providing me a starting point [vienna-smartmeter](https://github.com/platysma/vienna-smartmeter)
and especially [florianL21](https://github.com/florianL21/)
for his [fork](https://github.com/florianL21/vienna-smartmeter/network)
