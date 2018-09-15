# a2dp-null-sink

This python script will turn your linux PC into a null A2DP sink.
It allows your devices (phone, tablet, etc) to connect without authentication to the PC and tell you what codec is being used.

## Requirements
* Bluez 5.x


## Bluez configuration

### /etc/bluetooth/main.conf

```
# This will show a nice 'speaker icon' on your phone/tablet
# Sometimes bluez override this, you can disable it by starting bluetoothd with `-P hostname`
Class = 0x000414

# Make your PC always discoverable
DiscoverableTimeout = 0

# Make your pC always pairable
PairableTimeout = 0
```

This script has not been tested along with other bluetooth software. It might not work if you have another bluetooth manager running on your pc. This is intended for headless server.

## Tested on

* ⭕ Debian buster (testing) on Banana Pi M2+, with BCM20702A0 USB Bluetooth adapter.
* ❌ Arch Linux (clean install) on VMware, with passthroughed BCM20702A0 USB Bluetooth adapter.
