import time
import ccxt
import random
import requests
import hmac, base64
from tqdm import tqdm

import config
from config import api


randnetworks_lst = ["Arbitrum One", 'Optimism', 'zkSync Era', 'Base', 'Linea']
# ----main-options----#
switch_cex = config.CEX  # binance, okx, mexc, kucoin, gate, huobi, bybit, bitget
symbolWithdraw = "ETH"  # символ токена BNB, ETH, MATIC
network = "Linea"  # название сети  random тогда будет выбирать случайную из списка или zkSync Era/zkSyncEra (для bitget), BSC, Arbitrum One, Optimism, zkSync Lite, ETH/ERC20, MATIC
proxy_server = config.proxy_server  # "http://login:password@IP:port"
# ДЛЯ ОКЕКСА НЕ НУЖНЫ ПРОКСИ

# ----second-options----#
amount = config.amount  # минимальная и максимальная сумма
decimal_places = 5  # количество знаков, после запятой для генерации случайных чисел
delay = config.delay  # минимальная и максимальная задержка
shuffle_wallets = "no"  # нужно ли мешать кошельки yes/no


# ----end-all-options----#

class API:
	# binance API
	binance_apikey = api.binance_apikey
	binance_apisecret = api.binance_apisecret
	# okx API
	okx_apikey = api.okx_apikey
	okx_apisecret = api.okx_apisecret
	okx_passphrase = api.okx_passphrase
	# bitget API
	bitget_apikey = api.bitget_apikey
	bitget_apisecret = api.bitget_apisecret
	bitget_passphrase = api.bitget_passphrase
	# bybit API
	bybit_apikey = api.bybit_apikey
	bybit_apisecret = api.bybit_apisecret
	# gate API
	gate_apikey = api.gate_apikey
	gate_apisecret = api.gate_apisecret
	# kucoin API
	kucoin_apikey = api.kucoin_apikey
	kucoin_apisecret = api.kucoin_apisecret
	kucoin_passphrase = api.kucoin_passphrase
	# mexc API
	mexc_apikey = api.mexc_apikey
	mexc_apisecret = api.mexc_apisecret
	# huobi API
	huobi_apikey = api.huobi_apikey
	huobi_apisecret = api.huobi_apisecret


proxies = {
	"http": proxy_server, "https": proxy_server,
}


def sleeping(from_sleep, to_sleep):
	with tqdm(total=to_sleep - from_sleep, desc='Sleeping', unit='s') as pbar:
		for i in range(from_sleep, to_sleep):
			time.sleep(1)
			pbar.update(1)


