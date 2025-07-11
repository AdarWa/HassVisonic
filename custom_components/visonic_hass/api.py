from .const import DOMAIN
import requests as re
from .device import Device
import logging
import time
import asyncio
from retrying import retry # type: ignore

class API:
    entities = []
    continue_func = None
    
    def __init__(self, hostname):
        global tries
        tries = 0
        self.logger = logging.getLogger(DOMAIN)
        self.hostname = hostname
        self.secrets = {
            "email": None,
            "password": None,
            "app_id": None,
            "user_code": None,
            "panel_serial": None,
        }
        try:
            self.s = re.Session()
            adapter = re.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
            self.s.mount('https://', adapter)
            self.s.headers.update({'Content-Type': 'application/json'})  
        except Exception as e:
            self.logger.fatal("Exception occured while initializing the REST API: " + str(e.message))
        self.devices = []
        
    async def initAsync(self):
        await asyncio.to_thread(self.fetchVersion)
        await self.fetchDevicesAsync()
        self.logger.fatal("Finished Connecting to Rest API!")
        
        
    def makeUrl(self,url):
        return "https://"+self.hostname+"/rest_api/"+self.version+"/"+url
        
    def fetchVersion(self):
        self.version = re.get('https://' + self.hostname + '/rest_api/version').json()["rest_versions"][0]

    def obtainUserToken(self):
        auth_info = {
                'email': self.secrets["email"],
                'password': self.secrets["password"],
                'app_id': self.secrets["app_id"],
            }
        res = self.s.post(self.makeUrl("auth"), json=auth_info)
        if res.status_code == 200:
            return res.json()['user_token']
        else:
            return None

    def obtainSession(self, token):
        auth_info = {
                "user_code": str(self.secrets["user_code"]),
                "app_type": "com.visonic.powermaxapp",
                "app_id": self.secrets["app_id"],
                "panel_serial": self.secrets["panel_serial"]
            }
        headers = {
            "User-Token": token
        }
        res = self.s.post(self.makeUrl("panel/login"), json=auth_info, headers=headers)
        if res.status_code == 200:
            return res.json()['session_token']
        else:
            return None

    def isConnected(self, token, session):
        headers = {
            "User-Token": token,
            "Session-Token": session
        }
        res = self.s.get(self.makeUrl("status"), headers=headers)
        if res.status_code == 200:
            return res.json()['connected']
        else:
            return False
        
    def obtainToken(self):
        """Obtain user and session token from the API."""
        try:
            user = self.obtainUserToken()
            if user is None:
                self.logger.fatal("Failed to obtain user token. Check your credentials.")
                return None, None
            session = self.obtainSession(user)
            if session is None:
                self.logger.fatal("Failed to obtain session token. Check your credentials and panel serial.")
                return None, None
            while not self.isConnected(user, session):
                time.sleep(1)
            self.logger.info("Successfully obtained user and session tokens.")
            return user, session
        except re.HTTPError as e:
            self.logger.fatal(type(e).__name__ + " HTTP Error while obtaining tokens. Error Message: " + str(e.message))
            return None, None
        except re.ConnectionError as e:
            self.logger.fatal(type(e).__name__ + " Connection Error while obtaining tokens. Error Message: " + str(e.message))
            return None, None
        except re.Timeout as e:
            self.logger.fatal(type(e).__name__ + " Timeout while obtaining tokens. Error Message: " + str(e.message))
            return None, None
        except re.RequestException as e:
            self.logger.fatal(type(e).__name__ + " Request Exception while obtaining tokens. Error Message: " + str(e.message))
            return None, None
        
    
    
    def auth(self):
        try:
            token = self.obtainToken()
            self.user_token = token[0]
            self.session_token = token[1]
            self.s.headers.update({'User-Token': self.user_token, 'Session-Token': self.session_token})
        except Exception as e:
            self.logger.fatal("Exception while trying to auth: " + str(e))
    
    @retry(stop_max_attempt_number=7, wait_fixed=500, retry_on_result=lambda r: r is None)
    def __send_get(self, name):
        try:
            global tries
            r = self.s.get(self.makeUrl(name))
            if r.status_code == 403 and tries < 5:
                tries+=1
                return self.auth()
            elif r.status_code != 200:
                self.logger.fatal("Exception while sending GET to " + self.makeUrl(name) + ". status code: " + str(r.status_code) + ". tries: " + str(tries))
                return None
            
            return r.json()
        except re.RequestException as e:
            self.logger.fatal(type(e).__name__ + " Request Exception while sending a GET request to "+ self.makeUrl(name) + ". Error Message: " + str(e))
        except Exception as e:
            self.logger.fatal("Abnormal Exception " + str(e))
    
    @retry(stop_max_attempt_number=7, wait_fixed=500, retry_on_result=lambda r: r is None)
    def __send_post(self, name, data):
        try:
            global tries
            r = self.s.post(self.makeUrl(name), json=data)
            if r.status_code == 403 and tries < 5:
                tries+=1
                return self.auth()
            elif r.status_code != 200:
                self.logger.fatal("Exception while sending POST to " + self.makeUrl(name) + ". status code: " + str(r.status_code) + ". tries: " + str(tries))
                return None
            
            return r.json()
        except re.RequestException as e:
            self.logger.fatal(type(e).__name__ + " Request Exception while sending a POST request to "+ self.makeUrl(name) + ". Error Message: " + str(e))
        except Exception as e:
            self.logger.fatal("Abnormal Exception " + str(e))
    
    def arm(self, state):
        self.__send_post("set_state",{'partition': -1, 'state': state})
    
    async def triggerAsync(self):
        await asyncio.to_thread(self.trigger)
        
    async def muteAsync(self):
        await asyncio.to_thread(self.mute)
    
    def trigger(self):
        self.__send_post("activate_siren",{})
    
    def mute(self):
        self.__send_post("disable_siren",{'mode': 'all'})
    
    
    async def fetchDevicesAsync(self):
        return await asyncio.to_thread(self.fetchDevices)
    
    def fetchDevices(self):
        try:
            resp = self.__send_get("devices")
            temp = []
            for device in resp:
                bypassed = False
                if "traits" in device.keys():
                    if "bypass" in device["traits"].keys():
                        bypassed = device["traits"]["bypass"]["enabled"]
                temp.append(Device(device["subtype"], device["name"], bypassed, device["warnings"], str(device["id"])))
                
            if len(temp) > 0:
                self.devices = temp
        except Exception as e:
            self.logger.fatal(type(e).__name__ + " occured while fetching devices. " + str(e.message))
            
    def fetchState(self) -> dict:
        try:
            resp = self.__send_get("status")
            if "partitions" in resp.keys():
                parts = resp["partitions"]
                if len(parts) > 0:
                    return {
                        "state": "EXIT" if parts[0]["status"] == "EXIT" else parts[0]["state"],
                        "ready": parts[0]["ready"]
                    }
        except Exception as e:
            self.logger.fatal(type(e).__name__ + "occured while fetching state of panel. " + str(e.message))
    
        