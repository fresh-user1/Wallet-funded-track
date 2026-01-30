"""
Example Usage and Testing Guide for Wallet Funder Tracker
"""

# Example of how the script works:

## Step 1: Script monitors PairCreated events
# When a new token pair is created on BaseSwap, it emits a PairCreated event:
# Event PairCreated(
#     address indexed token0,
#     address indexed token1,
#     address pair,
#     uint256 allPairsLength  # Total number of pairs created
# )

## Step 2: Extract deployer address
# The deployer is the address that sent the transaction creating the pair
# This is found in the transaction's 'from' field

## Step 3: Trace back to funder wallet
# The funder wallet is identified by searching backwards through blocks
# to find the first transaction sent TO the deployer address
# This is typically the wallet that funded the deployer with initial gas

## Example flow:
"""
New Pair Created:
  Pair Address: 0xABCD1234...
  Token0: 0xToken0Addr...
  Token1: 0xToken1Addr...
  
  ↓

Transaction Analysis:
  Transaction Hash: 0x123abc...
  Deployer (tx.from): 0xDeployer123...
  
  ↓

Funder Tracing (search backwards):
  Block N-1000: No transaction to 0xDeployer123...
  Block N-500:  No transaction to 0xDeployer123...
  Block N-100:  Found! tx.to = 0xDeployer123...
                     tx.from = 0xFunder456... ← FUNDER WALLET
"""

## Running the script:
# 1. Install dependencies:
#    pip install -r requirements.txt
#
# 2. (Optional) Set custom RPC:
#    export BASE_RPC_URL='https://your-rpc-endpoint.com'
#
# 3. Run the script:
#    python main.py
#
# 4. The script will:
#    - Connect to Base network
#    - Monitor for new PairCreated events
#    - Extract deployer address
#    - Trace back to find funder wallet
#    - Print results in real-time

## Expected Output Format:
"""
================================================================================
NEW PAIR DETECTED!
================================================================================
Block Number: 12345678
Transaction: 0xabc123def456...
Pair Address: 0x1234567890abcdef...
Token0: 0xToken0Address...
Token1: 0xToken1Address...
--------------------------------------------------------------------------------
Deployer Address: 0xDeployerAddress...
Tracing back to find funder wallet...

🎯 FUNDER WALLET FOUND: 0xFunderWalletAddress...
================================================================================
"""

## Network Requirements:
# - Stable internet connection
# - Access to Base network RPC (default: https://mainnet.base.org)
# - For better reliability, use a paid RPC provider:
#   * Alchemy (https://www.alchemy.com/)
#   * Infura (https://www.infura.io/)
#   * QuickNode (https://www.quicknode.com/)

## Limitations:
# - Searches limited number of blocks (default: 2000 for funder tracing)
# - Public RPC endpoints may have rate limits
# - Very old deployers might not be found within search limit

## Customization:
# You can modify constants in main.py:
# - BASESWAP_FACTORY: Factory contract address
# - search_limit: Number of blocks to search backwards
# - poll_interval: Seconds between polling for new events
# - BASE_RPC_URLS: List of RPC endpoints to try

print("This is an example/documentation file.")
print("To run the actual tracker, execute: python main.py")
