import requests
import time
from neo4j import GraphDatabase

# Neo4j ----------------->
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "mehran11"  
DATABASE_NAME = "task1"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Bitcoin API ----------------->
BASE_URL = "https://blockstream.info/api"

def get_block_hash_by_height(height):
    r = requests.get(f"{BASE_URL}/block-height/{height}")
    r.raise_for_status()
    return r.text.strip()

def get_block_txs(block_hash):
    r = requests.get(f"{BASE_URL}/block/{block_hash}/txs")
    r.raise_for_status()
    return r.json()

def btc_from_sats(sats):
    return sats / 100_000_000

# Neo4j Functions ----------------->
def create_address(tx, addr):
    tx.run("MERGE (:Address {address: $addr})", addr=addr)

def create_transaction(tx, sender, receiver, amount, txid):
    tx.run("""
        MATCH (s:Address {address:$sender})
        MATCH (r:Address {address:$receiver})
        MERGE (s)-[:SENT {amount:$amount, txid:$txid}]->(r)
    """, sender=sender, receiver=receiver, amount=amount, txid=txid)

# Main ----------------->
def main():
    max_txs_to_show = 300  # تعداد جهت نمایش و ذخیره در neo4j
    shown = 0

    # .. Block to start ..
    current_height = 421000

    while shown < max_txs_to_show:
        print(f"\nFetching block {current_height}...")
        try:
            block_hash = get_block_hash_by_height(current_height)
            txs = get_block_txs(block_hash)
        except Exception as e:
            print("Error fetching block:", e)
            break

        with driver.session(database=DATABASE_NAME) as session:
            for tx in txs:
                if shown >= max_txs_to_show:
                    break
                shown += 1
                print(f"[Transaction {shown}] {tx['txid']}")

                senders = []
                receivers = []
                
                # if coinbase --->
                if tx['vin'][0].get('is_coinbase', False):

                    print("Inside Coinbase!")
                    # coinbase: فقط گیرنده‌ها را اضافه می‌کنیم
                    for vout in tx["vout"]:
                        addr = vout.get("scriptpubkey_address")
                        value = btc_from_sats(vout.get("value", 0))

                        if not addr:
                            addr = vout.get("scriptpubkey")

                        if addr:
                            receivers.append((addr, value))
                            session.execute_write(create_address, addr)
                    continue

                # فرستنده‌ها
                for vin in tx["vin"]:
                    if vin.get("prevout"):
                        addr = vin["prevout"].get("scriptpubkey_address")
                        if addr:
                            senders.append(addr)
                            session.execute_write(create_address, addr)

                # گیرنده‌ها
                for vout in tx["vout"]:
                    addr = vout.get("scriptpubkey_address")
                    value = btc_from_sats(vout.get("value", 0))
                    if addr:
                        receivers.append((addr, value))
                        session.execute_write(create_address, addr)

                # ایجاد فرستنده → گیرنده
                for sender in senders:
                    for receiver, value in receivers:
                        session.execute_write(create_transaction, sender, receiver, value, tx['txid'])

        current_height += 1
        time.sleep(0.3)

    print(f"\nDone! {shown} transactions imported to Neo4j.")

if __name__ == "__main__":
    main()


## Bitcoin txs (Json Form) ----->

# {
#   "txid": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
#   "version": 2,
#   "locktime": 0,
#   "vin": [
#     {
#       "txid": "c0ffee1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
#       "vout": 0,
#       "prevout": {
#         "scriptpubkey": "76a91489abcdefabbaabbaabbaabbaabbaabbaabba88ac",
#         "scriptpubkey_asm": "OP_DUP OP_HASH160 89abcdefabbaabbaabbaabbaabbaabbaabba88 OP_EQUALVERIFY OP_CHECKSIG",
#         "scriptpubkey_type": "p2pkh",
#         "scriptpubkey_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
#         "value": 5000000000
#       },
#       "scriptsig": "483045022100f3...",
#       "scriptsig_asm": "OP_PUSH 3045022100f3...",
#       "sequence": 4294967295
#     }
#   ],
#   "vout": [
#     {
#       "scriptpubkey": "76a914abcdefabcdefabcdefabcdefabcdefabcdef88ac",
#       "scriptpubkey_asm": "OP_DUP OP_HASH160 abcdefabcdefabcdefabcdefabcdefabcdef88 OP_EQUALVERIFY OP_CHECKSIG",
#       "scriptpubkey_type": "p2pkh",
#       "scriptpubkey_address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
#       "value": 4999000000
#     },
#     {
#       "scriptpubkey": "76a914feedfacefeedfacefeedfacefeedfacefeed88ac",
#       "scriptpubkey_asm": "OP_DUP OP_HASH160 feedfacefeedfacefeedfacefeedfacefeed88 OP_EQUALVERIFY OP_CHECKSIG",
#       "scriptpubkey_type": "p2pkh",
#       "scriptpubkey_address": "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
#       "value": 1000000
#     }
#   ],
#   "size": 225,
#   "weight": 900,
#   "fee": 10000
# }

