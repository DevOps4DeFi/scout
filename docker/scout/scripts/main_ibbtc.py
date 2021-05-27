import datetime
import json
import os
import sys
import time
import warnings

from brownie.exceptions import EventLookupError
from brownie.network.state import Chain
from eth_abi.codec import ABICodec
from prometheus_client import Counter, Gauge, start_http_server
from web3 import Web3
from web3._utils.events import get_event_data
from web3.datastructures import AttributeDict
from web3.exceptions import MismatchedABI

from scripts.addresses import ADDRESSES_IBBTC, checksum_address_dict
from scripts.logconf import log as logger
from scripts.main_bridge import BridgeScannerState
from scripts.scanner import EventScanner

PROMETHEUS_PORT = 8801
PROMETHEUS_PORT_FORWARDED = 8804

ETHNODEURL = os.environ["ETHNODEURL"]

ADDRESSES = checksum_address_dict(ADDRESSES_IBBTC)

BLOCK_START = 12388784
CHAIN_REORG_SAFETY_BLOCKS = 20
POLL_INTERVAL = 60

warnings.simplefilter("ignore")

provider = Web3.HTTPProvider(ETHNODEURL)
# remove the default JSON-RPC retry middleware to enable eth_getLogs block range throttling
provider.middlewares.clear()
w3 = Web3(provider)


class IbbtcScannerState(BridgeScannerState):
    def __init__(self):
        self.state = None
        self.fname = "ibbtc-scanner_state.json"
        self.last_save = 0


def process_transaction(web3, tx_hash, block_gauge, token_flow_counter, fees_counter):
    tx = web3.eth.getTransaction(tx_hash)
    tx_logs = web3.eth.getTransactionReceipt(tx_hash).logs

    block_number = tx.blockNumber
    block_timestamp = web3.eth.get_block(block_number)["timestamp"]

    erc20_abi = json.load(open("interfaces/ERC20.json", "r"))
    erc20 = web3.eth.contract(abi=erc20_abi)
    erc20_transfer_abi = erc20.events.Transfer._get_event_abi()

    transfers = {
        transfer: 0
        for transfer in [
            "ibBTC_minted",
            "ibBTC_burned",
            "bcrvRenBTC_sent",
            "bcrvRenBTC_received",
            "bcrvSBTC_sent",
            "bcrvSBTC_received",
            "bcrvTBTC_sent",
            "bcrvTBTC_received",
            "byvWBTC_sent",
            "byvWBTC_received",
            "fee_badger",
            "fee_defiDollar",
        ]
    }

    for log in tx_logs:
        try:
            event_data = get_event_data(web3.codec, erc20_transfer_abi, log)
            transfers = update_transfers(tx_hash, event_data, transfers)
        except MismatchedABI:  # not ERC20 transfer, so skip
            continue

    # update counters
    block_gauge.labels("block_number").set(block_number)
    block_gauge.labels("block_timestamp").set(block_timestamp)

    token_flow_counter.labels("ibBTC", "mint", "out").inc(transfers["ibBTC_minted"])
    token_flow_counter.labels("ibBTC", "burn", "in").inc(transfers["ibBTC_burned"])
    token_flow_counter.labels("bcrvRenBTC", "sent", "out").inc(
        transfers["bcrvRenBTC_sent"]
    )
    token_flow_counter.labels("bcrvRenBTC", "received", "in").inc(
        transfers["bcrvRenBTC_received"]
    )
    token_flow_counter.labels("bcrvSBTC", "sent", "out").inc(transfers["bcrvSBTC_sent"])
    token_flow_counter.labels("bcrvSBTC", "received", "in").inc(
        transfers["bcrvSBTC_received"]
    )
    token_flow_counter.labels("bcrvTBTC", "sent", "out").inc(transfers["bcrvTBTC_sent"])
    token_flow_counter.labels("bcrvTBTC", "received", "in").inc(
        transfers["bcrvTBTC_received"]
    )
    token_flow_counter.labels("byvWBTC", "sent", "out").inc(transfers["byvWBTC_sent"])
    token_flow_counter.labels("byvWBTC", "received", "in").inc(
        transfers["byvWBTC_received"]
    )

    fees_counter.labels("Badger DAO").inc(transfers["fee_badger"])
    fees_counter.labels("DefiDollar").inc(transfers["fee_defiDollar"])

    logger.info(
        f"Processed event: block timestamp {block_timestamp} block number {block_number}, hash {tx_hash}"
    )

    return transfers


def update_transfers(tx_hash, tx_transfer, tokens):
    token_addr = tx_transfer["address"]

    transfer_from = Web3.toChecksumAddress(tx_transfer["args"]["_from"])
    transfer_to = Web3.toChecksumAddress(tx_transfer["args"]["_to"])
    transfer_value = tx_transfer["args"]["_value"]

    if token_addr == ADDRESSES["ibBTC"] and transfer_from == ADDRESSES["zero"]:
        tokens["ibBTC_minted"] += transfer_value / 10 ** 18

    elif token_addr == ADDRESSES["ibBTC"] and transfer_to == ADDRESSES["zero"]:
        tokens["ibBTC_burned"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["bcrvRenBTC"]
        and transfer_from == ADDRESSES["badgerPeak"]
    ):
        tokens["bcrvRenBTC_sent"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["bcrvRenBTC"] and transfer_to == ADDRESSES["badgerPeak"]
    ):
        tokens["bcrvRenBTC_received"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["bcrvSBTC"] and transfer_from == ADDRESSES["badgerPeak"]
    ):
        tokens["bcrvSBTC_sent"] += transfer_value / 10 ** 18

    elif token_addr == ADDRESSES["bcrvSBTC"] and transfer_to == ADDRESSES["badgerPeak"]:
        tokens["bcrvSBTC_received"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["bcrvTBTC"] and transfer_from == ADDRESSES["badgerPeak"]
    ):
        tokens["bcrvTBTC_sent"] += transfer_value / 10 ** 18

    elif token_addr == ADDRESSES["bcrvTBTC"] and transfer_to == ADDRESSES["badgerPeak"]:
        tokens["bcrvTBTC_received"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["byvWBTC"] and transfer_from == ADDRESSES["byvWbtcPeak"]
    ):
        tokens["byvWBTC_sent"] += transfer_value / 10 ** 8

    elif token_addr == ADDRESSES["byvWBTC"] and transfer_to == ADDRESSES["byvWbtcPeak"]:
        tokens["byvWBTC_received"] += transfer_value / 10 ** 8

    elif (
        token_addr == ADDRESSES["ibBTC"]
        and transfer_from == ADDRESSES["feesink"]
        and transfer_to == ADDRESSES["badger_multisig"]
    ):
        tokens["fee_badger"] += transfer_value / 10 ** 18

    elif (
        token_addr == ADDRESSES["ibBTC"]
        and transfer_from == ADDRESSES["feesink"]
        and transfer_to == ADDRESSES["defiDollar_fees"]
    ):
        tokens["fee_defiDollar"] += transfer_value / 10 ** 18

    else:
        logger.debug(
            f"Transaction unmatched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        return tokens

    logger.debug(
        f"Transaction matched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
    )
    return tokens


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
    state.set_intended_end_block(end_block)

    logger.info(
        f"Scanning for ibBTC contract transactions from block {start_block} to {end_block}"
    )

    # run the scan
    result, total_chunks_scanned = scanner.scan(start_block, end_block)

    state.save()

    # process new mint/burn transactions
    tx_hashes = []
    for block_number, hash_list in state.state["blocks"].items():
        if (
            int(block_number) >= start_block
            and int(block_number) < end_block - CHAIN_REORG_SAFETY_BLOCKS
        ):
            tx_hashes.extend(hash_list)

    logger.info(f"Processing transaction events from {start_block} to {end_block}")
    for tx_hash in tx_hashes:
        process_transaction(w3, tx_hash, block_gauge, token_flow_counter, fees_counter)

    logger.info(f"Blocks {start_block} to {end_block} complete.")
    logger.info(
        f"Sleeping for {POLL_INTERVAL} seconds before starting next block chunks"
    )


def main():
    # set up prometheus
    logger.info(
        f"Starting Prometheus events server at http://localhost:{PROMETHEUS_PORT_FORWARDED}"
    )

    block_gauge = Gauge(
        name="block_info", documentation="block_info", labelnames=["info"]
    )

    token_flow_counter = Counter(
        name="ibbtc_token_flow",
        documentation="token,event,direction",
        labelnames=["token", "event", "direction"],
    )
    fees_counter = Counter(
        name="ibbtc_fees",
        documentation="entity",
        labelnames=["entity"],
    )

    start_http_server(PROMETHEUS_PORT)

    # set up scanner and scanner state
    # scan all blocks for Mint/Burn events with `eth_getLog`
    # works with nodes where `eth_newFilter` is not supported

    logger.info(f"Reading ibBTC contract at address {ADDRESSES['ibBTC']}")
    erc20_abi = json.load(open("interfaces/ERC20.json", "r"))
    ibbtc = w3.eth.contract(address=ADDRESSES["ibBTC"], abi=erc20_abi)

    state = IbbtcScannerState()
    state.restore()

    scanner = EventScanner(
        web3=w3,
        contract=ibbtc,
        state=state,
        events=[ibbtc.events.Transfer],
        filters={"address": ADDRESSES["ibBTC"]},
        num_blocks_rescan_for_forks=CHAIN_REORG_SAFETY_BLOCKS,
        max_chunk_scan_size=10000,
    )

    while True:
        run_scan(scanner, state, block_gauge, token_flow_counter, fees_counter)
        time.sleep(POLL_INTERVAL)
