from web3 import Web3
from rich.console import Console


ADDRESSES_ETH = {
    "zero": "0x0000000000000000000000000000000000000000",
    "treasury": "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B",
    ### The wallets listed here are looped over by scout and checked for all treasury tokens
    "badger_wallets": {
        "fees": "0x8dE82C4C968663a0284b01069DDE6EF231D0Ef9B",
        "team": "0xe4aa1d8aaf8a50422bc5c7310deb1262d1f6f657",
        "badgertree": "0x660802fc641b154aba66a62137e71f331b6d787a",
        "native_autocompounder": "0x5B60952481Eb42B66bdfFC3E049025AC5b91c127",
        "badgerhunt": "0x394dcfbcf25c5400fcc147ebd9970ed34a474543",
        "DAO_treasury": "0x4441776e6a5d61fa024a5117bfc26b953ad1f425",
        "rewards_escrow": "0x19d099670a21bc0a8211a89b84cedf59abb4377f",
        "dev_multisig": "0xB65cef03b9B89f99517643226d76e286ee999e77",
        "devtest_multisig": "0x33909cb2633d4B298a72042Da5686B45E9385ed0",
        "test_multisig": "0x33909cb2633d4B298a72042Da5686B45E9385ed0",
        "techops_multisig": "0x86cbD0ce0c087b482782c181dA8d191De18C8275",
        "ops_multisig": "0xD4868d98849a58F743787c77738D808376210292",
        "ops_deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
        "ops_deployer2": "0xeE8b29AA52dD5fF2559da2C50b1887ADee257556",
        "ops_deployer3": "0x283C857BA940A61828d9F4c09e3fceE2e7aEF3f7",
        "ops_deployer4": "0xef42D748e09A2d9eF89238c053CE0B6f00236210",
        "ops_guardian": "0x29F7F8896Fb913CF7f9949C623F896a154727919",
        "ops_keeper": "0x872213E29C85d7e30F1C8202FC47eD1Ec124BB1D",
        "ops_root-validator": "0x626f69162ea1556a75dd4443d87d2fe38dd25901",
        "ops_cycle_bot": "0x68de9E2b015904530593426d934CE608e117Fa7A",
        "ops_botsquad": "0xF8dbb94608E72A3C4cEeAB4ad495ac51210a341e",
        "ops_botsquad_cycle0": "0x1a6D6D120a7e3F71B084b4023a518c72F1a93EE9",
        "ops_earner": "0x46099Ffa86aAeC689D11F5D5130044Ff7082C2AD",
        "ops_harvester": "0x73433896620E71f7b1C72405b8D2898e951Ca4d5",
        "ops_external_harvester": "0x64E2286148Fbeba8BEb4613Ede74bAc7646B2A2B",
        "digg_treasury": "0x5A54Ca44e8F5A1A695f8621f15Bfa159a140bB61",
        "uniswap_rewards": "0x0c79406977314847a9545b11783635432d7fe019",
        "defiDollar_fees": "0x5b5cf8620292249669e1dcc73b753d01543d6ac7",
        "delegate": "0x14f83ff95d4ec5e8812ddf42da1232b0ba1015e6"
    },
    #Scout stores prices for all tokens here, either from coingecko or interpolation
    # Any token here that does not have a coingeco price must be included in sett_vaults
    # or one of the crv_ lists in order to have it's price calculated and not break scout.
    "treasury_tokens": {
        "FARM": "0xa0246c9032bC3A600820415aE600c6388619A14D",
        "BADGER": "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
        "ibBTC": "0xc4E15973E6fF2A35cC804c2CF9D2a1b817a8b40F",
        "DIGG": "0x798D1bE841a82a273720CE31c822C61a67a601C3",
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "USDT":  "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
        "SUSHI": "0x6b3595068778dd592e39a122f4f5a5cf09c90fe2",
        "bDIGG": "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        "bBADGER": "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28",
        "xSUSHI": "0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272",
        "MEOWSHI": "0x650F44eD6F1FE0E1417cb4b3115d52494B4D9b6D", ##TODO There is overhead to scan every token for every wallet, is this something we want to watch.manage in our treasury
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
        "crvHBTC": "0xb19059ebb43466C323583928285a49f558E572Fd",
        "crvBBTC": "0x410e3E86ef427e30B9235497143881f717d93c2A",
        "crvOBTC": "0x2fE94ea3d5d4a175184081439753DE15AeF9d614",
        "crvPBTC": "0xDE5331AC4B3630f94853Ff322B66407e0D6331E8",
        "CVX": "0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B",
        "cvxCRV": "0x62B9c7356A2Dc64a1969e19C23e4f579F9810Aa7",
        "crvTricrypto2" : "0xc4AD29ba4B3c580e6D59105FFf484999997675Ff",
        "crvTricrypto": "0xcA3d75aC011BF5aD07a98d02f18225F9bD9A6BDF"

    },
    ### I do not think these are used by scout
    "strategies": {
        "native.badger": "0x75b8E21BD623012Efb3b69E1B562465A68944eE6",
        "native.renCrv": "0x6582a5b139fc1c6360846efdc4440d51aad4df7b",
        "native.sbtcCrv": "0xf1ded284e891943b3e9c657d7fc376b86164ffc2",
        "native.tbtcCrv": "0x522bb024c339a12be1a47229546f288c40b62d29",
        "native.uniBadgerWbtc": "0x95826C65EB1f2d2F0EDBb7EcB176563B61C60bBf",
        "harvest.renCrv": "0xaaE82E3c89e15E6F26F60724f115d5012363e030",
        "native.sushiWbtcEth": "0x7A56d65254705B4Def63c68488C0182968C452ce",
        "native.sushiBadgerWbtc": "0x3a494D79AA78118795daad8AeFF5825C6c8dF7F1",
        "native.digg": "0x4a8651F2edD68850B944AD93f2c67af817F39F62",
        "native.uniDiggWbtc": "0xadc8d7322f2E284c1d9254170dbe311E9D3356cf",
        "native.sushiDiggWbtc": "0xaa8dddfe7DFA3C3269f1910d89E4413dD006D08a",
        "experimental.sushiIBbtcWbtc": "0xf4146A176b09C664978e03d28d07Db4431525dAd",
        "experimental.digg": "0xA6af1B913E205B8E9B95D3B30768c0989e942316",
        "native.hbtcCrv": "0xff26f400e57bf726822eacbb64fa1c52f1f27988",
        "native.pbtcCrv": "0x1C1fD689103bbFD701b3B7D41A3807F12814033D",
        "native.obtcCrv": "0x2bb864cdb4856ab2d148c5ca52dd7ccec126d138",
        "native.bbtcCrv": "0x4f3e7a4566320b2709fd1986f2e9f84053d3e2a0",
        "native.tricrypto": "0x05ec4356e1acd89cc2d16adc7415c8c95e736ac1",
        "native.tricrypto2": "0x2eB6479c2f033360C0F4575A88e3b8909Cbc6a03",
        "native.cvxCrv": "0x826048381d65a65DAa51342C51d464428d301896",
        "native.cvx": "0xBCee2c6CfA7A4e29892c3665f464Be5536F16D95",
        "native.mstableImBtc": "0xd409C506742b7f76f164909025Ab29A47e06d30A",
        "native.mstableFpMbtcHbtc": "0x54D06A0E1cE55a7a60Ee175AbCeaC7e363f603f3",
        "native.vestedCVX": "0x87fB47c2B9EB41d362BAb44F5Ec81514b6b1de13"
    },
    #Every slp token listed in treasury tokens above must also be listed here.  The lp_tokens in this list
    #are processed by scount to determine holdings and underlying value and set the price for the token in treasury_tokens
    #Note that only univ2 style tokens should be listed here
    "lp_tokens": {
        "slpWbtcEth": "0xceff51756c56ceffca006cd410b03ffc46dd3a58",
        "slpWbtcBadger": "0x110492b31c59716ac47337e616804e3e3adc0b4a",
        "uniWbtcBadger": "0xcd7989894bc033581532d2cd88da5db0a4b12859",
        "uniWbtcDigg": "0xe86204c4eddd2f70ee00ead6805f917671f56c52",
        "slpWbtcDigg": "0x9a13867048e01c663ce8ce2fe0cdae69ff9f35e3",
        "slpEthBBadger": "0x0a54d4b378c8dbfc7bc93be50c85debafdb87439",
        "slpEthBDigg": "0xf9440fedc72a0b8030861dcdac39a75b544e7a3c",
        "slpWbtcIbBTC": "0x18d98D452072Ac2EB7b74ce3DB723374360539f1",
    },
    #Every single asset curve pool listed in treasury tokens must also be listed here.  This does not inclide tricrypto or other crypto like pools.
    #This list contains curve pools in which all of the underlying tokens have basically the same value.
    #Again every curve pool listed in treasury_tokens must be in this list, or crv_crypto_pools below
    "crv_pools": {
        "crvRenBTC": "0x93054188d876f558f4a66B2EF1d97d16eDf0895B",
        "crvSBTC": "0x7fC77b5c7614E1533320Ea6DDc2Eb61fa00A9714",
        "crvTBTC": "0xc25099792e9349c7dd09759744ea681c7de2cb66",
        "crvHBTC": "0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F",
        "crvBBTC": "0x071c661B4DeefB59E2a3DdB20Db036821eeE8F4b",
        "crvOBTC": "0xd81dA8D904b52208541Bade1bD6595D8a251F8dd",
        "crvPBTC": "0x7F55DDe206dbAD629C080068923b36fe9D6bDBeF",
    },
    # Pool addresses for curve pools that handle non-stable coins like tricypto
    "crv_3_pools": {
        "crvTricrypto2": "0xD51a44d3FaE010294C616388b506AcdA1bfAAE46"
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
        "bcrvHBTC": "0x8c76970747afd5398e958bdfada4cf0b9fca16c4",
        "bcrvPBTC": "0x55912d0cf83b75c492e761932abc4db4a5cb1b17",
        "bcrvOBTC": "0xf349c0faa80fc1870306ac093f75934078e28991",
        "bcrvBBTC": "0x5dce29e92b1b939f8e8c60dcf15bde82a85be4a9",
#        "bcrvTricrypto": "0xBE08Ef12e4a553666291E9fFC24fCCFd354F2Dd2",
        "bcrvTricrypto2": "0x27E98fC7d05f54E544d16F58C194C2D7ba71e3B5",
        "bcvxCRV": "0x2B5455aac8d64C14786c3a29858E43b5945819C0",
        "bCVX": "0x53c8e199eb2cb7c01543c137078a038937a68e40",
        # "bbCVX": "0xE143aA25Eec81B4Fc952b38b6Bca8D2395481377",
    },
    "strategies": {
        "native.badger": "0x75b8E21BD623012Efb3b69E1B562465A68944eE6",
        "native.renCrv": "0x6582a5b139fc1c6360846efdc4440d51aad4df7b",
        "native.sbtcCrv": "0xf1ded284e891943b3e9c657d7fc376b86164ffc2",
        "native.tbtcCrv": "0x522bb024c339a12be1a47229546f288c40b62d29",
        "native.uniBadgerWbtc": "0x95826C65EB1f2d2F0EDBb7EcB176563B61C60bBf",
        "harvest.renCrv": "0xaaE82E3c89e15E6F26F60724f115d5012363e030",
        "native.sushiWbtcEth": "0x7A56d65254705B4Def63c68488C0182968C452ce",
        "native.sushiBadgerWbtc": "0x3a494D79AA78118795daad8AeFF5825C6c8dF7F1",
        "native.digg": "0x4a8651F2edD68850B944AD93f2c67af817F39F62",
        "native.uniDiggWbtc": "0xadc8d7322f2E284c1d9254170dbe311E9D3356cf",
        "native.sushiDiggWbtc": "0xaa8dddfe7DFA3C3269f1910d89E4413dD006D08a",
        "experimental.sushiIBbtcWbtc": "0xf4146A176b09C664978e03d28d07Db4431525dAd",
        "experimental.digg": "0xA6af1B913E205B8E9B95D3B30768c0989e942316",
        "native.hbtcCrv": "0xff26f400e57bf726822eacbb64fa1c52f1f27988",
        "native.pbtcCrv": "0x1C1fD689103bbFD701b3B7D41A3807F12814033D",
        "native.obtcCrv": "0x2bb864cdb4856ab2d148c5ca52dd7ccec126d138",
        "native.bbtcCrv": "0x4f3e7a4566320b2709fd1986f2e9f84053d3e2a0",
        "native.tricrypto": "0x05ec4356e1acd89cc2d16adc7415c8c95e736ac1",
        "native.tricrypto2": "0x2eB6479c2f033360C0F4575A88e3b8909Cbc6a03",
        "native.cvxCrv": "0x826048381d65a65DAa51342C51d464428d301896",
        "native.cvx": "0xBCee2c6CfA7A4e29892c3665f464Be5536F16D95",
        "native.mstableImBtc": "0xd409C506742b7f76f164909025Ab29A47e06d30A",
        "native.mstableFpMbtcHbtc": "0x54D06A0E1cE55a7a60Ee175AbCeaC7e363f603f3",
    },
    "yearn_vaults": {"byvWBTC": "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5"},
    "peaks": {
        "badgerPeak": "0x41671BA1abcbA387b9b2B752c205e22e916BE6e3",
        "byvWbtcPeak": "0x825218beD8BE0B30be39475755AceE0250C50627",
    },
    "custodians": {"multiswap": "0x533e3c0e6b48010873B947bddC4721b1bDFF9648"},
    "oracles": {
        "oracle": "0x058ec2Bf15011095a25670b618A129c043e2162E",
        "oracle_provider": "0x72dc16CFa95beB42aeebD2B10F22E55bD17Ce976",
    },
}

