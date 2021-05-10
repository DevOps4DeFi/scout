import json
import logging
from dataclasses import dataclass

import requests
from brownie import interface
from brownie.network.contract import InterfaceContainer
from web3 import Web3

from scripts.logconf import log


@dataclass
class lpToken:
    name: str
    token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {
                "token0": self.token.token0(),
                "token1": self.token.token1(),
                "token0_reserve": self.token.getReserves()[0],
                "token1_reserve": self.token.getReserves()[1],
                "totalSupply": self.token.totalSupply(),
                "decimals": self.token.decimals(),
            }

        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class Sett:
    name: str
    sett: InterfaceContainer

    def describe(self):
        scale = 10 ** self.sett.decimals()
        try:
            info = {
                "pricePerShare": self.sett.getPricePerFullShare() / scale,
                "totalSupply": self.sett.totalSupply() / scale,
                "balance": self.sett.balance() / scale,
                "available": self.sett.available() / scale,
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class TokenBalance:
    wallets: dict
    name: str
    token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = [
                {
                    "tokenName": self.name,
                    "tokenAddress": self.token.address,
                    "tokenBalance": self.token.balanceOf(wallet_address) / scale,
                    "walletName": wallet_name,
                    "walletAddress": wallet_address,
                }
                for wallet_name, wallet_address in self.wallets.items()
            ]
        except ValueError as e:
            info = []
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class Treasury:
    name: str
    token: InterfaceContainer
    treasury_address: str

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {"treasuryBalance": self.token.balanceOf(treasury_address) / scale}
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class Digg:
    name: str
    oracle: InterfaceContainer
    oracle_provider: str

    def describe(self):
        try:
            info = {
                "lastUpdated": self.oracle.providerReports(self.oracle_provider, 1)[0],
                "oraclePrice": self.oracle.providerReports(self.oracle_provider, 1)[1]
                / 1e18,
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class Badgertree:
    name: str
    badger_tree: InterfaceContainer

    def describe(self):
        try:
            info = {
                "lastPublishTimestamp": self.badger_tree.lastPublishTimestamp(),
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


def get_tokens_by_address(treasury_tokens):
    return {
        token_address: token_name
        for token_name, token_address in treasury_tokens.items()
    }


def get_token_interfaces(treasury_tokens):
    return {
        token_address: interface.ERC20(token_address)
        for token_name, token_address in treasury_tokens.items()
    }


def get_lp_data(lp_tokens):
    return [
        lpToken(name=lp_name, token=interface.lpToken(lp_address))
        for lp_name, lp_address in lp_tokens.items()
    ]


def get_sett_data(sett_vaults):
    return [
        Sett(name=sett_name, sett=interface.Sett(sett_address))
        for sett_name, sett_address in sett_vaults.items()
    ]


def get_digg_data(oracle, oracle_provider):
    return Digg(
        name="Digg Prices",
        oracle=interface.Oracle(oracle),
        oracle_provider=oracle_provider,
    )


def get_badgertree_data(badgertree):
    return Badgertree(
        name="Rewards Cycles",
        badger_tree=badgertree,
    )


def get_treasury_data(treasury_address, treasury_tokens):
    return [
        Treasury(
            name=token_name,
            token=interface.ERC20(token_address),
            treasury_address=treasury_address,
        )
        for token_name, token_address in treasury_tokens.items()
    ]


def get_token_balance_data(wallets, token_name, token_address):
    return TokenBalance(
        wallets=wallets, name=token_name, token=interface.ERC20(token_address)
    )


def get_wallet_balances_by_token(wallets, tokens):
    return {
        token_address: get_token_balance_data(wallets, token_name, token_address)
        for token_name, token_address in tokens.items()
    }


def get_json_request(request_type, url, request_data=None):
    """Takes a request object and request type, then returns the response in JSON format"""
    json_request = json.dumps(request_data)

    if request_type == "get":
        r = requests.get(f"{url}", data=json_request)
    elif request_type == "post":
        r = requests.post(f"{url}", data=json_request)
    else:
        return None

    return r.json()
