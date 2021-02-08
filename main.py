from fastapi import Security, Depends, FastAPI, HTTPException
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, JSONResponse

from pydantic import BaseModel
import uvicorn

from pyFS import pyFS

import logging
import warnings
warnings.simplefilter('ignore')
logging.basicConfig(level=logging.INFO)

# Max Devices Per User - can be updated.     
maxDevicesPerUser = 2

# Main Users Object to track logged-in Devices per user
Users = {}

# API Key Settings
API_KEY = "1234567asdfgh" # Please Change the API Key before running
API_KEY_NAME = "access_token"
COOKIE_DOMAIN = "byodlimit.fs"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):

    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    elif api_key_cookie == API_KEY:
        return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
        
# app: Main FastAPI Object to be used
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# fsApp: pyFS Object to POST DEX Property to the Platform 
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
    return {"message": "Welcome to Devices per User Count Enforcement."}

@app.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie(API_KEY_NAME, domain=COOKIE_DOMAIN)
    return response

@app.get("/openapi.json", tags=["documentation"])
async def get_open_api_endpoint(api_key: APIKey = Depends(get_api_key)):
    response = JSONResponse(
        get_openapi(title="FastAPI security test", version=1, routes=app.routes)
    )
    return response

@app.get("/documentation", tags=["documentation"])
async def get_documentation(api_key: APIKey = Depends(get_api_key)):
    response = get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
    response.set_cookie(
        API_KEY_NAME,
        value=api_key,
        domain=COOKIE_DOMAIN,
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    return response

@app.get("/test")
async def get_open_api_endpoint(api_key: APIKey = Depends(get_api_key)):
    response = "Authentication Test is successful!"
    return response

@app.get("/users")
async def get_users(api_key: APIKey = Depends(get_api_key)):
    return Users

@app.get("/maxdevices")
async def max_devices(api_key: APIKey = Depends(get_api_key)):
    return {"maxDevicesPerUser":maxDevicesPerUser} 

@app.post("/apipost/")
async def create_logEvent(_logevent: logEvent, api_key: APIKey = Depends(get_api_key)):
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
                         
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
