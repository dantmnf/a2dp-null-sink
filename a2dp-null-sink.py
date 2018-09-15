#!/usr/bin/python3

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

import argparse

dbus.Dict

argparser = argparse.ArgumentParser(description='A2DP null sink')
argparser.add_argument('--adapter', '-a', dest='adapter', help='Bluetooth adapter', default='hci0')
argparser.add_argument('--codec', '-c', dest='codecs', help='Configure supported additional codecs: none, mp3, aac, aptx, aptxhd, ldac', default='mp3,aac,aptx,aptxhd,ldac')

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

A2DP_SINK_UUID = "0000110b-0000-1000-8000-00805f9B34fb"
A2DP_SERVICE_UUID = "0000110d-0000-1000-8000-00805f9b34fb"
SBC_CODEC = dbus.Byte(0x00)
SBC_CAPABILITIES = dbus.Array([dbus.Byte(0xff), dbus.Byte(0xff), dbus.Byte(2), dbus.Byte(64)])
SBC_CONFIGURATION = dbus.Array([dbus.Byte(0x21), dbus.Byte(0x15), dbus.Byte(2), dbus.Byte(32)])

MP3_CODEC = dbus.Byte(0x01)
MP3_CAPABILITIES = dbus.Array([dbus.Byte(0x3f), dbus.Byte(0x07), dbus.Byte(0xff), dbus.Byte(0xfe)])
MP3_CONFIGURATION = dbus.Array([dbus.Byte(0x21), dbus.Byte(0x02), dbus.Byte(0x00), dbus.Byte(0x80)])

AAC_CODEC = dbus.Byte(2)
AAC_CAPABILITIES = dbus.ByteArray(b'\xC0\xFF\xFC\x80\xFF\xFF')

VENDOR_CODEC = dbus.Byte(0xFF)
APTX_CAPABILITIES = dbus.ByteArray(b'\x4F\x00\x00\x00\x01\x00\xF2')
APTXHD_CAPABILITIES = dbus.ByteArray(b'\xd7\x00\x00\x00\x24\x00\xF2\x00\x00\x00\x00')
LDAC_CAPABILITIES = dbus.ByteArray(b'\x2d\x01\x00\x00\xaa\x00\x3f\x01')

class Bluez():
    
    def __init__(self):

        self.bus = dbus.SystemBus()
        self.adapters = {}


        self.bus.add_signal_receiver(self._interfaceAdded, dbus_interface='org.freedesktop.DBus.ObjectManager', signal_name = "InterfacesAdded")
        self.bus.add_signal_receiver(self._interfaceRemoved, dbus_interface='org.freedesktop.DBus.ObjectManager', signal_name = "InterfacesRemoved")
        self.bus.add_signal_receiver(self._propertiesChanged, dbus_interface='org.freedesktop.DBus.Properties', signal_name = "PropertiesChanged", path_keyword = "path")

        # Find the adapters and create the objects
        obj_mgr = dbus.Interface(self.bus.get_object("org.bluez", "/"), 'org.freedesktop.DBus.ObjectManager')
        objs = obj_mgr.GetManagedObjects()
        for obj_path in objs:
            obj = objs[obj_path]
            if 'org.bluez.Adapter1' in obj:
                adapt_name = obj_path.split('/')[3]
                self.adapters[adapt_name] = Adapter(self.bus, obj_path)
                self.adapters[adapt_name].agentRegister()
               
    def _interfaceAdded(self, path, interface):
        # print("_interfaceAdded " + path + " | " + str(interface))
        adapt_name = path.split('/')[3]
        if 'org.bluez.Adapter1' in interface:
            self.adapters[adapt_name] = Adapter(self.bus, path)
            self.adapters[adapt_name].agentRegister()
        elif adapt_name in self.adapters:
            self.adapters[adapt_name]._interfaceAdded(path, interface)
                
    def _interfaceRemoved(self, path, interface):
        # print("_interfaceRemoved " + path + " | " + str(interface))
        spath = path.split('/')
        if len(spath) < 4:
            return
        adapt_name = spath[3]
        if 'org.bluez.Adapter1' in interface:
            del self.adapters[adapt_name]
        elif adapt_name in self.adapters:
            self.adapters[adapt_name]._interfaceRemoved(path, interface)

    def _propertiesChanged(self, interface, changed, invalidated, path):
        if not path.startswith("/org/bluez/"):
            return

        # print("_propertiesChanged " + path + " | " + str(interface) + " | " + str(changed) + " | " + str(invalidated))

        adapt_name = path.split('/')[3]
        if adapt_name in self.adapters:
            self.adapters[adapt_name]._propertiesChanged(interface, changed, invalidated, path)

    def getAdapter(self, adapt_name):
        if adapt_name in self.adapters:
            return self.adapters[adapt_name]
        return None


