def test_get_sett_data():
    from scripts.data import get_sett_data
    get_sett_data()


def test_get_treasury_data():
    from scripts.data import get_treasury_data
    get_treasury_data()


def test_get_digg_data():
    from scripts.data import get_digg_data
    get_digg_data()

def test_get_json_request():
    from scripts.data import get_json_request
    tokens = {
        "badger": "0x3472A5A71965499acd81997a54BBA8D852C6E53d", "digg": "0x798D1bE841a82a273720CE31c822C61a67a601C3"
        }
    response = get_json_request(url=f'https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses={tokens["badger"]}&vs_currencies=btc%2Cusd', request_type='get')
    print(response)