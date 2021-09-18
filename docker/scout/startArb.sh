#!/bin/sh
brownie networks add Ethereum Arb host=$ARBNODEURL chainid=42161
exec brownie run main_arb --network Arb