class Adapter():

    def __init__(self, bus, path):

        print("New adapter " + path)
        self.bus = bus
        self.path = path
        self.prop = dbus.Interface(self.bus.get_object("org.bluez", path), "org.freedesktop.DBus.Properties")
        self.devices = {}

        obj_mgr = dbus.Interface(self.bus.get_object("org.bluez", "/"), 'org.freedesktop.DBus.ObjectManager')
        objs = obj_mgr.GetManagedObjects()
        for obj_path in objs:
            obj = objs[obj_path]
            if 'org.bluez.Device1' in obj:
                dev_name = obj_path.split('/')[4]
                self.devices[dev_name] = Device(self.bus, obj_path)

    def __del__(self):
        print("Removed adapter " + self.path)

    def _interfaceAdded(self, path, interface):
        # print("adapter _interfaceAdded " + path)
        spath = path.split('/')
        dev_name = spath[4]
        if 'org.bluez.Device1' in interface:
            self.devices[dev_name] = Device(self.bus, path)
        elif dev_name in self.devices and len(spath) > 5:
            self.devices[dev_name]._interfaceAdded(path, interface)
        
    def _interfaceRemoved(self, path, interface):
        # print("adapter _interfaceRemoved " + path)
        spath = path.split('/')
        if len(spath) < 5:
            return
        dev_name = spath[4]
        if 'org.bluez.Device1' in interface:
            del self.devices[dev_name]
        elif dev_name in self.devices:
            self.devices[dev_name]._interfaceRemoved(path, interface)

    def _propertiesChanged(self, interface, changed, invalidated, path):
        # print("adapter _propertiesChanged " + path)
        spath = path.split('/')
        if len(spath) >= 5:
            dev_name  = spath[4]
            if dev_name in self.devices:
                self.devices[dev_name]._propertiesChanged(interface, changed, invalidated, path)
            return

        # Handle out property change here
        
    def powerSet(self, status):
        print("Turning on adapter " + self.path)
        self.prop.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(status))

    def discoverableSet(self, status):
        print("Making adapter " + self.path + " discoverable")
        self.prop.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(status))
    
    def pairableSet(self, status):
        print("Making adapter " + self.path + " pairable")
        self.prop.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(status))

    def mediaEndpointRegister(self, codecs):
        media = dbus.Interface(self.bus.get_object("org.bluez", self.path), "org.bluez.Media1")
        media_path = '/test/endpoint_sbc_' + self.path.split('/')[3]
        self.sbcMediaEndpoint = MediaEndpoint(self.bus, media_path, "sbc")
        properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : SBC_CODEC, "DelayReporting" : True, "Capabilities" : SBC_CAPABILITIES })
        media.RegisterEndpoint(media_path, properties)
        print("SBC MediaEndpoint registered for " + self.path)

        if "mp3" in codecs:
            media_path = '/test/endpoint_mp3_' + self.path.split('/')[3]
            self.aacMediaEndpoint = MediaEndpoint(self.bus, media_path, "mp3")
            properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : MP3_CODEC, "DelayReporting" : True, "Capabilities" : MP3_CAPABILITIES })
            media.RegisterEndpoint(media_path, properties)
            print("MP3 MediaEndpoint registered for " + self.path)

        if "aac" in codecs:
            media_path = '/test/endpoint_aac_' + self.path.split('/')[3]
            self.aacMediaEndpoint = MediaEndpoint(self.bus, media_path, "aac")
            properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : AAC_CODEC, "DelayReporting" : True, "Capabilities" : AAC_CAPABILITIES })
            media.RegisterEndpoint(media_path, properties)
            print("AAC MediaEndpoint registered for " + self.path)

        if "aptx" in codecs:
            media_path = '/test/endpoint_aptx_' + self.path.split('/')[3]
            self.aptxMediaEndpoint = MediaEndpoint(self.bus, media_path, "aptx")
            properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : VENDOR_CODEC, "DelayReporting" : True, "Capabilities" : APTX_CAPABILITIES })
            media.RegisterEndpoint(media_path, properties)
            print("aptX MediaEndpoint registered for " + self.path)

        if "aptxhd" in codecs:
            media_path = '/test/endpoint_aptxhd_' + self.path.split('/')[3]
            self.aptxhdMediaEndpoint = MediaEndpoint(self.bus, media_path, "aptxhd")
            properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : VENDOR_CODEC, "DelayReporting" : True, "Capabilities" : APTXHD_CAPABILITIES })
            media.RegisterEndpoint(media_path, properties)
            print("aptXHD MediaEndpoint registered for " + self.path)

        if "ldac" in codecs:
            media_path = '/test/endpoint_ldac_' + self.path.split('/')[3]
            self.aptxhdMediaEndpoint = MediaEndpoint(self.bus, media_path, "ldac")
            properties = dbus.Dictionary({ "UUID" : A2DP_SINK_UUID, "Codec" : VENDOR_CODEC, "DelayReporting" : True, "Capabilities" : LDAC_CAPABILITIES })
            media.RegisterEndpoint(media_path, properties)
            print("LDAC MediaEndpoint registered for " + self.path)

    def agentRegister(self):
        agent_path = '/test/agent_' + self.path.split('/')[3]
        self.agent = Agent(self.bus, agent_path)

        manager = dbus.Interface(self.bus.get_object("org.bluez", "/org/bluez"), "org.bluez.AgentManager1")
        manager.RegisterAgent(agent_path, "NoInputNoOutput")

        manager.RequestDefaultAgent(agent_path)

