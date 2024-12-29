import network
import socket
import json
import machine
import asyncio
import onewire
import ds18x20
import time
import ntptime
from machine import RTC

def read_wifi_config():
    """
    Reads WiFi credentials from a config file.
    The config file should be formatted as
    * line 1 : SSID
    * line 2: password
    * line 3: NNTP server
    Returns tuple of (ssid, password, nntp_server)
    """
    try:
        with open('wifi_config.txt', 'r') as f:
            config_lines = f.readlines()
            ssid = config_lines[0].strip()
            password = config_lines[1].strip()
            nntp_server = config_lines[2].strip()
            
        return (ssid, password, nntp_server)
    
    except OSError as e:
        print("Could not read wifi_config.txt")
        print("Please create file with network name on line 1, password on line 2, NNTP server on line 3")
        raise e

def setup_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to WiFi...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('Network config:', wlan.ifconfig())
    
def sync_time(nntp_server):

    ntptime.host = nntp_server
    
    try:
        # Sync with NTP server
        ntptime.settime()
        
        # Get the RTC object
        rtc = RTC()
        
        # Get current time tuple
        current_time = time.localtime()
        
        print("Time synchronized successfully!")
        print("Current time:", format_time(current_time))
        
    except Exception as e:
        print("Error syncing time:", e)

def format_time(time_tuple):
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
        time_tuple[0], # Year
        time_tuple[1], # Month
        time_tuple[2], # Day
        time_tuple[3], # Hour
        time_tuple[4], # Minute
        time_tuple[5]  # Second
    )

def create_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 80))
    s.listen(5)
    return s

async def read_sensor():
    ds_pin = machine.Pin(4)
    ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    
    roms = ds_sensor.scan()
    if not roms:
        print("No DS18X20 devices found!")
        return None
    
    ds_sensor.convert_temp()
    await asyncio.sleep_ms(750)
    
    try:
        raw_temp = ds_sensor.read_temp(roms[0])
        return raw_temp
    except Exception as e:
        print("Error reading temperature:", e)
        return None
    

async def handle_request(client):
    request = client.recv(1024)
    request = str(request)
    
    try:
        method = request.split()[0].split("'")[1]
        path = request.split()[1]
    except IndexError:
        client.close()
        return
    
    if method == 'GET' and path == '/':
        temperature = await read_sensor()
        
        current_time = time.localtime()
        formatted_time = format_time(current_time)
        
        if temperature is not None:
            data = {
                "status": "success",
                "timestamp": formatted_time,
                "temperature": temperature,
                "message": "Success"
            }
            status_code = "200 OK"
        else:
            data = {
                "status": "error",
                "timestamp": time.time(),
                "message": "Failed to read temperature sensor"
            }
            status_code = "503 Service Unavailable"
        
        response = f"HTTP/1.1 {status_code}\r\n"
        response += "Content-Type: application/json\r\n"
        response += "Connection: close\r\n\r\n"
        response += json.dumps(data)
        
        client.send(response.encode())
    
    client.close()

async def main():
    
    ssid, password, nntp_server = read_wifi_config()
    
    setup_wifi(ssid, password)
    server = create_server()
    print('Server started on port 80')
    
    sync_time(nntp_server)
    
    while True:
        try:
            client, addr = server.accept()
            print('Client connected from', addr)
            await handle_request(client)
        except Exception as e:
            print('Error:', e)
            client.close()

if __name__ == '__main__':
    asyncio.run(main())