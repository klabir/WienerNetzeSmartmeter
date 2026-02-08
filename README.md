# Wiener Netze Smartmeter Integration for Home Assistant

[![codecov](https://codecov.io/gh/DarwinsBuddy/WienerNetzeSmartmeter/branch/main/graph/badge.svg?token=ACYNOG1WFW)](https://codecov.io/gh/DarwinsBuddy/WienerNetzeSmartmeter)
![Tests](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/test.yml/badge.svg)

![Hassfest](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/hassfest.yml/badge.svg)
![Validate](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/validate.yml/badge.svg)
![Release](https://github.com/DarwinsBuddy/WienerNetzeSmartMeter/actions/workflows/release.yml/badge.svg)

## About 

This repo contains a custom component for [Home Assistant](https://www.home-assistant.io) for exposing a sensor
providing information about a registered [WienerNetze Smartmeter](https://www.wienernetze.at/smartmeter).

## Sensors

The integration exposes one main energy sensor per Zählpunkt (total increasing meter reading) and a daily
consumption sensor that reports the latest DAY value. It also exposes companion reading date sensors
that surface the selected reading date as a timestamp for both the meter reading and DAY values. Both
main sensors include raw API payloads and the dates used for meter reading lookups (yesterday and the
day before yesterday) in their attributes for easier debugging.

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

You can choose between ui configuration or manual (by adding your credentials to `configuration.yaml` and `secrets.yaml` resp.)
After successful configuration you can add sensors to your favourite dashboard, or even to your energy dashboard to track your total consumption.

### UI
<img src="./doc/wnsm1.png" alt="Settings" width="500"/>
<img src="./doc/wnsm2.png" alt="Integrations" width="500"/>
<img src="./doc/wnsm3.png" alt="Add Integration" width="500"/>
<img src="./doc/wnsm4.png" alt="Search for WienerNetze" width="500"/>
<img src="./doc/wnsm5.png" alt="Authenticate with your credentials" width="500"/>
<img src="./doc/wnsm6.png" alt="Observe that all your smartmeters got imported" width="500"/>

### Manual
See [Example configuration files](https://github.com/DarwinsBuddy/WienerNetzeSmartmeter/blob/main/example/configuration.yaml)
## Copyright

This integration uses the API of https://www.wienernetze.at/smartmeter
All rights regarding the API are reserved by [Wiener Netze](https://www.wienernetze.at/impressum)

Special thanks to [platrysma](https://github.com/platysma)
for providing me a starting point [vienna-smartmeter](https://github.com/platysma/vienna-smartmeter)
and especially [florianL21](https://github.com/florianL21/)
for his [fork](https://github.com/florianL21/vienna-smartmeter/network)
