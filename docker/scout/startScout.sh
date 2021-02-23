#!/bin/sh
brownie networks add Ethereum mynetwork host=$ETHNODEURL chainid=1
exec  brownie run main --network mynetwork

