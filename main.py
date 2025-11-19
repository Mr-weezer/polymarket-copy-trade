import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware
import time
from dotenv import load_dotenv
import os

load_dotenv()

# --- CONFIGURATION ---
INFURA_URL = os.getenv("INFURA_URL")
WALLET_TO_WATCH = os.getenv("WATCH_WALLET_ADDRESS")
print(INFURA_URL, WALLET_TO_WATCH)
POLL_INTERVAL = 2

target_address = None 

async def send_alert(tx_hash, tx_type, value, sender, receiver):
    print(f"\n🚨 ALERTE : Nouvelle Transaction détectée !")
    print(f"Type: {tx_type}")
    print(f"Hash: {tx_hash}")
    print(f"De: {sender}")
    print(f"Vers: {receiver}")
    print(f"Valeur: {value} MATIC")
    print("-" * 30)

async def process_block(w3, block_number):
    try:
        block = await w3.eth.get_block(block_number, full_transactions=True)
        
        print(f"🔍 Analyse du bloc {block_number} ({len(block.transactions)} txs)...", end='\r')

        for tx in block.transactions:
            tx_to = tx['to']
            tx_from = tx['from']
            
            if tx_to == target_address or tx_from == target_address:
                tx_type = "ENTRANTE 🟢" if tx_to == target_address else "SORTANTE 🔴"
                
                value_matic = float(w3.from_wei(tx['value'], 'ether'))
                
                await send_alert(tx['hash'].hex(), tx_type, value_matic, tx_from, tx_to)

    except Exception as e:
        print(f"\nErreur lors de l'analyse du bloc {block_number}: {e}")

async def main():
    global target_address
    
    w3 = AsyncWeb3(AsyncHTTPProvider(INFURA_URL))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if await w3.is_connected():
        print(f"✅ Connecté à Polygon via Infura")
    else:
        print("❌ Échec de connexion")
        return

    target_address = w3.to_checksum_address(WALLET_TO_WATCH)
    print(f"👀 Surveillance du wallet : {target_address}\n")

    latest_processed_block = await w3.eth.block_number

    while True:
        try:
            current_block = await w3.eth.block_number
            
            if current_block > latest_processed_block:
                for block_num in range(latest_processed_block + 1, current_block + 1):
                    await process_block(w3, block_num)
                
                latest_processed_block = current_block
            
            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"\nErreur dans la boucle principale : {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nArrêt du script.")