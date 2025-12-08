
# PII Redaction & Ethereum (Metamask) — Run Instructions

Quick steps to run the Django app locally and deploy the Solidity contract (AadhaarLedger) so Metamask can store hashes.

Prerequisites
- Python 3.10+
- Node.js 16+ and npm
- Git (optional)
- Metamask browser extension

1) Python backend — setup and run
---------------------------------
# Create and activate virtualenv (Linux/macOS)
python -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create admin user (optional)
python manage.py createsuperuser

# Run Django development server
python manage.py runserver

Open http://127.0.0.1:8000/ to upload a document.

2) Deploy the Solidity contract (Hardhat) — local network
---------------------------------------------------------
This project includes `contracts/AadhaarLedger.sol`.

# Initialize Node env and install dev-deps
npm install

# Start a local Hardhat node in a separate terminal
npx hardhat node

# In another terminal (same project), deploy to the local node:
# This will compile and deploy the contract and print the contract address
npx hardhat run --network localhost scripts/deploy.js

The deploy script prints the deployed contract address. Copy it.

3) Configure client-side contract address (static/js/ethereum.js)
------------------------------------------------------------------
Open `static/js/ethereum.js` and replace
REPLACE_WITH_DEPLOYED_CONTRACT_ADDRESS
with the deployed contract address (including 0x...).

You can also use the provided helper to update the file:
python scripts/update_contract_address.py 0xYourDeployedAddressHere

4) Connect Metamask to local Hardhat
------------------------------------
- In the terminal running `npx hardhat node` you'll see several accounts and their private keys.
- Add a new network in Metamask:
  - Network Name: Hardhat Local
  - RPC URL: http://127.0.0.1:8545
  - Chain ID: 31337
- Import one of the private keys (from Hardhat node) into Metamask to get funds (Hardhat provides balance).

5) Store hashes from the web UI
-------------------------------
- Upload a document, view detections on result page.
- Click "Connect Wallet" (Metamask popup -> approve), then "Store Hashes on Ethereum (Metamask)".
- Each addEntry call will prompt Metamask to sign/send a transaction. Confirm and wait for mining.

6) Deploy to a public testnet (optional)
----------------------------------------
- Create an Alchemy/Infura RPC URL for Sepolia (or other testnet).
- Create a `.env` file with:
  SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
  PRIVATE_KEY=0xYOUR_PRIVATE_KEY

Then run:
npx hardhat run --network sepolia scripts/deploy.js

After deployment, update `static/js/ethereum.js` with the contract address and switch Metamask network to the testnet.

7) Troubleshooting
------------------
- If Metamask doesn't detect a contract: ensure the correct RPC/network and correct contract address.
- If transactions fail: check gas settings, network, and account with funds.
- If PDF text extraction fails: test with a plain text file to verify detection pipeline.

Files provided to help:
- contracts/AadhaarLedger.sol (Solidity source)
- package.json (Hardhat dev-deps)
- hardhat.config.js (network config)
- scripts/deploy.js (deploy script)
- scripts/update_contract_address.py (helper to set contract address in static/js/ethereum.js)
- .env.example

That's all — start the Django server, deploy the contract, configure the front-end address, and use Metamask to store the PII hashes.
=======


