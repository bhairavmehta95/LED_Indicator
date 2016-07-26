import semsiot
import time 
import requests
import json

# Base URL as asssigned by SEMS
BASE_URL = "https://semsiot.3m.com/"

# Sends post requests to connect the device and update the status
def connect():
	headers = { 'Content-Type' : 'application/json' }
	
	# Query parameters to Connect
	## CONNECT IS THE SAME THING AS REGISTER
	register_url = BASE_URL + '/api/Register'
	query_parameters_register  = {
		"serialNumber" : "123456123456",
    	"applicationId": "EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC",
    	"apiKey": "gcT1vVuu=gwwspFsjkwg2hh2zFPDmmlWJanTSDq7pktnT",
		"deviceName": "led-indicator",
		"latitude" : 44.94,
		"longitude" : -93.09
	}
	
	# Posts a request with above parameters, we are looking for the two
	# Key values listed below
	
	response = requests.post(register_url , headers = headers, data = json.dumps(query_parameters_register) )	
	

	Authorization = response.json()['EventHubKey']

	# Authorizes connection
	headers.update( { 'Authorization' : Authorization } )
	return headers

def send_post(status_text, headers):
	query_parameters_post = {
		"serialNumber" : "123456123456",
   		"applicationId": "EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC",
    	"apiKey": "gcT1vVuu=gwwspFsjkwg2hh2zFPDmmlWJanTSDq7pktnT",
		"status" : status_text,
		"deviceDataTypeCode" : "HEARTBEAT"
	}

	
	# # Posts data (in this case status)
	#response = requests.post(event_hub_url, headers = headers, data = json.dumps(query_parameters_post))
	
	# # Posts an error code if something goes wrong
	# if response.status_code != 201:
	# 	print response.status_code, response.text
	
	# # configures a URL for the data, posts same thing
	post_data_url = BASE_URL + '/api/Data'
	#print headers, " are the headers inside of SEND POST"
	# # Posts data (in this case status)
	response = requests.post(post_data_url, headers = headers, data = json.dumps(query_parameters_post))

	#print response.json()


def get_bluetooth_status(headers):
	query_parameters_get = {
		"serialNumber" : "123456123456",
   		"applicationId": "EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC",
    	"apiKey": "gcT1vVuu=gwwspFsjkwg2hh2zFPDmmlWJanTSDq7pktnT",
	}

	get_url = BASE_URL + "/api/Data?request.applicationId=EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC%20&request.aPIKeyValue=InATu7b3CgBJsCUWfu%3D964d1fZdK1HKqgbs5K%3DetEYqzB&request.serialNumber=123456123456&request.lastXMinutes=30&request.historical=true"
	response = requests.get(get_url, headers = headers, data = json.dumps(query_parameters_get))
	#print "Here is the status code: ", response.status_code
	response_json = response.json()
	#print response_json

	# Default
	bluetooth_status = 'Missing'
	for entry in response_json['Data']:
		try:
			if entry['bluetooth_status'] != '':
				bluetooth_status = entry['bluetooth_status']
		except:
			pass

	return bluetooth_status


def get_visualize_data(minutes, headers):
	query_parameters_get = {
		"serialNumber" : "123456123456",
   		"applicationId": "EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC",
    	"apiKey": "gcT1vVuu=gwwspFsjkwg2hh2zFPDmmlWJanTSDq7pktnT",
	}

	get_url = BASE_URL + "/api/Data?request.applicationId=EBE05BA5-74A7-4152-9BF4-1EE5A9A64CDC%20&request.aPIKeyValue=InATu7b3CgBJsCUWfu%3D964d1fZdK1HKqgbs5K%3DetEYqzB&request.serialNumber=123456123456&request.lastXMinutes=" + str(minutes) + "&request.historical=true"
	response = requests.get(get_url, headers = headers, data = json.dumps(query_parameters_get))
	#print "Here is the status code: ", response.status_code
	response_json = response.json()
	free_state = 0
	out_state = 0
	busy_state = 0
	total_state = 0
	for entry in response_json['Data']:
		try:
			if entry['status'] == 'Free':
				free_state += 1
			elif entry['status'] == 'Out':
				out_state += 1
			elif entry['status'] == 'Busy':
				out_state += 1
			total_state +=  1
		except:
			pass

	status_dict = {
		'free_state' : free_state,
		'out_state' : out_state,
		'busy_state': busy_state,
		}

	return status_dict