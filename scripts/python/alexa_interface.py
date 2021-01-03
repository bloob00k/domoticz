#
# Derived from Amazon Alexa Remote Control by alex(at)loetzimmer.de
# See https://github.com/thorsten-gehrig/alexa-remote-control
#


import sys

from html.parser import HTMLParser
import requests
import json
import os.path
from http.cookiejar import LWPCookieJar

BROWSER='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:1.0) bash-script/1.0'
TTS_LOCALE='en-GB'
DEFAULT_NORMAL_VOL = 10 # This is the volume we will reset to after speaking if we can't detect the current volume


formfields = {}
targeturl = None

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global targeturl
        
        if tag == 'input':
            if ('type', 'hidden') in attrs:
                name = ''
                value = ''
                
                for attr in attrs:
                    if attr[0] == 'name':
                       name = attr[1]
                    elif attr[0] == 'value':
                        value = attr[1]

                if name != '':
                    formfields.update({name: value})

        if tag == 'form':
            url = ''
            found = False
            
            for attr in attrs:
                if attr[0] == 'action':
                    url = attr[1]
                if attr[0] == 'name' and attr[1] == 'signIn':
                    found = True
            if found and url != '':
                targeturl = url

def cookie_in(name, jar):
    for cookie in jar:
        if cookie.name == name:
            return True

    return False

def get_cookie_value(name, jar):
    for cookie in jar:
        if cookie.name == name:
            return cookie.value

    return ''


def get_volume(device):
    vol = None
    
    r = session.get("https://alexa.amazon.co.uk/api/media/state?deviceSerialNumber=%s&deviceType=%s" % (device['serialNumber'], device['deviceType']))
    
    if r.status_code == 200:
        device_state = r.json()
        if 'volume' in device_state:
            vol = device_state['volume']

    return vol


def speak(device, phrase, volume):

    if device is None or isinstance(device, str):
        device = get_device(device)
    
    if device is None:
        print("Device not found")
        return None
    
    MEDIAOWNERCUSTOMERID = device['deviceOwnerCustomerId']

    current_volume = get_volume(device)
    if current_volume is None:
        normal_volume = current_volume
    else:
        normal_volume = DEFAULT_NORMAL_VOL
    
    cmdsequence = {
            "@type": "com.amazon.alexa.behaviors.model.Sequence",
            "startNode": {
                "@type": "com.amazon.alexa.behaviors.model.SerialNode",
                "nodesToExecute":[
                    {
                        "@type": "com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode",
                        "type": "Alexa.DeviceControls.Volume",
                        "operationPayload": {
                            "deviceType": device['deviceType'],
                            "deviceSerialNumber": device['serialNumber'],
                            "customerId": MEDIAOWNERCUSTOMERID,
                            "locale": TTS_LOCALE,
                            "value": volume
                        }
                    },
                    {
                        "@type": "com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode",
                        "type": "Alexa.Speak",
                        "operationPayload":
                        {
                            "deviceType": device['deviceType'],
                            "deviceSerialNumber": device['serialNumber'],
                            "customerId": MEDIAOWNERCUSTOMERID,
                            "locale": TTS_LOCALE,
                            "textToSpeak": phrase.replace('"', ' ').replace('\\', ' ')
                        }
                    },
                    {
                        "@type": "com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode",
                        "type": "Alexa.DeviceControls.Volume",
                        "operationPayload":
                        {
                            "deviceType": device['deviceType'],
                            "deviceSerialNumber": device['serialNumber'],
                            "customerId": MEDIAOWNERCUSTOMERID,
                            "locale": TTS_LOCALE,
                            "value": current_volume
                        }
                    }
                ]
            }
        }

    alexacmd = {
        "behaviorId":"PREVIEW",
        "sequenceJson": json.dumps(cmdsequence),
        "status":"ENABLED"
    }

    r = session.post("https://alexa.amazon.co.uk/api/behaviors/preview", data = json.dumps(alexacmd))



def play(device, stationid):
    url = "https://alexa.amazon.co.uk/api/tunein/queue-and-play?deviceSerialNumber=%s&deviceType=%s&guideId=%s&contentType=station&callSign=&mediaOwnerCustomerId=%s" % (device['serialNumber'], device['deviceType'], stationid, device['deviceOwnerCustomerId'])

    print(url)
    r = session.post(url)



def check_auth_status():
    r = session.get("https://alexa.amazon.co.uk/api/bootstrap", allow_redirects=False)

    if r.status_code == 200:
        try:
            auth = r.json()
            if 'authentication' in auth and 'authenticated' in auth['authentication']:
                return auth['authentication']['authenticated']
        except ValueError:
            pass

    return False


def login(username, password):
    r = session.get("https://alexa.amazon.co.uk")

    parser = MyHTMLParser()
    parser.feed(r.text)

    print
    print

    formfields.update({'password': password, 'email': username })
    '''
    for k, v in formfields.items():
        print k, ': ', v

    print "TARGET: ", targeturl
    '''

    if targeturl != None:
        login_response = session.post(targeturl, data=formfields)

    #print login_response.text


def get_persistent_login(username, password):
    global session
    session = requests.Session()
    session.headers.update( { 'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'User-Agent' : BROWSER } )

    cj = LWPCookieJar('cookies.txt')
    if os.path.isfile('cookies.txt'):
        cj.load()
    session.cookies = cj

    logged_in = check_auth_status()

    if not logged_in:
        login(username, password)
        if not check_auth_status():
            print("Login failed")
            return False

    have_csrf = cookie_in('csrf', session.cookies)
    if not have_csrf:
        r = session.get('https://alexa.amazon.co.uk/api/language')
        have_csrf = cookie_in('csrf', session.cookies)

    if not have_csrf:
        r = session.get('https://alexa.amazon.co.uk/templates/oobe/d-device-pick.handlebars')
        have_csrf = cookie_in('csrf', session.cookies)

    if not have_csrf:
        print('No CSRF cookie, cannot continue')
        return False

    session.headers.update({'csrf' : get_cookie_value('csrf', session.cookies)})

    cj.save()

    return True


def get_device(device_name):
    global session

    r = session.get("https://alexa.amazon.co.uk/api/devices-v2/device?cached=false")

#    print 'Devices ', r

    devices = r.json()['devices']

    dev = None
    
    if device_name:
        for device in devices:
#            print device['accountName']
            if 'accountName' in device and device['accountName'] == device_name:
                dev = device
                break
    elif len(devices) > 0:
        dev = devices[0]

    return dev


def setup_alexa(username, password, device_name):
    if not get_persistent_login(username, password):
        return None

    return get_device(device_name)


def init():
    global session
    session = requests.Session()
    session.headers.update( { 'DNT': '1', 'Upgrade-Insecure-Requests': '1', 'User-Agent' : BROWSER } )

    cj = LWPCookieJar('cookies.txt')
    if os.path.isfile('cookies.txt'):
        cj.load()
    session.cookies = cj

    if check_auth_status() and cookie_in('csrf', session.cookies):
        session.headers.update({'csrf' : get_cookie_value('csrf', session.cookies)})
        return True

    return False
