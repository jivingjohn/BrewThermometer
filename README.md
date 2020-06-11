# BrewThermometer
Thermostat to control the temperature to within 0.5 of a degree

Below is a how-to on setting up the Wemos D1 mini on a Mac. I should probably put that in the Wiki, but hey-ho

Once the Wemos is built with MicroPython, you can put the main.py file in the root directory and let it boot.

The Wemos will first of all enter a Setup Mode, enabling you to connect to it as an Access Point (AP). Once connected (the password is **micropythoN**, or whatever the MicroPython default pasword is for your build), you can navigate to the [setup url](http://192.168.4.1) and enter the setup information.

Once you've submitted the information, it's stored on the Wemos in /config.json. The Wemos will then turn the AP off, and connect to the WiFI that you've supplied in the config.

Providing everything is ok, it'll then start sending readings to the location you've specified, at the interval you've specified.

Simple!!

# To Do
- Currently, it assumes the port for sending requests is 1880, as I'm using Node-Red, this should really be configurable
- Also assumes the server side is hosted at /BrewThermometer. This should be configurable
- Isn't currently controlling any relays. I'll update this when my new relay board arrives in the post
- Provide a wiring diagram

# Setting up the Wemos D1 Mini
## What you'll need
 - [Wemos D1 Mini](https://www.ebay.co.uk/itm/WeMos-D1-Mini-V2-ESP8266-ESP12-ESP-12-NodeMCU-Arduino-Development-Board-WiFi/182722400443)
 - [DS18b20 temperature sensor](https://www.ebay.co.uk/itm/DS18B20-Waterproof-Temperature-Sensor-for-Arduino-UK-Seller/322461235769). I chose a waterproof one, so I can insert it into liquids. Non-waterproof would do fine for a room control
 - [4.7kΩ resistor](https://www.ebay.co.uk/itm/50-x-4-7K-Ohm-Carbon-Resistor-4K7-Resistors-1-4W-1st-CLASS-POST/121524008061)
 - Bread board for testing
 - Strip board for final soldering
 - Some kind of box to put it in (I haven't done this yet)
 - USB Micro B connector cable

 ## Set up a Mac so that you can build the Wemos D1 Mini
 *Sorry if you're using Windows, I've only done this on a Mac, so can't help you...*
 First thing to do is to install MicroPython. To do this, you need to be able to communicate with the D1 Mini
 ### USB Driver
 Download the USB driver for your operating system
 - [Wemos Windows/Mac USB Drivers](https://wiki.wemos.cc/downloads)

 Plug the Wemos in to your computer using a USB Micro B cable (android phone charge cable). You need to work out what port it's attached to by running `ls /dev/cu.*`.

 The D1 Mini will show up as something like `/dev/cu.wchusbserial...` or `/dev/cu.SLAB_USBtoUART` depending on your OS / driver version
 If you don't get anything like this, it's likely you haven't got the driver installed correctly. Make sure it's installed, and start a new terminal window (or if you're paranoid, restart your computer)

Once you can see the Wemos, you're good to go!
### Python
My Mac already has Python 3 installed. If you don't have it, you'll need to install it.
### Pip
You need Pip for the next bit, if you don't have it, get it by completing the following from a terminal prompt

`curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`

`python get-pip.py`
### ESP Tool
Run the following to get the MicroPython ESP Tool for installing firmware

`pip install esptool`
### MicroPython Firmware Download
The MicroPython site is amazing... To get the latest stable build, head to this link to download the [firmware](http://micropython.org/download/#esp8266)

### Ampy command line tool from Adafruit
This tool allows you to run scripts on the Wemos, as well as manipulate the file system (put, get, delete files etc). More about it can be found [here](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/install-ampy), but for this how-to just run
`pip install adafruit-ampy`


## Flashing the Wemos D1 Mini with MicroPython
Plug in the Wemos if it isn't already, and locate it's path using `ls /dev/cu.*`
### Erasing the firmware
To wipe the Wemos, run the following command
`esptool.py --port /dev/cu.*your device id here* erase_flash`
### Installing MicroPython
To install MicroPython, run the following command

`esptool.py --port /dev/cu.*your device id here* --baud 115200 write_flash --flash_size=detect 0 *location of your MicroPython firmware download*`

It shouldn't go wrong, but if it does, play around with the baud rate until you get a success
## Installing the actual code (finally)
- Clone this repo
- Open a terminal prompt
- Connect the Wemos D1 Mini and confirm it's path using `ls /dev/cu.*`
- Run the following command to install the BrewThermometer
  - `ampy -p /dev/cu.wchusbserial640 -b 115200 -d 1 put main.py /main.py`
  - You need the **-b** to ensure it doesn't write too quickly
  - You need **-d 1** as otherwise it doesn't wait for MicroPython to exit interactive mode

# Adding an app to work with the temperature sensor
I've used Node-Red to create a simple web-app that you can host to control and display the temperature.
You can host it locally, or in the cloud, but it the Wemos will need to be able to communicate with it.
## Setting up Node-Red
This is easy enough, [install Node-Red](https://nodered.org/docs/getting-started/)
## Deploy the example flow
[node-red-flow.json](https://github.com/jivingjohn/BrewThermometer/blob/master/main.py) contains all you need to host a small web server that you can access from wherever you can access Node-Red.

Once it's deployed, simply go to <your node-red installation>:<your node-red port>/BrewThermometer
## Endpoints
- /BrewThermometer is the homepage, and will display the current temperature.
- /BrewThermometer/Config will display the current config settings as json.
  - If you post to this you can set the config values
## CurrentHeatingCoolingState and other State variables
I have a version of this that I can control from Apple HomeKit which is why these are named as they are.
In the long term, these will be best stored in a database, but for now I've stored them as flow variables.
If you restart node-red, you'll lose your current state. This doesn't matter too much right now as there isn't a relay component to control.