class Device():

    def __init__(self, bus, path):
        # print("New device " + path)
        self.bus = bus
        self.path = path
        self.mediaTransports = {}

    def __del__(self):
        # print("Removed device " + self.path)
        return

    def _interfaceAdded(self, path, interface):
        # print("device _interfaceAdded " + path)
        spath = path.split('/')
        if len(spath) < 6:
            return
        obj_name = spath[5]
        if 'org.bluez.MediaTransport1' in interface:
            self.mediaTransports[obj_name] = MediaTransport(self.bus, path)

    def _interfaceRemoved(self, path, interface):
        # print("device _interfaceRemoved " + path)
        obj_name = path.split('/')[5]
        if 'org.bluez.MediaTransport1' in interface and obj_name in self.mediaTransports:
            del self.mediaTransports[obj_name]

    def _propertiesChanged(self, interface, changed, invalidated, path):
        # print("device _propertiesChanged " + path)
        spath = path.split('/')

        if len(spath) >= 6:
            obj_name = spath[5]
            if 'org.bluez.MediaTransport1' in interface and obj_name in self.mediaTransports:
                self.mediaTransports[obj_name]._propertiesChanged(interface, changed, invalidated, path)

class MediaEndpoint(dbus.service.Object):

    def __init__(self, bus, path, codec):
        self.bus = bus
        self.path = path
        self.codec = codec
        super(MediaEndpoint, self).__init__(bus, path)

    @dbus.service.method("org.bluez.MediaEndpoint1", in_signature="ay", out_signature="ay")
    def SelectConfiguration(self, caps):
        print("[%s] SelectConfiguration (%s)" % (self.codec, caps))
        return self.configuration


    @dbus.service.method("org.bluez.MediaEndpoint1", in_signature="oay", out_signature="")
    def SetConfiguration(self, transport, config):
        print("[%s] SetConfiguration (%s, %s)" % (self.codec, transport, config))
        return

    @dbus.service.method("org.bluez.MediaEndpoint1", in_signature="o", out_signature="")
    def ClearConfiguration(self, transport):
        print("[%s] ClearConfiguration (%s)" % (self.codec, transport))


    @dbus.service.method("org.bluez.MediaEndpoint1", in_signature="", out_signature="")
    def Release(self):
        print("Release")


class MediaTransport():

    def __init__(self, bus, path):
        # print("New media transport " + path)
        self.bus = bus
        self.path = path
        self.pipeline = None

    def __del__(self):
        None
        # print("Removed media transport " + self.path)

    def _propertiesChanged(self, interface, changed, invalidated, path):
        # print("mediaTransport _propertiesChanged " + path)
        return


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"

class Agent(dbus.service.Object):

    @dbus.service.method('org.bluez.Agent1', in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        if (uuid == A2DP_SERVICE_UUID):
            print("Authorized A2DP for device " + device)
            return
        raise Rejected("Service unauthorized")


def find_adapters():

    adapts = {}
    objs = obj_mgr.GetManagedObjects()
    for obj_path in objs:
    
        obj = objs[obj_path]
        if 'org.bluez.Adapter1' in obj:
            adapts[obj_path] = obj['org.bluez.Adapter1']

    return adapts

def main():

    global args
    args = argparser.parse_args()

    bluez = Bluez()

    adapt = bluez.getAdapter(args.adapter)

    if not adapt:
        print("Adapter " + args.adapter + " not found")
        return

    adapt.powerSet(True)
    adapt.discoverableSet(True)
    adapt.mediaEndpointRegister(tuple(x.strip() for x in args.codecs.split(",")))

    mainloop = GLib.MainLoop()
    mainloop.run()
    return


if __name__ == '__main__':
    main()
