"""
<plugin key="Wiser" name="Drayton Wiser" author="bluebook" version="1.0.0" externallink="https://wiser.draytoncontrols.co.uk/" wikilink="https://github.com/bloob00k/domoticz/wiki">
    <description>
        <h2>Drayton Wiser Plugin</h2><br/>
        For each room you have configured in your system, up to three devices will be created by the plugin:
        <ul style="list-style-type:square">
            <li>Temperature or temperature and humidity</li>
            <li>Thermostat (set-point for the room)</li>
            <li>Demand</li>
        </ul>
        <p>
        These are explained in more detail below.  Note that the plug-in does not create a device per iTRV.  If you only have a single iTRV in a room then
        it's a moot point, but if you have more than one then you will still only see one device of each of the above types per room; in that case the room-level
        device represents the aggregate of the individual devices - just as it does in the app.</p>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Temperature and Humidity - Shows temperature and humidity reported by a smart room thermostat</li>
            <li>Temperature - Shows the temperature in a room calculated from its radiator thermostat(s)</li>
            <li>Thermostat - Reports the current set point for the room, and allows it to be overridden temporarily (until next scheduled event)</li>
            <li>Hot Water - Show and control on/off state of the Hot Water circuit (conventional boiler only)</li>
            <li>Heating Channel - Read-only.  Reports current state of the heating relay for the channel.  If it's on, then the control unit is asking the boiler to provide
                heat to this circuit.  As a minimum that should mean that the pump is circulating water through this heating circuit.  Whether or not the
                boiler is actually on is a function of how hot the water is in the circuit, and if there are any other demands on the boiler.</li>
            <li>Demand - Reports the heating demand in the room (percentage)</li>
            <li>SmartPlug - Show and control on/off state of a smart plug</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
       <param field="Address" label="IP Address" required="true" />
       <param field="Mode1" label="HeatHub Secret" width="600px" required="true"/>
       <param field="Mode2" label="Update Frequency (seconds)" default="60" required="false"/>
       <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Python" value="18"/>
                <option label="Connections+Queue" value="146"/>
                <option label="All" value="-1"/>
            </options>
      </param>
    </params>
</plugin>
"""


'''
Wiser API info

https://github.com/chrisduffer/drayton-wiser/blob/master/smartapps/chrisduffer/drayton-wiser-connect.src/drayton-wiser-connect.groovy
https://github.com/RobPope/DraytonWiser/blob/master/src/main/java/org/openhab/binding/draytonwiser/internal/connection/DraytonWiserConnection.java


'''





import Domoticz
import json

