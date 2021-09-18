import datetime
import os
import re
import warnings

from brownie import chain, interface
from prometheus_client import Gauge, start_http_server
from web3 import Web3

from scripts.addresses import ADDRESSES_BSC, checksum_address_dict
from scripts.data import (
    get_lp_data,
    get_sett_data,
    get_token_interfaces,
    get_wallet_balances_by_token,
)
from scripts.logconf import console, log
from scripts.main import (
    get_token_prices,
    update_lp_tokens_gauge,
    update_price_gauge,
    update_sett_gauge,
    update_wallets_gauge,
)

warnings.simplefilter("ignore")

PROMETHEUS_PORT = 8801
PROMETHEUS_PORT_FORWARDED = 8803

NETWORK = "BSC"
ETHNODEURL = os.environ["ETHNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))


NATIVE_TOKENS = ["bBADGER", "bDIGG", "BADGER"]

# get all addresses
ADDRESSES = checksum_address_dict(ADDRESSES_BSC)

badger_wallets = ADDRESSES["badger_wallets"]
treasury_tokens = ADDRESSES["treasury_tokens"]
lp_tokens = ADDRESSES["lp_tokens"]
sett_vaults = ADDRESSES["sett_vaults"]
coingecko_tokens = ADDRESSES["coingecko_tokens"]

usd_prices_by_token_address = {}


def update_bridge_gauge(bridge_gauge, token_name, token_interfaces, treasury_tokens):
    token_address = treasury_tokens[token_name]

    log.debug(
        f"Checking supply of bridged native token [bold]{token_name}: {token_address}"
    )

    token_interface = token_interfaces[token_address]
    token_supply = token_interface.totalSupply()
    token_scale = 10 ** token_interface.decimals()

    bridge_gauge.labels(token_name, "multiswap", "totalSupply").set(
        token_supply / token_scale
    )


def main():
    # set up prometheus
    log.info(
        f"Starting Prometheus bsc-collector server at http://localhost:{PROMETHEUS_PORT_FORWARDED}"
    )

    block_gauge = Gauge(
        name="bsc_blocks",
        documentation="Info about blocks processed",
    )
    coingecko_price_gauge = Gauge(
        name="bsc_coingecko",
        documentation="Token price data from Coingecko",
        lablnames=["token", "countercurrency", "tokenAddress"],
    )
    lp_tokens_gauge = Gauge(
        name="bsc_lp",
        documentation="LP token data",
        labelnames=["token", "param", "tokenAddress"],
    )
    sett_gauge = Gauge(
        name="bsc_sett",
        documentation="Badger Sett vaults data",
        labelnames=["sett", "param", "tokenAddress", "token"],
    )
    wallets_gauge = Gauge(
        name="bsc_wallets",
        documentation="Watched wallet balances",
        labelnames=["walletName", "walletAddress", "token", "tokenAddress", "param"],
    )
    bridge_gauge = Gauge(
        name="bsc_xtokens",
        documentation="Native tokens on bsc",
        labelnames=["token", "bridge", "param"],
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

    lp_data = get_lp_data(lp_tokens)

    sett_data = get_sett_data(sett_vaults)

    wallet_balances_by_token = get_wallet_balances_by_token(
        badger_wallets, treasury_tokens
    )

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
                coingecko_price_gauge,
                treasury_tokens,
                token_prices,
                token_name,
                token_address,
                countertoken_csv,
                NETWORK,
            )

        # process lp data
        for lp_token in lp_data:
            update_lp_tokens_gauge(
                lp_tokens_gauge, lp_tokens, lp_token, token_interfaces
            )

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
            NETWORK,
        )

        # process bridged tokens
        for token_name in NATIVE_TOKENS:
            update_bridge_gauge(
                bridge_gauge, token_name, token_interfaces, treasury_tokens
            )
