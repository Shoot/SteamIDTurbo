import time
import json
import base64
import requests
from Cryptodome.Cipher import PKCS1_v1_5
from Cryptodome.PublicKey import RSA

with open('user.json', 'r') as file:
	user = json.loads(file.read())

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6"

def login(username, password, emailauth="", emailsteamid="", twofactorcode="", captchagid="", captchatext=""):
	getrsa_payload = {
		'donotcache': round(time.time() * 1000),
		'username': user['username']
	}

	rsa_data = requests.post('https://steamcommunity.com/login/getrsakey/', data=getrsa_payload).json()

	mod = int(rsa_data["publickey_mod"], 16)
	exp = int(rsa_data["publickey_exp"], 16)
	rsa = RSA.construct((mod, exp))
	cipher = PKCS1_v1_5.new(rsa)

	encrypted_password = base64.b64encode(cipher.encrypt(user['password'].encode("utf-8")))
	rsatimestamp = rsa_data["timestamp"]

	login_payload = {
		"username": user['username'],
		"password": encrypted_password,
		"rsatimestamp": rsatimestamp,
		"remember_login": True,
		"emailauth": emailauth,
		"captchagid": captchagid,
		"captcha_text": captchatext,
		"emailsteamid": emailsteamid,
		"twofactorcode": twofactorcode,
		"donotcache": time.time() * 1000
	}

	resp = session.post("https://steamcommunity.com/login/dologin/", data=login_payload).json()

	if not resp['success']:
		if resp.get("captcha_needed"):
			print("CAPTCHA detected. Please try again later.")
			captcha_resp = requests.get("https://steamcommunity.com/login/rendercaptcha/?gid=" + resp['captcha_gid'])
			with open('captcha.png', 'wb') as f:
				f.write(captcha_resp.content)
			var = input('Enter CAPTCHA: ')
			gid = str(resp['captcha_gid'])
			login(username, password, captchagid=gid, captchatext=var)
		elif resp.get("requires_twofactor"):
			twofac = input("Enter your 2FA: ")
			login(username, password, twofactorcode=twofac)
	else:
		print("Logged in successfully")

def convert_vanitys():
	id_list = []
	va_list = []

	for id in open('ids.txt', 'r').read().split('\n'):
		id = id.lower()
		try:
			payload = {
				'key': user['apikey'],
				'vanityurl': id
			}
			resp = requests.get('http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/', params=payload).json()
			id_list.append(resp['response']['steamid'])
			va_list.append(id)
		except:
			print(id + " encountered an error, therefore it was skipped.")
			pass
	
	return id_list, va_list

def check_all(id_list, va_list):
	session.get("http://steamcommunity.com/my/edit")
	sessionid = session.cookies['sessionid']

	print('Started turbo')

	while True:
		print(requests_cnt, end='\r')
		try:
			resp = session.get(f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={user['apikey']}&steamids={','.join(id_list)}").text
			requests_cnt += 1
			for id in va_list:
				if not f'/{id}/' in str(resp).lower():
					claim(id, sessionid)
		except Exception as e:
			print(str(e))
			print('There has been an error. Continuing on.')
		except KeyboardInterrupt:
			quit()

def claim(id, sessionid):
	session.get(f"http://steamcommunity.com/my/edit/?sessionID={sessionid}&type=profileSave&customURL={id}").text
	check = session.get('https://steamcommunity.com/my').text
	if f'https://steamcommunity.com/id/{id}/home/' in check:
		print('Successfully claimed /id/' + id)
		quit()
	else:
		print('Failed to claim /id/' + id)
		convert_vanitys()

if __name__ == "__main__":
	login(user['username'], user['password'])
	id_list, va_list = convert_vanitys()
	check_all()