import os
import json as jsond
import time
import platform
import subprocess
import requests

try:
    if os.name == 'nt':
        import win32security
except ModuleNotFoundError:
    pass

class api:
    name = ownerid = version = hash_to_check = ""
    sessionid = enckey = ""
    initialized = False

    def __init__(self, name, ownerid, version, hash_to_check):
        self.name = name
        self.ownerid = ownerid
        self.version = version
        self.hash_to_check = hash_to_check
        self.init()

    def init(self):
        if self.sessionid != "":
            os._exit(1)
        post_data = {
            "type": "init",
            "ver": self.version,
            "hash": self.hash_to_check,
            "name": self.name,
            "ownerid": self.ownerid
        }
        response = self.__do_request(post_data)
        if response == "KeyAuth_Invalid":
            os._exit(1)
        json = jsond.loads(response)
        if json["message"] == "invalidver":
            if json["download"] != "":
                os.system(f"start {json['download']}")
                time.sleep(3)
                os._exit(1)
            else:
                time.sleep(3)
                os._exit(1)
        if not json["success"]:
            time.sleep(3)
            os._exit(1)
        self.sessionid = json["sessionid"]
        self.initialized = True

    def register(self, user, password, license, hwid=None):
        self.checkinit()
        if hwid is None:
            hwid = others.get_hwid()
        post_data = {
            "type": "register",
            "username": user,
            "pass": password,
            "key": license,
            "hwid": hwid,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        json = jsond.loads(self.__do_request(post_data))
        if json["success"]:
            self.__load_user_data(json["info"])
        else:
            os._exit(1)

    def login(self, user, password, code=None, hwid=None):
        self.checkinit()
        if hwid is None:
            hwid = others.get_hwid()
        post_data = {
            "type": "login",
            "username": user,
            "pass": password,
            "hwid": hwid,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid,
        }
        if code is not None:
            post_data["code"] = code
        json = jsond.loads(self.__do_request(post_data))
        if json["success"]:
            self.__load_user_data(json["info"])
            return True
        else:
            return False

    def license(self, key, code=None, hwid=None):
        self.checkinit()
        if hwid is None:
            hwid = others.get_hwid()
        post_data = {
            "type": "license",
            "key": key,
            "hwid": hwid,
            "sessionid": self.sessionid,
            "name": self.name,
            "ownerid": self.ownerid
        }
        if code is not None:
            post_data["code"] = code
        json = jsond.loads(self.__do_request(post_data))
        if json["success"]:
            self.__load_user_data(json["info"])
            return True
        else:
            return False

    def checkinit(self):
        if not self.initialized:
            os._exit(1)

    class application_data_class:
        numUsers = numKeys = app_ver = customer_panel = onlineUsers = ""

    class user_data_class:
        username = ip = hwid = expires = createdate = lastlogin = subscription = subscriptions = ""

    user_data = user_data_class()
    app_data = application_data_class()

    def __load_user_data(self, data):
        self.user_data.username = data["username"]
        self.user_data.ip = data["ip"]
        self.user_data.hwid = data["hwid"] or "N/A"
        self.user_data.expires = data["subscriptions"][0]["expiry"]
        self.user_data.createdate = data["createdate"]
        self.user_data.lastlogin = data["lastlogin"]
        self.user_data.subscription = data["subscriptions"][0]["subscription"]
        self.user_data.subscriptions = data["subscriptions"]

    def __do_request(self, post_data):
        response = requests.post("https://keyauth.win/api/1.3/", data=post_data, timeout=10)
        return response.text

class others:
    @staticmethod
    def get_hwid():
        if platform.system() == "Linux":
            with open("/etc/machine-id") as f:
                return f.read()
        elif platform.system() == 'Windows':
            winuser = os.getlogin()
            sid = win32security.LookupAccountName(None, winuser)[0]
            return win32security.ConvertSidToStringSid(sid)
        elif platform.system() == 'Darwin':
            output = subprocess.Popen("ioreg -l | grep IOPlatformSerialNumber", stdout=subprocess.PIPE, shell=True).communicate()[0]
            serial = output.decode().split('=', 1)[1].replace(' ', '')
            return serial[1:-2]
