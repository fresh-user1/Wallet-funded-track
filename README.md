# Wallet Funder Tracker

A Python script that monitors new token pairs created on Uniswap V2/BaseSwap on the Base network and traces back to find the "Funder Wallet" - the wallet that initially funded the deployer address.

## Features

- 🔍 Monitors new pair creation events on BaseSwap (Uniswap V2 compatible) on Base network
- 📍 Extracts deployer address from each new pair
- 🔙 Traces back the first incoming transaction to the deployer to find the funder wallet
- 📊 Real-time monitoring with detailed output

## How It Works

1. **Monitor PairCreated Events**: The script listens to `PairCreated` events from the BaseSwap factory contract
2. **Get Deployer Address**: When a new pair is detected, it extracts the transaction sender (deployer)
3. **Trace Funder Wallet**: It searches backwards through blockchain history to find the first transaction sent TO the deployer address
4. **Output Results**: Prints the funder wallet address along with pair and deployer information

## Prerequisites

- Python 3.7 or higher
- Internet connection to access Base network RPC

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Wallet-funded-track
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file to configure custom RPC URL:
```bash
cp .env.example .env
# Edit .env and add your RPC URL if needed
```

## Usage

Run the script:
```bash
python main.py
```

The script will:
- Connect to the Base network
- Start monitoring from the current block
- Display information about each new pair detected
- Print the funder wallet address for each deployer

### Sample Output

```
================================================================================
WALLET FUNDER TRACKER - Base Network
================================================================================

Connecting to Base network: https://mainnet.base.org
✓ Connected successfully!
✓ Current block: 12345678

Monitoring new pairs on BaseSwap Factory: 0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB
Connected to Base network: https://mainnet.base.org
--------------------------------------------------------------------------------
Starting from block: 12345678

Checking blocks 12345679 to 12345680...

================================================================================
NEW PAIR DETECTED!
================================================================================
Block Number: 12345680
Transaction: 0xabc123...
Pair Address: 0x1234567890abcdef...
Token0: 0xToken0Address...
Token1: 0xToken1Address...
--------------------------------------------------------------------------------
Deployer Address: 0xDeployerAddress...
Tracing back to find funder wallet...

🎯 FUNDER WALLET FOUND: 0xFunderWalletAddress...
================================================================================
```

## Configuration

### Environment Variables

You can customize the script behavior using environment variables:

- `BASE_RPC_URL`: Custom RPC endpoint for Base network (default: `https://mainnet.base.org`)

Create a `.env` file:
```
BASE_RPC_URL=https://your-custom-rpc-url.com
```

### Constants

You can modify these constants in `main.py`:

- `BASESWAP_FACTORY`: Factory contract address (default: BaseSwap on Base)
- `search_limit` in `get_funder_wallet()`: Number of blocks to search backwards (default: 5000)
- `poll_interval`: Seconds between polling for new events (default: 2)

## Technical Details

### BaseSwap Factory
- Address: `0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB`
- Network: Base (Chain ID: 8453)
- Compatible with Uniswap V2

### Event Monitoring
The script monitors the `PairCreated` event:
```solidity
event PairCreated(
    address indexed token0,
    address indexed token1,
    address pair,
    uint256
);
```

### Funder Wallet Detection
The funder wallet is identified as the address that sent the first transaction TO the deployer address. This is typically the wallet that funded the deployer with initial gas fees or tokens.

## Limitations

- The script searches backwards through a limited number of blocks (default: 2000 for funder tracing)
- For very old deployer addresses, the funder might not be found if it's beyond the search limit
- Requires a stable connection to a Base network RPC endpoint with good historical data access
- Public RPC endpoints may have rate limits
- Funder tracing can take several minutes per pair and uses many RPC calls

## Troubleshooting

### Connection Issues
If you cannot connect to the Base network:
1. Check your internet connection
2. Try a different RPC URL (Alchemy, Infura, QuickNode, etc.)
3. Verify the RPC endpoint supports the Base network

### Rate Limiting
If you experience rate limiting:
1. Use a private RPC endpoint
2. Increase the `poll_interval` in the script
3. Consider using a paid RPC provider for higher limits

### Funder Not Found
If the funder wallet is not found:
1. The deployer might be very old (beyond search limit)
2. Increase `search_limit` in `get_funder_wallet()` function
3. Consider using an archive node for historical data

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for educational and research purposes only. Always verify the information independently before making any decisions based on the output.
