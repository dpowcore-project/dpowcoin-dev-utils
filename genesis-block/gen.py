import hashlib
import binascii
import struct
import array
import os
import time
import sys
import optparse
from construct import *

import dpowcoin_yespower
import argon2

def GetArgon2idHash(input, salts, cost):
    hash = argon2.low_level.hash_secret_raw(
        time_cost=2, memory_cost=cost, parallelism=2,
        hash_len=32, secret=input, salt=salts,
        type=argon2.low_level.Type.ID,
    )
    return hash


def main():
    options = get_args()
    
    algorithm = get_algorithm(options)
    
    input_script  = create_input_script(options.timestamp)
    output_script = create_output_script(options.pubkey)
    tx = create_transaction(input_script, output_script,options)
    hash_merkle_root = hashlib.sha256(hashlib.sha256(tx).digest()).digest()
    print_block_info(options, hash_merkle_root)
    
    block_header = create_block_header(hash_merkle_root, options.time, options.bits, options.nonce)
    genesis_hash, nonce, sha256_hash, header_hash1 = generate_hash(block_header, algorithm, options.nonce, options.bits)
    announce_found_genesis(genesis_hash, nonce, sha256_hash, header_hash1)


def get_args():
    parser = optparse.OptionParser()
    parser.add_option("-t", "--time", dest="time", default=int(time.time()), type="int", help="the (unix) time when the genesisblock is created")
    parser.add_option("-z", "--timestamp", dest="timestamp", default="The Times 03/Jan/2009 Chancellor on brink of second bailout for banks", type="string", help="the pszTimestamp found in the coinbase of the genesisblock")
    parser.add_option("-n", "--nonce", dest="nonce", default=0, type="int", help="the first value of the nonce that will be incremented when searching the genesis hash")
    parser.add_option("-a", "--algorithm", dest="algorithm", default="SHA256", help="the PoW algorithm: [SHA256|scrypt|dpowcoin]")
    parser.add_option("-p", "--pubkey", dest="pubkey", default="040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9", type="string", help="the pubkey found in the output script")
    parser.add_option("-v", "--value", dest="value", default=5000000000, type="int", help="the value in coins for the output, full value (exp. in bitcoin 5000000000 - To get other coins value: Block Value * 100000000)")
    parser.add_option("-b", "--bits", dest="bits", type="int", help="the target in compact representation, associated to a difficulty of 1")

    (options, args) = parser.parse_args()
    if not options.bits:
        if options.algorithm == "scrypt" or options.algorithm == "dpowcoin":
            options.bits = 0x1e0ffff0
        else:
            options.bits = 0x1d00ffff
    return options

def get_algorithm(options):
    supported_algorithms = ["SHA256", "scrypt", "dpowcoin"]
    if options.algorithm in supported_algorithms:
        return options.algorithm
    else:
        sys.exit("Error: Given algorithm must be one of: " + str(supported_algorithms))

def create_input_script(psz_timestamp):
    psz_prefix = ""
    if len(psz_timestamp) > 76:
        psz_prefix = '4c'

    script_prefix = '04ffff001d0104' + psz_prefix + binascii.hexlify(chr(len(psz_timestamp)).encode()).decode()
    return binascii.unhexlify((script_prefix + binascii.hexlify(psz_timestamp.encode()).decode()).encode())


def create_output_script(pubkey):
    script_len = '41'
    OP_CHECKSIG = 'ac'
    return binascii.unhexlify((script_len + pubkey + OP_CHECKSIG).encode())


def create_transaction(input_script, output_script,options):
    transaction = Struct("transaction",
                        Bytes("version", 4),
                        Byte("num_inputs"),
                        StaticField("prev_output", 32),
                        UBInt32('prev_out_idx'),
                        Byte('input_script_len'),
                        Bytes('input_script', len(input_script)),
                        UBInt32('sequence'),
                        Byte('num_outputs'),
                        Bytes('out_value', 8),
                        Byte('output_script_len'),
                        Bytes('output_script',  0x43),
                        UBInt32('locktime'))

    tx = transaction.parse(b'\x00'*(127 + len(input_script)))
    tx.version           = struct.pack('<I', 1)
    tx.num_inputs        = 1
    tx.prev_output       = struct.pack('<qqqq', 0,0,0,0)
    tx.prev_out_idx      = 0xFFFFFFFF
    tx.input_script_len  = len(input_script)
    tx.input_script      = input_script
    tx.sequence          = 0xFFFFFFFF
    tx.num_outputs       = 1
    tx.out_value         = struct.pack('<q' ,options.value)#0x000005f5e100)#012a05f200) #50 coins
    tx.output_script_len = 0x43
    tx.output_script     = output_script
    tx.locktime          = 0 
    return transaction.build(tx)


