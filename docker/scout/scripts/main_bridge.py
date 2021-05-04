#!/usr/local/bin/python3
import datetime
import json
import logging
import os
import sys
import time
import warnings

from brownie.network.state import Chain
from prometheus_client import Counter, Gauge, start_http_server
from rich.console import Console
from rich.logging import RichHandler
from tqdm import tqdm
from web3 import Web3
from web3.datastructures import AttributeDict

from scripts.events import process_transaction
from scripts.scanner import EventScanner, EventScannerState

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
CHAIN_REORG_SAFETY_BLOCKS = 10
POLL_INTERVAL = 60

warnings.simplefilter("ignore")
console = Console()
# logging.basicConfig(
#     level="INFO",
#     format="%(message)s",
#     datefmt="[%X]",
#     handlers=[RichHandler(rich_tracebacks=True)],
# )
# logger = logging.getLogger("rich")

provider = Web3.HTTPProvider(ETHNODEURL)
# remove the default JSON-RPC retry middleware to enable eth_getLogs block range throttling
provider.middlewares.clear()
w3 = Web3(provider)


class BridgeScannerState(EventScannerState):
    """Store the state of scanned blocks and all events.

    All state is an in-memory dict.
    Simple load/store massive JSON on start up.

    Adapted from: https://web3py.readthedocs.io/en/stable/examples.html?highlight=newfilter
    """

    def __init__(self):
        self.state = None
        self.fname = "bridge-scanner_state.json"
        self.last_save = 0

    def reset(self):
        """Create initial state of nothing scanned."""
        self.state = {"last_scanned_block": 0, "blocks": {}}

    def restore(self):
        """Restore the last scan state from a file"""
        try:
            self.state = json.load(open(self.fname, "rt"))
            console.log(
                f"Restored the state, previously blocks up to block {self.state['last_scanned_block']} have been scanned"
            )
        except (IOError, json.decoder.JSONDecodeError):
            console.log("State JSON not found, starting from scratch")
            self.reset()

    def save(self):
        """Save everything we have scanned so far in a file."""
        with open(self.fname, "wt") as f:
            json.dump(self.state, f)
        self.last_save = time.time()

    def get_last_scanned_block(self):
        """The number of the last block we have stored."""
        return self.state["last_scanned_block"]

    def delete_data(self, since_block):
        """Remove potentially reorganised blocks from the scan data."""
        for block_num in range(since_block, self.get_last_scanned_block()):
            if block_num in self.state["blocks"]:
                del self.state["blocks"][block_num]

    def start_chunk(self, block_number, chunk_size):
        pass

    def end_chunk(self, block_number):
        """Save at the end of each block, so we can resume in the case of a crash or CTRL+C"""
        # next time the scanner is started we will resume from this block
        self.state["last_scanned_block"] = block_number

        # save the database file every minute
        if time.time() - self.last_save > 60:
            self.save()

        # ---------------------------------------------------------
        #  PROCESS TRANSACTION TRANSFER EVENTS AND UPDATE COUNTERS
        # ---------------------------------------------------------

    def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> str:
        """Record an event in the JSON database."""
        # events are keyed by their transaction hash and log index
        # one transaction may contain multiple events and each one of those gets their own log index

        # event_name = event.event
        # log_index = event.logIndex  # log index within the block
        # transaction_index = event.transactionIndex  # transaction index within the block
        tx_hash = event.transactionHash.hex()  # transaction hash
        block_number = event.blockNumber

        # save transaction hash only; will look up tx and tx events separately
        # create empty dict as the block that contains all transactions by txhash
        if block_number not in self.state["blocks"]:
            self.state["blocks"][block_number] = {}

        # dummy var so store only unique hashes
        # issue with set() and list(set()) serializing as json
        self.state["blocks"][block_number][tx_hash] = ""

        # return a label that allows us to look up this event later if needed
        return f"{block_number}-{tx_hash}"


def run_scan(scanner, state, block_gauge, token_flow_counter, fees_counter):
    # discard last few blocks in case of chain reorgs
    scanner.delete_potentially_forked_block_data(
        state.get_last_scanned_block() - CHAIN_REORG_SAFETY_BLOCKS
    )

    # scan from last scanned block to latest block
    # min starting block is bridge contract creation block
    start_block = max(
        state.get_last_scanned_block() - CHAIN_REORG_SAFETY_BLOCKS, BLOCK_START
    )
    end_block = scanner.get_suggested_scan_end_block()

    console.log(
        f"Scanning for bridge contract transactions from block {start_block} to {end_block}"
    )

    # run the scan
    result, total_chunks_scanned = scanner.scan(start_block, end_block)

    state.save()

    # process new mint/burn transactions
    tx_hashes = []
    for block_number, hash_dict in state.state["blocks"].items():
        if int(block_number) >= start_block and int(block_number) <= end_block:
            tx_hashes.extend(list(hash_dict.keys()))

    console.log(f"Processing transaction events from {start_block} to {end_block}")
    for tx_hash in tx_hashes:
        process_transaction(tx_hash, block_gauge, token_flow_counter, fees_counter)
    console.log(
        f"Scanning and processing of blocks {start_block} to {end_block} complete."
    )
    console.log(
        f"Sleeping for {POLL_INTERVAL} seconds before starting next block chunks"
    )


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

    console.log(
        f"Initializing Prometheus metrics server at http://localhost:{PROMETHEUS_PORT}"
    )
    start_http_server(PROMETHEUS_PORT)

    # set up event filters
    # filter bridge contract events
    # bridge_abi = open("interfaces/Bridge.json", "r").read()
    # bridge = w3.eth.contract(address=ADDRS["bridge_v2"], abi=bridge_abi)
    # console.log(f"Read Badger BTC Bridge contract at address {ADDRS['bridge_v2']}")
    # filters = [
    #     bridge.events.Mint.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
    #     bridge.events.Burn.createFilter(fromBlock=BLOCK_START, toBlock="latest"),
    # ]

    # watch events
    # chain = Chain()
    # console.log(
    #     f"Processing prior events from block {BLOCK_START} to {w3.eth.blockNumber}"
    # )
    # process_prior_events(chain, filters, block_gauge, token_flow_counter, fees_counter)

    # console.log("Listening for new events in latest blocks...")
    # listen_new_events(
    #     chain, filters, block_gauge, token_flow_counter, fees_counter, POLL_INTERVAL
    # )

    # set up scanner and scanner state
    # scan all blocks for Mint/Burn events with `eth_getLog`
    # works with nodes where `eth_newFilter` is not supported

    # erc20_abi = json.loads("interfaces/ERC20.json")
    # erc20 = web3.eth.contract(abi=abi)
    # wbtc = w3.eth.contract(address=ADDRS["WBTC"], abi=erc20_abi)
    # renbtc = w3.eth.contract(address=ADDRS["renBTC"], abi=erc20_abi)

    console.log(f"Reading Badger BTC Bridge contract at address {ADDRS['bridge_v2']}")
    bridge_abi = json.load(open("interfaces/Bridge.json", "r"))
    bridge = w3.eth.contract(address=ADDRS["bridge_v2"], abi=bridge_abi)

    state = BridgeScannerState()
    state.restore()

    scanner = EventScanner(
        web3=w3,
        contract=bridge,
        state=state,
        events=[bridge.events.Mint, bridge.events.Burn],
        filters={},
        max_chunk_scan_size=10000,
    )

    while True:
        run_scan(scanner, state, block_gauge, token_flow_counter, fees_counter),
        time.sleep(POLL_INTERVAL)