def binance_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.binance({
		'apiKey': API.binance_apikey, 'secret': API.binance_apisecret, 'enableRateLimit': True, 'proxies': proxies,
		'options': {
			'defaultType': 'spot'
		}
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, tag=None, params={
			"network": network
		})
		print(f'\n>>>[Binance] Вывел {amount_to_withdrawal} {symbolWithdraw} {network}', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[Binance] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def bitget_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.bitget({
		'apiKey': API.bitget_apikey, 'secret': API.bitget_apisecret, 'password': API.bitget_passphrase,
		'enableRateLimit': True, 'proxies': proxies, 'options': {
			'defaultType': 'spot'
		}
	})
	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, tag=None, params={
			"chain": network
		})
		print(f'\n>>>[Bitget] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[Bitget] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def okx_withdraw_new(address, amount_to_withdrawal, wallet_number):
	wallet = address
	SYMBOL = symbolWithdraw
	if network == 'random':
		CHAIN = random.choice(randnetworks_lst)  # если нужно выводить в рандомной
	else:
		CHAIN = network  # если нужен вывод в одной
	api_key = API.okx_apikey
	secret_key = API.okx_apisecret
	passphras = API.okx_passphrase
	AMOUNT = amount_to_withdrawal

	# take FEE for withdraw
	_, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/currencies?ccy={SYMBOL}", meth="GET")
	response = requests.get(f"https://www.okx.cab/api/v5/asset/currencies?ccy={SYMBOL}", timeout=10, headers=headers)

	for lst in response.json()['data']:
		if lst['chain'] == f'{SYMBOL}-{CHAIN}':
			FEE = lst['minFee']

	try:
		body = {
			"ccy": SYMBOL, "amt": AMOUNT, "fee": FEE, "dest": "4", "chain": f"{SYMBOL}-{CHAIN}", "toAddr": wallet
		}
		_, _, headers = okx_data(api_key, secret_key, passphras, request_path=f"/api/v5/asset/withdrawal", meth="POST", body=str(body))
		a = requests.post("https://www.okx.cab/api/v5/asset/withdrawal", data=str(body), timeout=10, headers=headers)
		result = a.json()

		if result['code'] == '0':
			print(f'\n>>>[OKx] Вывел {AMOUNT} {SYMBOL} {CHAIN}', flush=True)
			print(f'    [{wallet_number}]{wallet}', flush=True)
	except Exception as error:
		print(f"OKX | Withdraw unsuccess to {wallet} | error : {error}")


def okx_data(api_key, secret_key, passphras, request_path="/api/v5/account/balance?ccy=ETH", body='', meth="GET"):
	try:
		import datetime
		def signature(timestamp: str, method: str, request_path: str, secret_key: str, body: str = "") -> str:
			if not body:
				body = ""

			message = timestamp + method.upper() + request_path + body
			mac = hmac.new(bytes(secret_key, encoding="utf-8"), bytes(message, encoding="utf-8"), digestmod="sha256", )
			d = mac.digest()
			return base64.b64encode(d).decode("utf-8")

		dt_now = datetime.datetime.utcnow()
		ms = str(dt_now.microsecond).zfill(6)[:3]
		timestamp = f"{dt_now:%Y-%m-%dT%H:%M:%S}.{ms}Z"

		base_url = "https://www.okex.com"
		headers = {
			"Content-Type": "application/json", "OK-ACCESS-KEY": api_key,
			"OK-ACCESS-SIGN": signature(timestamp, meth, request_path, secret_key, body),
			"OK-ACCESS-TIMESTAMP": timestamp, "OK-ACCESS-PASSPHRASE": passphras, 'x-simulated-trading': '0'
		}
	except Exception as ex:
		logger.error(ex)
	return base_url, request_path, headers


def okx_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.okx({
		'apiKey': API.okx_apikey, 'secret': API.okx_apisecret, 'password': API.okx_passphrase, 'enableRateLimit': True,
		'proxies': proxies,
	})

	try:
		chainName = symbolWithdraw + "-" + network
		fee = get_withdrawal_fee(symbolWithdraw, chainName)
		exchange.withdraw(symbolWithdraw, amount_to_withdrawal, address, params={
			"toAddress": address, "chainName": chainName, "dest": 4, "fee": fee, "pwd": '-',
			"amt": amount_to_withdrawal, "network": network
		})

		print(f'\n>>>[OKx] Вывел {amount_to_withdrawal} {symbolWithdraw} {network}', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[OKx] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def bybit_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.bybit({
		'apiKey': API.bybit_apikey, 'secret': API.bybit_apisecret,
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, tag=None, params={
			"forceChain": 1, "network": network
		})
		print(f'\n>>>[ByBit] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[ByBit] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def gate_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.gate({
		'apiKey': API.gate_apikey, 'secret': API.gate_apisecret,
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, params={
			"network": network
		})
		print(f'\n>>>[Gate.io] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[Gate.io] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def kucoin_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.kucoin({
		'apiKey': API.kucoin_apikey, 'secret': API.kucoin_apisecret, 'password': API.kucoin_passphrase,
		'enableRateLimit': True,
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, params={
			"network": network
		})
		print(f'\n>>>[Kucoin] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[Kucoin] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def mexc_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.mexc({
		'apiKey': API.mexc_apikey, 'secret': API.mexc_apisecret, 'enableRateLimit': True,
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, params={
			"network": network
		})
		print(f'\n>>>[MEXC] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[MEXC] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


def huobi_withdraw(address, amount_to_withdrawal, wallet_number):
	exchange = ccxt.huobi({
		'apiKey': API.huobi_apikey, 'secret': API.huobi_apisecret, 'enableRateLimit': True,
	})

	try:
		exchange.withdraw(code=symbolWithdraw, amount=amount_to_withdrawal, address=address, params={
			"network": network
		})
		print(f'\n>>>[Huobi] Вывел {amount_to_withdrawal} {symbolWithdraw} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)
	except Exception as error:
		print(f'\n>>>[Huobi] Не удалось вывести {amount_to_withdrawal} {symbolWithdraw}: {error} ', flush=True)
		print(f'    [{wallet_number}]{address}', flush=True)


async def choose_cex(address, amount_to_withdrawal, wallet_number, switch_cex):
    if switch_cex == "binance":
        binance_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "okx":
        okx_withdraw_new(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "bybit":
        bybit_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "gate":
        gate_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "huobi":
        huobi_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "kucoin":
        kucoin_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "mexc":
        mexc_withdraw(address, amount_to_withdrawal, wallet_number)
    elif switch_cex == "bitget":
        bitget_withdraw(address, amount_to_withdrawal, wallet_number)
    else:
        raise ValueError("Неверное значение CEX. Поддерживаемые значения: binance, okx, bybit, gate, huobi, kucoin, mexc.")


def get_withdrawal_fee(symbolWithdraw, chainName):
	exchange = ccxt.okx({
		'apiKey': API.okx_apikey, 'secret': API.okx_apisecret, 'password': API.okx_passphrase, 'enableRateLimit': True,
		'proxies': proxies,
	})
	currencies = exchange.fetch_currencies()
	for currency in currencies:
		if currency == symbolWithdraw:
			currency_info = currencies[currency]
			network_info = currency_info.get('networks', None)
			if network_info:
				for network in network_info:
					network_data = network_info[network]
					network_id = network_data['id']
					if network_id == chainName:
						withdrawal_fee = currency_info['networks'][network]['fee']
						if withdrawal_fee == 0:
							return 0
						else:
							return withdrawal_fee
	raise ValueError(f"     не могу получить сумму комиссии, проверьте значения symbolWithdraw и network")


def shuffle(wallets_list, shuffle_wallets):
	numbered_wallets = list(enumerate(wallets_list, start=1))
	if shuffle_wallets.lower() == "yes":
		random.shuffle(numbered_wallets)
	elif shuffle_wallets.lower() == "no":
		pass
	else:
		raise ValueError("\n>>> Неверное значение переменной 'shuffle_wallets'. Ожидается 'yes' или 'no'.")
	return numbered_wallets


async def amount_to_withdraw(a,s, dec):
	return round(random.uniform(a, s), dec)


