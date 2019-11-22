import turbo
import logging

logging.basicConfig(
	level=logging.INFO,
	format="[%(asctime)s] %(levelname)s: %(message)s",
	datefmt="%H:%M:%S"
)

if __name__ == "__main__":
	client = turbo.Turbo()
	client.login('username', 'password')

	with open('ids.txt', 'r') as file:
		vanity_list = file.read().split('\n')
	
	if not client.apikey:
		client.get_apikey()

	list = client.convert_vanity_urls(vanity_list)

	while True:
		for _ in range(100000):
			target = client.target(list, vanity_list)
			if target:
				claim = client.claim(target)
				if not claim:
					list = client.convert_vanity_urls(vanity_list)
				else:
					quit()

		client.get_apikey()