from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from tutorial.authhelper import get_signin_url, get_token_from_code, get_user_email_from_id_token
from tutorial.outlookservice import get_my_events, create_busy, delete_busy_event, add_time_busy
from datetime import datetime, timedelta
from time import sleep
import os
import subprocess
import pytz

from sems_api import send_post, connect, get_bluetooth_status, get_visualize_data, get_most_recent_status, get_latest_device_for_user


HEADERS_SEMS_API = {}

# Renders the sign in page, which will redirect to OAuth Login
def home(request):
	global HEADERS_SEMS_API
	redirect_uri = request.build_absolute_uri(reverse('tutorial:gettoken'))
	sign_in_url = get_signin_url(redirect_uri)
	context = {'sign_in_url' : sign_in_url}
	return render(request, 'tutorial/index.html', context)

# Gets token, allows application to proceed
def gettoken(request):
	auth_code = request.GET['code']
	redirect_uri = request.build_absolute_uri(reverse('tutorial:gettoken'))
	token = get_token_from_code(auth_code, redirect_uri)
	access_token = token.get('access_token')
	user_email = get_user_email_from_id_token(token.get('id_token'))
	
	# Save the token in the session, send user to events homepage
	request.session['access_token'] = access_token
	request.session['user_email'] = user_email

	return HttpResponseRedirect(reverse('tutorial:device_register'))

def device_register(request):
	return render(request, 'tutorial/device_register.html')

def check_if_visualize(request, HEADERS_SEMS_API):
	minutes = 60 * 24
	visualize_request = False
	if request.POST.get('Day', False):
		minutes = 60 * 24
		visualize_request = True
	elif request.POST.get('Week', False):
		minutes = 60 * 24 * 7
		visualize_request = True
	elif request.POST.get('Month', False):
		minutes = 60 * 24 * 30
		visualize_request = True

	user_email = request.session['user_email']
	user = user_email.split('@')
	
	status_dictionary = get_visualize_data(user, minutes, HEADERS_SEMS_API)

	if visualize_request:
		status = get_most_recent_status(user, HEADERS_SEMS_API)
		status_dictionary['status'] = status

	return status_dictionary
	
# Events	 
def events(request):
	HEADERS_SEMS_API = connect()
	# Integer to define status. -1 : Unknown, 0: Free, 1: Busy, 2: Out
	status = -1
	access_token = request.session['access_token']
	user_email = request.session['user_email']

	# Monitors events.html to see what POST requests get sent back
	if (request.method == "POST" and request.POST.get('Busy', False)):
		status = 1
		delete_busy_event(access_token, user_email)	
		create_busy(access_token, user_email)
	elif (request.method == "POST" and request.POST.get('Out', False)):
		status = 2
		delete_busy_event(access_token, user_email)	
	elif (request.method == "POST" and request.POST.get('Free', False)):
		status = 0
		delete_busy_event(access_token, user_email)

	# If there is no token in the session, redirect to home
	if not access_token:
		return HttpResponseRedirect(reverse('tutorial:home'))
	else:
		context = []

	time_busy_end = ""

	# If for some reason the events are not returned, return to home
	# try:
	# 	events['value']
	# except:
	# 	return HttpResponseRedirect(reverse('tutorial:home'))

	try:
		device_id = request.POST.get('device_id', False)
	except:
		device_id = get_latest_device_for_user(user, HEADERS_SEMS_API)
	
	# For loop that loops through all of the events
	# returned by get_my_events
	
	# formats the events to a format that can be used for date arithmetic

	# TO DO: Find less awful way to convert time from UTC to CST
	if access_token:
		events = get_my_events(access_token, user_email)
		status_dict = check_if_visualize(request, HEADERS_SEMS_API)
		print events['value'], "is events value"
		for i, val in enumerate(events['value']):
			start = events['value'][i]['Start']['DateTime']
			adjust = timedelta(hours=5)
			start = datetime.strptime(start,'%Y-%m-%dT%H:%M:%S.%f0')
			start -= adjust
			end = events['value'][i]['End']['DateTime']
			end = datetime.strptime(end,'%Y-%m-%dT%H:%M:%S.%f0')
			end -= adjust
			now = datetime.now() - adjust
			start_diff = start - now
			end_diff = end - now
			subject = events['value'][i]['Subject']
			new_dictionary = { 'Subject' : subject, 'Start': start, 'End':end }
			print new_dictionary
			if subject != "Busy":
				context.append(new_dictionary)
			else:
				time_busy_end = end
			if start_diff <= timedelta(0) and end_diff >= timedelta(0) and subject != "Busy":
				status = 2

		# Default value: Free
		if status == -1:
			status = 0

		try:
			status_text = status_dict['status']
		except:
			status_text = get_status(status)

		user = user_email.split('@')[0]

		device_id = None

		send_post(user, device_id, status_text, HEADERS_SEMS_API)
		bluetooth_status = get_bluetooth_status(user, device_id, HEADERS_SEMS_API)

		free_state = status_dict['free_state']
		out_state = status_dict['out_state']
		busy_state = status_dict['busy_state']

		# Renders the events template with each event 
		values = { 'events': context, 
			'status' : status_text, 
			'time_busy_end' : time_busy_end,
			'bluetooth_status' : bluetooth_status,
			 'free_state' : free_state,
			 'out_state' : out_state,
			 'busy_state' : busy_state,
			 'device_id' : device_id,
		}

		print context, "is context"

		return render(request, 'tutorial/events.html', values)

# Integer values for status
def get_status(status):
	return {
			-1: "Unknown",
			0: "Free",
			1: "Busy",
			2: "Out",
		}.get(status, "Unknown Error")



