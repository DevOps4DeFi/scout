#!/bin/sh
brownie networks add Ethereum eth host=$ETHNODEURL chainid=1
exec brownie run main_ibbtc --network eth
