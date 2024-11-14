import requests
import json
from configs.variables import DEV_TG_BOT_URL

def transfer_to_dexscreener_agent(coin_name: str) -> str:
    """Search for a meme coin's contract address on dexscreener API."""
    
    # Construct the URL with the coin name as the search query
    url = f"https://api.dexscreener.com/latest/dex/search?q={coin_name}"
    
    try:
        # Send a GET request to the DexScreener API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        # Extract relevant information
        if 'pairs' in data and len(data['pairs']) > 0:
            for pair in data['pairs']:
                if pair['baseToken']['symbol'].lower() == coin_name.lower():
                    contract_address = pair['baseToken']['address']
                    base_token_name = pair['baseToken']['name']
                    return f"Contract address for {coin_name}: {contract_address}\nBase token name: {base_token_name}"
            
            # If no exact match found, return the first result
            contract_address = data['pairs'][0]['baseToken']['address']
            base_token_name = data['pairs'][0]['baseToken']['name']
            return f"Contract address for {coin_name} (closest match): {contract_address}\nBase token name: {base_token_name}"
        else:
            return f"No results found for {coin_name}."
    except requests.RequestException as e:
        return f"An error occurred while fetching data for {coin_name}: {str(e)}"
    
def transfer_to_telegram_agent(token_address: str):
    """Query token address to telegram bot."""
    try:
        url = f"{DEV_TG_BOT_URL}/send_message"
        payload = {
            "text": f"/c {token_address}"
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"An error occurred while sending message to telegram: {str(e)}"
    

def solana_balance(address: str) -> str:
    """Get balance of a Solana address."""

    from configs.variables import SOLANA_RPC_URL

    try:
        # Query SOL balance
        sol_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [address]
        }

        sol_response = requests.post(SOLANA_RPC_URL, json=sol_payload)
        sol_response.raise_for_status()
        sol_data = sol_response.json()
        
        sol_balance = float(sol_data["result"]["value"]) / 1e9 # Convert lamports to SOL
        
        # Query token accounts for the address
        token_payload = {
            "jsonrpc": "2.0", 
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                address,
                {
                    "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
        }

        token_response = requests.post(SOLANA_RPC_URL, json=token_payload)
        token_response.raise_for_status()
        token_data = token_response.json()

        balances = [f"SOL Balance: {sol_balance}"]

        if "result" in token_data and "value" in token_data["result"]:
            for account in token_data["result"]["value"]:
                if "account" in account and "data" in account["account"]:
                    parsed_data = account["account"]["data"]["parsed"]["info"]
                    mint = parsed_data["mint"]
                    balance = parsed_data["tokenAmount"]["uiAmount"]
                    if balance > 0:  # Only include tokens with non-zero balance
                        # First try local token metadata endpoint
                        try:
                            local_metadata_url = f"https://dev-token-search.justx.ai/proxy/tokens/address/{mint}"
                            local_response = requests.get(local_metadata_url)
                            local_response.raise_for_status()
                            token_info = local_response.json()
                            token_name = token_info.get("name", "Unknown Token")
                            token_symbol = token_info.get("symbol", "")
                            balances.append(f"Token: {token_name} ({token_symbol})\nMint Address: {mint}\nBalance: {balance}")
                            continue
                        except requests.RequestException:
                            # If local endpoint fails, try telegram bot
                            try:
                                tg_response = transfer_to_telegram_agent(mint)
                                if isinstance(tg_response, dict):
                                    token_name = tg_response.get("name", "Unknown Token")
                                    token_symbol = tg_response.get("symbol", "")
                                    balances.append(f"Token: {token_name} ({token_symbol})\nMint Address: {mint}\nBalance: {balance}")
                                else:
                                    balances.append(f"Token Mint: {mint}, Balance: {balance}")
                            except:
                                balances.append(f"Token Mint: {mint}, Balance: {balance}")
            
            return "\n".join(balances)
        else:
            return f"SOL Balance: {sol_balance}\nNo token accounts found"

    except requests.RequestException as e:
        return f"Error querying balances: {str(e)}"