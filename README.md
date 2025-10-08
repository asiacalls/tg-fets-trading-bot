# 🤖 TG-Fets Trading Bot

A comprehensive Telegram bot for cryptocurrency trading on BSC and Ethereum networks, featuring wallet management, token scanning, and automated trading capabilities.

## ✨ Features

- **🔐 Wallet Management**: Create new wallets or import existing ones with secure encryption
- **💰 Trading**: Buy and sell tokens on BSC and Ethereum networks
- **🔍 Token Scanner**: Analyze token contracts and get detailed information
- **💳 Balance Checking**: View balances across multiple chains
- **💸 Transfers**: Send native tokens and ERC20 tokens
- **⚙️ Settings**: Customize bot preferences and privacy settings
- **🐦 Social Integration**: Twitter authentication for trading signals (coming soon)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Firebase project (optional, for production use)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd tg-fets-trading-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Firebase Configuration (optional)
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com

# Blockchain RPC Endpoints
ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
BSC_RPC_URL=https://bsc-dataseed.binance.org/
BSC_TEST_RPC_URL=https://data-seed-prebsc-1-s1.binance.org:8545/

# Encryption
ENCRYPTION_KEY=your-32-character-secret-key-here

# Demo Mode (for testing)
DEMO_MODE=false
```

## 🏗️ Project Structure

```
tg-fets-trading-bot/
├── main.py                 # Main bot entry point
├── bot_handlers.py         # Telegram bot command handlers
├── blockchain_manager.py   # Blockchain interaction logic
├── trading_manager.py      # Trading execution logic
├── firebase_manager.py     # Database operations
├── keyboard_manager.py     # Inline keyboard layouts
├── encryption.py           # Private key encryption
├── config.py              # Configuration constants
├── demo.py                # Demo mode for testing
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🔧 Usage

### Basic Commands

- `/start` - Start the bot and show main menu
- `/menu` - Show main menu
- `/help` - Show help information

### Main Features

1. **Wallet Management**
   - Create new wallet
   - Import existing wallet
   - View wallet details
   - Show private key (with confirmation)
   - Delete wallet

2. **Trading**
   - Select buy/sell action
   - Choose blockchain network
   - Enter trade amount
   - Specify token address
   - Confirm and execute trade

3. **Balance & Transfers**
   - Check balances across chains
   - Transfer native tokens
   - Transfer ERC20 tokens

4. **Token Scanner**
   - Scan token contracts
   - View token information
   - Check contract details

## 🧪 Testing

### Demo Mode

Run the bot in demo mode to test functionality without Telegram:

```bash
export DEMO_MODE=true
python main.py
```

### Manual Testing

```bash
python demo.py
```

## 🔒 Security Features

- **Private Key Encryption**: All private keys are encrypted using Fernet encryption
- **Secure Storage**: Encrypted keys stored in Firebase (or mock database for testing)
- **Input Validation**: Comprehensive validation of all user inputs
- **Error Handling**: Graceful error handling without exposing sensitive information

## 🌐 Supported Networks

- **BSC Testnet**: For testing and development
- **BSC Mainnet**: Binance Smart Chain mainnet
- **Ethereum**: Ethereum mainnet (requires Infura key)

## 📱 Telegram Bot Interface

The bot features an intuitive inline keyboard interface with:

- **Main Menu**: Access to all major features
- **Contextual Menus**: Dynamic menus based on user state
- **Confirmation Dialogs**: Safety confirmations for critical actions
- **Navigation**: Easy back/forward navigation between menus

## 🚨 Important Notes

- **Private Keys**: Never share your private keys with anyone
- **Testnet First**: Always test on testnet before using mainnet
- **Gas Fees**: Be aware of gas fees when trading on Ethereum
- **Slippage**: Understand slippage tolerance in trading

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if `TELEGRAM_BOT_TOKEN` is set correctly
   - Verify bot is not blocked by users

2. **Firebase connection failed**
   - Check credentials file path
   - Verify Firebase project configuration

3. **Blockchain connection issues**
   - Check RPC endpoint URLs
   - Verify network connectivity

### Debug Mode

Enable debug logging by modifying the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This bot is for educational and development purposes. Use at your own risk. The developers are not responsible for any financial losses incurred while using this bot.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the demo mode for functionality testing
- Review the configuration examples

---

**Happy Trading! 🚀📈**


