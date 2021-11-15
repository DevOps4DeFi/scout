import datetime
import os
import re
import warnings

from brownie import chain
from brownie import interface  # noqa
from prometheus_client import Gauge
from prometheus_client import start_http_server  # noqa
from web3 import Web3

from scripts.addresses import ADDRESSES_ARBITRUM
from scripts.addresses import checksum_address_dict
from scripts.data import get_badgertree_data
from scripts.data import get_json_request
from scripts.data import get_lp_data
from scripts.data import get_sett_data
from scripts.data import get_token_by_address
from scripts.data import get_token_interfaces
from scripts.data import get_wallet_balances_by_token
from scripts.logconf import console
from scripts.logconf import log

warnings.simplefilter("ignore")

PROMETHEUS_PORT = 8801

NETWORK = "ARBITRUM"
ETHNODEURL = os.environ["ARBNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))

NATIVE_TOKENS = ["BADGER", "DIGG", "bBADGER", "bDIGG"]

# get all addresses
ADDRESSES = checksum_address_dict(ADDRESSES_ARBITRUM)
badger_wallets = ADDRESSES["badger_wallets"]
treasury_tokens = ADDRESSES["treasury_tokens"]
lp_tokens = ADDRESSES["lp_tokens"]
crv_pools = ADDRESSES["crv_pools"]
crv_3_pools = ADDRESSES["crv_3_pools"]
sett_vaults = ADDRESSES["sett_vaults"]
coingecko_tokens = ADDRESSES["coingecko_tokens"]


usd_prices_by_token_address = {}


def get_token_prices(token_csv, countertoken_csv, network):
    log.info("Fetching token prices from CoinGecko ...")

    if network == "ETH":
        # fetch prices by token_address on ETH
        url = (f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?"
               f"contract_addresses={token_csv}&vs_currencies={countertoken_csv}")
    else:
        # fetch prices by coingecko_name on BSC
        url = (f"https://api.coingecko.com/api/v3/simple/price"
               f"?ids={token_csv}&vs_currencies={countertoken_csv}")

    token_prices = get_json_request(request_type="get", url=url)
    return token_prices


def update_price_gauge(
    treasury_tokens,
    token_prices,
    token_name,
    token_address,
    network,
):
    lp_prefixes = ("uni", "slp", "crv", "cake")

    # BSC token_names are coingecko_names, so lookup token symbol from treasury_tokens
    fetched_name = get_token_by_address(treasury_tokens, token_address)

    try:
        if not fetched_name.startswith(lp_prefixes):
            log.info(
                f"Processing CoinGecko price for [bold]{fetched_name}: {token_address} ..."
            )
            if network == "ETH":
                price_key = token_address.lower()
            else:
                price_key = token_name

            price = token_prices[price_key]
#               We already have coingecko pricing on eth.
#            for countertoken in countertoken_csv.split(","):
#              coingecko_price_gauge.labels(
#                    "ETH" if fetched_name == "WETH"
#                    else fetched_name,
#                    token_address,
#                    countertoken,
#                ).set(price[countertoken])

            usd_prices_by_token_address[token_address] = price["usd"]
        else:
            log.info(
                f"Skipping CoinGecko price for [bold]{fetched_name}: {token_address} ..."
            )
    except Exception as e:
        log.warning(
            f"Error getting CoinGecko price for [bold]{fetched_name}: {token_address}"
        )
        log.warning(e)
        log.warning(token_prices, token_name, fetched_name, token_address)


def update_lp_tokens_gauge(lp_tokens_gauge, lp_tokens, lp_token, token_interfaces):
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

    lp_tokens_gauge.labels(lp_name, lp_address, f"{token0.symbol()}_supply").set(
        token0_reserve / token0_scale
    )
    lp_tokens_gauge.labels(lp_name, lp_address, f"{token1.symbol()}_supply").set(
        token1_reserve / token1_scale
    )
    lp_tokens_gauge.labels(lp_name, lp_address, "totalLpTokenSupply").set(
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
        log.warning(e)


def update_crv_3_tokens_guage(guage, pool_name, pool_address):
    log.info(f"Processing crvToken data for [bold]{pool_name}...")
    pool_token_interface = interface.ERC20(treasury_tokens[pool_name])
    pool = interface.tricryptoPool(pool_address)
    pool_divisor = 10 ** pool_token_interface.decimals()
    total_supply = pool_token_interface.totalSupply() / pool_divisor
    balance = pool_token_interface.balance() / pool_divisor

    tokenlist = []
    usd_balance = 0
    for i in range(3):
        tokenlist.append(interface.ERC20(pool.coins(i)))
    for tokenInterface in tokenlist:
        guage.labels(
            pool_name, pool_token_interface.address,
            f"{tokenInterface.symbol()}_balance").set(
            tokenInterface.balanceOf(pool_address) / 10 ** tokenInterface.decimals()
        )
        usd_balance += (
                tokenInterface.balanceOf(pool_address) / 10 ** tokenInterface.decimals()
                * usd_prices_by_token_address[tokenInterface.address]
        )
    usd_price = (usd_balance / total_supply)
    guage.labels(pool_name, pool_token_interface.address, "usdPricePerShare").set(usd_price)
    guage.labels(pool_name, pool_token_interface.address, "totalSupply").set(total_supply)
    guage.labels(pool_name, pool_token_interface.address, "balance").set(balance)
    usd_prices_by_token_address[pool_token_interface.address] = usd_price
    for tokenInterface in tokenlist:
        guage.labels(
            pool_name, pool_token_interface.address, f"{tokenInterface.symbol()}_per_share"
        ).set(
            (tokenInterface.balanceOf(pool_address) / 10 ** tokenInterface.decimals()
             ) / (pool_token_interface.totalSupply() / pool_divisor)
        )


def update_crv_tokens_gauge(crv_tokens_gauge, pool_name, pool_address):
    log.info(f"Processing crvToken data for [bold]{pool_name}: {pool_address} ...")

    pool_token_name = pool_name
    pool_token_address = treasury_tokens[pool_token_name]

    wbtc_address = treasury_tokens["WBTC"]

    virtual_price = interface.CRVswap(pool_address).get_virtual_price() / 1e18
    usd_price = virtual_price * usd_prices_by_token_address[wbtc_address]

    crv_tokens_gauge.labels(pool_name, wbtc_address, "pricePerShare").set(virtual_price)
    crv_tokens_gauge.labels(pool_name, wbtc_address, "usdPricePerShare").set(usd_price)

    usd_prices_by_token_address[pool_token_address] = usd_price


def update_sett_gauge(sett_gauge, sett, sett_vaults, treasury_tokens):
    sett_name = sett.name
    sett_address = sett_vaults[sett_name]
    sett_token_name = sett_name[1:]
    sett_token_address = treasury_tokens[re.sub("harvest", "", sett_token_name)]

    sett_info = sett.describe()

    log.info(f"Processing Sett data for [bold]{sett_name}: {sett_address} ...")

    for param, value in sett_info.items():
        sett_gauge.labels(sett_name, sett_address, sett_token_name, param).set(value)

    try:
        usd_prices_by_token_address[sett_address] = (
            sett_info["pricePerShare"] * usd_prices_by_token_address[sett_token_address]
        )
        sett_gauge.labels(sett_name, sett_address, sett_token_name, "usdBalance").set(
            usd_prices_by_token_address[sett_address] * sett_info["balance"]
        )
    except Exception as e:
        log.warning(f"Error calculating USD price for Sett [bold]{sett_name}")
        log.warning(e)


def update_wallets_gauge(
    wallets_gauge,
    wallet_balances_by_token,
    token_name,
    token_address,
    treasury_tokens,
    step: int,
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
        is_10th_step = step % 10 == 0
        if token_balance == 0.0 and not is_10th_step:
            log.info(f"Skip checking balance for {token_name} "
                     f"in {wallet_name} wallet with step {step}")
            continue

        eth_name = "ETH"
        eth_address = treasury_tokens[f"W{eth_name}"]
        eth_balance = float(w3.fromWei(w3.eth.getBalance(wallet_address), "ether"))

        wallets_gauge.labels(
            wallet_name, wallet_address, token_name, token_address, "balance"
        ).set(token_balance)
        wallets_gauge.labels(
            wallet_name, wallet_address, eth_name, "None", "balance"
        ).set(eth_balance)

        try:
            wallets_gauge.labels(
                wallet_name, wallet_address, token_name, token_address, "usdBalance"
            ).set(token_balance * usd_prices_by_token_address[token_address])
            wallets_gauge.labels(
                wallet_name, wallet_address, eth_name, "none", "usdBalance"
            ).set(eth_balance * usd_prices_by_token_address[eth_address])
        except Exception as e:
            log.warning(
                f"Error calculating USD balances for wallet [bold]{wallet_name}"
            )
            log.info(e)


def update_rewards_gauge(rewards_gauge, badgertree, badger, treasury_tokens):
    log.info(f"Calculating Badgertree reward holdings ...")

    badger_rewards = badger.balanceOf(badgertree.address) / 1e18

    rewards_gauge.labels("BADGER", treasury_tokens["BADGER"]).set(badger_rewards)


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
        labelnames=["token", "tokenAddress", "countercurrency"],
    )
    lp_tokens_gauge = Gauge(
        name="lptokens",
        documentation="LP token data",
        labelnames=["token", "tokenAddress", "param"],
    )
    crv_tokens_gauge = Gauge(
        name="crvtokens",
        documentation="CRV token data",
        labelnames=["token", "tokenAddress", "param"],
    )
    crv_nonbtc_tokens_gauge = Gauge(
        name="nonbtcCrvTokens",
        documentation="CRV Tricrypto data",
        labelnames=["token", "tokenAddress", "param"],
    )
    sett_gauge = Gauge(
        name="sett",
        documentation="Badger Sett vaults data",
        labelnames=["sett", "tokenAddress", "token", "param"],
    )
    wallets_gauge = Gauge(
        name="wallets",
        documentation="Watched wallet balances",
        labelnames=["walletName", "walletAddress", "token", "tokenAddress", "param"],
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

    wallet_balances_by_token = get_wallet_balances_by_token(
        badger_wallets, treasury_tokens
    )

    lp_data = get_lp_data(lp_tokens)

    sett_data = get_sett_data(sett_vaults)

    badgertree = interface.Badgertree(badger_wallets["badgertree"])
    badgertree_cycles = get_badgertree_data(badgertree)

    # coingecko price query variables
    token_csv = ",".join(coingecko_tokens.keys())
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
        token_prices = get_token_prices(token_csv, countertoken_csv, NETWORK)
        for token_name, token_address in coingecko_tokens.items():
            update_price_gauge(
                treasury_tokens,
                token_prices,
                token_name,
                token_address,
                NETWORK,
            )

        # process lp data
        for lp_token in lp_data:
            update_lp_tokens_gauge(
                lp_tokens_gauge, lp_tokens, lp_token, token_interfaces
            )

        # process curve pool data
        for pool_name, pool_address in crv_pools.items():
            update_crv_tokens_gauge(crv_tokens_gauge, pool_name, pool_address)

        # process 3crv data data
        for pool_name, pool_address in crv_3_pools.items():
            update_crv_3_tokens_guage(crv_nonbtc_tokens_gauge, pool_name, pool_address)

        # process sett data
        for sett in sett_data:
            update_sett_gauge(sett_gauge, sett, sett_vaults, treasury_tokens)

        # process wallet balances for *one* treasury token
        token_name, token_address = list(treasury_tokens.items())[
            step % num_treasury_tokens
        ]
        update_wallets_gauge(
            wallets_gauge,
            wallet_balances_by_token,
            token_name,
            token_address,
            treasury_tokens,
            step,
        )

        # process rewards balances
        update_rewards_gauge(rewards_gauge, badgertree, badger, treasury_tokens)

        # process badgertree cycles
        last_cycle_unixtime = badgertree_cycles.describe()
        update_cycle_gauge(cycle_gauge, last_cycle_unixtime)
