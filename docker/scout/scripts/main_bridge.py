#!/usr/local/bin/python3
import asyncio
import logging
import os
import warnings

from brownie.network.state import Chain
from prometheus_client import Counter, Gauge, start_http_server
from rich.console import Console
from web3 import Web3

from scripts.events import process_event

ETHNODEURL = os.environ["ETHNODEURL"]
PROMETHEUS_PORT = 8801

ADDRS = {
    "zero_addr": "0x0000000000000000000000000000000000000000",
    "badger_multisig": "0xB65cef03b9B89f99517643226d76e286ee999e77",
    "badger_bridge_team": "0xE95b56685327C9caf83C3e6F0A54b8D9708f32c4",
    "bridge_v1": "0xcB5c2B0FE765069708f17376981C9aFE56Fed339",
    "bridge_v2": "0xb6ea1d3fb9100a2Cf166FEBe11f24367b5FCD24A",
    "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
    "renBTC": "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",
    "renvm_darknodes_fee": "0xE33417797d6b8Aec9171d0d6516E88002fbe23E7",
    "unk_curve_1": "0x2393c368c70b42f055a4932a3fbec2ac9c548011",
    "unk_curve_2": "0xfae8bd34190615f3388f38191dc332b44c53e10b",
}
ADDRS = {label: Web3.toChecksumAddress(addr) for label, addr in ADDRS.items()}

BLOCK_START = 12285143
POLL_INTERVAL = 10

warnings.simplefilter("ignore")
console = Console()

w3 = Web3(Web3.HTTPProvider(ETHNODEURL))


def process_prior_events(chain, filters, block_gauge, token_flow_counter, fees_counter):
    """Process all prior Mint/Burn calls, from contract creation block to current block."""
    for f in filters:
        for event in f.get_all_entries():
            process_event(chain, event, block_gauge, token_flow_counter, fees_counter)


def listen_new_events(
    chain, filters, block_gauge, token_flow_counter, fees_counter, poll_interval
):
    """Listen for and process new Mint/Burn txs on latest blocks.

    https://web3py.readthedocs.io/en/latest/filters.html#getting-events-without-setting-up-a-filter
    """

    async def count_loop(f, poll_interval):
        while True:
            for event in f.get_new_entries():
                process_event(
                    chain, event, block_gauge, token_flow_counter, fees_counter
                )
            await asyncio.sleep(poll_interval)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(*[count_loop(f, poll_interval) for f in filters])
        )
    finally:
        loop.close()


def main():
    # set up prometheus
    block_gauge = Gauge(
        name="block_info", documentation="block_info", labelnames=["info"]
    )

    token_flow_counter = Counter(
        name="token_flow",
        documentation="token,event,direction",
        labelnames=["token", "event", "direction"],
    )
    fees_counter = Counter(name="fees", documentation="entity", labelnames=["entity"],)

    start_http_server(PROMETHEUS_PORT)

    console.log(
        f"Initialized Prometheus metrics server at http://localhost:{PROMETHEUS_PORT}"
    )

    # set up event filters
    # filter bridge contract events
    bridge_abi = open("interfaces/Bridge.json", "r").read()
    bridge = w3.eth.contract(address=ADDRS["bridge_v2"], abi=bridge_abi)
    console.log(f"Read Badger BTC Bridge contract at address {ADDRS['bridge_v2']}")
    filters = [
        bridge.events.Mint.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
        bridge.events.Burn.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
    ]

    # watch events
    chain = Chain()
    console.log(
        f"Processing prior events from block {BLOCK_START} to {w3.eth.blockNumber}"
    )
    process_prior_events(chain, filters, block_gauge, token_flow_counter, fees_counter)

    console.log("Listening for new events in latest blocks...")
    listen_new_events(
        chain, filters, block_gauge, token_flow_counter, fees_counter, POLL_INTERVAL
    )
