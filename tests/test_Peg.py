import pytest

from web3 import Web3

from brownie import (
	accounts,
	ERC20,
	Peg,
	reverts,
)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

@pytest.fixture(scope="module")
def ERC20Contract(ERC20, accounts):
	yield ERC20.deploy("Base Token", "BASE", 18, 2000, {'from': accounts[0]})

@pytest.fixture(scope="module")
def PegContract(Peg, ERC20Contract, accounts):
	yield Peg.deploy("Peg Token", "PEG", ERC20Contract.address, {'from': accounts[0]})

def test_ERC20_deployed(ERC20Contract, accounts):

	assert ERC20Contract.balanceOf(accounts[0]) == Web3.toWei(2000, 'ether')

def test_mint_peg(ERC20Contract, PegContract, accounts):

	tx1 = ERC20Contract.approve(PegContract.address, Web3.toWei(100, 'ether'), {'from': accounts[0]})

	assert tx1.events[0]['owner'] == accounts[0]
	assert tx1.events[0]['spender'] == PegContract.address
	assert tx1.events[0]['value'] == Web3.toWei(100, 'ether')

	tx2 = PegContract.mintPeg(Web3.toWei(100, 'ether'), {'from': accounts[0]})

	assert ERC20Contract.balanceOf(accounts[0]) == Web3.toWei(1900, 'ether')
	assert ERC20Contract.balanceOf(PegContract.address) == Web3.toWei(100, 'ether')

	assert PegContract.balanceOf(accounts[0]) == Web3.toWei(100000, 'ether')
	assert PegContract.totalSupply() == Web3.toWei(100000, 'ether')


	assert tx2.events[0]['sender'] == accounts[0]
	assert tx2.events[0]['receiver'] == PegContract.address
	assert tx2.events[0]['value'] == Web3.toWei(100, 'ether')

	assert tx2.events[1]['sender'] == ZERO_ADDRESS
	assert tx2.events[1]['receiver'] == accounts[0]
	assert tx2.events[1]['value'] == Web3.toWei(100000, 'ether')

	assert tx2.events[2]['minter'] == accounts[0]
	assert tx2.events[2]['valueMinted'] == Web3.toWei(100000, 'ether')

def test_redeem_peg(ERC20Contract, PegContract, accounts):

	tx1 = PegContract.redeemPeg(Web3.toWei(10000, 'ether'), {'from': accounts[0]})

	assert PegContract.balanceOf(accounts[0]) == Web3.toWei(90000, 'ether')
	assert PegContract.totalSupply() == Web3.toWei(90000, 'ether')
	assert ERC20Contract.balanceOf(accounts[0]) == Web3.toWei(1910, 'ether')

	assert tx1.events[0]['sender'] == accounts[0]
	assert tx1.events[0]['receiver'] == ZERO_ADDRESS
	assert tx1.events[0]['value'] == Web3.toWei(10000, 'ether')

	assert tx1.events[1]['sender'] == PegContract.address
	assert tx1.events[1]['receiver'] == accounts[0]
	assert tx1.events[1]['value'] == Web3.toWei(10, 'ether')

	assert tx1.events[2]['redeemer'] == accounts[0]
	assert tx1.events[2]['valueRedeemed'] == Web3.toWei(10000, 'ether')



def test_transfer_peg(PegContract, accounts):

	tx1 = PegContract.transfer(accounts[1], Web3.toWei(40000, 'ether'))

	assert PegContract.balanceOf(accounts[0]) == Web3.toWei(50000, 'ether')
	assert PegContract.balanceOf(accounts[1]) == Web3.toWei(40000, 'ether')
	assert PegContract.totalSupply() == Web3.toWei(90000, 'ether')

	assert tx1.events[0]['sender'] == accounts[0]
	assert tx1.events[0]['receiver'] == accounts[1]
	assert tx1.events[0]['value'] == Web3.toWei(40000, 'ether')

def test_redeem_peg_after_transfer(ERC20Contract, PegContract, accounts):

	tx1 = PegContract.redeemPeg(Web3.toWei(40000, 'ether'), {'from': accounts[1]})

	assert PegContract.balanceOf(accounts[1]) == 0
	assert PegContract.totalSupply() == Web3.toWei(50000, 'ether')
	assert ERC20Contract.balanceOf(accounts[1]) == Web3.toWei(40, 'ether')
	assert ERC20Contract.balanceOf(PegContract.address) == Web3.toWei(50, 'ether')

	assert tx1.events[0]['sender'] == accounts[1]
	assert tx1.events[0]['receiver'] == ZERO_ADDRESS
	assert tx1.events[0]['value'] == Web3.toWei(40000, 'ether')

	assert tx1.events[1]['sender'] == PegContract.address
	assert tx1.events[1]['receiver'] == accounts[1]
	assert tx1.events[1]['value'] == Web3.toWei(40, 'ether')

	assert tx1.events[2]['redeemer'] == accounts[1]
	assert tx1.events[2]['valueRedeemed'] == Web3.toWei(40000, 'ether')

def test_over_redeem(PegContract, accounts):

	with reverts():
		tx1 = PegContract.redeemPeg(Web3.toWei(50001, 'ether'), {'from': accounts[0]})

def test_redeem_zero(PegContract, accounts):

	tx1 = PegContract.redeemPeg(0, {'from': accounts[0]})

	assert PegContract.balanceOf(accounts[0]) == Web3.toWei(50000, 'ether')
	assert PegContract.totalSupply() == Web3.toWei(50000, 'ether')

	assert tx1.events[0]['sender'] == accounts[0]
	assert tx1.events[0]['receiver'] == ZERO_ADDRESS
	assert tx1.events[0]['value'] == 0

	assert tx1.events[1]['sender'] == PegContract.address
	assert tx1.events[1]['receiver'] == accounts[0]
	assert tx1.events[1]['value'] == 0

	assert tx1.events[2]['redeemer'] == accounts[0]
	assert tx1.events[2]['valueRedeemed'] == 0
