#!/bin/sh
brownie networks add Ethereum bsc host=$ETHNODEURL chainid=56
exec  brownie run main_bsc --network bsc

