import warnings
from dataclasses import dataclass
from brownie import interface
from brownie.network.contract import InterfaceContainer
from rich.console import Console
import logging
import json
import requests
from rich.logging import RichHandler
from web3 import Web3


warnings.simplefilter( "ignore" )

console = Console()
logging.basicConfig( level="ERROR", format="%(message)s", datefmt="[%X]",
                     handlers=[RichHandler( rich_tracebacks=True )] )
log = logging.getLogger( "rich" )

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
network = "bsc"
@dataclass
class lpToken:
    name: str
    token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {
                "token0": self.token.token0(),
                "token1": self.token.token1(),
                "token0_reserve": self.token.getReserves()[0],
                "token1_reserve": self.token.getReserves()[1],
                "totalSupply": self.token.totalSupply(),
                "decimals": self.token.decimals()
            }

            #console.print(f'token0:{token0_name}, token1: {token1_name}, getReserves:{reserves}')

            #info = {
            #    "token0Name": self.token.token0.key('token0')
            #    "token1Name": self.token.token1.key('token1')
            #    "token0Reserve": self.sett.getReserves()['_reserve0'] / scale,
            #    "token1Reserve": self.sett.getReserves()['_reserve1'] / token1_scale,
            #    "totalSupply"  : self.sett.totalSupply() / scale,
            #}
        except ValueError as e:
            info = {}
            log.exception( str( e ) )

        return info

@dataclass
class Sett:
    name: str
    sett: InterfaceContainer

    def describe(self):
        scale = 10 ** self.sett.decimals()
        try:
            info = {
                    "pricePerShare": self.sett.getPricePerFullShare() / scale,
                    "totalSupply"  : self.sett.totalSupply() / scale,
                    "balance": self.sett.balance() / scale,
                    "available"    : self.sett.available() / scale,
                    }
        except ValueError as e:
            info = {}
            log.exception( str( e ) )

        return info

@dataclass
class TokenBalance:
    wallets: dict
    token: InterfaceContainer
    tokenName: str

    def describe(self):
        info = []
        for name, address in self.wallets.items():
            scale = 10 ** self.token.decimals()
            try:
                info.append({
                    "balance": self.token.balanceOf( address ) / scale,
                    "tokenName": self.tokenName,
                    "tokenAddress": self.token,
                    "walletAddress": address,
                    "walletName": name
                })
            except ValueError as e:
                log.exception( str( e ) )
        return info

badger_wallets_input  = {
    "deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
    "guardian": "0x29F7F8896Fb913CF7f9949C623F896a154727919",
    "keeper": "0x872213E29C85d7e30F1C8202FC47eD1Ec124BB1D",
    "devMultisig": "0x6DA4c138Dd178F6179091C260de643529A2dAcfe",
    "opsMultisig": "0x7c7054bd87431378C837B2679f223f6d6aa602C1",
    "devProxyAdmin": "0x6354e79f21b56c11f48bcd7c451be456d7102a36",
}
badger_wallets = {}
for name, address in badger_wallets_input.items():
    badger_wallets[name] = Web3.toChecksumAddress(address)


sett_vault_input = {
        "bcakeBnbBtcb": "0xaf4B9C4b545D5324904bAa15e29796D2E2f90813",
        "bcakebBadgerBtcb": "0x857F91f735f4B03b19D2b5c6E476C73DB8241F55",
        "bcakebDiggBtcb": "0xa861Ba302674b08f7F2F24381b705870521DDfed"
        }
sett_vaults = {}
for name, address in sett_vault_input.items():
    sett_vaults[name] = Web3.toChecksumAddress(address)

coingecko_tokens_input = {
    "0x753fbc5800a8C8e3Fb6DC6415810d627A387Dfc9" :  'badger-dao',
    "0x1F7216fdB338247512Ec99715587bb97BBf96eae" :'badger-sett-badger',
    "0x5986D5c77c65e5801a5cAa4fAE80089f870A71dA" : 'badger-sett-digg',
    "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c" : 'binance-bitcoin',
    "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": 'binancecoin',
    "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82" : 'pancakeswap-token',
}
coingecko_tokens = {}
for address, id in coingecko_tokens_input.items():
    coingecko_tokens[Web3.toChecksumAddress(address)] = id

treasury_tokens_input = {
    "BADGER" :        '0x753fbc5800a8C8e3Fb6DC6415810d627A387Dfc9',
    "bBADGER" :'0x1F7216fdB338247512Ec99715587bb97BBf96eae', 
    "bDIGG" : '0x5986D5c77c65e5801a5cAa4fAE80089f870A71dA',
    "BTCb" : '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c',
    "WBNB": '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c',
    "CAKE" : '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
    "cakebBadgerBtcb" : '0x10F461CEAC7A17F59e249954Db0784d42EfF5DB5',
    "cakebDiggBtcb" : '0xE1E33459505bB3763843a426F7Fd9933418184ae',
    "cakeBnbBtcb" : '0x7561EEe90e24F3b348E1087A005F78B4c8453524',
}
treasury_tokens = {}
for name, address in treasury_tokens_input.items():
    treasury_tokens[name] = Web3.toChecksumAddress(address)

lp_tokens_input = {
    "cakebBadgerBtcb" : '0x10F461CEAC7A17F59e249954Db0784d42EfF5DB5',
    "cakebDiggBtcb" : '0xE1E33459505bB3763843a426F7Fd9933418184ae',
    "cakeBnbBtcb": '0x7561eee90e24f3b348e1087a005f78b4c8453524'
    }
lp_tokens = {}
for name,address in lp_tokens_input.items():
    lp_tokens[name] = Web3.toChecksumAddress(address)

oracle = Web3.toChecksumAddress('0x058ec2Bf15011095a25670b618A129c043e2162E')
oracle_provider = Web3.toChecksumAddress('0x72dc16CFa95beB42aeebD2B10F22E55bD17Ce976')
badgertree   = Web3.toChecksumAddress('0x660802Fc641b154aBA66a62137e71f331B6d787A')

def treasury_tokes():
    return treasury_tokens
def get_lp_data():
    return [lpToken( name=f'{name}', token=interface.lpToken(token)) for name, token in lp_tokens.items()]

def get_sett_data():
    return [Sett( name=f'{name}', sett=interface.Sett( sett ) ) for name, sett in sett_vaults.items()]


def get_token_balance_data(wallets, tokenAddress, tokenName):
    return TokenBalance(wallets=wallets, token=interface.ERC20(tokenAddress), tokenName=tokenName)

def get_json_request(request_type, url, request_data=None):
    # Take a request object and request type, then return the response in JSON format
    json_request = json.dumps(request_data)
    if(request_type == 'get'):
        r = requests.get(f'{url}', data=json_request)
    elif(request_type == 'post'):
        r = requests.post(f'{url}', data=json_request)
    else:
        return None
    return r.json()
