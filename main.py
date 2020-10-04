# Brewers Thermometer #
import ds18x20, gc, json, network, onewire, os, socket, sys, time, urequests
from machine import Pin

setup_html = """
    <head><title>Setup Brew Thermometer</title></head>
    <body><h1>Set up the thermometer</h1>
        <form method="GET" action="/">
            <label for="ip_address">IP Address of Thermometer</label>
            <input type="text" name="ip_address" />
            <label for="essid">WiFI Name</label>
            <input type="text" name="essid" />
            <label for="password">WiFI Password</label>
            <input type="text" name="password" />
            <button type="submit">Submit</button>
        </form>
    </body>"""

setup_complete_html = """
    <head><title>Setup Brew Thermometer</title></head>
    <body>
        <h1>Setup complete</h1>
    </body>"""

# WiFI variables
ap_if = network.WLAN(network.AP_IF) # WiFI access point
sta_if = network.WLAN(network.STA_IF) # WiFI station

# default relay values
default_relay_pins = { "Cooling" : 5, "Heating" : 4, "R3" : 0, "R4" : 2 }
default_relay_values = { "Cooling" : 0, "Heating" : 0, "R3" : 0, "R4" : 0 }

# default current heating cooling state
default_current_heating_cooling_state = { "CurrentHeatingCoolingState" : 0 }

# default board config
default_board_config = { "sample_frequency_seconds": 5, "one_wire_pin": 12, "relay_pins" : default_relay_pins }

# host a simple web page that can collect config for us
# returns config as json formatted string
def host_setup_webpage(setup_page, confirmation_page):
    passed_params = "nothing"
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(5)
    while passed_params == "nothing":
        cl, addr = s.accept()
        request = cl.recv(1024)
        request = str(request)
        response = setup_page
        if "/?" in request: # look for querystring in request
            for element in request.split():
                if "/?" in element:
                    passed_params = element.replace("/?", "").replace("=", '":"').replace("&", '","').replace("\n","")
                    response = confirmation_page
                    break
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()
    gc.collect()
    return '{"%s"}' % passed_params

# connect to the wifi with the given credentials
# this would loop forever if it can't connect...
def connect_to_wifi(essid, password):
    if not sta_if.isconnected():
        sta_if.active(True) # activate station interface
        sta_if.connect(essid, password) # credentials here
        while not sta_if.isconnected():
            pass # wait until we're connected
    gc.collect()

# Enables AP if we don't have a configuration file
# Disables AP once config stored
# Returns config as json object
def get_config(config_file, setup_page, confirmation_page):
    files = os.listdir()
    # setup mode
    if not config_file in files:
        while not ap_if.active():
            ap_if.active(True)
        gc.collect()
        config_json = host_setup_webpage(setup_page, confirmation_page)
        f = open(config_file, "w")
        f.write(config_json)
        f.close()
        gc.collect()
    # read config file
    f = open(config_file, 'r')
    config_content = json.loads(f.read())
    f.close()
    gc.collect()

    ap_if.active(False) # turn off the AP
    gc.collect()
    return config_content

# to remove a config file
def remove_config(configuration_file):
    files = os.listdir()
    if configuration_file in files:
        os.remove(configuration_file)

# try and get a json response from a url
# returns retrieved json object or default value
def get_request_with_default(request_url, default_value):
    for attempt in range(5):
        try:
            response = urequests.get(request_url)
            response_json = response.json()
        except Exception as e:
            print("Error in get request:", e)
        finally:
            gc.collect()
            return response_json
    else:
        response_json = default_value
    return response_json

# set up the relays
def setup_relays(relay_pins):
    return_relays = {}
    for pin in relay_pins.keys():
        return_relays[pin] = Pin(relay_pins[pin], Pin.OUT)
        return_relays[pin].value(1)
    return return_relays

# set the relay states
def set_relay_states(relays, CurrentHeatingCoolingState):
    current_state = CurrentHeatingCoolingState["CurrentHeatingCoolingState"]
    # relay state: 0 is on and 1 is off
    # CurrentHeatingCoolingState: 0 is off, 1 is heat, 2 is cool
    if (current_state == 1):
        # we want to heat things up
        relays["Cooling"].value(1)
        relays["Heating"].value(0)
    elif (current_state == 2):
        # we want to cool things down
        relays["Cooling"].value(0)
        relays["Heating"].value(1)
    else:
        # turn both relays off
        relays["Cooling"].value(1)
        relays["Heating"].value(1)

# Get the config
config = get_config("config.json", setup_html, setup_complete_html)

# connect to WiFI
connect_to_wifi(config["essid"], config["password"])

# create urls from config
base_url = "http://%s:1880/BrewThermometer" % config["ip_address"]
config_url = "%s/Config" % base_url
current_temperature_url = "%s/CurrentTemperature" % base_url
current_heating_cooling_state_url = "%s/CurrentHeatingCoolingState" % base_url

# get the board config
setup_config = get_request_with_default(config_url, default_board_config)

# set up the DS18b20
ds_pin = Pin(setup_config["one_wire_pin"]) # microPy 12 is pin 6 on Wemos D1 mini
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
sensors = ds_sensor.scan() # may be more than one sensor
gc.collect()

# setup the relays
relay_control = setup_relays(setup_config["relay_pins"])
print(relay_control)
# read the temperature and report
# control the relays
while True:
    current_temp = 0 # temperature reading
    if len(sensors):
        ds_sensor.convert_temp() # initialise for reading
        time.sleep_ms(750) # takes a while to initialise
        for sensor in sensors:
            current_temp += ds_sensor.read_temp(sensor) # read the sensor
        current_temp = current_temp / len(sensors)
    else:
        current_temp = 8008
        print("Error, no ds18b20 sensors were detected")

    connect_to_wifi(config["essid"], config["password"]) # connect to WiFI

    try:
        # post the current temperature
        response = urequests.post(current_temperature_url, json = {
            "CurrentTemperature" : current_temp
        })
        # get the relay states
        response = get_request_with_default(current_heating_cooling_state_url, default_current_heating_cooling_state)
        set_relay_states(relay_control, response)
    except Exception as e:
        print("Error in main while loop:", e)
    finally:
        gc.collect()
        time.sleep(setup_config["sample_frequency_seconds"]) # delay time
