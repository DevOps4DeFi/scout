#!/usr/local/bin/python3
import logging
import math
import os
import warnings
import json

from eth_abi.codec import ABICodec
from brownie.network.state import Chain
from brownie.exceptions import EventLookupError
from web3.exceptions import MismatchedABI
from prometheus_client import Counter, Gauge, start_http_server
from rich.console import Console
from rich.logging import RichHandler
from web3 import Web3
from web3._utils.events import get_event_data

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
logger = logging.getLogger("rich")

ETHNODEURL = os.environ["ETHNODEURL"]
w3 = Web3(Web3.HTTPProvider(ETHNODEURL))


def process_transaction(tx_hash, block_gauge, token_flow_counter, fees_counter):
    tx = w3.eth.getTransaction(tx_hash)
    tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
    tx_logs = tx_receipt.logs

    block_number = tx.blockNumber
    block_timestamp = w3.eth.get_block(block_number)["timestamp"]

    erc20_abi = json.load(open("interfaces/ERC20.json", "r"))
    erc20 = w3.eth.contract(abi=erc20_abi)
    erc20_transfer_abi = erc20.events.Transfer._get_event_abi()

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

    for log in tx_logs:
        try:
            log_event = get_event_data(w3.codec, erc20_transfer_abi, log)
            tokens = update_tokens(tx_hash, log_event, tokens)
        except MismatchedABI:  # not ERC20 transfer, so skip
            continue

    # chain = Chain()
    # tx = chain.get_transaction(tx_hash)

    # block_number = tx.block_number
    # block_timestamp = tx.timestamp

    # print(tx.events)
    # try:
    #     tx_transfers = tx.events["Transfer"]
    #     print("event okay")
    # except EventLookupError:
    #     print("event lookup error 1: trying to decode")

    #     tx_receipt = w3.eth.getTransactionReceipt(tx_hash)

    #     bridge_abi = json.load(open("interfaces/Bridge.json", "r"))
    #     bridge = w3.eth.contract(address=ADDRS["bridge_v2"], abi=bridge_abi)

    #     bridge_event_mint_abi = bridge.events.Mint._get_event_abi()
    #     bridge_event_burn_abi = bridge.events.Burn._get_event_abi()

    #     try:
    #         tx_events = get_event_data(w3.codec, bridge_event_mint_abi, tx.events)
    #         print(tx_events)
    #     except EventLookupError:
    #         print("event loopup error 2: not mint event, trying burn")
    #         tx_events = get_event_data(w3.codec, bridge_event_burn_abi, tx.events)
    #         print(tx_events)

    # for transfer in tx_transfers:
    #     tokens = update_tokens(tx_hash, transfer, tokens)

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

    logger.info(
        f"Processed event: block timestamp {block_timestamp} block number {block_number}, hash {tx_hash}"
    )

    return tokens, balances


def update_tokens(tx_hash, tx_transfer, tokens):
    token_addr = tx_transfer["address"]

    try:
        transfer_from = Web3.toChecksumAddress(tx_transfer["args"]["_from"])
        transfer_to = Web3.toChecksumAddress(tx_transfer["args"]["_to"])
        transfer_value = tx_transfer["args"]["_value"] / DECIMALS
    except EventLookupError:
        transfer_from = Web3.toChecksumAddress["args"](tx_transfer["from"])
        transfer_to = Web3.toChecksumAddress(tx_transfer["args"]["to"])
        transfer_value = tx_transfer["args"]["value"] / DECIMALS

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
        logger.debug(
            f"Transaction partial match, unk_curve_1: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        pass

    elif (
        token_addr == ADDRS["WBTC"]
        and transfer_from == ADDRS["bridge_v2"]
        and transfer_to == ADDRS["unk_curve_2"]
    ):
        # WBTC; EOA -> bridge -> unk_curve_2 -> unk_curve_1
        logger.debug(
            f"Transaction partial match, unk_curve_2: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        pass

    else:
        logger.debug(
            f"Transaction unmatched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )

    logger.debug(
        f"Transaction matched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
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


def trunc(number, digits):
    """Truncates a number to a set number of decimals.

    https://stackoverflow.com/a/37697840
    """
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper
