from brownie import (
	ERC20,
	Peg,
	accounts,
)

def main():
	acct = accounts.load('deployment_account')
	erc20 = ERC20.deploy("Base Token", "BASE", 18, 200e18, {'from': acct})
	print(erc20.address)

	peg = Peg.deploy("Peg Token", "PEG", erc20.address, {'from': acct})
