# @version ^0.2.0

# @dev Implementation of ERC-20 token standard.
# @author Takayuki Jimba (@yudetamago)
# https://github.com/ethereum/EIPs/blob/master/EIPS/eip-20.md

from vyper.interfaces import ERC20

implements: ERC20

event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256

name: public(String[64])
symbol: public(String[32])
decimals: public(uint256)

# NOTE: By declaring `balanceOf` as public, vyper automatically generates a 'balanceOf()' getter
#       method to allow access to account balances.
#       The _KeyType will become a required parameter for the getter and it will return _ValueType.
#       See: https://vyper.readthedocs.io/en/v0.1.0-beta.8/types.html?highlight=getter#mappings
balanceOf: public(HashMap[address, uint256])
# By declaring `allowance` as public, vyper automatically generates the `allowance()` getter
allowance: public(HashMap[address, HashMap[address, uint256]])
# By declaring `totalSupply` as public, we automatically create the `totalSupply()` getter
totalSupply: public(uint256)


# @dev Address of base token to be converted
baseToken: public(ERC20)

# @dev Conversion ratio of base token to fractionalised tokens
PEG_RATIO: constant(uint256) = 1000

# @dev Initial supply
INITIAL_SUPPLY: constant(uint256) = 0

# @dev Decimals
DECIMALS: constant(uint256) = 18

@external
def __init__(_name: String[64], _symbol: String[32], _baseTokenAddress: address):

    self.name = _name
    self.symbol = _symbol
    self.decimals = DECIMALS
    self.totalSupply = INITIAL_SUPPLY
    self.baseToken = ERC20(_baseTokenAddress)

@external
def transfer(_to : address, _value : uint256) -> bool:
    """
    @dev Transfer token for a specified address
    @param _to The address to transfer to.
    @param _value The amount to be transferred.
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[msg.sender] -= _value
    self.balanceOf[_to] += _value
    log Transfer(msg.sender, _to, _value)
    return True


@external
def transferFrom(_from : address, _to : address, _value : uint256) -> bool:
    """
     @dev Transfer tokens from one address to another.
     @param _from address The address which you want to send tokens from
     @param _to address The address which you want to transfer to
     @param _value uint256 the amount of tokens to be transferred
    """
    # NOTE: vyper does not allow underflows
    #       so the following subtraction would revert on insufficient balance
    self.balanceOf[_from] -= _value
    self.balanceOf[_to] += _value
    # NOTE: vyper does not allow underflows
    #      so the following subtraction would revert on insufficient allowance
    self.allowance[_from][msg.sender] -= _value
    log Transfer(_from, _to, _value)
    return True


@external
def approve(_spender : address, _value : uint256) -> bool:
    """
    @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
         Beware that changing an allowance with this method brings the risk that someone may use both the old
         and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
         race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
         https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
    @param _spender The address which will spend the funds.
    @param _value The amount of tokens to be spent.
    """
    self.allowance[msg.sender][_spender] = _value
    log Approval(msg.sender, _spender, _value)
    return True


@external
def mintPeg(_base_token_quantity: uint256):
    """
    @dev Mint the Peg token by transferring the Base token to the contract.
         This encapsulates the modification of balances such that the
         proper events are emitted.
    @param _base_token_quantity The amount of Base tokens to convert to peg.
    """

    self.baseToken.transferFrom(msg.sender, self, _base_token_quantity)
    _newPegTokens: uint256 = _base_token_quantity * 1000
    self.totalSupply += _newPegTokens
    self.balanceOf[msg.sender] += _newPegTokens
    log Transfer(ZERO_ADDRESS, msg.sender, _newPegTokens)


@internal
def _burn(_to: address, _value: uint256):
    """
    @dev Internal function that burns an amount of the token of a given
         account.
    @param _to The account whose tokens will be burned.
    @param _value The amount that will be burned.
    """
    assert _to != ZERO_ADDRESS
    self.totalSupply -= _value
    self.balanceOf[_to] -= _value
    log Transfer(_to, ZERO_ADDRESS, _value)


@external
def redeemPeg(_value: uint256):
    """
    @dev Redeem an amount of the Peg token of msg.sender.
    @param _value The amount that will be redeemed.
    """
    assert _value <= self.balanceOf[msg.sender]
    self._burn(msg.sender, _value)

    _redeemedBaseTokens: uint256 = _value / 1000
    self.baseToken.transfer(msg.sender, _redeemedBaseTokens)
