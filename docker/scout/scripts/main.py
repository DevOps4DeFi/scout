#!/usr/local/bin/python3
from rich.console import Console
from prometheus_client import Gauge, start_http_server
import warnings
import datetime
from scripts.data import get_sett_data, get_treasury_data, get_digg_data, get_badgertree_data, get_json_request, get_lp_data, get_token_balance_data, treasury_tokens
from brownie import chain
from brownie import interface

warnings.simplefilter( "ignore" )
console = Console()

##TODO copied to keep dashboards looking good.  In a week retire all lowercase names and adjust dashboard to use uppercase
new_tokens = {
    "BADGER": "0x3472A5A71965499acd81997a54BBA8D852C6E53d".lower(),
    "DIGG": "0x798D1bE841a82a273720CE31c822C61a67a601C3".lower(),
    "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
    "xSUSHI": "0x8798249c2e607446efb7ad49ec89dd1865ff4272",
    "FARM": "0xa0246c9032bc3a600820415ae600c6388619a14d",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599".lower(),
    'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
}

token_interfaces = {}
for name, address in new_tokens.items():
    token_interfaces.update({address : interface.ERC20(address)})

tokens = {
    "badger": "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
    "BADGER": "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
    "digg": "0x798D1bE841a82a273720CE31c822C61a67a601C3",
    "DIGG": "0x798D1bE841a82a273720CE31c822C61a67a601C3",
    "sushi": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
    "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
    "xSUSHI": "0x8798249c2e607446efb7ad49ec89dd1865ff4272",
    "farm": "0xa0246c9032bc3a600820415ae600c6388619a14d",
    "FARM": "0xa0246c9032bc3a600820415ae600c6388619a14d",
    "wbtc": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
        }

badger_wallets = {
    "fees": "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B",
    "team": "0xe4aa1d8aaf8a50422bc5c7310deb1262d1f6f657",
    "DAO_treasury": "0x4441776e6a5d61fa024a5117bfc26b953ad1f425",
    "uniswap_rewards": "0x0c79406977314847a9545b11783635432d7fe019",
    "badgerhunt": "0x394dcfbcf25c5400fcc147ebd9970ed34a474543",
    "rewardsEscrow": "0x19d099670a21bc0a8211a89b84cedf59abb4377f",
    "badgertree": "0x660802fc641b154aba66a62137e71f331b6d787a",
    "badger_deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
    "dev_multisig": "0xB65cef03b9B89f99517643226d76e286ee999e77"
}

crvpools = {
    'crvRenWBTC'  : '0x93054188d876f558f4a66B2EF1d97d16eDf0895B',
    'crvRenWSBTC' : '0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714',
    'crvTbtcSbtc': '0xc25099792e9349c7dd09759744ea681c7de2cb66',
}

tree = '0x660802Fc641b154aBA66a62137e71f331B6d787A'

badger = token_interfaces[new_tokens['BADGER'].lower()]
digg = token_interfaces[new_tokens['DIGG'].lower()]
wbtc = token_interfaces[new_tokens['WBTC'].lower()]
badgertree = interface.Badgertree( tree )
slpDiggWbtc = interface.Pair('0x9a13867048e01c663ce8Ce2fE0cDAE69Ff9F35E3')
uniDiggWbtc = interface.Pair('0xe86204c4eddd2f70ee00ead6805f917671f56c52')

treasury_tokens_address_list = list(treasury_tokens.values())
number_treasury_tokens = len(treasury_tokens_address_list)
treasury_tokens_name_list = list(treasury_tokens.keys())

def main():
    sett_gauge = Gauge("sett", "Data from Badger Vaults", ["sett", "param", "token"])
    treasury_gauge = Gauge("treasury", '', ['token', 'param'])
    rewards_gauge = Gauge( 'rewards', '', ['token'])
    digg_gauge = Gauge('digg_price', '', ['value'])
    cycle_guage = Gauge('badgertree', 'Badgretree rewards', ['lastCycleUnixtime'])
    coingecko_price_gauge = Gauge('coingecko_prices', 'Pricing data from Coingecko', ['token','countertoken'])
    lpTokens_gauge = Gauge('lptokens', "LP Token data", ['lptoken', 'token'])
    crvtoken_gauge = Gauge('crvtokens', "CRV token data", ['token', 'param'])
    wallets_gauge = Gauge('wallets', 'Watched Wallet Balances', ['walletName', 'walletAddress', 'tokenName', 'tokenAddress'])
    start_http_server( 8801 )
    lpTokens = get_lp_data()
    setts = get_sett_data()
    treasury = get_treasury_data()
    wallet_balances_by_token = {}
    for tokenAddress in treasury_tokens.values():
        wallet_balances_by_token[tokenAddress] = get_token_balance_data(badger_wallets, tokenAddress)
    digg_prices = get_digg_data()
    badgertree_cycles = get_badgertree_data()

    countertoken_csv = "btc,usd,eur"
    token_csv = ""
    for key in tokens.keys():
        token_csv += (tokens[key] + ",")
    token_csv.rstrip(",")

