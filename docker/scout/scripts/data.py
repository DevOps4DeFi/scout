import json
import logging
from dataclasses import dataclass

import requests
from brownie import interface
from brownie.network.contract import InterfaceContainer
from rich.console import Console
from rich.logging import RichHandler
from web3 import Web3

from scripts.logconf import console, log


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

            log.debug(
                f"token0: {self.token.token0()}, token1: {self.token.token1()}, getReserves: {self.token.getReserves()}"
            )
        except ValueError as e:
            info = {}
            log.exception(e)

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
                    "balance": self.token.balanceOf(address) / scale,
                    "tokenName": self.tokenName,
                    "tokenAddress": self.token,
                    "walletAddress": address,
                    "walletName": wallet,
                }
                for wallet, address in self.wallets.items()
            ]
        except ValueError as e:
            info = []
            log.exception(e)

        return info


@dataclass
class Treasury:
    name: str
    token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {
                "treasuryBalance": self.token.balanceOf(ADDRESSES["treasury"]) / scale
            }
        except ValueError as e:
            info = {}
            log.exception(e)

        return info


@dataclass
class Digg:
    name: str
    digg_oracle: InterfaceContainer

    def describe(self):
        try:
            info = {
                "lastUpdated": self.digg_oracle.providerReports(
                    oracles["oracle_provider"], 1
                )[0],
                "oracle_price": self.digg_oracle.providerReports(
                    oracles["oracle_provider"], 1
                )[1]
                / 1e18,
            }
        except ValueError as e:
            info = {}
            log.exception(e)

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

        return info


def get_tokens_by_address(treasury_tokens):
    return {address: token for token, address in treasury_tokens.items()}


def get_token_interfaces(treasury_tokens):
    return {
        address: interface.ERC20(address) for token, address in treasury_tokens.items()
    }


def get_lp_data(lp_tokens):
    return [
        lpToken(name=lp_token, token=interface.lpToken(address))
        for lp_token, address in lp_tokens.items()
    ]


def get_sett_data(sett_vaults):
    return [
        Sett(name=sett_vault, sett=interface.Sett(address))
        for sett_vault, address in sett_vaults.items()
    ]


def get_digg_data(oracle):
    return Digg(name="Digg Prices", digg_oracle=interface.Oracle(oracle))


def get_badgertree_data(badgertree):
    return Badgertree(
        name="Rewards Cycles",
        badger_tree=interface.Badgertree(badgertree),
    )


def get_treasury_data(treasury_tokens):
    return [
        Treasury(name=token, token=interface.ERC20(address))
        for token, address in treasury_tokens.items()
    ]


def get_token_balance_data(wallets, token, address):
    return TokenBalance(wallets=wallets, name=token, token=interface.ERC20(address))


def get_wallet_balances_by_token(wallets):
    return {
        address: get_token_balance_data(badger_wallets, token, address)
        for token, address in wallets.items()
    }


def get_json_request(request_type, url, request_data=None):
    """Takes a request object and request type, then returns the response in JSON format"""
    json_request = json.dumps(request_data)

    if request_type == "get":
        r = requests.get(url, data=json_request)
    elif request_type == "post":
        r = requests.post(url, data=json_request)
    else:
        return None

    return r.json()
