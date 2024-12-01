import requests
import json
from configs.variables import DEV_TG_BOT_URL, VALIDATORS_API_URL, TOKEN_METADATA_URL
#from solana.rpc.api import Client
import json
import base64
from datetime import datetime
import os

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
    
def solana_get_sol_price():
    """Get SOL price in USD."""
    try:
        response = requests.get("https://frontend-api.pump.fun/sol-price")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"An error occurred while fetching SOL price: {str(e)}"

def solana_balance_checker(address: str) -> str:
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
        
        # Get SOL price in USD
        try:
            sol_price_data = solana_get_sol_price()
            sol_price = float(sol_price_data["solPrice"])
            sol_usd_value = sol_balance * sol_price
            sol_balance_str = f"SOL Balance: {sol_balance} (${sol_usd_value:.2f})"
        except requests.RequestException:
            sol_balance_str = f"SOL Balance: {sol_balance}"
        
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

        balances = [sol_balance_str]
        token_addresses = []
        token_balances = {}

        if "result" in token_data and "value" in token_data["result"]:
            for account in token_data["result"]["value"]:
                if "account" in account and "data" in account["account"]:
                    parsed_data = account["account"]["data"]["parsed"]["info"]
                    mint = parsed_data["mint"]
                    balance = parsed_data["tokenAmount"]["uiAmount"]
                    if balance > 0:  # Only include tokens with non-zero balance
                        token_addresses.append(mint)
                        token_balances[mint] = balance
                        # First try local token metadata endpoint
                        try:
                            local_metadata_url = os.getenv("TOKEN_METADATA_URL", TOKEN_METADATA_URL).format(mint=mint)
                            local_response = requests.get(local_metadata_url)
                            local_response.raise_for_status()
                            token_info = local_response.json()
                            token_name = token_info.get("name", "Unknown Token")
                            token_symbol = token_info.get("symbol", "")
                            balances.append(f"Token: {token_name} ({token_symbol})\nMint Address: {mint}\nToken Balance: {balance}")
                            continue
                        except requests.RequestException:
                            # If local endpoint fails, use Unknown token
                            balances.append(f"Token: Unknown Token\nMint Address: {mint}\nToken Balance: {balance}")

            # Get USD values
            if token_addresses:
                try:
                    usd_values = get_token_prices(",".join(token_addresses), token_balances)
                    balances.append("\nUSD Values:")
                    balances.append(f"SOL: ${sol_usd_value:.2f}")
                    balances.append(usd_values)
                    # Calculate total USD value
                    total_usd = sol_usd_value
                    for line in usd_values.split('\n'):
                        if '$' in line:
                            try:
                                # Extract USD amount from string like "Token XYZ: $123.45"
                                usd_str = line.split('$')[1].strip()
                                total_usd += float(usd_str)
                            except (IndexError, ValueError):
                                continue
                    
                    balances.append(f"\nTotal Portfolio Value: ${total_usd:.2f}")
                except Exception as e:
                    balances.append(f"\nError getting USD values: {str(e)}")
            
            return "\n".join(balances)
        else:
            return sol_balance_str + "\nNo token accounts found"

    except requests.RequestException as e:
        return f"Error querying balances: {str(e)}"

