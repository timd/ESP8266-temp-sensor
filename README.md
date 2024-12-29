# ESP8266-based Temperature Server

* ESP8266 D1
* DS18X20 temp sensor
* Micropython

Exposes an HTTP server on port 80, and returns current temperature reading in response to a `GET '/'` request.

## Setup

* Create a `wifi_config.txt` file in the root
* File should have the following format:
  ```
  <wifi ssid>
  <wifi password>
  <nntp server IP or hostname (e.g. ntp.pool.org)>
  ```