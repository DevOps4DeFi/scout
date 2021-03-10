import warnings
from dataclasses import dataclass
from brownie import interface
from brownie.network.contract import InterfaceContainer
from rich.console import Console
import logging
import json
import requests
from rich.logging import RichHandler

warnings.simplefilter( "ignore" )

console = Console()
logging.basicConfig( level="ERROR", format="%(message)s", datefmt="[%X]",
                     handlers=[RichHandler( rich_tracebacks=True )] )
log = logging.getLogger( "rich" )

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
TREASURY_ADDRESS = '0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B'

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

    def describe(self):
        info = []
        for name, address in self.wallets.items():
            scale = 10 ** self.token.decimals()
            try:
                info.append({
                    "balance": self.token.balanceOf( address ) / scale,
                    "tokenName": self.token.symbol(),
                    "tokenAddress": self.token,
                    "walletAddress": address.lower(),
                    "walletName": name
                })
            except ValueError as e:
                log.exception( str( e ) )
        return info

@dataclass
class Treasury:
    name: str
    token: InterfaceContainer
    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {
                    "treasuryBalance": self.token.balanceOf( TREASURY_ADDRESS ) / scale
                    }
        except ValueError as e:
            info = {}
            log.exception( str( e ) )

        return info


@dataclass
class Digg:
    name: str
    digg_oracle: InterfaceContainer

    def describe(self):
        try:
            info = {
                    "lastUpdated":  self.digg_oracle.providerReports( oracle_provider, 1 )[0],
                    "oracle_price"      : self.digg_oracle.providerReports( oracle_provider, 1 )[1] / 1e18
                    }
        except ValueError as e:
            info = {}
            log.exception( str( e ) )

        return info

@dataclass
class Badgertree:
    name: str
    badger_tree: InterfaceContainer

    def describe(self):
        try:
            info = {
                "lastPublishTimestamp":  self.badger_tree.lastPublishTimestamp(),
            }
        except ValueError as e:
            info = {}
            log.exception( str( e ) )

        return info

sett_vaults = {
        "bBADGER"         : "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28",
        "brenCrv"         : "0x6dEf55d2e18486B9dDfaA075bc4e4EE0B28c1545",
        "bsbtcCrv"        : "0xd04c48A53c111300aD41190D63681ed3dAd998eC",
        "btbtcCrv"        : "0xb9D076fDe463dbc9f915E5392F807315Bf940334",
        "buniBadgerWbtc"  : "0x235c9e24D3FB2FAFd58a2E49D454Fdcd2DBf7FF1",
        "bslpBadgerWbtc"  : '0x1862A18181346EBd9EdAf800804f89190DeF24a5',
        "bharvestRenCrv"  : "0xAf5A1DECfa95BAF63E0084a35c62592B774A2A87",
        "bDIGG"           : "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        "buniDiggWbtc"    : "0xC17078FDd324CC473F8175Dc5290fae5f2E84714",
        "bslpDiggWbtc"  : "0x88128580ACdD9c04Ce47AFcE196875747bF2A9f6",
        "bslpEthWbtc"   : "0x758A43EE2BFf8230eeb784879CdcFF4828F2544D"
        }

treasury_tokens = {
        'FARM'        : '0xa0246c9032bC3A600820415aE600c6388619A14D',
        'BADGER'      : '0x3472A5A71965499acd81997a54BBA8D852C6E53d',
        'DIGG'        : '0x798D1bE841a82a273720CE31c822C61a67a601C3',
        'USDC'        : '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        'WBTC'        : '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        'WETH'        : '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
        'SUSHI'       : "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
        'bDIGG'       : "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        'bBADGER'     : '0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28',
        'xSUSHI'      : '0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272',
        'crvRenWBTC'  : '0x49849C98ae39Fff122806C06791Fa73784FB3675',
        'crvRenWSBTC' : '0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3',
        'crvTbtcSbtc': '0x64eda51d3Ad40D56b9dFc5554E06F94e1Dd786Fd',
        'slpWbtcEth' : '0xceff51756c56ceffca006cd410b03ffc46dd3a58',
        'slpWbtcBadger': '0x110492b31c59716ac47337e616804e3e3adc0b4a',
        'uniWbtcBadger': '0xcd7989894bc033581532d2cd88da5db0a4b12859',
        'uniWbtcDigg'  : '0xe86204c4eddd2f70ee00ead6805f917671f56c52',
        'slpWbtcDigg' : '0x9a13867048e01c663ce8ce2fe0cdae69ff9f35e3'
        }
lp_tokens = {
    'slpWbtcEth' : '0xceff51756c56ceffca006cd410b03ffc46dd3a58',
    'slpWbtcBadger': '0x110492b31c59716ac47337e616804e3e3adc0b4a',
    'uniWbtcBadger': '0xcd7989894bc033581532d2cd88da5db0a4b12859',
    'uniWbtcDigg'  : '0xe86204c4eddd2f70ee00ead6805f917671f56c52',
    'slpWbtcDigg' : '0x9a13867048e01c663ce8ce2fe0cdae69ff9f35e3'
}

oracle = '0x058ec2Bf15011095a25670b618A129c043e2162E'
oracle_provider = '0x72dc16CFa95beB42aeebD2B10F22E55bD17Ce976'
badgertree   = '0x660802Fc641b154aBA66a62137e71f331B6d787A'

def treasury_tokes():
    return treasury_tokens
def get_lp_data():
    return [lpToken( name=f'{name}', token=interface.lpToken(token)) for name, token in lp_tokens.items()]

def get_sett_data():
    return [Sett( name=f'{name}', sett=interface.Sett( sett ) ) for name, sett in sett_vaults.items()]

def get_treasury_data():
    return [Treasury( name=f'{name}', token=interface.ERC20( token ) ) for name, token in treasury_tokens.items()]

def get_token_balance_data(wallets, tokenAddress):
    return TokenBalance(wallets=wallets, token=interface.ERC20(tokenAddress))

def get_digg_data():
    return Digg( name='Digg Prices', digg_oracle=interface.Oracle( oracle ) )

def get_badgertree_data():
    return Badgertree( name='Rewards Cycles', badger_tree=interface.Badgertree( badgertree ) )

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
