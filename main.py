import json
import asyncio
import random

from tqdm import tqdm
import time
from web3 import Web3
from web3.eth import AsyncEth

max_gwei=10

from_sleep=150
to_sleep=300

linea_rpc= 'https://linea.decubate.com'
eth_rpc='https://ethereum-rpc.publicnode.com'


# ---------------------------------------


abi=json.loads('[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[{"internalType":"bytes4","name":"proxyId","type":"bytes4"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"},{"internalType":"uint256","name":"quantity","type":"uint256"}],"name":"getAccountInfoInLaunchpad","outputs":[{"internalType":"bool[]","name":"boolData","type":"bool[]"},{"internalType":"uint256[]","name":"intData","type":"uint256[]"},{"internalType":"bytes[]","name":"byteData","type":"bytes[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"bytes4","name":"","type":"bytes4"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"},{"internalType":"uint256","name":"quantity","type":"uint256"}],"name":"getAccountInfoInLaunchpadV2","outputs":[{"internalType":"bool[]","name":"boolData","type":"bool[]"},{"internalType":"uint256[]","name":"intData","type":"uint256[]"},{"internalType":"bytes[]","name":"byteData","type":"bytes[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"}],"name":"getAlreadyBuyBty","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"","type":"bytes4"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256[]","name":"","type":"uint256[]"}],"name":"getLaunchpadInfo","outputs":[{"internalType":"bool[]","name":"boolData","type":"bool[]"},{"internalType":"uint256[]","name":"intData","type":"uint256[]"},{"internalType":"address[]","name":"addressData","type":"address[]"},{"internalType":"bytes[]","name":"bytesData","type":"bytes[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"","type":"bytes4"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"}],"name":"getLaunchpadSlotInfo","outputs":[{"internalType":"bool[]","name":"boolData","type":"bool[]"},{"internalType":"uint256[]","name":"intData","type":"uint256[]"},{"internalType":"address[]","name":"addressData","type":"address[]"},{"internalType":"bytes4[]","name":"bytesData","type":"bytes4[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slot","type":"uint256"},{"internalType":"uint256","name":"maxBuy","type":"uint256"}],"name":"hashForWhitelist","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"},{"internalType":"address[]","name":"accounts","type":"address[]"},{"internalType":"uint256[]","name":"offChainMaxBuy","type":"uint256[]"},{"internalType":"bytes[]","name":"offChainSign","type":"bytes[]"}],"name":"isInWhiteList","outputs":[{"internalType":"uint8[]","name":"wln","type":"uint8[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"","type":"bytes4"},{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"},{"internalType":"uint256","name":"quantity","type":"uint256"},{"internalType":"uint256[]","name":"additional","type":"uint256[]"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"launchpadBuy","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"components":[{"internalType":"bytes4","name":"launchpadId","type":"bytes4"},{"internalType":"uint256","name":"slotId","type":"uint256"},{"internalType":"uint256","name":"quantity","type":"uint256"},{"internalType":"uint256","name":"maxWhitelistBuy","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"internalType":"struct DataType.BuyParameter[]","name":"parameters","type":"tuple[]"}],"name":"launchpadBuys","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"}]')
contract_address=Web3.to_checksum_address('0xBcFa22a36E555c507092FF16c1af4cB74B8514C8')

async def sleep(from_sleep : int | None=150, to_sleep : int | None = 300):
	sleep = random.randint(from_sleep, to_sleep)
	for _ in tqdm(range(sleep), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
		time.sleep(1)


async def main():
	web3 = Web3(provider=Web3.AsyncHTTPProvider(endpoint_uri=linea_rpc, ), modules={'eth': (AsyncEth,)}, middlewares=[])
	with open('privatekeys.txt') as f:
		p_keys = f.read().splitlines()
		random.shuffle(p_keys)
		for pk in p_keys:
			cted = Web3(provider=Web3.AsyncHTTPProvider(endpoint_uri=eth_rpc, ), modules={'eth': (AsyncEth,)}, middlewares=[])

			while True:
				gas = int(cted.from_wei((await cted.eth.gas_price), 'Gwei'))
				if gas>max_gwei:
					print(f'Current gas price is too high {gas} is higher than {max_gwei}')
					await asyncio.sleep(10)
				break

			account = web3.eth.account.from_key(private_key=pk)

			wallet_address = Web3.to_checksum_address(account.address)

			contract = web3.eth.contract(address=contract_address, abi=abi)
			data = contract.encodeABI('launchpadBuy', args=('0x0c21cfbb', '0x53b93973', 0, 1, [], b''))

			tx = {
				'chainId': await web3.eth.chain_id, 'maxPriorityFeePerGas': await web3.eth.max_priority_fee,
				'maxFeePerGas': (await web3.eth.gas_price) + (await web3.eth.max_priority_fee),
				'nonce': await web3.eth.get_transaction_count(wallet_address), 'from': wallet_address,
				'to': contract_address, 'data': data, 'value': int(0),
			}



			variation_factor = random.uniform(1.01, 1.2)
			tx['gas'] = int((await web3.eth.estimate_gas(tx))*variation_factor)

			sign = web3.eth.account.sign_transaction(tx, account.key)
			tx_hash = await web3.eth.send_raw_transaction(sign.rawTransaction)

			try:
				data = await web3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
				if 'status' in data and data['status'] == 1:
					print(f'transaction was successful: {wallet_address}, {tx_hash.hex()}')

				else:
					print(f'{wallet_address} | transaction failed {data["transactionHash"].hex()}')

			except Exception as e:
				print(f'{wallet_address} | unexpected error in <verif_tx> function')

			await sleep(from_sleep=from_sleep, to_sleep=to_sleep)



if __name__ == '__main__':
	asyncio.run(main())




