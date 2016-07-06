# Copyright (c) Microsoft. All rights reserved. Licensed under the MIT license. See full license at the bottom of this file.
from urllib import quote, urlencode
from urlparse import urlparse
import requests
import requests
import base64
import json

# Client ID and secret
client_id = '3f8d2f93-3b81-47f4-b250-b6414e2d352b'
client_secret = 'pztmrmz3hiU6Ob8kCeSBZ8t'

# Constant strings for OAuth2 flow
# The OAuth authority
authority = 'https://login.microsoftonline.com'

# The authorize URL that initiates the OAuth2 client credential flow for admin consent
authorize_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/authorize?{0}')

# The token issuing endpoint
token_url = '{0}{1}'.format(authority, '/common/oauth2/v2.0/token')

# The scopes required by the app
scopes = [ 'openid',
           'profile',
           'https://outlook.office.com/mail.read',
           'https://outlook.office.com/calendars.readwrite',
           'https://outlook.office.com/contacts.read',
]

def get_signin_url(redirect_uri):
  # Build the query parameters for the signin url
  params = { 'client_id': client_id,
             'redirect_uri': redirect_uri,
             'response_type': 'code',
             'scope': ' '.join(str(i) for i in scopes)
           }
           
  signin_url = authorize_url.format(urlencode(params))
  
  return signin_url
  
def get_token_from_code(auth_code, redirect_uri):
  # Build the post form for the token request
  post_data = { 'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'scope': ' '.join(str(i) for i in scopes),
                'client_id': client_id,
                'client_secret': client_secret
              }

              
  r = requests.post(token_url, data = post_data)
  
  try:
    return r.json()
  except:
    return 'Error retrieving token: {0} - {1}'.format(r.status_code, r.text)
    
def get_user_email_from_id_token(id_token):
  # JWT is in three parts, header, token, and signature
  # separated by '.'
  token_parts = id_token.split('.')
  encoded_token = token_parts[1]
  
  # base64 strings should have a length divisible by 4
  # If this one doesn't, add the '=' padding to fix it
  leftovers = len(encoded_token) % 4
  if leftovers == 2:
      encoded_token += '=='
  elif leftovers == 3:
      encoded_token += '='
  
  # URL-safe base64 decode the token parts
  # NOTE: Per issue #2, added additional encode('utf-8') call on
  # encoded_token so this call will work in Python 2.*
  decoded = base64.urlsafe_b64decode(encoded_token.encode('utf-8')).decode('utf-8')
  
  # Load decoded token into a JSON object
  jwt = json.loads(decoded)
  
  return jwt['preferred_username']

# MIT License: 
 
# Permission is hereby granted, free of charge, to any person obtaining 
# a copy of this software and associated documentation files (the 
# ""Software""), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions: 
 
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software. 
 
# THE SOFTWARE IS PROVIDED ""AS IS"", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