class BasePlugin:
    enabled = False
    def __init__(self):
        #self.var = 123
        self.UpdateInterval = 60
        self.WaitCount = self.UpdateInterval / 10
        self.Units = {}
        self.Commands = []
        self.CmdState = 'Disconnected'
        return

    def getNextUnit(self):
        for id in range(1, 255):
            if id not in Devices:
                return id

        return None


    def addDevices(self, info):
        DevID = 'systemAway'
        if DevID not in self.Units:
            unit = self.getNextUnit()
            Domoticz.Device(Name = 'Away Mode',  Unit = unit, DeviceID = DevID, TypeName = 'Switch', Subtype = 0, Image = 9).Create()
            self.Units[DevID] = unit
            Domoticz.Log("Created device " + 'Away Mode')


        for r in info['Room']:
            # For rooms, thermostat device id = room['id']
            DevID = r['id']
            if str(DevID) not in self.Units:
                if 'RoomStatId' in r:
                    typeName = 'Temp+Hum'
                else:
                    typeName = 'Temperature'

                unit = self.getNextUnit()
                Domoticz.Device(Name=r['Name'],  Unit=unit, DeviceID = str(DevID), TypeName=typeName).Create()
                self.Units[str(DevID)] = unit
                Domoticz.Log("Created device " + r['Name'])

                DevID = 256 + r['id']
                unit = self.getNextUnit()
                Domoticz.Device(Name=r['Name'],  Unit=unit, DeviceID = str(DevID), Type=242, Subtype=1).Create()
                self.Units[str(DevID)] = unit
                Domoticz.Log("Created device " + r['Name'] + ' thermostat')

                DevID = 4096 + r['id']
                if str(DevID) not in self.Units:
                    unit = self.getNextUnit()
                    Domoticz.Device(Name=r['Name'] + ' Demand',  Unit=unit, DeviceID = str(DevID), Type=243, Subtype=6).Create()
                    self.Units[str(DevID)] = unit
                    Domoticz.Log("Created device " + r['Name'] + ' Demand')

        if 'HotWater' in info:
            for h in info['HotWater']:
                DevID = 512 + h['id']
                if str(DevID) not in self.Units:
                    # All images available by JSON API call "/json.htm?type=custom_light_icons"
                    unit = self.getNextUnit()
                    Domoticz.Device(Name='Hot Water', Unit=unit, DeviceID = str(DevID), TypeName = "Switch", Subtype = 0, Image = 11).Create()
                    self.Units[str(DevID)] = unit
                    Domoticz.Log("Created device Hot Water")

        if 'SmartPlug' in info:
            for p in info['SmartPlug']:
                DevID = 1024 + p['id']
                if str(DevID) not in self.Units:
                    # All images available by JSON API call "/json.htm?type=custom_light_icons"
                    unit = self.getNextUnit()
                    Domoticz.Device(Name=p['Name'], Unit=unit, DeviceID = str(DevID), TypeName = "Switch", Subtype = 0, Image = 1).Create()
                    self.Units[str(DevID)] = unit
                    Domoticz.Log("Created device " + p['Name'])

        if 'HeatingChannel' in info:
            for b in info['HeatingChannel']:
                DevID = 2048 + b['id']
                if str(DevID) not in self.Units:
                    # All images available by JSON API call "/json.htm?type=custom_light_icons"
                    unit = self.getNextUnit()
                    Domoticz.Device(Name=b['Name'], Unit=unit, DeviceID = str(DevID), TypeName = "Switch", Subtype = 0, Image = 15).Create()
                    self.Units[str(DevID)] = unit
                    Domoticz.Log("Created device " + b['Name'])

    def updateRoom(self, Room, RoomStats):
        sValue = ""

        Unit = self.Units[ str(0 + Room['id']) ]

        # Temp + Hum
        if Devices[Unit].Type == 82:
            if 'RoomStatId' not in Room:
                Domoticz.Log("Device %d typ is Temp+Hum but not associated with Wiser RoomStat" % Devices[Unit].ID)
                return

            for stat in RoomStats:
                if Room['RoomStatId'] == stat['id']:
                    if 'MeasuredHumidity' in stat:
                        humidity = stat['MeasuredHumidity']
                        sValue = "%.1f;%d;0" % (Room['CalculatedTemperature'] * 0.1, humidity)
                    else:
                        sValue = "%.1f" % (Room['CalculatedTemperature'] * 0.1)
                    break
        else:
            sValue = "%.1f" % (Room['CalculatedTemperature'] * 0.1)

        # If stat is unreachable we get -32768, ignore
        if Room['CalculatedTemperature'] > 0:
            Devices[Unit].Update(nValue=0, sValue=sValue, TimedOut = 0)

        # Now the thermostat
        sValue = "%.1f" % (Room['CurrentSetPoint'] * 0.1)
        Unit = self.Units[ str(256 + Room['id']) ]
        Devices[Unit].Update(nValue=0, sValue=sValue, TimedOut=0)

        if 'PercentageDemand' in Room:
            sValue = "%s" % Room['PercentageDemand']
            Unit = self.Units[ str(4096 + Room['id']) ]
            Devices[Unit].Update(nValue=0, sValue=sValue, TimedOut=0)





    def updateHotWater(self, WaterInfo):
        Unit = self.Units[ str(512 + WaterInfo['id']) ]

        if WaterInfo['WaterHeatingState'] == "On":
            nValue = 1
        elif WaterInfo['WaterHeatingState'] == "Off":
            nValue = 0
        else:
            Domoticz.Log("WaterHeatingState '%s' for device %d is unrecognised, skipping device." % (WaterInfo['WaterHeatingState'], Devices[Unit].ID))
            return

        if Devices[Unit].nValue != nValue:
            Devices[Unit].Update(nValue=nValue, sValue='', TimedOut=0)
        else:
            Devices[Unit].Touch()


    def updateSmartPlug(self, Plug):
        Unit = self.Units[ str(1024 + Plug['id']) ]

        if Plug['OutputState'] == "On":
            nValue = 1
        elif Plug['OutputState'] == "Off":
            nValue = 0
        else:
            Domoticz.Log("SmartPlug state '%s' for device %d is unrecognised, skipping device." % (Plug['OutputState'], Devices[Unit].ID))
            return

        if Devices[Unit].nValue != nValue:
            Devices[Unit].Update(nValue=nValue, sValue='', TimedOut=0)
        else:
            Devices[Unit].Touch()

    def updateBoiler(self, Boiler):
        Unit = self.Units[ str(2048 + Boiler['id']) ]

        if Boiler['HeatingRelayState'] == "On":
            nValue = 1
        elif Boiler['HeatingRelayState'] == "Off":
            nValue = 0
        else:
            Domoticz.Log("HeatingChannel state '%s' for device %d is unrecognised, skipping device." % (Boiler['OutputState'], Devices[Unit].ID))
            return

        if Devices[Unit].nValue != nValue:
            Devices[Unit].Update(nValue=nValue, sValue='', TimedOut=0)
        else:
            Devices[Unit].Touch()

    def updateSystem(self, System):
        if 'OverrideType' in System and System['OverrideType'] == 'Away':
            nValue = 1
        else:
            nValue = 0

        Unit = self.Units['systemAway']

        if Devices[Unit].nValue != nValue:
            Devices[Unit].Update(nValue=nValue, sValue='', TimedOut=0)
        else:
            Devices[Unit].Touch()


    def updateDevices(self, info):
        self.updateSystem(info['System'])

        if 'Room' in info:
            for r in info['Room']:
                self.updateRoom(r, info['RoomStat'])

        if 'HotWater' in info:
            for h in info['HotWater']:
                self.updateHotWater(h)

        if 'SmartPlug' in info:
            for s in info['SmartPlug']:
                self.updateSmartPlug(s)

        if 'HeatingChannel' in info:
            for b in info['HeatingChannel']:
                self.updateBoiler(b)

    def apiPatch(self, Connection, path, data):
        try:
            sendData = { 'Verb' : 'PATCH',
                         'URL'  : '/data/domain/' + path,
                         'Headers' : { 'SECRET': Parameters["Mode1"], "Accept": '*/*', 'Content-Length' : "%d"%(len(data)) },
                         'Data' : data
                }

            Connection.Send(sendData)

        except Exception as e:
            Domoticz.Log("PATCH failed " + str(e))

    def apiPatch2(self, Connection, path, data):
        try:
            sendData = { 'Verb' : 'PATCH',
                         'URL'  : '/data/v2/domain/' + path,
                         'Headers' : { 'SECRET': Parameters["Mode1"], "Accept": '*/*', 'Content-Length' : "%d"%(len(data)) },
                         'Data' : data
                }

            Connection.Send(sendData)

        except Exception as e:
            Domoticz.Log("PATCH failed")

    def overrideSetpoint(self, Connection, Room, Temperature):
        payload = {
            "RequestOverride": { "Type": "Manual",  "SetPoint": + int(Temperature * 10) }
        }

        path = 'Room/' + str(Room)

        Domoticz.Debug("Payload: " + json.dumps(payload))

        self.apiPatch(Connection, path, json.dumps(payload))


    def switchHotWater(self, Connection, HotWater, SwitchOn):
        payload = {
            "Type": "Manual",  "SetPoint": + int(1100 if SwitchOn else -200)
        }

        path = 'HotWater/' + str(HotWater) + '/RequestOverride/'

        Domoticz.Debug("Payload: " + json.dumps(payload))

        self.apiPatch(Connection, path, json.dumps(payload))


    def switchSmartPlug(self, Connection, SmartPlug, SwitchOn):
        payload = {
            "RequestOutput": 'On' if SwitchOn else 'Off'
        }

        path = 'SmartPlug/' + str(SmartPlug) + '/'

        Domoticz.Debug("Payload: " + json.dumps(payload))

        self.apiPatch2(Connection, path, json.dumps(payload))


    def switchAway(self, Connection, SwitchOn):
        payload = {
            "Type": 'Away' if SwitchOn else 'None'
        }

        path = 'System/RequestOverride'

        Domoticz.Debug("Payload: " + json.dumps(payload))

        self.apiPatch2(Connection, path, json.dumps(payload))

    def doCommand(self, Connection, Command, Unit, Level):
        Domoticz.Debug("doCommand: " + Connection.Name)
        Domoticz.Debug("Command " + Command)

        DeviceID = Devices[Unit].DeviceID

        # This is a bit ugly.  If I had my time again...
        if DeviceID.isdigit():
            DeviceID = int(DeviceID)

            if DeviceID < 256:
                Room = DeviceID
            elif DeviceID < 512:
                Thermostat = DeviceID - 256
                Domoticz.Debug('"%s" on thermostat ID %d to %.1f' % (Command, Thermostat, Level))
                self.overrideSetpoint(Connection, Thermostat, Level)
            elif DeviceID < 1024:
                HotWaterSystem = DeviceID - 512
                Domoticz.Debug('"%s" on hot water ID %d' % (Command, HotWaterSystem))
                self.switchHotWater(Connection, HotWaterSystem, Command.upper() == 'ON')
            elif DeviceID < 2048:
                SmartPlug = DeviceID - 1024
                Domoticz.Debug('"%s" on smart plug ID %d' % (Command, SmartPlug))
                self.switchSmartPlug(Connection, SmartPlug, Command.upper() == 'ON')
        elif DeviceID == 'systemAway':
            Domoticz.Debug('"%s" on Away mode' % (Command))
            self.switchAway(Connection, Command.upper() == 'ON')
        else:
            Domoticz.Error('Command for unrecognised Device ID "%s", unit "%d"' % (DeviceID, Unit))

        # Force status update ASAP, to reflect any changes we have just made.
        self.WaitCount = 0

    def doCommands(self, Connection, Commands):
        Domoticz.Debug("doCommands")
        while len(Commands) > 0:
            c = Commands.pop(0)
            self.doCommand(Connection, c['Command'], c['Unit'], c['Level'])



    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
            
        if 'Mode2' in Parameters:
            updateInterval = Parameters['Mode2']
            if updateInterval != '':
                if not updateInterval.isdigit():
                    Domoticz.Error("Update interval parameter must be an integer - ignored '%s'" % updateInterval)
                else:
                    updateInterval = int(updateInterval)
                    if updateInterval < 10:
                        Domoticz.Error("Minimum update interval is 10 seconds")
                        updateInterval = 10
                    self.UpdateInterval = updateInterval

        for d in Devices:
            self.Units[Devices[d].DeviceID] = d
            
        self.httpConn = Domoticz.Connection(Name="Wiser", Transport="TCP/IP", Protocol="HTTP", Address=Parameters["Address"], Port="80")
        self.httpCmdConn = Domoticz.Connection(Name="WiserCmd", Transport="TCP/IP", Protocol="HTTP", Address=Parameters["Address"], Port="80")
        self.httpConn.Connect()

        Domoticz.Debug("onStart called")

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")
        if (Status == 0):
            Domoticz.Debug("Wiser connected successfully "+ Connection.Name)
            if not Connection.Connected():
                Domoticz.Log("onConnect but not connected "+ Connection.Name)

            if Connection.Name == 'Wiser':  # Regular status poll
                sendData = { 'Verb' : 'GET',
                             'URL'  : '/data/domain/',
                             'Headers' : { 'SECRET': Parameters["Mode1"] }
                }
                Connection.Send(sendData)
            else:
                self.CmdState = 'Connected'
                c = self.Commands.pop(0)
                self.doCommand(Connection, c['Command'], c['Unit'], c['Level'])