ADDRESSES_IBBTC = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_multisig": ADDRESSES_ETH["badger_wallets"]["dev_multisig"],
    "defiDollar_fees": "0x5b5cf8620292249669e1dcc73b753d01543d6ac7",
    "feesink": "0x3b823864cd0cbad8a1f2b65d4807906775becaa7",
    "ibBTC": ADDRESSES_ETH["treasury_tokens"]["ibBTC"],
    "WBTC": ADDRESSES_ETH["treasury_tokens"]["WBTC"],
    "renBTC": "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",
    "badgerPeak": ADDRESSES_ETH["peaks"]["badgerPeak"],
    "byvWbtcPeak": ADDRESSES_ETH["peaks"]["byvWbtcPeak"],
    "bcrvRenBTC": ADDRESSES_ETH["sett_vaults"]["bcrvRenBTC"],
    "bcrvSBTC": ADDRESSES_ETH["sett_vaults"]["bcrvSBTC"],
    "bcrvTBTC": ADDRESSES_ETH["sett_vaults"]["bcrvTBTC"],
    "byvWBTC": ADDRESSES_ETH["yearn_vaults"]["byvWBTC"],
}

ADDRESSES_BSC = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_wallets": {
        "badgertree": "0x660802Fc641b154aBA66a62137e71f331B6d787A",
        "dev_proxy_admin": "0x6354e79f21b56c11f48bcd7c451be456d7102a36",
        "dev_multisig_deprecated": "0x6DA4c138Dd178F6179091C260de643529A2dAcfe",
        "dev_multisig_new": "0x329543f0F4BB134A3f7a826DC32532398B38a3fA",
        "ops_multisig": "0x777061674751834993bfBa2269A1F4de5B4a6E7c",
        "ops_deployer": "0xDA25ee226E534d868f0Dd8a459536b03fEE9079b",
        "ops_guardian": "0x29F7F8896Fb913CF7f9949C623F896a154727919",
        "ops_keeper": "0x872213E29C85d7e30F1C8202FC47eD1Ec124BB1D",
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
        "cakeBdiggBtcbV2": "0x81d776C90c89B8d51E9497D58338933127e2fA80",
        "cakeBbadgerBtcbV2": "0x5A58609dA96469E9dEf3fE344bC39B00d18eb9A5",
    },
    "lp_tokens": {
        "cakebBadgerBtcb": "0x10F461CEAC7A17F59e249954Db0784d42EfF5DB5",
        "cakebDiggBtcb": "0xE1E33459505bB3763843a426F7Fd9933418184ae",
        "cakeBnbBtcb": "0x7561eee90e24f3b348e1087a005f78b4c8453524",
        "cakeBdiggBtcbV2": "0x81d776C90c89B8d51E9497D58338933127e2fA80",
        "cakeBbadgerBtcbV2": "0x5A58609dA96469E9dEf3fE344bC39B00d18eb9A5",
    },
    "sett_vaults": {
        "bcakeBnbBtcb": "0xaf4B9C4b545D5324904bAa15e29796D2E2f90813",
        "bcakebBadgerBtcb": "0x857F91f735f4B03b19D2b5c6E476C73DB8241F55",
        "bcakebDiggBtcb": "0xa861Ba302674b08f7F2F24381b705870521DDfed",
    },
    "coingecko_tokens": {
        "badger-dao": "0x753fbc5800a8C8e3Fb6DC6415810d627A387Dfc9",
        "badger-sett-badger": "0x1F7216fdB338247512Ec99715587bb97BBf96eae",
        "badger-sett-digg": "0x5986D5c77c65e5801a5cAa4fAE80089f870A71dA",
        "binance-bitcoin": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
        "binancecoin": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
        "pancakeswap-token": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
    },
}

