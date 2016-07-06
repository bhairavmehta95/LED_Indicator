# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license. See full license at the bottom of this file.
import requests
import uuid
import json 
from datetime import datetime, timedelta


outlook_api_endpoint = 'https://outlook.office.com/api/v2.0{0}'

# Generic API Sending
def make_api_call(method, url, token, user_email, payload = None, parameters = None):
    # Send these headers with all API calls
    headers = { 'User-Agent' : 'python_tutorial/1.0',
                'Authorization' : 'Bearer {0}'.format(token),
                'Accept' : 'application/json',
                'X-AnchorMailbox' : user_email,
				 }
                
    # Use these headers to instrument calls. Makes it easier
    # to correlate requests and responses in case of problems
    # and is a recommended best practice.
    request_id = str(uuid.uuid4())
    instrumentation = { 'client-request-id' : request_id,
                        'return-client-request-id' : 'true',
						'outlook.timezone' : "Central Standard Time" }
                        
    headers.update(instrumentation)
    
    response = None
    
    if (method.upper() == 'GET'):
        response = requests.get(url, headers = headers, params = parameters)
    elif (method.upper() == 'DELETE'):
        response = requests.delete(url, headers = headers, params = parameters)
    elif (method.upper() == 'PATCH'):
        headers.update({ 'Content-Type' : 'application/json' })
        response = requests.patch(url, headers = headers, data = json.dumps(payload), params = parameters)
    elif (method.upper() == 'POST'):
        headers.update({ 'Content-Type' : 'application/json' })
        response = requests.post(url, headers = headers, data = json.dumps(payload), params = parameters)
        
    return response
    
    
def get_my_events(access_token, user_email):
  get_events_url = outlook_api_endpoint.format('/Me/CalendarView')
  today = datetime.today()
  today = str(today).partition(' ')[0]
  
  start_of_day = 'T00:00:00.0000000'
  end_of_day = 'T23:59:00.0000000'
  start_of_day = today + start_of_day
  end_of_day = today + end_of_day
  query_parameters = { '$select' : 'Subject, Start, End',
					   '$orderby' : 'Start/DateTime ASC',
					  'startDateTime': start_of_day,
					  'endDateTime' : end_of_day  
					  }
                      
  r = make_api_call('GET', get_events_url, access_token, user_email, parameters = query_parameters)
  if (r.status_code == requests.codes.ok):
    return r.json()
  else:
    return "{0}: {1}".format(r.status_code, r.text)


def create_busy(access_token, user_email):
  # Get the Calendar ID
  get_calendar_url = outlook_api_endpoint.format('/Me/Calendars')
  query_parameters = { '$select' : 'Id',
					  }
  r = make_api_call('GET', get_calendar_url, access_token, user_email, parameters = query_parameters)
  default_calendar_id = r.json()['value'][0]['Id']

  endpoint_formatting_url = '/Me/Calendars/' + default_calendar_id + '/events'
  get_events_url = outlook_api_endpoint.format(endpoint_formatting_url)

  now = datetime.now()
  end_time = now + timedelta(minutes = 30)
  start_time = now
  start_time = str(start_time).partition('.')[0]
  end_time = str(end_time).partition('.')[0]

  start = {"DateTime": start_time, "TimeZone" : 'Central Standard Time'}
  end = {"DateTime": end_time, "TimeZone" : 'Central Standard Time'}

  query_parameters = {
			"Subject": "Busy",
			"Start" : start,
			"End" : end, 
			"IsReminderOn" : "False"
  }

  r = make_api_call('POST', get_events_url, access_token, user_email, query_parameters)
  if (r.status_code == requests.codes.ok or r.status_code == 201):
    print "BUSYEVENT posted successfully\n"
  else:
    print ("BUSYEVENT post UNSUCCESSFUL\n")

def delete_busy_event(access_token, user_email):
  events = get_my_events(access_token, user_email)
  busy_event = ""
  for event in events['value']:
    if event['Subject'] == 'Busy':
      print "Found our event with ID: ", event['Id']
      busy_event = event['Id']
      break
    else:
      print event['Subject']
  get_events_url = '/Me/Events/' + busy_event

  get_events_url = outlook_api_endpoint.format(get_events_url)    
  if busy_event != "":              
    print busy_event, " is the busy"
    r = make_api_call('DELETE', get_events_url, access_token, user_email)
    print "{0}: {1}".format(r.status_code, r.text)

def add_time_busy(access_token, user_email):
  events = get_my_events(access_token, user_email)
  busy_event = ""
  end_time = ""
  print events['value']
  for event in events['value']:
    if event['Subject'] == 'Busy':
      print "Found our event with ID: ", event['Id']
      busy_event = event['Id']
      end_time = event['End']['DateTime']
      break
    else:
      print event['Subject']
  get_events_url = '/Me/Events/' + busy_event
  get_events_url = outlook_api_endpoint.format(get_events_url) 
  additional_time = timedelta(minutes = 30)
  print end_time, type(end_time)
  end_time = datetime.strptime(end_time,'%Y-%m-%dT%H:%M:%S.%f0')
  print end_time 
  end_time += additional_time
  print end_time
  end_time = datetime.strptime(str(end_time),'%Y-%m-%d %H:%M:%S')
  end = {"DateTime": str(end_time), "TimeZone" : 'Central Standard Time'}
  query_parameters = {'End' : end }

  if busy_event != "":              
    print busy_event, " is the busy"
    r = make_api_call('PATCH', get_events_url, access_token, user_email, query_parameters)
    print "{0}: {1}".format(r.status_code, r.text)