#    badger_price = token_prices[tokens["badger"].lower()]["usd"]
#    digg_price = token_prices[tokens["digg"].lower()]["usd"]
#    console.print(f"Badger: {badger_price}")
#    console.print(f"Digg: {digg_price}")
    step = 0
    for block in chain.new_blocks( height_buffer=1 ):
        step += 1
        now = datetime.datetime.now()
        timestamp = (now.strftime("%Y-%m-%d %H:%M:%S"))
        console.rule(title=f'[green]{block.number} at {timestamp} step number {step}')
        console.print( f'Calculating reward holdings..' )

        badger_rewards = badger.balanceOf( badgertree.address ) / 1e18
        digg_rewards = digg.balanceOf( badgertree.address ) / 1e9

        rewards_gauge.labels( 'badger' ).set( badger_rewards )
        rewards_gauge.labels( 'digg' ).set( digg_rewards )
        for token in lpTokens:
            if step % 2 == 1: # only run every other step
                break
            info = token.describe()
            console.print( f'Processing lpToken reserves [bold]{token.name}...' )
            token0 = token_interfaces[info["token0"].lower()]
            token1 = token_interfaces[info["token1"].lower()]
            token0_reserve = info["token0_reserve"]
            token1_reserve = info["token1_reserve"]
            lpTokens_gauge.labels(token.name,
                                  f"{token0.symbol()}_supply").set(token0_reserve / (10 ** token0.decimals()))
            lpTokens_gauge.labels(token.name,
                                  f"{token1.symbol()}_supply").set(token1_reserve / (10 ** token1.decimals()))
            lpTokens_gauge.labels(token.name, "totalLpTokenSupply").set(info["totalSupply"] / (10 ** info["decimals"]))

        # process wallets for one treasury token
        tokenAddress = treasury_tokens_address_list[step % number_treasury_tokens]
        name = treasury_tokens_name_list[step % number_treasury_tokens]
        info = wallet_balances_by_token[tokenAddress]
        console.print(f'Processing wallet balances  for [bold]{name}:{tokenAddress}...')
        for metric in info.describe():
                wallets_gauge.labels(metric["walletName"], metric["walletAddress"], metric["tokenName"], metric["tokenAddress"]).set(metric["balance"])

        for token in crvpools:
            console.print(f'Processing crv token data for [bold]{token}:{crvpools[token]}...')
            virtual_price = interface.CRVswap(crvpools[token]).get_virtual_price()/1e18
            crvtoken_gauge.labels(token, "pricePerShare").set(virtual_price)

        token_prices = get_json_request(url=f'https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={token_csv}&vs_currencies={countertoken_csv}', request_type='get')

        for token in tokens:
            console.print( f'Processing Coingecko price for [bold]{token}...' )
            for countertoken in countertoken_csv.split(","):
                #    badger_price = token_prices[tokens["badger"].lower()]["usd"]
                coingecko_price_gauge.labels( token, countertoken ).set ( token_prices[tokens[token].lower()][countertoken])

        for sett in setts:
            info = sett.describe()
            console.print( f'Processing Sett [bold]{sett.name}...' )
            for param, value in info.items():
                if param != "token":
                    sett_gauge.labels(sett.name, param, info["token"]).set( value )
        for token in treasury:
            info = token.describe()
            console.print( f'Processing Ecosystem Token [bold]{token.name}...' )
            for param, value in info.items():
                treasury_gauge.labels( token.name, param ).set( value )
        price = digg_prices.describe()
        last_cycle_unixtime = badgertree_cycles.describe()

        for param, value in last_cycle_unixtime.items():
            console.print( f'Processing Badgertree [bold]{param}...' )
            cycle_guage.labels( param ).set( value )
        for param, value in price.items():
            console.print( f'Processing Digg Oracle [bold]{param}...' )
            digg_gauge.labels( param ).set( value )

        digg_sushi_price = (slpDiggWbtc.getReserves()[0] / 1e8) / (slpDiggWbtc.getReserves()[1] / 1e9)
        digg_uni_price = (uniDiggWbtc.getReserves()[0] / 1e8) / (uniDiggWbtc.getReserves()[1] / 1e9)

        digg_gauge.labels( 'sushiswap' ).set(digg_sushi_price)
        digg_gauge.labels('uniswap').set(digg_uni_price)