ADDRESSES_POLYGON = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_wallets": {
        "badgertree": "0x2C798FaFd37C7DCdcAc2498e19432898Bc51376b",
        "rewardLogger": "0xd0EE2A5108b8800D688AbC834445fd03b3b2738e",
        "ops_multisig": "0xeb7341c89ba46CC7945f75Bd5dD7a04f8FA16327",
        "dev_multisig": "0x4977110Ed3CD5eC5598e88c8965951a47dd4e738",
    },
    "treasury_tokens": {
        "BADGER": "0x1FcbE5937B0cc2adf69772D228fA4205aCF4D9b2",
    },
    "sett_vaults": {
        "bslpibBTCWbtc": '0xEa8567d84E3e54B32176418B4e0C736b56378961',
        "bqlpUsdcWbtc": '0x6B2d4c4bb50274c5D4986Ff678cC971c0260E967',
        "bcrvRenBTC": '0x7B6bfB88904e4B3A6d239d5Ed8adF557B22C10FC',
        "bcrvTricrypto": "0x85E1cACAe9a63429394d68Db59E14af74143c61c"
    },
    "sett_strategies": {
        "bslpibBTCWbtc": '0xDed61Bd8a8c90596D8A6Cf0e678dA04036146963',
        "bqlpUsdcWbtc": '0x809990849D53a5109e0cb9C446137793B9f6f1Eb',
        "bcrvRenBTC": '0xF8F02D0d41C79a1973f65A440C98acAc7eAA8Dc1',
        "bcrvTricrypto": "0xDb0C3118ef1acA6125200139BEaCc5D675F37c9C",
    },
    "guestLists": {
        "bslpibBTCWbtc": '0x35a1E68d6fe09020C58edf30feE827c9050dB3F5',
        "bqlpUsdcWbtc": '0x6Fba2E04D16Ca67E9E918Ecc9A114d822532159F',
        "bcrvRenBTC": '0xde1E5A892b540334E5434aB7880BDb64c4970579'
    },
    "registry": "0xFda7eB6f8b7a9e9fCFd348042ae675d1d652454f",
}

