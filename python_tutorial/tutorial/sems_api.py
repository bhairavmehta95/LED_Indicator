import semsiot
import time 
import requests
import json

# Base URL as asssigned by SEMS
BASE_URL = "https://semsiotdev.3m.com/"

# Sends post requests to connect the device and update the status
def send_post(status_text):
	headers = { 'Content-Type' : 'application/json' }
	
	# Query parameters to Connect
	## CONNECT IS THE SAME THING AS REGISTER
	register_url = BASE_URL + '/api/Register'
	query_parameters_register  = {
		"serialNumber" : "123456123456",
		"applicationId": "823bd53b-ebd3-4432-bc8b-356a6b232b69",
		"apiKey": "5e036211500c4ae58c10e9d611d7b4d5ee2a2b951fa54",
		"deviceName": "led-indicator",
		"latitude" : 44.94,
		"longitude" : -93.09
	}
	
	# Posts a request with above parameters, we are looking for the two
	# Key values listed below
	
	response = requests.post(register_url , headers = headers, data = json.dumps(query_parameters_register) )	
	
	Authorization = response.json()['EventHubKey']
	event_hub_url = response.json()['EventHubUrl']

	# Authorizes connection
	headers.update( { 'Authorization' : Authorization } )
	
	query_parameters_post = {
		"serialNumber" : "123456123456",
		"applicationId": "823bd53b-ebd3-4432-bc8b-356a6b232b69",
		"apiKey": "5e036211500c4ae58c10e9d611d7b4d5ee2a2b951fa54",
		"status" : status_text,
		"deviceDataTypeCode" : "HEARTBEAT"
	}
	
	# Posts data (in this case status)
	response = requests.post(event_hub_url, headers = headers, data = json.dumps(query_parameters_post))
	
	# Posts an error code if something goes wrong
	if response.status_code != 201:
		print response.status_code, response.text
	
	# configures a URL for the data, posts same thing
	post_data_url = BASE_URL + '/api/Data'
	
	# Posts data (in this case status)
	response = requests.post(post_data_url, headers = headers, data = json.dumps(query_parameters_post))

	