def solana_search_validators(validator_search=None, limit=10, order_by="stake"):
    try:
        # Base URL for validators API
        base_url = os.getenv("VALIDATORS_API_URL", VALIDATORS_API_URL)

        # Validate order_by parameter
        if order_by not in ["stake", "score"]:
            order_by = "stake"  # Default to stake if invalid order parameter

        if validator_search:
            # Get all validators when searching
            response = requests.get(f"{base_url}?order={order_by}")
        else:
            # Get validators with specified limit and ordering
            response = requests.get(f"{base_url}?order={order_by}&limit={limit}")

        response.raise_for_status()
        validators = response.json()

        if validator_search:
            validator_search = validator_search.lower()
            best_match = None
            best_match_score = 0

            for validator in validators:
                # Calculate similarity score for address matching
                account_score = sum(1 for a, b in zip(validator_search, validator["account"].lower()) if a == b)
                vote_account_score = sum(1 for a, b in zip(validator_search, validator["vote_account"].lower()) if a == b)
                
                # Use the better of the two scores
                score = max(account_score, vote_account_score)
                
                # If exact match found
                if validator_search in validator["account"].lower() or \
                   validator_search in validator["vote_account"].lower():
                    return f"Validator Found:\n" \
                           f"Name: {validator['name']}\n" \
                           f"Account: {validator['account']}\n" \
                           f"Vote Account: {validator['vote_account']}\n" \
                           f"Status: {'Active' if validator['is_active'] else 'Inactive'}\n" \
                           f"Active Stake: {validator['active_stake'] / 1e9:.2f} SOL\n" \
                           f"Commission: {validator['commission']}%\n" \
                           f"Score: {validator['total_score']}"
                
                # Keep track of best partial match
                if score > best_match_score:
                    best_match = validator
                    best_match_score = score

            # If we found a good partial match (more than 50% characters match)
            if best_match and best_match_score >= len(validator_search) / 2:
                return f"Closest Matching Validator Found:\n" \
                       f"Name: {best_match['name']}\n" \
                       f"Account: {best_match['account']}\n" \
                       f"Vote Account: {best_match['vote_account']}\n" \
                       f"Status: {'Active' if best_match['is_active'] else 'Inactive'}\n" \
                       f"Active Stake: {best_match['active_stake'] / 1e9:.2f} SOL\n" \
                       f"Commission: {best_match['commission']}%\n" \
                       f"Score: {best_match['total_score']}"
                       
            return "Validator not found"

        # Format validators info based on limit
        top_validators = []
        # Convert limit to integer before slicing
        limit = int(limit) if limit else None
        for validator in validators[:limit]:  # Slice validators based on limit
            validator_info = f"Name: {validator['name']}\n" \
                           f"Account: {validator['account']}\n" \
                           f"Status: {'Active' if validator['is_active'] else 'Inactive'}\n" \
                           f"Active Stake: {validator['active_stake'] / 1e9:.2f} SOL\n" \
                           f"Commission: {validator['commission']}%\n" \
                           f"Score: {validator['total_score']}\n"
            top_validators.append(validator_info)

        order_type = "stake amount" if order_by == "stake" else "performance score"
        return f"Top {limit} validators ordered by {order_type}:\n\n" + "\n".join(top_validators)

    except requests.RequestException as e:
        return f"Error fetching validators: {str(e)}"
    

def get_token_prices(token_addresses: str, token_balances: dict = None) -> str:
    """
    Get prices for multiple token mint addresses and optionally calculate USD values if balances provided.
    Results are sorted by USD value in descending order, with price-unknown tokens at bottom.
    
    Args:
        token_addresses: Comma separated string of token mint addresses
        token_balances: Optional dict mapping token address to balance amount
    """
    try:
        # Try Jupiter API first
        jupiter_url = f"https://api.jup.ag/price/v2?ids={token_addresses}"
        response = requests.get(jupiter_url)
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        if 'data' in data:
            for token, details in data['data'].items():
                if details and details.get('price'):
                    prices[token] = float(details['price'])
        
        # For any missing prices, try Raydium API
        missing_tokens = [addr for addr in token_addresses.split(',') if addr not in prices]
        if missing_tokens:
            raydium_url = f"https://api-v3.raydium.io/mint/price?mints={','.join(missing_tokens)}"
            response = requests.get(raydium_url)
            response.raise_for_status()
            raydium_data = response.json()
            
            if raydium_data.get('success') and raydium_data.get('data'):
                for token, price in raydium_data['data'].items():
                    if price is not None:
                        prices[token] = float(price)

        # Prepare token data for sorting
        token_data = []
        unknown_price_tokens = []
        total_usd = 0
        
        for token in token_addresses.split(','):
            price = prices.get(token)
            if price is None:
                unknown_price_tokens.append(f"{token}: Price not found")
                continue
                
            if token_balances and token in token_balances:
                balance = float(token_balances[token])
                usd_value = balance * price
                total_usd += usd_value
                token_data.append({
                    'token': token,
                    'price': price,
                    'balance': balance,
                    'usd_value': usd_value,
                    'text': f"{token}:\nPrice: ${price:.6f}\nBalance: {balance:.6f}\nUSD Value: ${usd_value:.2f}"
                })
            else:
                token_data.append({
                    'token': token,
                    'price': price,
                    'balance': 0,
                    'usd_value': 0,
                    'text': f"{token}:\nPrice: ${price:.6f}"
                })
        
        # Sort token data by USD value in descending order
        token_data.sort(key=lambda x: x['usd_value'], reverse=True)
        
        # Combine sorted results with unknown price tokens at bottom
        result = [item['text'] for item in token_data] + unknown_price_tokens
        
        response_text = "\n\n".join(result)
        # if token_balances:
        #     response_text += f"\n\nTotal USD Value: ${total_usd:.2f}"
            
        return response_text

    except requests.RequestException as e:
        return f"Error fetching token prices: {str(e)}"



