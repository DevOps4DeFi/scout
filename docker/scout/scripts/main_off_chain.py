"""
This is module with scout scripts that doesn't require running on chain
"""
from time import sleep
from typing import Dict
from typing import List

from prometheus_client import Gauge
from prometheus_client import start_http_server  # noqa
from web3 import Web3

from scripts.addresses import ADDRESSES_ETH
from scripts.addresses import CHAIN_ETH
from scripts.addresses import SUPPORTED_CHAINS
from scripts.addresses import checksum_address_dict
from scripts.addresses import reverse_addresses
from scripts.data import get_apr_from_convex
from scripts.data import get_sett_roi_data
from scripts.logconf import log

PROMETHEUS_PORT = 8801


ADDRESSES = checksum_address_dict(ADDRESSES_ETH)
# Flatten CVX dicts
CVX_ADDRESSES = {
    **ADDRESSES['crv_pools'],
    **ADDRESSES['crv_3_pools'],
    **ADDRESSES['crv_stablecoin_pools'],
}


def update_crv_setts_roi_gauge(
    sett_roi_gauge: Gauge, sett_data: List[Dict]
):
    if not sett_data:
        return
    for sett_name, sett_address in CVX_ADDRESSES.items():
        for cvx_item in sett_data:
            if Web3.toChecksumAddress(cvx_item['swap']) == sett_address:
                log.info(f"Updated CVX CRV pool {sett_name}")
                sett_roi_gauge.labels(
                    sett_name, "none", CHAIN_ETH, "cvxROI"
                ).set(float(cvx_item['cvxApr']) * 100)


def update_setts_roi_gauge(
        sett_roi_gauge: Gauge, sett_data: List[Dict], network: str
) -> None:
    reversed_addresses = reverse_addresses()[network]
    for sett in sett_data:
        sett_name = reversed_addresses[sett['settToken']]
        sett_roi_gauge.labels(sett_name, "none", network, "ROI").set(sett['apr'])
        # Gather data for each Sett source separately now
        for source in sett['sources']:
            sett_roi_gauge.labels(sett_name, source['name'], network, "apr").set(source['apr'])
            sett_roi_gauge.labels(
                sett_name, source['name'], network, "minApr"
            ).set(source['minApr'])
            sett_roi_gauge.labels(
                sett_name, source['name'], network, "maxApr").set(source['maxApr'])


def main():
    log.info(
        f"Starting Prometheus scout-collector server at http://localhost:{PROMETHEUS_PORT}"
    )
    start_http_server(PROMETHEUS_PORT)
    badger_sett_roi_gauge = Gauge(
        name="settRoi",
        documentation="Badger Sett ROI data",
        labelnames=["sett", "source", "chain", "param"],
    )
    while True:
        for network in SUPPORTED_CHAINS:
            setts_roi = get_sett_roi_data(network)
            update_setts_roi_gauge(badger_sett_roi_gauge, setts_roi, network)
        # Get data from convex to compare it to data from Badger API
        crvcvx_pools_data = get_apr_from_convex()
        update_crv_setts_roi_gauge(badger_sett_roi_gauge, crvcvx_pools_data)
        sleep(60)
