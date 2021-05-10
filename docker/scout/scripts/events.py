import json
import math
import warnings

from brownie.exceptions import EventLookupError
from eth_abi.codec import ABICodec
from web3 import Web3
from web3._utils.events import get_event_data
from web3.exceptions import MismatchedABI

from scripts.addresses import ADDRESSES_BRIDGE, checksum_address_dict
from scripts.logconf import log as logger

ADDRESSES = checksum_address_dict(ADDRESSES_BRIDGE)

DECIMALS = 1e8

warnings.simplefilter("ignore")


def process_transaction(web3, tx_hash, block_gauge, token_flow_counter, fees_counter):
    tx = web3.eth.getTransaction(tx_hash)
    tx_logs = web3.eth.getTransactionReceipt(tx_hash).logs

    block_number = tx.blockNumber
    block_timestamp = web3.eth.get_block(block_number)["timestamp"]

    erc20_abi = json.load(open("interfaces/ERC20.json", "r"))
    erc20 = web3.eth.contract(abi=erc20_abi)
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
            event_data = get_event_data(web3.codec, erc20_transfer_abi, log)
            tokens = update_tokens(tx_hash, event_data, tokens)
        except MismatchedABI:  # not ERC20 transfer, so skip
            continue

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
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["zero"]
        and transfer_to == ADDRESSES["bridge_v2"]
    ):
        tokens["ren_minted"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to == ADDRESSES["zero"]
    ):
        tokens["ren_burned"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from != ADDRESSES["zero"]
        and transfer_from != ADDRESSES["unk_curve_1"]
        and transfer_to == ADDRESSES["bridge_v2"]
    ):
        tokens["ren_received"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["unk_curve_1"]
        and transfer_to == ADDRESSES["bridge_v2"]
    ):
        tokens["ren_bought"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to != ADDRESSES["badger_multisig"]
        and transfer_to != ADDRESSES["badger_bridge_team"]
        and transfer_to != ADDRESSES["unk_curve_2"]
        and transfer_to != ADDRESSES["zero"]
    ):
        tokens["ren_sent"] += transfer_value

    elif (
        token_addr == ADDRESSES["WBTC"]
        and transfer_from != ADDRESSES["zero"]
        and transfer_from != ADDRESSES["unk_curve_1"]
        and transfer_to == ADDRESSES["bridge_v2"]
    ):
        tokens["wbtc_received"] += transfer_value

    elif (
        token_addr == ADDRESSES["WBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to != ADDRESSES["badger_multisig"]
        and transfer_to != ADDRESSES["unk_curve_2"]
        and transfer_to != ADDRESSES["badger_bridge_team"]
        and transfer_to != ADDRESSES["zero"]
    ):
        tokens["wbtc_sent"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to == ADDRESSES["badger_multisig"]
    ):
        tokens["fee_badger"] += transfer_value

    elif (
        token_addr == ADDRESSES["renBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to == ADDRESSES["badger_bridge_team"]
    ):
        tokens["fee_renvm"] += transfer_value

    elif (
        token_addr == ADDRESSES["WBTC"]
        and transfer_from == ADDRESSES["unk_curve_1"]
        and transfer_to == ADDRESSES["bridge_v2"]
    ):
        # WBTC; unk_curve_1 -> bridge -> EOA
        logger.debug(
            f"Transaction partial match, unk_curve_1: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        return tokens

    elif (
        token_addr == ADDRESSES["WBTC"]
        and transfer_from == ADDRESSES["bridge_v2"]
        and transfer_to == ADDRESSES["unk_curve_2"]
    ):
        # WBTC; EOA -> bridge -> unk_curve_2 -> unk_curve_1
        logger.debug(
            f"Transaction partial match, unk_curve_2: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        return tokens

    else:
        logger.debug(
            f"Transaction unmatched: token {token_addr}, from {transfer_from}, to {transfer_to} value {transfer_value}, hash {tx_hash}\n"
        )
        return tokens

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
