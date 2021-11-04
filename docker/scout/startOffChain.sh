#!/bin/sh
brownie networks add Ethereum eth_mock host=$ETHNODEURL chainid=1
exec brownie run main_off_chain --network eth_mock
