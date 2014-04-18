import sys
sys.path.append('/var/www/dev.bibliosaur.com/scripts')

import urllib
import urllib2
import webapp2
import json
import logging
import logging.config

from sets import Set

toplevelurl = "http://dev.bibliosaur.com"
topleveldirectory = "/var/www/dev.bibliosaur.com"

logger = logging.getLogger()
hdlr = logging.FileHandler('/var/www/dev.bibliosaur.com/bibliosaur.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

GOOGLE_CLIENT_ID = "507497402664-k5r3h55tp2jvo0gc6s3vfu18a595k3mj.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "WUK3lud8Vmba67QTV3ZN2u65"

class google_login(webapp2.RequestHandler):
    def get(self):
		token_request_uri = "https://accounts.google.com/o/oauth2/auth"
		response_type = "code"
		redirect_uri = toplevelurl + "/login/google/auth"
		scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
		url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
			token_request_uri = token_request_uri,
			response_type = response_type,
			client_id = GOOGLE_CLIENT_ID,
			redirect_uri = redirect_uri,
			scope = scope)
		return self.redirect(url)
    def post(self):
		token_request_uri = "https://accounts.google.com/o/oauth2/auth"
		response_type = "code"
		redirect_uri = toplevelurl + "/login/google/auth"
		scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
		url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
			token_request_uri = token_request_uri,
			response_type = response_type,
			client_id = GOOGLE_CLIENT_ID,
			redirect_uri = redirect_uri,
			scope = scope)
		return self.redirect(url)
    
class google_authenticate(webapp2.RequestHandler):
    def handle_exception(self, exception, debug):
		logging.warning("login failed: " + str(exception))
		return self.redirect(toplevelurl)
    def get(self):
		try:
		  code = self.request.get_all('code')
		except:
		  logging.error("Login failed:  'code' not available")
		  return self.redirect(toplevelurl)

		url = 'https://accounts.google.com/o/oauth2/token'
		redirect_uri = toplevelurl + "/login/google/auth"
		values = {'code' : code[0], 
			      'redirect_uri' : redirect_uri,
			      'client_id' : GOOGLE_CLIENT_ID,
			      'client_secret' : GOOGLE_CLIENT_SECRET,
			      'grant_type' : 'authorization_code'}
		data = urllib.urlencode(values)
		headers={'content-type':'application/x-www-form-urlencoded'}
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req).read()
		token_data = json.JSONDecoder().decode(response)
		response = urllib2.urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token={accessToken}".format(accessToken=token_data['access_token'])).read()
		logging.info("response:  " + str(response))
		#this gets the google profile!!
		google_profile = json.JSONDecoder().decode(response)
		#log the user in-->
		#HERE YOU LOG THE USER IN, OR ANYTHING ELSE YOU WANT
		#THEN REDIRECT TO PROTECTED PAGE
				
		return google_profile
