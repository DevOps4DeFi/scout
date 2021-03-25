#!/usr/local/bin/python3
from rich.console import Console
from prometheus_client import Gauge, start_http_server
import warnings
import datetime
from scripts.data_bsc import get_sett_data, get_json_request, get_lp_data, get_token_balance_data, treasury_tokens, sett_vaults, lp_tokens, badger_wallets, coingecko_tokens
from brownie import chain
from brownie import interface
from web3 import Web3
import re
import os

## WEB3 INIT
ETHNODEURL = os.environ["ETHNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))


warnings.simplefilter( "ignore" )
console = Console()

token_interfaces = {}
for tokenname, address in treasury_tokens.items():
    token_interfaces.update({address: interface.ERC20(address)})


console.print ("Treasury Tokens")
console.print (treasury_tokens)

treasury_tokens_address_list = list(treasury_tokens.values())
number_treasury_tokens = len(treasury_tokens_address_list)
treasury_tokens_name_list = list(treasury_tokens.keys())

def main():
    sett_gauge = Gauge("bsc_sett", "Data from Badger Vaults", ["sett", "param", "tokenAddress", "token"])
    lpTokens_gauge = Gauge('bsc_lp', "LP Token data", ['token', 'param', 'tokenAddress'])
    coingecko_price_gauge = Gauge('bsc_coingecko', 'Pricing data from Coingecko', ['token','countercurrency', 'tokenAddress'])
    wallets_gauge = Gauge('bsc_wallets', 'Watched Wallet Balances', ['walletName', 'walletAddress', 'token', 'tokenAddress', 'param'])
    block_gauge = Gauge('bsc_blocks', 'Information about blocks processed')
    start_http_server( 8801 )
    lpTokens = get_lp_data()
    setts = get_sett_data()
    wallet_balances_by_token = {}
    for tokenName, tokenAddress in treasury_tokens.items():
        wallet_balances_by_token[tokenAddress] = get_token_balance_data(badger_wallets, tokenAddress, tokenName)

    countertoken_csv = "usd"
    countertoken = "usd"
    token_csv = ""
    for key in coingecko_tokens.keys():
        token_csv += (coingecko_tokens[key] + ",")
    token_csv.rstrip(",")
    token_name_by_address={}
    for name, address in treasury_tokens.items():
        token_name_by_address[Web3.toChecksumAddress(address)] = name

    step = 0

    for block in chain.new_blocks( height_buffer=1 ):
        wallet_balance_by_token_address = {}
        usd_prices_by_token_address = {}
        step += 1
        block_gauge.set(block.number)
        now = datetime.datetime.now()
        timestamp = (now.strftime("%Y-%m-%d %H:%M:%S"))
        console.rule(title=f'[green]{block.number} at {timestamp} step number {step}')
        block_gauge.set(block.number)


        token_prices = get_json_request(url=f'https://api.coingecko.com/api/v3/simple/price?ids={token_csv}&vs_currencies={countertoken_csv}', request_type='get')

        for address, id in coingecko_tokens.items():
            token = token_name_by_address[address]
            console.print( f'Processing Coingecko price for [bold]{token}...' )
            try:
                exists_test = token_prices[id]
                coingecko_price_gauge.labels(token, "usd", address).set(token_prices[id][countertoken])
                usd_prices_by_token_address[address] = token_prices[id]["usd"]
                if token == "WBNB":
                    coingecko_price_gauge.labels("BNB", countertoken, address).set(token_prices[id][countertoken])
            except:
                console.print(f"can't get coingeck price for: {token}")



    ### LP Tokens
        for token in lpTokens:
            info = token.describe()
            console.print(f'Processing lpToken reserves [bold]{token.name}...')
            token0_address = Web3.toChecksumAddress(info["token0"])
            token1_address = Web3.toChecksumAddress(info["token1"])
            token0 = token_interfaces[token0_address]
            token1 = token_interfaces[token1_address]
            token0_reserve = info["token0_reserve"]
            token1_reserve = info["token1_reserve"]
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
                price = (token1_reserve / (10 ** token1.decimals()) / (info["totalSupply"] / (10 ** info["decimals"]))) * usd_prices_by_token_address[token1_address] * 2
                usd_prices_by_token_address[lp_tokens[token.name]] = price
                lpTokens_gauge.labels(token.name, "usdPricePerShare", lp_tokens[token.name]).set(price)
            except:
                console.print(f"Failed to find USD price for lptoken {token.name}")

        for name, address in badger_wallets.items():
            wallets_gauge.labels(name, address, "BNB", "None", "balance").set(float(w3.fromWei(w3.eth.getBalance(address), 'ether')))
            try:
                wallets_gauge.labels(name, address, "BNB", "None", "usdBalance").set(float(w3.fromWei(w3.eth.getBalance(address), 'ether')) * usd_prices_by_token_address[treasury_tokens["WBNB"]])
            except:
                console.print("Can't find USD price for BNB")

        for token, address in treasury_tokens.items():
            console.print(f'Processing wallet balances for [bold]{token}:{address}...')
            info = wallet_balances_by_token[address]
            for metric in info.describe():
                wallets_gauge.labels(metric["walletName"], metric["walletAddress"], metric["tokenName"], metric["tokenAddress"], "balance").set(metric["balance"])
                try:
                    wallets_gauge.labels(metric["walletName"], metric["walletAddress"], metric["tokenName"], metric["tokenAddress"], "usdBalance").set(metric["balance"] * usd_prices_by_token_address[address])
                except:
                    console.print(f"error calculating USD token balance")


        ### Setts
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


