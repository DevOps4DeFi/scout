#!/usr/local/bin/python3
import logging
import math
import os
import warnings

from brownie.network.state import Chain
from prometheus_client import Counter, Gauge, start_http_server
from rich.console import Console
from rich.logging import RichHandler
from web3 import Web3

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

DECIMALS = 1e8

warnings.simplefilter("ignore")
console = Console()
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("rich")


def trunc(number, digits):
    """Truncates a number to a set number of decimals.

    https://stackoverflow.com/a/37697840
    """
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper


def process_event(chain, event, block_gauge, token_flow_counter, fees_counter):
    block_number = event["blockNumber"]
    block_timestamp = chain[block_number]["timestamp"]

    tx_hash = event["transactionHash"]
    tx = chain.get_transaction(tx_hash)

    # FIX: Works locally, but when run in Docker, the `brownie.network.event.EventDict`
    # object contains raw event topics?
    tx_transfers = tx.events["Transfer"]

    tokens = {
        transfer: 0
        for transfer in [
            "ren_minted",
            "ren_received",
            "ren_bought",
            "ren_burned",
            "ren_sent",
            "wbtc_received",
            "wbtc_sent",
            "fee_badger",
            "fee_renvm",
        ]
    }
    for transfer in tx_transfers:
        tokens = update_tokens(tx_hash, transfer, tokens)

    balances = calc_balances(tokens)

    # update counters
    block_gauge.labels("block_number").set(block_number)
    block_gauge.labels("block_timestamp").set(block_timestamp)

    token_flow_counter.labels("BTC", "mint", "in").inc(balances["btc_in"])
    token_flow_counter.labels("BTC", "burn", "out").inc(balances["btc_out"])
    token_flow_counter.labels("WBTC", "burn", "in").inc(balances["wbtc_received"])
    token_flow_counter.labels("WBTC", "mint", "out").inc(balances["wbtc_sent"])
    token_flow_counter.labels("renBTC", "burn", "in").inc(balances["ren_received"])
    token_flow_counter.labels("renBTC", "mint", "out").inc(balances["ren_sent"])

    fees_counter.labels("Badger DAO").inc(balances["fee_badger_dao"])
    fees_counter.labels("Badger Bridge Team").inc(balances["fee_badger_bridge"])
    fees_counter.labels("RenVM Darknodes").inc(balances["fee_darknodes"])

    log.info(
        f"Processed event: block timestamp {block_timestamp} block number {block_number}, hash {tx_hash.hex()}"
    )

    return tokens, balances


def update_tokens(tx_hash, tx_transfer, tokens):
    token_addr = tx_transfer.address
    transfer_from = Web3.toChecksumAddress(tx_transfer["_from"])
    transfer_to = Web3.toChecksumAddress(tx_transfer["_to"])
    transfer_value = tx_transfer["_value"] / DECIMALS

    if (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["zero_addr"]
        and transfer_to == ADDRS["bridge_v2"]
    ):
        tokens["ren_minted"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to == ADDRS["zero_addr"]
    ):
        tokens["ren_burned"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from != ADDRS["zero_addr"]
        and transfer_from != ADDRS["unk_curve_1"]
        and transfer_to == ADDRS["bridge_v2"]
    ):
        tokens["ren_received"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["unk_curve_1"]
        and transfer_to == ADDRS["bridge_v2"]
    ):
        tokens["ren_bought"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to != ADDRS["badger_multisig"]
        and transfer_to != ADDRS["badger_bridge_team"]
        and transfer_to != ADDRS["unk_curve_2"]
        and transfer_to != ADDRS["zero_addr"]
    ):
        tokens["ren_sent"] += transfer_value

    elif (
        token_addr == ADDRS["WBTC"]
        and transfer_from != ADDRS["zero_addr"]
        and transfer_from != ADDRS["unk_curve_1"]
        and transfer_to == ADDRS["bridge_v2"]
    ):
        tokens["wbtc_received"] += transfer_value

    elif (
        token_addr == ADDRS["WBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to != ADDRS["badger_multisig"]
        and transfer_to != ADDRS["unk_curve_2"]
        and transfer_to != ADDRS["badger_bridge_team"]
        and transfer_to != ADDRS["zero_addr"]
    ):
        tokens["wbtc_sent"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to == ADDRS["badger_multisig"]
    ):
        tokens["fee_badger"] += transfer_value

    elif (
        token_addr == ADDRS["renBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to == ADDRS["badger_bridge_team"]
    ):
        tokens["fee_renvm"] += transfer_value

    elif (
        token_addr == ADDRS["WBTC"]
        and transfer_from == ADDRS["unk_curve_1"]
        and transfer_to == ADDRS["bridge_v2"]
    ):
        # WBTC; unk_curve_1 -> bridge -> EOA
        log.debug(
            f"Transaction partial match, unk_curve_1: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash.hex()}\n"
        )
        pass

    elif (
        token_addr == ADDRS["WBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to == ADDRS["unk_curve_2"]
    ):
        # WBTC; EOA -> bridge -> unk_curve_2 -> unk_curve_1
        log.debug(
            f"Transaction partial match, unk_curve_2: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash.hex()}\n"
        )
        pass

    else:
        log.debug(
            f"Transaction unmatched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash.hex()}\n"
        )

    log.debug(
        f"Transaction matched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash.hex()}\n"
    )

    return tokens


def calc_balances(tokens):
    balances = {
        balance: 0
        for balance in [
            "btc_in",
            "btc_out",
            "wbtc_received",
            "wbtc_sent",
            "wbtc_total",
            "ren_minted",
            "ren_received",
            "ren_sent",
            "ren_total",
            "fee_badger_dao",
            "fee_badger_bridge",
            "fee_darknodes",
            "fee_miners",
        ]
    }

    balances["wbtc_received"] = tokens["wbtc_received"]
    balances["wbtc_sent"] = tokens["wbtc_sent"]  # -
    balances["ren_minted"] = tokens["ren_minted"]
    balances["ren_received"] = tokens["ren_received"]
    balances["ren_sent"] = tokens["ren_sent"]  # -
    balances["fee_badger_dao"] = tokens["fee_badger"]
    balances["fee_badger_bridge"] = tokens["fee_renvm"]

    balances["ren_total"] = balances["ren_received"] + balances["ren_sent"]
    balances["wbtc_total"] = balances["wbtc_received"] + balances["wbtc_sent"]

    if tokens["ren_minted"] > 0:
        balances["btc_in"] = trunc((tokens["ren_minted"] / 0.9975) + 0.001, 8)
        balances["fee_darknodes"] = trunc((tokens["ren_minted"] / 0.9975) * 0.0025, 8)
        balances["fee_miners"] = 0.001

    if tokens["wbtc_received"] > 0 or tokens["ren_received"] > 0:
        balances["btc_out"] = tokens["ren_burned"]
        balances["fee_darknodes"] = trunc(tokens["ren_burned"] * 0.001, 8)

    return balances
