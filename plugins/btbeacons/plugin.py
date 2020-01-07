# Basic Python Plugin Example
#
# Author: GizMoCuz
#
"""
<plugin key="btbeacons" name="Bluetooth Beacons" author="bluebook" version="1.0.0" externallink="https://www.google.com/">
    <description>
        <h2>Bluetooth Beacons</h2><br/>
        Overview...
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Device Type - What it does...</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
       <param field="Address" label="Bluetooth Adapter" required="false" />
       <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
      </param>
    </params>
</plugin>
"""





import Domoticz
import json
import select

from mgmt import *
import tempo


_IDLE = 1
_DISCOVERY_STARTED = 2
_DISCOVERING = 3


class BasePlugin:
    enabled = False
    def __init__(self):
        #self.var = 123
        self.UpdateInterval = 300
        self.WaitCount = self.UpdateInterval / 10
        self.Units = {}
        self.NextCommand = {}
        self.btsock = None
        self.state = _IDLE
        
        return

    def getNextUnit(self):
        for id in range(1, 255):
            if id not in Devices:
                return id

        return None
    
            
    def addTempoDevice(self, device):
        unit = self.getNextUnit()
        device_name = device.get_name()[0]
        device_id = device.get_address()
        Domoticz.Device(Name=device_name,  Unit=unit, DeviceID = device_id, TypeName="Temperature").Create()
        self.Units[device_id] = unit
        Domoticz.Log("Created tempo device " + device_name)
                

    def updateTempoDevice(self, device, tempo_data):
        unit = self.Units[ device.get_address() ]

        if unit is None:
            Domoticz.Log("No unit for tempo device " + device.get_address())
            return
        
        Devices[unit].Update(nValue=0, sValue="%.1f" % tempo_data.temp, SignalLevel=device.rssi + 100, BatteryLevel=tempo_data.battery)
                

    def get_tempo_data(self, mfg_data):
        pdu1 = None
        pdu2 = None

        for record in mfg_data:
            if record['id'] == tempo.BLUEMAESTRO_MFR_CODE:
                if pdu1 is None:
                    pdu1 = record['data']
                else:
                    pdu2 = record['data']
                    break

        if pdu1 is not None:
            try:
                return tempo.tempo_data(pdu1, pdu2)

            except ValueError as e:
                Domoticz.Debug(e.str())

        return None
        



    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
            
        Domoticz.Debug("onStart called")

        for d in Devices:
            self.Units[Devices[d].DeviceID] = d
            
        self.btsock = mgmt_open()
        self.btsock.setblocking(False)
        self.WaitCount = 0  # Start up immediately

    def onStop(self):
        Domoticz.Debug("onStop called")
        self.btsock.close()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")
            

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")
        
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        self.WaitCount -= 1

        if (self.WaitCount > 0):
            return
        
        if self.state == _IDLE:
            Domoticz.Debug("starting discovery")
            mgmt_start_discovery(self.btsock)
            Domoticz.Debug("discovery started")
            self.state = _DISCOVERY_STARTED
            Domoticz.Heartbeat(1)

        inputs = [self.btsock]
        outputs = []          
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 0.1)
        for s in readable:
            if s is self.btsock:
                event, data = mgmt_get_event(self.btsock)
                Domoticz.Debug("Event %d" % event)

                if self.state == _DISCOVERY_STARTED:
                    if event == MGMT_EV_CMD_STATUS:
                        cmd_status = mgmt_ev_cmd_status(data)
                        if cmd_status.status != MGMT_STATUS_SUCCESS:
                            if cmd_status.status == MGMT_STATUS_PERMISSION_DENIED:
                                Domoticz.Log("Access denied starting discovery")
                            else:
                                Domoticz.Log("Start discovery faile %.2X") % cmd_status.status
                            self.state = _IDLE

                    elif event == MGMT_EV_CMD_COMPLETE:
                        Domoticz.Debug("Command complete")
                        
                    elif event == MGMT_EV_DISCOVERING:
                        Domoticz.Debug("Discovering...")
                        self.state = _DISCOVERING

                    else:
                        Domoticz.Log("Unexpected event %d in discovery_started stated" % event)

                elif self.state == _DISCOVERING:
                    if event == MGMT_EV_DEVICE_FOUND:
                        device = mgmt_ev_device_found(data)
                        mfg_data = device.get_manufacturer_data()
                        tempo_data = self.get_tempo_data(mfg_data)
                        if tempo_data and tempo_data.temp:
                            device_id = device.get_address()
                            Domoticz.Debug("Address: %s; Name: %s; Flags: %X" % (device_id, device.get_name()[0], device.flags))
                            if device_id not in self.Units:
                                self.addTempoDevice(device)
                            self.updateTempoDevice(device, tempo_data)
                            Domoticz.Debug("Temperature: %.1f" % tempo_data.temp)
                    elif event == MGMT_EV_DISCOVERING:
                        Domoticz.Debug("Discovery complete")
                        self.state = _IDLE
                    else:
                        Domoticz.Log("unexpected event %d in discovering state" % event)
                    
        if self.state == _IDLE:
            self.WaitCount = self.UpdateInterval / 20
            Domoticz.Heartbeat(20)
            
            


            
            


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device DeviceID: '" + str(Devices[x].DeviceID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
            
    return

