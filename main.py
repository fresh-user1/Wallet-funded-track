"""
Wallet Funder Tracker for Base Network
Monitors new token pairs on BaseSwap/Uniswap V2 and traces back to find funder wallets
"""

import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base network RPC URL (public endpoint)
# Users can override this with their own RPC URL via environment variable
# Multiple fallback options for better connectivity
BASE_RPC_URLS = [
    os.getenv('BASE_RPC_URL', 'https://mainnet.base.org'),
    'https://base.llamarpc.com',
    'https://base-rpc.publicnode.com',
    'https://1rpc.io/base',
]

# BaseSwap Factory Address on Base (Uniswap V2 compatible)
# This is the factory contract that creates new pairs
BASESWAP_FACTORY = '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB'

# Uniswap V2 Factory ABI (minimal - just PairCreated event)
FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "token0", "type": "address"},
            {"indexed": True, "name": "token1", "type": "address"},
            {"indexed": False, "name": "pair", "type": "address"},
            {"indexed": False, "name": "allPairsLength", "type": "uint256"}
        ],
        "name": "PairCreated",
        "type": "event"
    }
]


def get_deployer_address(w3, pair_address):
    """
    Get the deployer address of a contract by finding the transaction that created it.
    
    Args:
        w3: Web3 instance
        pair_address: Address of the pair contract
        
    Returns:
        Address of the deployer (transaction sender)
    """
    try:
        # Get the contract creation transaction
        # We need to search through blocks to find when this contract was created
        # For efficiency, we'll trace the contract code and find its creation
        
        # Get the current block
        current_block = w3.eth.block_number
        
        # Search backwards from current block (limited search)
        # In a production system, you might want to use an indexer or archive node
        search_limit = 1000  # Search last 1000 blocks
        
        for block_num in range(current_block, max(0, current_block - search_limit), -1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            
            for tx in block['transactions']:
                # Check if this transaction created the pair contract
                if tx['to'] is None:  # Contract creation
                    receipt = w3.eth.get_transaction_receipt(tx['hash'])
                    if receipt['contractAddress'] and receipt['contractAddress'].lower() == pair_address.lower():
                        return tx['from']
                        
                # Also check if transaction is to the factory creating this pair
                if tx['to'] and tx['to'].lower() == BASESWAP_FACTORY.lower():
                    receipt = w3.eth.get_transaction_receipt(tx['hash'])
                    # Check logs for PairCreated event with our pair address
                    for log in receipt['logs']:
                        if len(log['topics']) > 0:
                            # Check if this is a PairCreated event
                            try:
                                if log['address'].lower() == BASESWAP_FACTORY.lower():
                                    # Decode the pair address from event data
                                    # The pair address is in the data field (non-indexed)
                                    pair_from_log = '0x' + log['data'][-40:]
                                    if pair_from_log.lower() == pair_address.lower():
                                        return tx['from']
                            except (ValueError, KeyError, IndexError) as e:
                                continue
        
        # If we couldn't find it in recent blocks, return None
        print(f"Warning: Could not find deployer for {pair_address} in last {search_limit} blocks")
        return None
        
    except Exception as e:
        print(f"Error getting deployer address: {e}")
        return None


def get_funder_wallet(w3, deployer_address):
    """
    Find the funder wallet by tracing the first incoming transaction to the deployer address.
    
    Args:
        w3: Web3 instance
        deployer_address: Address of the deployer
        
    Returns:
        Address of the funder wallet (sender of first transaction to deployer)
    """
    try:
        # Get current block
        current_block = w3.eth.block_number
        
        # Search backwards through blocks to find first transaction TO this address
        # We'll search a reasonable number of blocks
        search_limit = 2000  # Reduced from 5000 for better performance
        
        first_incoming_tx = None
        first_block_num = float('inf')  # Track the earliest block number
        
        # Search backwards from current to past
        for block_num in range(current_block, max(0, current_block - search_limit), -1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    # Check if this transaction is TO the deployer address
                    if tx['to'] and tx['to'].lower() == deployer_address.lower():
                        # This is an incoming transaction
                        # Keep track of the earliest (first) one
                        if block_num < first_block_num:
                            first_block_num = block_num
                            first_incoming_tx = tx
                            
            except Exception as e:
                # Skip blocks that cause errors and continue searching
                continue
        
        if first_incoming_tx:
            return first_incoming_tx['from']
        else:
            print(f"Warning: Could not find incoming transaction for {deployer_address} in last {search_limit} blocks")
            return None
            
    except Exception as e:
        print(f"Error getting funder wallet: {e}")
        return None


def monitor_new_pairs(w3, factory_contract, rpc_url, poll_interval=2):
    """
    Monitor new pair creation events and trace back to funder wallets.
    
    Args:
        w3: Web3 instance
        factory_contract: Factory contract instance
        rpc_url: RPC URL being used
        poll_interval: Seconds between polling for new events
    """
    print(f"Monitoring new pairs on BaseSwap Factory: {BASESWAP_FACTORY}")
    print(f"Connected to Base network: {rpc_url}")
    print("-" * 80)
    
    # Get the latest block to start monitoring from
    latest_block = w3.eth.block_number
    print(f"Starting from block: {latest_block}\n")
    
    processed_pairs = set()  # Keep track of processed pairs to avoid duplicates
    consecutive_failures = 0  # Track consecutive failures
    MAX_CONSECUTIVE_FAILURES = 10  # Exit after 10 consecutive failures
    
    try:
        while True:
            try:
                # Get current block
                current_block = w3.eth.block_number
                
                # Check for new PairCreated events
                if current_block > latest_block:
                    print(f"Checking blocks {latest_block + 1} to {current_block}...")
                    
                    # Get PairCreated events in the new blocks
                    pair_filter = factory_contract.events.PairCreated.create_filter(
                        fromBlock=latest_block + 1,
                        toBlock=current_block
                    )
                    
                    events = pair_filter.get_all_entries()
                    
                    for event in events:
                        pair_address = event['args']['pair']
                        token0 = event['args']['token0']
                        token1 = event['args']['token1']
                        block_number = event['blockNumber']
                        tx_hash = event['transactionHash'].hex()
                        
                        # Skip if already processed
                        if pair_address in processed_pairs:
                            continue
                            
                        processed_pairs.add(pair_address)
                        
                        print(f"\n{'='*80}")
                        print(f"NEW PAIR DETECTED!")
                        print(f"{'='*80}")
                        print(f"Block Number: {block_number}")
                        print(f"Transaction: {tx_hash}")
                        print(f"Pair Address: {pair_address}")
                        print(f"Token0: {token0}")
                        print(f"Token1: {token1}")
                        print("-" * 80)
                        
                        # Get the transaction that created this pair
                        tx = w3.eth.get_transaction(event['transactionHash'])
                        deployer_address = tx['from']
                        
                        print(f"Deployer Address: {deployer_address}")
                        
                        # Get the funder wallet
                        print("Tracing back to find funder wallet...")
                        print("⚠️  Note: This may take a few minutes as it searches through historical blocks")
                        funder_wallet = get_funder_wallet(w3, deployer_address)
                        
                        if funder_wallet:
                            print(f"\n🎯 FUNDER WALLET FOUND: {funder_wallet}")
                        else:
                            print(f"\n⚠️  Could not find funder wallet for deployer {deployer_address}")
                        
                        print(f"{'='*80}\n")
                    
                    latest_block = current_block
                    consecutive_failures = 0  # Reset on success
                
                # Wait before next poll
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                # Allow clean exit on Ctrl+C
                raise
            except Exception as e:
                consecutive_failures += 1
                print(f"Error in monitoring loop (failure {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}")
                
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"\n❌ Exiting after {MAX_CONSECUTIVE_FAILURES} consecutive failures")
                    sys.exit(1)
                
                # Wait before retrying
                time.sleep(poll_interval * 2)
                continue
                
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        sys.exit(0)


def main():
    """Main function to start monitoring."""
    print("=" * 80)
    print("WALLET FUNDER TRACKER - Base Network")
    print("=" * 80)
    print()
    
    # Try to connect to Base network with fallback RPC URLs
    w3 = None
    connected_rpc = None
    
    # Get custom timeout from environment or use default
    rpc_timeout = int(os.getenv('RPC_TIMEOUT', '60'))  # Default 60 seconds
    
    for rpc_url in BASE_RPC_URLS:
        try:
            print(f"Attempting connection to: {rpc_url}")
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': rpc_timeout}))
            
            # Check connection
            if w3.is_connected():
                # Test by getting current block
                current_block = w3.eth.block_number
                connected_rpc = rpc_url
                print(f"✓ Connected successfully!")
                print(f"✓ Current block: {current_block}")
                print()
                break
            else:
                print(f"✗ Connection failed")
        except Exception as e:
            print(f"✗ Connection failed: {str(e)[:100]}")
            continue
    
    if not w3 or not connected_rpc:
        print("\n" + "=" * 80)
        print("ERROR: Could not connect to Base network")
        print("=" * 80)
        print("\nTried the following RPC endpoints:")
        for url in BASE_RPC_URLS:
            print(f"  - {url}")
        print("\nPlease try:")
        print("1. Check your internet connection")
        print("2. Set a custom RPC URL via environment variable:")
        print("   export BASE_RPC_URL='https://your-rpc-endpoint.com'")
        print("3. Get a free RPC endpoint from:")
        print("   - Alchemy: https://www.alchemy.com/")
        print("   - Infura: https://www.infura.io/")
        print("   - QuickNode: https://www.quicknode.com/")
        sys.exit(1)
    
    try:
        # Create factory contract instance
        factory_contract = w3.eth.contract(
            address=Web3.to_checksum_address(BASESWAP_FACTORY),
            abi=FACTORY_ABI
        )
        
        # Start monitoring
        monitor_new_pairs(w3, factory_contract, connected_rpc)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