#                self.doCommands(Connection, self.Commands)

        else:
            Domoticz.Log("Failed to connect " + Connection.Name + " (error " + str(Status) +") to: " + Parameters["Address"] + " with error: " + Description)
            

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called")
        # Keys: Headers, Status, Data

        # DumpHTTPResponseToLog(Data)
        
        Status = int(Data["Status"])

        if Status != 200:
            Domoticz.Log("Wiser query failed %d" % Status)
        else:
            Domoticz.Debug("Data length: " + str(len(Data['Data'])))
            strData = Data["Data"].decode("utf-8", "ignore")
            wiser_info = json.loads(strData)
            if Connection.Name == "Wiser":
                self.addDevices(wiser_info)
                self.updateDevices(wiser_info)
            else:
                Domoticz.Debug(strData)

            if Connection.Connected():
                Connection.Disconnect()
        
    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        # onCommand called for Unit 4: Parameter 'On', Level: 0
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        params = params.capitalize()
        Domoticz.Log("Action " + action + ", params: " + params)

        self.Commands.append({
            'Command': Command,
            'Level': Level,
            'Unit': Unit
        })

        if self.httpCmdConn.Connected():
            Domoticz.Debug("Command Connection connected already")
            self.doCommands(self.httpCmdConn, self.Commands)
        elif self.httpCmdConn.Connecting():
            Domoticz.Debug("Connection in progress")
        elif self.CmdState != 'Connecting'and self.CmdState != 'Connected':
            self.CmdState = 'Connecting'
            self.httpCmdConn.Connect()


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called for " + Connection.Name)
        if Connection.Name == 'WiserCmd':
            self.CmdState = 'Disconnected'
            if len(self.Commands) > 0:
                Connection.Connect()

    def onHeartbeat(self):
        self.WaitCount -= 1

        if (self.WaitCount <= 0):
            self.WaitCount = self.UpdateInterval / 10
            if self.httpConn.Connected():
                Domoticz.Debug("onHeartBeat: httpConn is already connected; sending request")
                sendData = { 'Verb' : 'GET',
                             'URL'  : '/data/domain/',
                             'Headers' : { 'SECRET': Parameters["Mode1"] }
                }
                self.httpConn.Send(sendData)
            else:
                self.httpConn.Connect()
            


            
            


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

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")
