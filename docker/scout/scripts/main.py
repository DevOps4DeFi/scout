#!/usr/local/bin/python3
from rich.console import Console
from prometheus_client import Gauge, start_http_server
import warnings
import datetime
from scripts.data import get_sett_data, get_treasury_data, get_digg_data, get_badgertree_data, get_json_request, get_lp_data, get_token_balance_data, treasury_tokens, sett_vaults,crvpools, lp_tokens, badger_wallets
from brownie import chain
from brownie import interface
from web3 import Web3
import re
import os

## WEB3 INIT
ETHNODEURL = os.environ["ETHNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))

native_tokens = ["BADGER", "DIGG", "bBADGER", "bDIGG"]

warnings.simplefilter( "ignore" )
console = Console()

token_interfaces = {}
for tokenname, address in treasury_tokens.items():
    token_interfaces.update({address: interface.ERC20(address)})


console.print ("Treasury Tokens")
console.print (treasury_tokens)

tree = Web3.toChecksumAddress('0x660802Fc641b154aBA66a62137e71f331B6d787A')

badger = token_interfaces[treasury_tokens['BADGER']]
digg = token_interfaces[treasury_tokens['DIGG']]
wbtc = token_interfaces[treasury_tokens['WBTC']]
badgertree = interface.Badgertree( tree )
slpDiggWbtc = interface.Pair(Web3.toChecksumAddress('0x9a13867048e01c663ce8Ce2fE0cDAE69Ff9F35E3'))
uniDiggWbtc = interface.Pair(Web3.toChecksumAddress('0xe86204c4eddd2f70ee00ead6805f917671f56c52'))

treasury_tokens_address_list = list(treasury_tokens.values())
number_treasury_tokens = len(treasury_tokens_address_list)
treasury_tokens_name_list = list(treasury_tokens.keys())

def main():
    sett_gauge = Gauge("sett", "Data from Badger Vaults", ["sett", "param", "tokenAddress", "token"])
    rewards_gauge = Gauge('rewards', '', ['token','tokenAddress'])
    digg_gauge = Gauge('digg_price', '', ['value'])
    cycle_guage = Gauge('badgertree', 'Badgretree rewards', ['lastCycleUnixtime'])
    coingecko_price_gauge = Gauge('coingecko_prices', 'Pricing data from Coingecko', ['token','countercurrency', 'tokenAddress'])
    lpTokens_gauge = Gauge('lptokens', "LP Token data", ['token', 'param', 'tokenAddress'])
    crvtoken_gauge = Gauge('crvtokens', "CRV token data", ['token', 'param', 'tokenAddress'])
    wallets_gauge = Gauge('wallets', 'Watched Wallet Balances', ['walletName', 'walletAddress', 'token', 'tokenAddress', 'param'])
    block_gauge = Gauge('blocks', 'Information about blocks processed')
    xchain_bridge_gauge = Gauge('xchainBridge', 'Information about tokens in custody', ['chain', 'token', 'bridge', 'param'])
    start_http_server( 8801 )
    lpTokens = get_lp_data()
    setts = get_sett_data()
    wallet_balances_by_token = {}
    for tokenName, tokenAddress in treasury_tokens.items():
        wallet_balances_by_token[tokenAddress] = get_token_balance_data(badger_wallets, tokenAddress, tokenName)
    digg_prices = get_digg_data()
    badgertree_cycles = get_badgertree_data()

    countertoken_csv = "usd"
    token_csv = ""
    for key in treasury_tokens.keys():
        token_csv += (treasury_tokens[key] + ",")
    token_csv.rstrip(",")

#    badger_price = token_prices[tokens["badger"]]["usd"]
#    digg_price = token_prices[tokens["digg"]]["usd"]
#    console.print(f"Badger: {badger_price}")
#    console.print(f"Digg: {digg_price}")
    step = 0
    usd_prices_by_token_address = {}
    wallet_balance_by_token_address = {}
    for block in chain.new_blocks( height_buffer=1 ):
        step += 1
        block_gauge.set(block.number)
        now = datetime.datetime.now()
        timestamp = (now.strftime("%Y-%m-%d %H:%M:%S"))
        console.rule(title=f'[green]{block.number} at {timestamp} step number {step} and block numbne {block.number}')
        block_gauge.set(block.number)

        console.print( f'Calculating reward holdings..' )

        badger_rewards = badger.balanceOf( badgertree.address ) / 1e18
        digg_rewards = digg.balanceOf( badgertree.address ) / 1e9

        rewards_gauge.labels('BADGER', treasury_tokens['BADGER']).set(badger_rewards)
        rewards_gauge.labels('DIGG', treasury_tokens['DIGG'] ).set(digg_rewards)
        token_prices = get_json_request(url=f'https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={token_csv}&vs_currencies={countertoken_csv}', request_type='get')

        for token, address in treasury_tokens.items():
            console.print( f'Processing Coingecko price for [bold]{token}...' )
            for countertoken in countertoken_csv.split(","):
                #    badger_price = token_prices[tokens["badger"]]["usd"]
                try:
                    exists_test = token_prices[treasury_tokens[token].lower()]
                    coingecko_price_gauge.labels(token, countertoken, address).set(token_prices[treasury_tokens[token].lower()][countertoken])
                    usd_prices_by_token_address[address] = token_prices[address.lower()]["usd"]
                    if token == "WETH":
                        coingecko_price_gauge.labels("ETH", countertoken, address).set(token_prices[treasury_tokens[token].lower()][countertoken])
                except:
                    console.print(f"can't get coingeck price for: {token}")

        for token in lpTokens:
            info = token.describe()
            console.print(f'Processing lpToken reserves [bold]{token.name}...')
            token0_address = Web3.toChecksumAddress(info["token0"])
            token1_address = Web3.toChecksumAddress(info["token1"])
            token0 = token_interfaces[token0_address]
            token1 = token_interfaces[token1_address]
            token0_reserve = info["token0_reserve"]
            token1_reserve = info["token1_reserve"]
            price = (token1_reserve / (10 ** token1.decimals()) / (info["totalSupply"] / (10 ** info["decimals"]))) * usd_prices_by_token_address[token1_address] * 2
            lpTokens_gauge.labels(token.name,
                                  f"{token0.symbol()}_supply",
                                  treasury_tokens[token.name]).set(token0_reserve / (10 ** token0.decimals()))
            lpTokens_gauge.labels(token.name,
                                  f"{token1.symbol()}_supply",
                                  treasury_tokens[token.name]).set(token1_reserve / (10 ** token1.decimals()))
            lpTokens_gauge.labels(token.name,
                                  "totalLpTokenSupply",
                                  treasury_tokens[token.name]).set(info["totalSupply"] / (10 ** info["decimals"]))
            try:
                usd_prices_by_token_address[lp_tokens[token.name]] = price
                lpTokens_gauge.labels(token.name,
                                      "usdPricePerShare",
                                      lp_tokens[token.name]).set(price)
            except:
                console.print(f"Failed to find USD price for lptoken {token.name}")

        for token in crvpools:
            console.print(f'Processing crv token data for [bold]{token}:{crvpools[token]}...')
            virtual_price = interface.CRVswap(crvpools[token]).get_virtual_price()/1e18
            usd_price = virtual_price * usd_prices_by_token_address[treasury_tokens["WBTC"]]
            crvtoken_gauge.labels(token, "pricePerShare", treasury_tokens["WBTC"]).set(virtual_price)
            crvtoken_gauge.labels(token, "usdPricePerShare", treasury_tokens["WBTC"]).set(usd_price)
            usd_prices_by_token_address[treasury_tokens[token]] = usd_price

        #  Processing Bridged tokens
        custodians = {
            "multiswap": Web3.toChecksumAddress("0x533e3c0e6b48010873B947bddC4721b1bDFF9648")
        }
        for custodian, address in custodians.items():
            console.print(f"Checking Balances on bridge {custodian} address {address}")
            for token in native_tokens:
                ti = token_interfaces[treasury_tokens[token]]
                xchain_bridge_gauge.labels("BSC", token, custodian, "balance").set(ti.balanceOf(address)/(10 ** ti.decimals()))
                xchain_bridge_gauge.labels("BSC", token, custodian, "usdBalance").set(ti.balanceOf(address)/(10 ** ti.decimals()) * usd_prices_by_token_address[treasury_tokens[token]])

        # process wallets for one treasury token
        tokenAddress = treasury_tokens_address_list[step % number_treasury_tokens]
        name = treasury_tokens_name_list[step % number_treasury_tokens]
        console.print(f'Processing wallet balances for [bold]{name}:{tokenAddress}...')
        info = wallet_balances_by_token[tokenAddress]
        for metric in info.describe():
            wallet_web3_addr =  Web3.toChecksumAddress(metric["walletAddress"])
            wallets_gauge.labels(metric["walletName"], metric["walletAddress"], metric["tokenName"], metric["tokenAddress"], "balance").set(metric["balance"])
            wallets_gauge.labels(metric["walletName"], metric["walletAddress"], "ETH", "None", "balance").set(float(w3.fromWei(w3.eth.getBalance(wallet_web3_addr), 'ether')))
            try:
                wallets_gauge.labels(metric["walletName"], metric["walletAddress"], "ETH", "None", "usdBalance").set(float(w3.fromWei(w3.eth.getBalance(wallet_web3_addr), 'ether')) * usd_prices_by_token_address[treasury_tokens["WETH"]])
                wallets_gauge.labels(metric["walletName"], metric["walletAddress"], metric["tokenName"], metric["tokenAddress"], "usdBalance").set(metric["balance"] * usd_prices_by_token_address[tokenAddress])
            except:
                console.print("error calculating USD token balance")

        for sett in setts:
            info = sett.describe()
            console.print(f'Processing Sett [bold]{sett.name}...')
            for param, value in info.items():
                sett_gauge.labels(sett.name, param, sett_vaults[sett.name], sett.name[1:]).set(value)

            try:
                usd_prices_by_token_address[sett_vaults[sett.name]] = (info["pricePerShare"] * usd_prices_by_token_address[treasury_tokens[re.sub("harvest", "", sett.name[1:])]])
                sett_gauge.labels(sett.name, "usdBalance", sett_vaults[sett.name], sett.name[1:]).set(usd_prices_by_token_address[sett_vaults[sett.name]]*info["balance"])
            except:
                console.print (f"Could not set USD price for Sett {sett.name}")
                pass

        price = digg_prices.describe()
        last_cycle_unixtime = badgertree_cycles.describe()

        for param, value in last_cycle_unixtime.items():
            console.print( f'Processing Badgertree [bold]{param}...')
            cycle_guage.labels( param ).set( value )

        for param, value in price.items():
            console.print( f'Processing Digg Oracle [bold]{param}...')
            digg_gauge.labels( param ).set(value)

        digg_sushi_price = (slpDiggWbtc.getReserves()[0] / 1e8) / (slpDiggWbtc.getReserves()[1] / 1e9)
        digg_uni_price = (uniDiggWbtc.getReserves()[0] / 1e8) / (uniDiggWbtc.getReserves()[1] / 1e9)

        digg_gauge.labels( 'sushiswap' ).set(digg_sushi_price)
        digg_gauge.labels('uniswap').set(digg_uni_price)

