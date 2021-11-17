import json
import re
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional

import requests
from brownie import interface
from brownie.network.contract import InterfaceContainer

from scripts.addresses import MAPPING_TO_SETT_API_CHAIN_PARAM
from scripts.logconf import log


@dataclass
class lpToken:
    name: str
    token: InterfaceContainer

    def describe(self):
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
            info = {
                "treasuryBalance": self.token.balanceOf(self.treasury_address) / scale
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class yearnVault:
    name: str
    vault: InterfaceContainer

    def describe(self):
        scale = 10 ** self.vault.decimals()
        try:
            info = {
                "pricePerShare": self.vault.pricePerShare() / scale,
                "totalSupply": self.vault.totalSupply() / scale,
                "balance": (self.vault.pricePerShare() / scale)
                * (self.vault.totalSupply() / scale),
            }
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


@dataclass
class ibBTC:
    name: str
    token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.token.decimals()
        try:
            info = {
                "totalSupply": self.token.totalSupply() / scale,
                "pricePerShare": self.token.pricePerShare() / scale,
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class PeakSettUnderlying:
    peak_name: str
    peak_address: str
    sett_name: str
    sett_address: str
    sett_token: InterfaceContainer

    def describe(self):
        scale = 10 ** self.sett_token.decimals()
        try:
            if "bcrv" in self.sett_name:
                price_per_share = self.sett_token.getPricePerFullShare() / scale
            elif "byv" in self.sett_name:
                price_per_share = self.sett_token.pricePerShare() / scale

            info = {
                "balance": self.sett_token.balanceOf(self.peak_address) / scale,
                "pricePerShare": price_per_share,
            }
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


@dataclass
class Peak:
    name: str
    peak: InterfaceContainer

    def describe(self):
        try:
            info = {"portfolioValue": self.peak.portfolioValue() / 1e18}
        except ValueError as e:
            info = {}
            log.exception(e)
            log.debug(e)

        return info


def get_token_by_address(token_dict, query_address):
    for token_name, token_address in token_dict.items():
        if token_address == query_address:
            return token_name


def get_token_interfaces(token_dict):
    return {
        token_address: interface.ERC20(token_address)
        for token_name, token_address in token_dict.items()
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


def get_yvault_data(yearn_vaults):
    return [
        yearnVault(name=f"{name}", vault=interface.yearnVault(vault))
        for name, vault in yearn_vaults.items()
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


def get_ibbtc_data(token, token_name="ibBTC"):
    return ibBTC(name=token_name, token=token)


def get_peak_value_data(peaks):
    return [
        Peak(name=peak_name, peak=interface.Peak(peak_address))
        for peak_name, peak_address in peaks.items()
    ]


def get_peak_composition_data(peaks, peak_sett_composition):
    peak_sett_underlyings = []
    for peak_name, peak_address in peaks.items():
        for sett_name, sett_address in peak_sett_composition[peak_name].items():
            if "bcrv" in sett_name:
                sett_token = interface.Sett(sett_address)
            elif "byv" in sett_name:
                sett_token = interface.yearnVault(sett_address)
            else:
                log.error("Incorrect Sett specified in Peak composition")

            peak_sett_underlyings.append(
                PeakSettUnderlying(
                    peak_name,
                    peak_address,
                    sett_name,
                    sett_address,
                    sett_token,
                )
            )

    return peak_sett_underlyings


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
        token_address: TokenBalance(
            wallets=wallets, name=token_name, token=interface.ERC20(token_address)
        )
        for token_name, token_address in tokens.items()
    }


CVX_GRAPH_QUERY = """{
  platforms(first: 5) {
    id
    curvePools {
      name,
      swap,
      lpToken,
      token,
      gauge,
      cvxApr,
    }
  }
}
"""


def get_apr_from_convex() -> Optional[List[Dict]]:
    result = requests.post(
        'https://api.thegraph.com/subgraphs/name/convex-community/curve-pools',
        json={'query': CVX_GRAPH_QUERY}
    )
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError:
        log.error("Got error from CVX graph API")
        return
    return result.json()['data']['platforms'][0]['curvePools']


def get_sett_roi_data(network: Optional[str] = "ETH") -> Optional[List[Dict]]:
    log.info("Fetching ROI from Badger API")
    chain = MAPPING_TO_SETT_API_CHAIN_PARAM[network]
    response = get_json_request(
        request_type="get", url=f"https://api.badger.finance/v2/setts?chain={chain}"
    )
    if not response:
        log.warning("Cannot fetch Sett ROI data from Badger API")
        return

    setts_data = []
    for sett in response:
        setts_data.append(sett)
    return setts_data


TOKEN_TO_TREASURY_TOKEN_NAME_MAPPING = {
    'btc': "WTBC",
    'usd': "USDT",
    'cvx': "CVX",
    'mim': "USDT",
    'frax': "USDT",
    '3pool': "USDT",
    '3crv': "USDT",
}


def get_treasury_token_addr_by_pool_name(pool_name: str, treasury_tokens: Dict) -> Optional[str]:
    token = None
    for key, value in TOKEN_TO_TREASURY_TOKEN_NAME_MAPPING.items():
        if re.search(key, pool_name, re.IGNORECASE):
            token = value
    return treasury_tokens.get(token) if token else None


def get_json_request(request_type, url, request_data=None):
    """Takes a request object and request type, then returns the response in JSON format"""
    json_request = json.dumps(request_data) if request_data else None
    if request_type == "get":
        r = requests.get(f"{url}", data=json_request)
    elif request_type == "post":
        r = requests.post(f"{url}", data=json_request)
    else:
        return None
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        log.error(f"Got error from {url}")
        return
    return r.json()


def get_token_prices(token_csv, countertoken_csv, network) -> Optional[Dict]:
    log.info("Fetching token prices from CoinGecko ...")

    if network == "ETH":
        # fetch prices by token_address on ETH
        # fetch prices by token_address on ETH
        url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum?" \
              f"contract_addresses={token_csv}&vs_currencies={countertoken_csv}"
    elif network == "BSC":
        # fetch prices by coingecko_name on BSC
        url = f"https://api.coingecko.com/api/v3/simple/price?" \
              f"ids={token_csv}&vs_currencies={countertoken_csv}"
    else:
        return

    token_prices = get_json_request(request_type="get", url=url)
    return token_prices
