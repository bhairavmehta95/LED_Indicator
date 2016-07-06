from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from tutorial.authhelper import get_signin_url, get_token_from_code, get_user_email_from_id_token
from tutorial.outlookservice import get_my_events, create_busy, delete_busy_event, add_time_busy
from datetime import datetime, timedelta
from time import sleep
import os
import subprocess
import pytz
import bluetooth

# Create your views here.
def home(request):
  redirect_uri = request.build_absolute_uri(reverse('tutorial:gettoken'))
  sign_in_url = get_signin_url(redirect_uri)
  context = {'sign_in_url' : sign_in_url}
  return render(request, 'tutorial/index.html', context)

def run_piblaster():
	path = "/home/pi/pi-blaster"
	os.chdir( path )
	os.system("sudo ./pi-blaster")

def red():
	run_piblaster()
	
	os.system('echo 17=1> /dev/pi-blaster')
	os.system('echo 18=0 > /dev/pi-blaster')
	os.system('echo 22=0 > /dev/pi-blaster')

def blue():
	run_piblaster()
	
	os.system('echo 17=0 > /dev/pi-blaster')
	os.system('echo 18=1 > /dev/pi-blaster')
	os.system('echo 22=0 > /dev/pi-blaster')


def green():
	run_piblaster()
	
	os.system('echo 17=0 > /dev/pi-blaster')
	os.system('echo 18=0 > /dev/pi-blaster')
	os.system('echo 22=1 > /dev/pi-blaster')

  
def gettoken(request):
  auth_code = request.GET['code']
  redirect_uri = request.build_absolute_uri(reverse('tutorial:gettoken'))
  token = get_token_from_code(auth_code, redirect_uri)
  access_token = token.get('access_token')
  user_email = get_user_email_from_id_token(token.get('id_token'))
  
  # Save the token in the session, send user to events homepage
  request.session['access_token'] = access_token
  request.session['user_email'] = user_email
  return HttpResponseRedirect(reverse('tutorial:events'))
  
def events(request):
  # Integer to define status. -1 : Unknown, 0: Free, 1: Busy, 2: Out
  status = -1
  access_token = request.session['access_token']
  user_email = request.session['user_email']

  if (request.GET.get('red')):
    red()
    status = 1
    delete_busy_event(access_token, user_email)	
    create_busy(access_token, user_email)

  elif (request.GET.get('blue')):
    blue()
    status = 2
    delete_busy_event(access_token, user_email)	
  elif (request.GET.get('green')):
    status = 0
    green()
    delete_busy_event(access_token, user_email)	

  # If there is no token in the session, redirect to home
  if not access_token:
    return HttpResponseRedirect(reverse('tutorial:home'))
  else:
    events = get_my_events(access_token, user_email)
    context = []
  time_busy_end = ""

  if access_token:
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
		if subject != "Busy":
			context.append(new_dictionary)
		else:
			time_busy_end = end
		if start_diff <= timedelta(0) and end_diff >= timedelta(0):
			blue()
			status = 2

  if status == -1:
	status = 0
	green()
  #if bluetooth_scan():
	#status = 2
	#blue() 
  status_text = get_status(status)
  events = { 'events': context , 'status' : status_text, 'time_busy_end' : time_busy_end}
  return render(request, 'tutorial/events.html', events)

def bluetooth_scan():
	bt_name = "Bhairav's iPhone"
	bt_addr = None

	nearby_devices = bluetooth.discover_devices()

	for addr in nearby_devices:
		if bt_name == bluetooth.lookup_name( addr ):
			bt_addr = addr
			break
	if bt_addr != None:
		print "found", bt_addr
		return True
	else:
		print "Not found!:"
		return False

def get_status(status):
  return {
        -1: "Unknown",
        0: "Free",
		1: "Busy",
        2: "Out",
    }.get(status, "Unknown Error")