ADDRESSES_ARBITRUM = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_wallets": {
        "badgertree": "0x635EB2C39C75954bb53Ebc011BDC6AfAAcE115A6",
        "techops_multisig": "0xF6BC36280F32398A031A7294e81131aEE787D178",
        "dev_multisig": "0x468A0FF843BC5D185D7B07e4619119259b03619f"
    },
    "sett_vaults": {
        "bslpWbtcWeth": "0xFc13209cAfE8fb3bb5fbD929eC9F11a39e8Ac041",
        "bslpSushiWeth": "0xe774D1FB3133b037AA17D39165b8F45f444f632d",
        "bcrvRenBTC": "0xBA418CDdd91111F5c1D1Ac2777Fa8CEa28D71843",
        "bcrvTricrypto": "0x4591890225394BF66044347653e112621AF7DDeb"
    },
    "strategies": {
        "native.renCrv": "0x4C5d19Da5EaeC298B79879a5f7481bEDE055F4F8",
        "native.tricrypto": "0xE83A790fC3B7132fb8d7f8d438Bc5139995BF5f4",
        "native.sushiWbtcWeth": "0xA6827f0f14D0B83dB925B616d820434697328c22",
        "native.sushiSushiWEth": "0x86f772C82914f5bFD168f99e208d0FC2C371e9C2",
    },
    "treasury_tokens": {
      "BADGER" : "0xbfa641051ba0a0ad1b0acf549a89536a0d76472e",
      "WBTC": "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",
      "CRV": "0x11cdb42b0eb46d95f990bedd4695a6e3fa034978",
      "SUSHI": "0xd4d42f0b6def4ce0383636770ef773390d85c61a",
      "renBTC": "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",
      "slpWbtcEth": "",
    },
    "lp_tokens": {
        "slpWbtcWeth": "0x515e252b2b5c22b4b2b6Df66c2eBeeA871AA4d69",
        "slpSushiWeth": "0x3221022e37029923aCe4235D812273C5A42C322d",
    },
    "crv_pools": {
        "crvRenBTC": "0x3E01dD8a5E1fb3481F0F589056b428Fc308AF0Fb",
    },
    "crv_3_pools": {
        "crvTricrypto": "0x960ea3e3C7FB317332d990873d354E18d7645590"
    },

    "coingecko_tokens": {
        "badger-dao": "0xbfa641051ba0a0ad1b0acf549a89536a0d76472e",
        "wrapped-bitcoin": "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f",
        "curve-dao-token": "0x11cdb42b0eb46d95f990bedd4695a6e3fa034978",
        "sushi": "0xd4d42f0b6def4ce0383636770ef773390d85c61a",
        "renbtc": "0xeb4c2781e4eba804ce9a9803c67d0893436bb27d",
    },
    "controller": "0x3811448236d4274705b81C6ab99d617bfab617Cd",
    "rewardsLogger": "0x85E1cACAe9a63429394d68Db59E14af74143c61c"
}

