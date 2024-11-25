import requests
import json
from configs.variables import DEV_TG_BOT_URL, SOLANA_RPC_URL
#from solana.rpc.api import Client
import json
import base64
from datetime import datetime

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
    

def solana_search_validators(validator_search=None):
    try:
        # Get all validators
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getVoteAccounts",
            "params": []
        }

        response = requests.post(SOLANA_RPC_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        if "result" not in data:
            return "Error fetching validator data"

        # Combine current and delinquent validators
        current_validators = data["result"].get("current", [])
        delinquent_validators = data["result"].get("delinquent", [])
        all_validators = current_validators + delinquent_validators

        # If searching for specific validator
        if validator_search:
            validator_search = validator_search.lower()
            best_match = None
            best_match_score = 0

            for validator in all_validators:
                # Check if validator is active (in current_validators)
                is_active = validator in current_validators
                status = "Active" if is_active else "Inactive"

                # Calculate similarity score for address matching
                vote_key_score = sum(1 for a, b in zip(validator_search, validator["votePubkey"].lower()) if a == b)
                node_key_score = sum(1 for a, b in zip(validator_search, validator.get("nodePubkey", "").lower()) if a == b)
                
                # Use the better of the two scores
                score = max(vote_key_score, node_key_score)
                
                # If exact match found
                if validator_search in validator["votePubkey"].lower() or \
                   validator_search in validator.get("nodePubkey", "").lower():
                    return f"Validator Found:\nAddress: {validator['votePubkey']}\n" \
                           f"Node Address: {validator.get('nodePubkey', 'N/A')}\n" \
                           f"Status: {status}\n" \
                           f"Active Stake: {validator.get('activatedStake', 0) / 1e9:.2f} SOL"
                
                # Keep track of best partial match
                if score > best_match_score:
                    best_match = validator
                    best_match_score = score
                    best_match_status = status

            # If we found a good partial match (more than 50% characters match)
            if best_match and best_match_score >= len(validator_search) / 2:
                return f"Closest Matching Validator Found:\nAddress: {best_match['votePubkey']}\n" \
                       f"Node Address: {best_match.get('nodePubkey', 'N/A')}\n" \
                       f"Status: {best_match_status}\n" \
                       f"Active Stake: {best_match.get('activatedStake', 0) / 1e9:.2f} SOL"
                       
            return "Validator not found"

        # Calculate total stake for percentage calculation
        total_stake = sum(float(v.get("activatedStake", 0)) for v in all_validators)

        # Sort validators by stake
        sorted_validators = sorted(all_validators, 
                                 key=lambda x: float(x.get("activatedStake", 0)), 
                                 reverse=True)

        # Get top 10 validators
        top_validators = []
        for validator in sorted_validators[:10]:
            stake = float(validator.get("activatedStake", 0))
            stake_percentage = (stake / total_stake) * 100 if total_stake > 0 else 0
            is_active = validator in current_validators
            status = "Active" if is_active else "Inactive"
            
            validator_info = f"Address: {validator['votePubkey']}\n" \
                           f"Status: {status}\n" \
                           f"Active Stake: {stake / 1e9:.2f} SOL\n" \
                           f"Stake Percentage: {stake_percentage:.2f}%\n"
            top_validators.append(validator_info)

        return "\n".join(top_validators)

    except requests.RequestException as e:
        return f"Error fetching validators: {str(e)}"