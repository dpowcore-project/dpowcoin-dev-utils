## Genesis Block Proof of Work for multiple Hash Algorithms for python 3.7.x + ( test at 3.9.2 )!.


## setup

```js

sudo pip install construct==2.5.2

sudo pip install dpowcoin-yespower

sudo pip install argon2-cffi==23.1.0


cd genesis-block

```

## help

```js 
Usage: gen.py [options]
    
    Options:
      -h, --help show this help message and exit
      -t TIME, --time=TIME  the (unix) time when the genesisblock is created
      -z TIMESTAMP, --timestamp=TIMESTAMP
         the pszTimestamp found in the coinbase of the genesisblock
      -n NONCE, --nonce=NONCE
         the first value of the nonce that will be incremented
         when searching the genesis hash
      -a ALGORITHM, --algorithm=ALGORITHM
         the PoW algorithm: [X11|neoscrypt|quark|qubit|keccak|lyra2re]
      -p PUBKEY, --pubkey=PUBKEY
         the pubkey found in the output script
      -v VALUE, --value=VALUE
         the value in coins for the output, full value (exp. in bitcoin 5000000000 - To get other coins value: Block Value * 100000000)
      -b BITS, --bits=BITS
         the target in compact representation, associated to a difficulty of 1
```



## Genesis Block Proof of Work for SHA256 Algorithms.

```js
python3 gen.py -z "One POW? Why not two? 17/04/2024" -p "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f" -a dpowcoin -b 0x1f1fffff -t 1713510000 -n 8808588

```

## Genesis Block Proof of Work for dpowcoin Algorithms.

```js
python3 gen8.py -z "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks" -p "04678afdb0fe5548271967f1a67130b7105cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b8d578a4c702b6bf11d5f" -a SHA256 -b 0x1d00ffff -t 1231006505 -n 2083236893

```