def create_block_header(hash_merkle_root, time, bits, nonce):
    block_header = Struct("block_header",
                         Bytes("version",4),
                         Bytes("hash_prev_block", 32),
                         Bytes("hash_merkle_root", 32),
                         Bytes("time", 4),
                         Bytes("bits", 4),
                         Bytes("nonce", 4))
    
    genesisblock = block_header.parse(b'\x00'*80)
    genesisblock.version          = struct.pack('<I', 1)
    genesisblock.hash_prev_block  = struct.pack('<qqqq', 0,0,0,0)
    genesisblock.hash_merkle_root = hash_merkle_root
    genesisblock.time             = struct.pack('<I', time)
    genesisblock.bits             = struct.pack('<I', bits)
    genesisblock.nonce            = struct.pack('<I', nonce)
    return block_header.build(genesisblock)


def generate_hash(data_block, algorithm, start_nonce, bits):
    print('Searching for genesis hash..')
    nonce = start_nonce
    last_updated = time.time()
    target = (bits & 0xffffff) * 2**(8*((bits >> 24) - 3))
    max_nonce = 0xFFFFFFFF
    
    while True:
        sha256_hash, header_hash, header_hash1 = generate_hashes_from_block(data_block, algorithm)
        last_updated = calculate_hashrate(nonce, last_updated)
        if is_genesis_hash(header_hash, header_hash1, target):
            if algorithm == "yespower" or algorithm == "dpowcoin":
                return (header_hash, nonce, sha256_hash, header_hash1)
            return (sha256_hash, nonce, sha256_hash, header_hash1 )
        else:
            nonce += 1
            data_block = data_block[0:len(data_block) - 4] + struct.pack('<I', nonce)  
        
        if nonce == max_nonce:
            print("All nonces exhausted. Starting next round...")
            nonce = start_nonce
            last_updated = time.time()
            print("Update time to:", last_updated)

def generate_hashes_from_block(data_block, algorithm):
    sha256_hash = hashlib.sha256(hashlib.sha256(data_block).digest()).digest()[::-1]
    sha512_hash = hashlib.sha256(hashlib.sha256(hashlib.sha512(hashlib.sha512(data_block).digest()).digest()).digest()).digest()[::-1]
    header_hash = b""
    header_hash1 = b""
    if algorithm == 'dpowcoin':
        try:
            import dpowcoin_yespower
        except ImportError:
            sys.exit("Cannot run dpowcoin_yespower algorithm: module bitweb_yespower not found")
        data_sha512 = hashlib.sha512(hashlib.sha512(data_block).digest()).digest()
        data_argon2id = GetArgon2idHash(data_block, data_sha512, 4096)
        header_hash = GetArgon2idHash(data_block, data_argon2id, 32768)[::-1]
        header_hash1 = dpowcoin_yespower.getPoWHash(data_block)[::-1]
    elif algorithm == 'scrypt':
        header_hash = scrypt.hash(data_block, data_block, 1024, 1, 1, 32)[::-1]
        header_hash1 = scrypt.hash(data_block, data_block, 1024, 1, 1, 32)[::-1]
    elif algorithm == 'SHA256':
        header_hash = sha256_hash
        header_hash1 = sha256_hash
    return sha256_hash, header_hash, header_hash1

def is_genesis_hash(header_hash, header_hash1, target):
    return (int(binascii.hexlify(header_hash), 16) < target)  and \
           (int(binascii.hexlify(header_hash1), 16) < target)

def calculate_hashrate(nonce, last_updated):
    if nonce % 1000000 == 999999:
        now             = time.time()
        hashrate        = round(1000000/(now - last_updated))
        generation_time = round(pow(2, 32) / hashrate / 3600, 1)
        sys.stdout.write("\r%s hash/s, estimate: %s h"%(str(hashrate), str(generation_time)))
        sys.stdout.flush()
        return now
    else:
        return last_updated

def print_block_info(options, hash_merkle_root):
    print("algorithm: " + (options.algorithm))
    print("merkle hash: " + binascii.hexlify(hash_merkle_root[::-1]).decode())
    print("pszTimestamp: " + options.timestamp)
    print("pubkey: " + options.pubkey)
    print("time: " + str(options.time))
    print("bits: " + str(hex(options.bits)))

def announce_found_genesis(genesis_hash, nonce, sha256_hash, header_hash1):
    print("genesis hash found!")
    print("nonce: " + str(nonce))
    print("genesis hash : " + binascii.hexlify(genesis_hash).decode())
    print("genesis hash1 : " + binascii.hexlify(header_hash1).decode())
    print("genesis hash (SHA256): " + binascii.hexlify(sha256_hash).decode())

# GOGOGO!
main()