ADDRESSES_BRIDGE = {
    "zero": "0x0000000000000000000000000000000000000000",
    "badger_multisig": ADDRESSES_ETH["badger_wallets"]["dev_multisig"],
    "badger_bridge_team": "0xE95b56685327C9caf83C3e6F0A54b8D9708f32c4",
    "bridge_v1": "0xcB5c2B0FE765069708f17376981C9aFE56Fed339",
    "bridge_v2": "0xb6ea1d3fb9100a2Cf166FEBe11f24367b5FCD24A",
    "WBTC": ADDRESSES_ETH["treasury_tokens"]["WBTC"],
    "renBTC": ADDRESSES_IBBTC["renBTC"],
    "renvm_darknodes_fee": "0xE33417797d6b8Aec9171d0d6516E88002fbe23E7",
    "unk_curve_1": "0x2393c368c70b42f055a4932a3fbec2ac9c548011",
    "unk_curve_2": "0xfae8bd34190615f3388f38191dc332b44c53e10b",
}


def checksum_address_dict(addresses):
    checksummed = {}
    for k, v in addresses.items():
        if isinstance(v, str):
            checksummed[k] = Web3.toChecksumAddress(v)
        elif isinstance(v, dict):
            checksummed[k] = {
                name: Web3.toChecksumAddress(address) for name, address in v.items()
            }
        else:
            Console.print("Addresses formatted incorrectly")

    return checksummed
