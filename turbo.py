import json
import time
import base64
import logging
import requests
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5

log = logging.getLogger(__name__)

class Turbo:
	def __init__(self):
		# Initialize the session for requests and the API key
		self.session = requests.Session()
		self.apikey = None

	def login(self, username, password, **kwargs):
		""" Login to Steam
		
		:param username: the user's Steam username
		:param password: the user's Steam password
		
		kwargs:
		:param emailauth: the email authentication code received after a login attempt
		:param captchagid: the GID for the CAPTCHA attempted after a login attempt
		:param captchatext: the CAPTCHA text from the user after a login attempt
		:param twofactorcode: 2FA from Steam guard to allow the user to login """
		
		# Set the user-agent to be like a browser
		self.session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6'

		payload = {
			'donotcache': round(time.time() * 1000),
			'username': username
		}

		# Get the RSA key for our username at the current time, so we can encrypt our password
		resp = self.session.post('https://steamcommunity.com/login/getrsakey/', data=payload)

		if resp.status_code != 200:
			return False

		rsa_data = resp.json()

		mod = int(rsa_data['publickey_mod'], 16)
		exp = int(rsa_data['publickey_exp'], 16)
		rsa = RSA.construct((mod, exp))
		cipher = PKCS1_v1_5.new(rsa)

		payload = {
			'username': username,
			'password': base64.b64encode(cipher.encrypt(password.encode('utf-8'))),
			'rsatimestamp': rsa_data['timestamp'],
			'remember_login': True,
			'emailauth': kwargs.get('emailauth'),
			'captchagid': kwargs.get('captchagid'),
			'captcha_text': kwargs.get('captchatext'),
			'twofactorcode': kwargs.get('twofactorcode'),
			'donotcache': time.time() * 1000
		}

		# Attempt to log in to Steam
		resp = self.session.post('https://steamcommunity.com/login/dologin/', data=payload)
		login_result = resp.json()

		# Handle different possibilities for the login
		if not login_result['success']:
			if login_result.get('captcha_needed'):
				log.info("CAPTCHA is needed")
				gid = login_result['captcha_gid']
				self.login(username, password, captchagid=gid, captchatext=self.captcha(gid))
			elif login_result.get('requires_twofactor'):
				log.info("2FA code is needed")
				self.login(username, password, twofactorcode=input('Enter your 2FA: '))
			else:
				return False
		else:
			log.info("Logged in successfully")
			self.session.get('https://steamcommunity.com')
			return True

	def captcha(self, gid):
		""" Saves a CAPTCHA image to the folder so that the user can solve it
		
		:param gid: the GID of the CAPTCHA """
		
		# Get the rendered CAPTCHA from Steam
		resp = self.session.get('https://steamcommunity.com/login/rendercaptcha/?gid=' + gid)
		
		# Write the content of the response to a new file
		with open('captcha.png', 'wb') as file:
			file.write(resp.content)

		# Get the user to input the CAPTCHA's text
		captcha_text = input('Enter CAPTCHA: ')
		return captcha_text

	def get_apikey(self):
		""" Generates a new Steam API key """
		
		payload = {
			'Revoke': 'Revoke My Steam Web API Key',
			'sessionid': self.session.cookies['sessionid']
		}
		
		# Revoke the old Steam API key
		self.session.post('https://steamcommunity.com/dev/revokekey', data=payload)

		payload = {
			'domain': 'github.com/Shoot',
			'agreeToTerms': 'agreed',
			'sessionid': self.session.cookies['sessionid'],
			'Submit': 'Register'
		}
		
		# Sign up for a new one, then parse the response text to get the key
		resp = self.session.post('https://steamcommunity.com/dev/registerkey', data=payload)
		self.apikey = resp.text.split('<p>Key: ')[-1].split('</p>')[0]
		log.info("Got a new API key: " + self.apikey)

	def convert_vanity_urls(self, list):
		""" Converts vanity URLs into SteamID64 format
		
		:param list: array of vanity URLs """
		
		if not self.apikey:
			log.error("An API key is necessary for this function")
			return False

		steam64_list = []

		# Convert each vanity to SteamID64 format
		for vanity in list:
			payload = {
				'key': self.apikey,
				'vanityurl': vanity
			}
			
			# Get the owner's information
			resp = requests.get('http://api.steampowered.com/ISteamUser/ResolveVanityUrl/v0001/', params=payload)
			steam_user = resp.json()

			# Append it to the array
			steam64_list.append(steam_user['response']['steamid'])

		log.info("Converted " + str(len(steam64_list)) + " vanity URLs")
		return steam64_list

	def target(self, s64list, vanitylist):
		""" Checks to see if the vanity URL is no longer in the list of Steam profiles
		
		:param s64list: the list of SteamID64 addresses (from convert_vanity_urls())
		:param vanitylist: the list of vanity URLs to check """
		
		if not self.apikey:
			return False

		# Get the users who own the vanity URLs
		resp = self.session.get('http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=' + self.apikey + '&steamids=' + ','.join(s64list))
		
		# Handle some possible issues
		if resp.status_code != 200:
			return False
		if not resp.json().get('response'):
			return False
		if not resp.json()["response"].get("players"):
			return False
		
		# Check if the vanity URL is not longer present
		for vanity in vanitylist:
			if not 'steamcommunity.com/id/' + vanity + '/' in resp.text.lower():
				log.info("Got a target: " + vanity)
				return vanity

	def claim(self, vanity):
		""" Attempt to claim the vanity URL
		
		:param vanity: the vanity URL to try and claim """
		
		payload = {
			'sessionID': self.session.cookies['sessionid'],
			'type': 'profileSave',
			'customURL': vanity
		}

		# Attempt to change our Steam vanity URL
		self.session.get('https://steamcommunity.com/my/edit/', params=payload)
		resp = self.session.get('https://steamcommunity.com/my/edit')
		
		if '/id/' + vanity + '/home' in resp.text:
			log.info("Successfully claimed " + target)
			return True
		else:
			log.info("Failed to claim " + target)
			return False
