import asyncio
import datetime
import json
import os
import sys
import time
import warnings

from brownie.network.state import Chain
from prometheus_client import Counter, Gauge, start_http_server
from web3 import Web3
from web3.datastructures import AttributeDict
from web3.middleware import local_filter_middleware

from scripts.addresses import ADDRESSES_BRIDGE, checksum_address_dict
from scripts.events import process_event
from scripts.logconf import log

PROMETHEUS_PORT = 8801
PROMETHEUS_PORT_FORWARDED = 8802

ETHNODEURL = os.environ["ETHNODEURL"]
ALCHEMYURL = os.environ["ALCHEMYURL"]

ADDRESSES = checksum_address_dict(ADDRESSES_BRIDGE)

BLOCK_START = 12297120
# BLOCK_START = 12500000
POLL_INTERVAL = 150

warnings.simplefilter("ignore")

w3 = Web3(Web3.HTTPProvider(ALCHEMYURL))
# w3.middleware_onion.add(local_filter_middleware)


def process_prior_events(chain, bridge, block_gauge, token_flow_counter, fees_counter):
    """Process all prior Mint/Burn calls, from contract creation block to current block."""
    log.info(
        f"Processing prior events from block {BLOCK_START} to {w3.eth.blockNumber}"
    )

    filters = [
        bridge.events.Burn.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
        bridge.events.Mint.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
    ]
    for f in filters:
        try:
            # potential issue with dropped filters?
            # see: https://github.com/ethereum/web3.py/issues/1485#issuecomment-551274660
            # see: https://github.com/ethereum/web3.py/issues/551
            for event in f.get_all_entries():
                process_event(
                    chain, event, block_gauge, token_flow_counter, fees_counter
                )
        except Exception as e:
            log.info(e)
            log.info(f)
            log.info(f.filter_params)


def listen_new_events(
    chain, bridge, block_gauge, token_flow_counter, fees_counter, poll_interval
):
    """Listen for and process new Mint/Burn txs on latest blocks.
    https://web3py.readthedocs.io/en/latest/filters.html#getting-events-without-setting-up-a-filter
    """
    log.info("Listening for new events in latest blocks...")

    filters = [
        bridge.events.Burn.createFilter(fromBlock="latest"),
        bridge.events.Mint.createFilter(fromBlock="latest"),
    ]

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
    log.info(
        f"Starting Prometheus events server at http://localhost:{PROMETHEUS_PORT_FORWARDED}"
    )

    block_gauge = Gauge(
        name="block_info", documentation="block_info", labelnames=["info"]
    )

    token_flow_counter = Counter(
        name="bridge_token_flow",
        documentation="token,event,direction",
        labelnames=["token", "event", "direction"],
    )
    fees_counter = Counter(
        name="bridge_fees",
        documentation="entity",
        labelnames=["entity"],
    )

    start_http_server(PROMETHEUS_PORT)

    # set up event filters
    # filter bridge contract events
    log.info(f"Reading Badger BTC Bridge contract at address {ADDRESSES['bridge_v2']}")
    bridge_abi = json.load(open("interfaces/Bridge.json", "r"))
    bridge = w3.eth.contract(address=ADDRESSES["bridge_v2"], abi=bridge_abi)

    # watch events
    chain = Chain()
    process_prior_events(chain, bridge, block_gauge, token_flow_counter, fees_counter)

    listen_new_events(
        chain, bridge, block_gauge, token_flow_counter, fees_counter, POLL_INTERVAL
    )
