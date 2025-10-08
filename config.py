import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL')

# Blockchain RPC Endpoints
RPC_ENDPOINTS = {
    'ETH': os.getenv('ETH_RPC_URL', 'https://mainnet.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb'),
    'BSC': os.getenv('BSC_RPC_URL', 'https://bsc-dataseed.binance.org/'),
    'SEPOLIA': os.getenv('SEPOLIA_RPC_URL', 'https://sepolia.infura.io/v3/7294966a87974f75ae25d7835d2eb8bb')
}

"""DEX contract configuration for mainnets"""
PANCAKESWAP_CONTRACT = {
    'BSC': {
        'address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',  # PancakeSwap V2 Router (BSC Mainnet)
        'router': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        'factory': '0xCA143Ce32Fe78f1f7019d7d551a6402fC5350c73',  # PancakeSwap V2 Factory
        'wbnb': '0xBB4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'    # WBNB (BSC Mainnet)
    }
}

# Uniswap V2 Contract Configuration (Ethereum Mainnet & Sepolia Testnet)
UNISWAP_CONTRACT = {
    'ETH': {
        'address': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2 Router (ETH Mainnet)
        'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
        'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',   # Uniswap V2 Factory
        'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'      # WETH (ETH Mainnet)
    },
    'SEPOLIA': {
        'address': '0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3',  # Uniswap V2 Router (Sepolia Testnet)
        'router': '0xeE567Fe1712Faf6149d80dA1E6934E354124CfE3',
        'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',   # Uniswap V2 Factory (same as mainnet)
        'weth': '0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14'      # WETH (Sepolia Testnet)
    }
}

# Trading Configuration
TRADING_CONFIG = {
    'BSC': {
        'enabled': True,
        'min_amount': 0.001,
        'max_amount': 10.0,
        'slippage': 0.5,
        'gas_limit': 800000  # Increased for faster processing
    },
    'ETH': {
        'enabled': True,
        'min_amount': 0.001,
        'max_amount': 10.0,
        'slippage': 0.5,
        'gas_limit': 1000000  # Increased for faster processing
    },
    'SEPOLIA': {
        'enabled': True,
        'min_amount': 0.001,
        'max_amount': 10.0,
        'slippage': 0.5,
        'gas_limit': 1000000  # Increased for faster processing
    }
}

# Encryption Configuration
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-secret-encryption-key-32-chars')

# Supported Chains
SUPPORTED_CHAINS = ['ETH', 'BSC', 'SEPOLIA']

# Menu States
MENU_STATES = {
    'MAIN': 'main',
    'BUY_SELL': 'buy_sell',
    'WALLET': 'wallet',
    'BALANCE': 'balance',
    'SETTINGS': 'settings',
    'TRANSFER': 'transfer',
    'TOKEN_SCANNER': 'token_scanner'
}

# Conversation states for trading
TRADING_STATES = {
    'WAITING_FOR_AMOUNT': 10,
    'WAITING_FOR_TOKEN_ADDRESS': 11,
    'WAITING_FOR_TRADE_CONFIRMATION': 12
}
