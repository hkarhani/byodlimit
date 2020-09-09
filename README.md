# Enforcing BYOD devices Limit per User

fastAPI Service to help in limiting BYOD devices count per User on Forescout Platform.

## 1. Preparing the Docker image

Either by building it locally on your Docker host:
`git clone https://github.com/hkarhani/byodlimit.git`

and then build it within the downloaded folder 'byodlimit':
`docker build -t byodlimit .`

or simply pull the auto-built image:
`docker pull hkarhani/byodlimit`

## 2. Run the Docker image

This image will have both Jupyter Notebook (exposed port 8888) and fastAPI (exposed port 5000) running.

If you pulled the auto-built image you can run the container by executing the following command:
`docker run -itd -p 8888:8888 -p 5000:5000 hkarhani/byodlimit`

otherwise, you can run your custom built image:

`docker run -itd -p 8888:8888 -p 5000:5000 byodlimit`

If you want to run the container without Jupyter Notebook Interface permantenly (with restart always) on your docker host after making the changes to your settings: 

`docker run -itd -p 5000:5000 --restart always byodlimit uvicorn main:app --host 0.0.0.0 --port 5000 --reload`

## 3. Edit the fsconfig.yml file

In order for pyFS library to properly POST DEX attributes to Forescout platform, please ensure you edit the fsconfig.yml with the IP and credentials of your Forescout Platform running OIM. Provide both web-api (not used in this code) / DEX (used to update the guest_tag DEX attribute). Please note that username for DEX needs to be in format: name@username as per CounterACT Web Service Accounts configuration.

Please edit main.py to change:
- maxDevicesPerUser = 2 # default it is 2 concurrent BYOD devices.
- API_KEY = "1234567asdfgh" # Please change the API Key

You can change other API_KEY_NAME or COOKIE_DOMAIN parameters while reflecting those changes in your DEX POST Web Service Request.

## 4. Run the fastAPI web-service on the container

Use the following command to run the fastAPI service. You can either execute it against the container in CLI from your docker host by using `docker exec ..` or easier to use the Jupyter Notebook at: `http://<docker-host-ip>:8888` => New Terminal.

`uvicorn main:app --host 0.0.0.0 --port 5000 --reload`

You will be able to monitor the fastAPI service from the command output.

If you want to run the container without Jupyter Notebook Interface permantenly (with restart always) on your docker host after making the changes to your settings: 

`docker run -itd -p 5000:5000 --restart always byodlimit uvicorn main:app --host 0.0.0.0 --port 5000 --reload`

## P.S. Security Note:

Please use this script in controlled Environment.

Security features are disabled for Jupyter Notebook (anyone with IP reachability to docker host port 8888 will be able to browse the Notebook / scripts - to simplify config editing). You can either modify the Jupyter Notebook settings file or stop sharing the port 8888. 


fastAPI (default port 5000) is implementing http only and I just updated the code the accept API Key either via: 
- URL Query: /apipost/?access_token=api-key
- or Authentication Headers - by adding header: access_token:api-key 
- or Cookie (COOKIE_DOMAIN: access_token:api-key)


