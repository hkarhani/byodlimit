from fastapi import FastAPI
from pydantic import BaseModel

from pyFS import pyFS

import logging
import warnings
warnings.simplefilter('ignore')
logging.basicConfig(level=logging.INFO)

# app: Main FastAPI Object to be used
app = FastAPI()

# fsApp: pyFS Object to POST DEX Property to Forescout Platform 
# by default Object will load fsconfig.yml file as input. 
fsApp = pyFS()

# logEvent: pydantic BaseModel Object - representing the expected POST JSON data to be received from Forescout Platform
class logEvent(BaseModel):
    action: str
    http_login_user: str
    access_ip: str
    nbthost: str
    mac: str
    authLogin: str

# Max Devices Per User - can be updated.     
maxDevicesPerUser = 2

# Main Users Object to track logged-in Devices per user
Users = {}

# Function to add new Device to User / newUser 
def addUserDev(Users, newUser, device, maxDevicesPerUser = 2):
    # if user not seen before create it and assign it the added device
    if newUser not in list(Users.keys()):
        Users[newUser] = [device]
        return None 
    else: 
        
        if len(Users[newUser]) < maxDevicesPerUser:
            # if maxDevicesPerUser not reached append new device to the User. 
            if device not in Users[newUser]:
                Users[newUser].append(device)
            return None 
        else: 
            # reaching maxDevicesPerUser - use FIFO. Could be changed to LIFO if required. 
            deviceToBeKicked = Users[newUser].pop(0)
            Users[newUser].append(device)
            # Returns the device IP to be kicked out - otherwise its None 
            return deviceToBeKicked

        
def delUserDev(Users, existingUser, device):
    if existingUser not in list(Users.keys()):
        print(f'Warning: User {existingUser} was not found!')
        return None 
    if device not in Users[existingUser]:
        print(f'Warning: device {device} was not found for user {existingUser}. Current devices are: {Users[existingUser]}')
        return None 
    Users[existingUser].pop(Users[existingUser].index(device))
    return device  

@app.get("/")
async def read_root():
    return {"message": "Welcome to Devices per User Count Enforcement using fastAPI!"}

@app.get("/users")
async def get_users():
    return Users

@app.get("/maxdevices")
async def max_devices():
    return {"maxDevicesPerUser":maxDevicesPerUser} 

@app.post("/apipost/")
async def create_logEvent(_logevent: logEvent):
    logDict = _logevent.dict()
    if logDict['action'] == 'Login':       
        ret = addUserDev(Users, logDict['http_login_user'], logDict['access_ip'])
        if not ret: 
            logging.info(f"User {logDict['http_login_user']} with {logDict['access_ip']} is added.")
        else: 
            logging.info(f"Device {ret} will be kicked out as {maxDevicesPerUser} devices are logged in for {logDict['http_login_user']}")
            fsApp.postDEX(ret, 'guest_tag', 'kickout', debug=False)
            
    elif logDict['action'] == 'LoggedOut': 
        ret = delUserDev(Users, logDict['http_login_user'], logDict['access_ip'])
        if ret: 
            user = logDict['http_login_user']
            logging.info(f'Device {ret} has logged out. {len(Users[user])} remaining devices are logged in: {Users[user]}')
    else: 
        logging.info(f"action is not recognized! Log event: {logDict}")
    return {"status":"ok"}