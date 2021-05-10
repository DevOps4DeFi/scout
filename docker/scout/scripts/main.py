import datetime
import os
import re
import warnings

from brownie import chain, interface
from prometheus_client import Gauge, start_http_server
from web3 import Web3

from scripts.addresses import ADDRESSES_ETH, checksum_address_dict
from scripts.data import (
    get_badgertree_data,
    get_digg_data,
    get_json_request,
    get_lp_data,
    get_sett_data,
    get_token_interfaces,
    get_wallet_balances_by_token,
)
from scripts.logconf import console, log

warnings.simplefilter("ignore")

PROMETHEUS_PORT = 8801

ETHNODEURL = os.environ["ETHNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))

NATIVE_TOKENS = ["BADGER", "DIGG", "bBADGER", "bDIGG"]

# get all addresses
ADDRESSES = checksum_address_dict(ADDRESSES_ETH)

badger_wallets = ADDRESSES["badger_wallets"]
treasury_tokens = ADDRESSES["treasury_tokens"]
lp_tokens = ADDRESSES["lp_tokens"]
crv_pools = ADDRESSES["crv_pools"]
sett_vaults = ADDRESSES["sett_vaults"]
custodians = ADDRESSES["custodians"]
oracles = ADDRESSES["oracles"]

usd_prices_by_token_address = {}


def get_token_prices(treasury_tokens, token_csv, countertoken_csv):
    log.info("Fetching token prices from CoinGecko ...")
    token_prices = get_json_request(
        request_type="get",
        url=f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={token_csv}&vs_currencies={countertoken_csv}",
    )
    return token_prices


def update_price_gauge(
    coingecko_price_gauge, token_prices, token_name, token_address, countertoken_csv
):
    lp_prefixes = ("uni", "slp", "crv", "cake")

    try:
        if not token_name.startswith(lp_prefixes):
            log.info(
                f"Processing CoinGecko price for [bold]{token_name}: {token_address} ..."
            )

            price = token_prices[token_address.lower()]

            for countertoken in countertoken_csv.split(","):
                coingecko_price_gauge.labels(
                    "ETH"
                    if token_name == "WETH"
                    else "BNB"
                    if token_name == "WBNB"
                    else token_name,
                    countertoken,
                    token_address,
                ).set(price[countertoken])

            usd_prices_by_token_address[token_address] = price["usd"]
        else:
            log.info(
                f"Skipping CoinGecko price for [bold]{token_name}: {token_address} ..."
            )
    except Exception as e:
        log.warning(
            f"Error getting CoinGecko price for [bold]{token_name}: {token_address}"
        )
        log.debug(e)


def update_digg_gauge(digg_gauge, digg_prices, slpWbtcDigg, uniWbtcDigg):
    # process digg oracle price
    digg_oracle_price = digg_prices.describe()
    for param, value in digg_oracle_price.items():
        log.info(
            f"Processing Oracle param [bold]{param}[/] for [bold]DIGG: {digg_prices.oracle.address} ..."
        )
        digg_gauge.labels(param).set(value)

    # process digg AMM prices
    log.info(f"Processing SushiSwap price for [bold]DIGG: {uniWbtcDigg.address} ...")
    digg_uni_price = (uniWbtcDigg.getReserves()[0] / 1e8) / (
        uniWbtcDigg.getReserves()[1] / 1e9
    )
    digg_gauge.labels("uniswap").set(digg_uni_price)

    log.info(f"Processing Uniswap price for [bold]DIGG: {slpWbtcDigg.address} ...")
    digg_sushi_price = (slpWbtcDigg.getReserves()[0] / 1e8) / (
        slpWbtcDigg.getReserves()[1] / 1e9
    )
    digg_gauge.labels("sushiswap").set(digg_sushi_price)


def update_lp_tokens_gauge(lp_tokens_gauge, lp_token, token_interfaces):
    lp_name = lp_token.name
    lp_address = lp_tokens[lp_name]

    log.info(f"Processing lpToken reserves for [bold]{lp_name}: {lp_address} ...")

    lp_info = lp_token.describe()
    lp_scale = 10 ** lp_info["decimals"]
    lp_supply = lp_info["totalSupply"]

    token0_address = lp_info["token0"]
    token1_address = lp_info["token1"]
    token0 = token_interfaces[token0_address]
    token1 = token_interfaces[token1_address]
    token0_reserve = lp_info["token0_reserve"]
    token1_reserve = lp_info["token1_reserve"]
    token0_scale = 10 ** token0.decimals()
    token1_scale = 10 ** token1.decimals()

    lp_tokens_gauge.labels(lp_name, f"{token0.symbol()}_supply", lp_address).set(
        token0_reserve / token0_scale
    )
    lp_tokens_gauge.labels(lp_name, f"{token1.symbol()}_supply", lp_address).set(
        token1_reserve / token1_scale
    )
    lp_tokens_gauge.labels(lp_name, "totalLpTokenSupply", lp_address).set(
        lp_supply / lp_scale
    )

    try:
        price = (
            ((token1_reserve / token1_scale) / (lp_supply / lp_scale))
            * usd_prices_by_token_address[token1_address]
            * 2
        )
        usd_prices_by_token_address[lp_address] = price
        lp_tokens_gauge.labels(lp_name, "usdPricePerShare", lp_address).set(price)
    except Exception as e:
        log.warning(f"Error calculating USD price for lpToken [bold]{lp_name}")
        log.debug(e)


def update_crv_tokens_gauge(crv_tokens_gauge, pool_name, pool_address):
    log.info(f"Processing crvToken data for [bold]{pool_name}: {pool_address} ...")

    pool_token_name = pool_name
    pool_token_address = treasury_tokens[pool_token_name]

    wbtc_address = treasury_tokens["WBTC"]

    virtual_price = interface.CRVswap(pool_address).get_virtual_price() / 1e18
    usd_price = virtual_price * usd_prices_by_token_address[wbtc_address]

    crv_tokens_gauge.labels(pool_name, "pricePerShare", wbtc_address).set(virtual_price)
    crv_tokens_gauge.labels(pool_name, "usdPricePerShare", wbtc_address).set(usd_price)

    usd_prices_by_token_address[pool_token_address] = usd_price


def update_sett_gauge(sett_gauge, sett):
    sett_name = sett.name
    sett_address = sett_vaults[sett_name]
    sett_token_name = sett_name[1:]
    sett_token_address = treasury_tokens[re.sub("harvest", "", sett_token_name)]

    sett_info = sett.describe()

    log.info(f"Processing Sett data for [bold]{sett.name}: {sett_address} ...")

    for param, value in sett_info.items():
        sett_gauge.labels(sett_name, param, sett_address, sett_token_name).set(value)

    try:
        usd_prices_by_token_address[sett_address] = (
            sett_info["pricePerShare"] * usd_prices_by_token_address[sett_token_address]
        )
        sett_gauge.labels(sett_name, "usdBalance", sett_address, sett_token_name).set(
            usd_prices_by_token_address[sett_address] * sett_info["balance"]
        )
    except Exception as e:
        log.warning(f"Error calculating USD price for Sett [bold]{sett_name}")
        log.debug(e)


def update_wallets_gauge(
    wallets_gauge, wallet_balances_by_token, token_name, token_address
):
    log.info(f"Processing wallet balances for [bold]{token_name}: {token_address} ...")

    wallet_info = wallet_balances_by_token[token_address]
    for wallet in wallet_info.describe():
        (
            token_name,
            token_address,
            token_balance,
            wallet_name,
            wallet_address,
        ) = wallet.values()

        eth_balance = float(w3.fromWei(w3.eth.getBalance(wallet_address), "ether"))

        wallets_gauge.labels(
            wallet_name, wallet_address, token_name, token_address, "balance"
        ).set(token_balance)
        wallets_gauge.labels(wallet_name, wallet_address, "ETH", "None", "balance").set(
            eth_balance
        )

        try:
            wallets_gauge.labels(
                wallet_name, wallet_address, token_name, token_address, "usdBalance"
            ).set(token_balance * usd_prices_by_token_address[token_address])
            wallets_gauge.labels(
                wallet_name, wallet_address, "ETH", "none", "usdBalance"
            ).set(eth_balance * usd_prices_by_token_address[treasury_tokens["WETH"]])
        except Exception as e:
            log.warning(
                f"Error calculating USD balances for wallet [bold]{wallet_name}"
            )
            log.debug(e)


def update_xchain_bridge_gauge(
    xchain_bridge_gauge, custodian_name, custodian_address, token_interfaces
):
    log.info(
        f"Checking balances on bridge [bold]{custodian_name}: {custodian_address} ..."
    )

    for token_name in NATIVE_TOKENS:
        token_address = treasury_tokens[token_name]

        token_interface = token_interfaces[token_address]
        token_scale = 10 ** token_interface.decimals()
        token_balance = token_interface.balanceOf(custodian_address)

        xchain_bridge_gauge.labels("BSC", token_name, custodian_name, "balance").set(
            token_balance / token_scale
        )
        xchain_bridge_gauge.labels("BSC", token_name, custodian_name, "usdBalance").set(
            (token_balance / token_scale) * usd_prices_by_token_address[token_address]
        )


def update_rewards_gauge(rewards_gauge, badgertree, badger, digg):
    log.info(f"Calculating Badgertree reward holdings ...")

    badger_rewards = badger.balanceOf(badgertree.address) / 1e18
    digg_rewards = digg.balanceOf(badgertree.address) / 1e9

    rewards_gauge.labels("BADGER", treasury_tokens["BADGER"]).set(badger_rewards)
    rewards_gauge.labels("DIGG", treasury_tokens["DIGG"]).set(digg_rewards)


def update_cycle_gauge(cycle_gauge, last_cycle_unixtime):
    for param, value in last_cycle_unixtime.items():
        log.info(f"Processing Badgertree [bold]{param} ...")
        cycle_gauge.labels(param).set(value)


def main():
    # set up prometheus
    log.info(
        f"Starting Prometheus scout-collector server at http://localhost:{PROMETHEUS_PORT}"
    )

    block_gauge = Gauge(
        name="blocks",
        documentation="Info about blocks processed",
    )
    coingecko_price_gauge = Gauge(
        name="coingecko_prices",
        documentation="Token price data from Coingecko",
        labelnames=["token", "countercurrency", "tokenAddress"],
    )
    digg_gauge = Gauge(
        name="digg_price",
        documentation="Digg price data from oracle and AMMs",
        labelnames=["value"],
    )
    lp_tokens_gauge = Gauge(
        name="lptokens",
        documentation="LP token data",
        labelnames=["token", "param", "tokenAddress"],
    )
    crv_tokens_gauge = Gauge(
        name="crvtokens",
        documentation="CRV token data",
        labelnames=["token", "param", "tokenAddress"],
    )
    sett_gauge = Gauge(
        name="sett",
        documentation="Badger Sett vaults data",
        labelnames=["sett", "param", "tokenAddress", "token"],
    )
    wallets_gauge = Gauge(
        name="wallets",
        documentation="Watched wallet balances",
        labelnames=["walletName", "walletAddress", "token", "tokenAddress", "param"],
    )
    xchain_bridge_gauge = Gauge(
        name="xchainBridge",
        documentation="Info about tokens in custody",
        labelnames=["chain", "token", "bridge", "param"],
    )
    rewards_gauge = Gauge(
        name="rewards",
        documentation="Badgertree reward holdings",
        labelnames=["token", "tokenAddress"],
    )
    cycle_gauge = Gauge(
        name="badgertree",
        documentation="Badgertree reward timestamp",
        labelnames=["lastCycleUnixtime"],
    )

    start_http_server(PROMETHEUS_PORT)

    # get all data
    num_treasury_tokens = len(treasury_tokens)
    str_treasury_tokens = "".join(
        [
            f"\n\t[bold]{token_name}: {token_address}"
            for token_name, token_address in treasury_tokens.items()
        ]
    )

    log.info(f"Loading ERC20 interfaces for treasury tokens ... {str_treasury_tokens}")
    token_interfaces = get_token_interfaces(treasury_tokens)
    badger = token_interfaces[treasury_tokens["BADGER"]]
    digg = token_interfaces[treasury_tokens["DIGG"]]
    wbtc = token_interfaces[treasury_tokens["WBTC"]]

    wallet_balances_by_token = get_wallet_balances_by_token(
        badger_wallets, treasury_tokens
    )

    lp_data = get_lp_data(lp_tokens)

    sett_data = get_sett_data(sett_vaults)

    digg_prices = get_digg_data(oracles["oracle"], oracles["oracle_provider"])

    slpWbtcDigg = interface.Pair(lp_tokens["slpWbtcDigg"])
    uniWbtcDigg = interface.Pair(lp_tokens["uniWbtcDigg"])

    badgertree = interface.Badgertree(badger_wallets["badgertree"])
    badgertree_cycles = get_badgertree_data(badgertree)

    # coingecko price query variables
    token_csv = ",".join(treasury_tokens.values())
    countertoken_csv = "usd"

    # scan new blocks and update gauges
    for step, block in enumerate(chain.new_blocks(height_buffer=1)):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        console.print()
        console.rule(
            title=f"[green]{timestamp} step number {step}, block number {block.number}"
        )

        block_gauge.set(block.number)

        # process token prices
        token_prices = get_token_prices(treasury_tokens, token_csv, countertoken_csv)
        for token_name, token_address in treasury_tokens.items():
            update_price_gauge(
                coingecko_price_gauge,
                token_prices,
                token_name,
                token_address,
                countertoken_csv,
            )

        # process digg oracle prices
        update_digg_gauge(digg_gauge, digg_prices, slpWbtcDigg, uniWbtcDigg)

        # process lp data
        for lp_token in lp_data:
            update_lp_tokens_gauge(lp_tokens_gauge, lp_token, token_interfaces)

        # process curve pool data
        for pool_name, pool_address in crv_pools.items():
            update_crv_tokens_gauge(crv_tokens_gauge, pool_name, pool_address)

        # process sett data
        for sett in sett_data:
            update_sett_gauge(sett_gauge, sett)

        # process wallet balances for *one* treasury token
        token_name, token_address = list(treasury_tokens.items())[
            step % num_treasury_tokens
        ]
        update_wallets_gauge(
            wallets_gauge, wallet_balances_by_token, token_name, token_address
        )

        # process bridged tokens
        for custodian_name, custodian_address in custodians.items():
            update_xchain_bridge_gauge(
                xchain_bridge_gauge, custodian_name, custodian_address, token_interfaces
            )

        # process rewards balances
        update_rewards_gauge(rewards_gauge, badgertree, badger, digg)

        # process badgertree cycles
        last_cycle_unixtime = badgertree_cycles.describe()
        update_cycle_gauge(cycle_gauge, last_cycle_unixtime)
