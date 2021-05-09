import logging

from rich.logging import RichHandler
from web3 import Web3

logging.basicConfig(
    level="ERROR",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("rich")

ADDRESSES_ETH = {
    "zero": "0x0000000000000000000000000000000000000000",
    "treasury": "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B",
    "badger_wallets": {
        "fees": "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B",
        "team": "0xe4aa1d8aaf8a50422bc5c7310deb1262d1f6f657",
        "badgertree": "0x660802fc641b154aba66a62137e71f331b6d787a",
        "badgerhunt": "0x394dcfbcf25c5400fcc147ebd9970ed34a474543",
        "DAO_treasury": "0x4441776e6a5d61fa024a5117bfc26b953ad1f425",
        "rewards_escrow": "0x19d099670a21bc0a8211a89b84cedf59abb4377f",
        "dev_multisig": "0xB65cef03b9B89f99517643226d76e286ee999e77",
        "ops_multisig": "0xD4868d98849a58F743787c77738D808376210292",
        "ops_deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
        "ops_guardian": "0x29F7F8896Fb913CF7f9949C623F896a154727919",
        "ops_keeper": "0x872213E29C85d7e30F1C8202FC47eD1Ec124BB1D",
        "ops_root-validator": "0x626f69162ea1556a75dd4443d87d2fe38dd25901",
        "digg_treasury": "0x5A54Ca44e8F5A1A695f8621f15Bfa159a140bB61",
        "uniswap_rewards": "0x0c79406977314847a9545b11783635432d7fe019",
    },
    "sett_vaults": {
        "bBADGER": "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28",
        "bDIGG": "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        "bcrvRenBTC": "0x6dEf55d2e18486B9dDfaA075bc4e4EE0B28c1545",
        "bcrvSBTC": "0xd04c48A53c111300aD41190D63681ed3dAd998eC",
        "bcrvTBTC": "0xb9D076fDe463dbc9f915E5392F807315Bf940334",
        "bharvestcrvRenBTC": "0xAf5A1DECfa95BAF63E0084a35c62592B774A2A87",
        "buniWbtcBadger": "0x235c9e24D3FB2FAFd58a2E49D454Fdcd2DBf7FF1",
        "bslpWbtcBadger": "0x1862A18181346EBd9EdAf800804f89190DeF24a5",
        "buniWbtcDigg": "0xC17078FDd324CC473F8175Dc5290fae5f2E84714",
        "bslpWbtcDigg": "0x88128580ACdD9c04Ce47AFcE196875747bF2A9f6",
        "bslpWbtcEth": "0x758A43EE2BFf8230eeb784879CdcFF4828F2544D",
    },
    "treasury_tokens": {
        "FARM": "0xa0246c9032bC3A600820415aE600c6388619A14D",
        "BADGER": "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
        "DIGG": "0x798D1bE841a82a273720CE31c822C61a67a601C3",
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
        "bDIGG": "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        "bBADGER": "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28",
        "xSUSHI": "0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272",
        "crvRenBTC": "0x49849C98ae39Fff122806C06791Fa73784FB3675",
        "crvSBTC": "0x075b1bb99792c9E1041bA13afEf80C91a1e70fB3",
        "crvTBTC": "0x64eda51d3Ad40D56b9dFc5554E06F94e1Dd786Fd",
        "slpWbtcEth": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
        "slpWbtcBadger": "0x110492b31c59716ac47337e616804e3e3adc0b4a",
        "uniWbtcBadger": "0xcd7989894bc033581532d2cd88da5db0a4b12859",
        "uniWbtcDigg": "0xe86204c4eddd2f70ee00ead6805f917671f56c52",
        "slpWbtcDigg": "0x9a13867048e01c663ce8ce2fe0cdae69ff9f35e3",
        "slpEthBBadger": "0x0a54d4b378c8dbfc7bc93be50c85debafdb87439",
        "slpEthBDigg": "0xf9440fedc72a0b8030861dcdac39a75b544e7a3c",
    },
    "lp_tokens": {
        "slpWbtcEth": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
        "slpWbtcBadger": "0x110492b31c59716ac47337e616804e3e3adc0b4a",
        "uniWbtcBadger": "0xcd7989894bc033581532d2cd88da5db0a4b12859",
        "uniWbtcDigg": "0xe86204c4eddd2f70ee00ead6805f917671f56c52",
        "slpWbtcDigg": "0x9a13867048e01c663ce8ce2fe0cdae69ff9f35e3",
        "slpEthBBadger": "0x0a54d4b378c8dbfc7bc93be50c85debafdb87439",
        "slpEthBDigg": "0xf9440fedc72a0b8030861dcdac39a75b544e7a3c",
    },
    "crv_pools": {
        "crvRenBTC": "0x93054188d876f558f4a66B2EF1d97d16eDf0895B",
        "crvSBTC": "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714",
        "crvTBTC": "0xc25099792e9349c7dd09759744ea681c7de2cb66",
    },
    "oracles": {
        "oracle": "0x058ec2Bf15011095a25670b618A129c043e2162E",
        "oracle_provider": "0x72dc16CFa95beB42aeebD2B10F22E55bD17Ce976",
    },
}

ADDRESSES_BSC = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_wallets": {
        "badgertree": "0x660802Fc641b154aBA66a62137e71f331B6d787A",
        "dev_proxy_admin": "0x6354e79f21b56c11f48bcd7c451be456d7102a36",
        "dev_multisig": "0x6DA4c138Dd178F6179091C260de643529A2dAcfe",
        "ops_multisig": "0x7c7054bd87431378C837B2679f223f6d6aa602C1",
        "ops_deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
        "ops_guardian": "0x29F7F8896Fb913CF7f9949C623F896a154727919",
        "ops_keeper": "0x872213E29C85d7e30F1C8202FC47eD1Ec124BB1D",
    },
    "sett_vaults": {
        "bcakeBnbBtcb": "0xaf4B9C4b545D5324904bAa15e29796D2E2f90813",
        "bcakebBadgerBtcb": "0x857F91f735f4B03b19D2b5c6E476C73DB8241F55",
        "bcakebDiggBtcb": "0xa861Ba302674b08f7F2F24381b705870521DDfed",
    },
    "treasury_tokens": {
        "BADGER": "0x753fbc5800a8C8e3Fb6DC6415810d627A387Dfc9",
        "bBADGER": "0x1F7216fdB338247512Ec99715587bb97BBf96eae",
        "bDIGG": "0x5986D5c77c65e5801a5cAa4fAE80089f870A71dA",
        "BTCb": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
        "WBNB": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "cakebBadgerBtcb": "0x10F461CEAC7A17F59e249954Db0784d42EfF5DB5",
        "cakebDiggBtcb": "0xE1E33459505bB3763843a426F7Fd9933418184ae",
        "cakeBnbBtcb": "0x7561EEe90e24F3b348E1087A005F78B4c8453524",
    },
    "lp_tokens": {
        "cakebBadgerBtcb": "0x10F461CEAC7A17F59e249954Db0784d42EfF5DB5",
        "cakebDiggBtcb": "0xE1E33459505bB3763843a426F7Fd9933418184ae",
        "cakeBnbBtcb": "0x7561eee90e24f3b348e1087a005f78b4c8453524",
    },
    "coingecko_tokens": {
        "0x753fbc5800a8C8e3Fb6DC6415810d627A387Dfc9": "badger-dao",
        "0x1F7216fdB338247512Ec99715587bb97BBf96eae": "badger-sett-badger",
        "0x5986D5c77c65e5801a5cAa4fAE80089f870A71dA": "badger-sett-digg",
        "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c": "binance-bitcoin",
        "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c": "binancecoin",
        "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82": "pancakeswap-token",
    },
    "oracles": {
        "oracle": "0x058ec2Bf15011095a25670b618A129c043e2162E",
        "oracle_provider": "0x72dc16CFa95beB42aeebD2B10F22E55bD17Ce976",
    },
}


def checksum_address_dict(addresses):
    checksummed = {}
    for k, v in addresses.items():
        if isinstance(v, str):
            checksummed[k] = Web3.toChecksumAddress(v)
        elif isinstance(v, dict):
            checksummed[k] = {
                label: Web3.toChecksumAddress(address) for label, address in v.items()
            }
        else:
            log.error("Addresses formatted incorrectly")

    return checksummed
