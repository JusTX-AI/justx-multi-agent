import requests
import json
from configs.variables import DEV_TG_BOT_URL, VALIDATORS_API_URL, TOKEN_METADATA_URL
#from solana.rpc.api import Client
import json
import base64
from datetime import datetime
import os

# def transfer_to_dexscreener_agent(coin_name: str) -> str:
    # """Search for a meme coin's contract address on dexscreener API."""
    
    # # Construct the URL with the coin name as the search query
    # url = f"https://api.dexscreener.com/latest/dex/search?q={coin_name}"
    
    # try:
    #     # Send a GET request to the DexScreener API
    #     response = requests.get(url)
    #     response.raise_for_status()  # Raise an exception for bad status codes
        
    #     # Parse the JSON response
    #     data = response.json()
        
    #     # Extract relevant information
    #     if 'pairs' in data and len(data['pairs']) > 0:
    #         for pair in data['pairs']:
    #             if pair['baseToken']['symbol'].lower() == coin_name.lower():
    #                 contract_address = pair['baseToken']['address']
    #                 base_token_name = pair['baseToken']['name']
    #                 return f"Contract address for {coin_name}: {contract_address}\nBase token name: {base_token_name}"
            
    #         # If no exact match found, return the first result
    #         contract_address = data['pairs'][0]['baseToken']['address']
    #         base_token_name = data['pairs'][0]['baseToken']['name']
    #         return f"Contract address for {coin_name} (closest match): {contract_address}\nBase token name: {base_token_name}"
    #     else:
    #         return f"No results found for {coin_name}."
    # except requests.RequestException as e:
    #     return f"An error occurred while fetching data for {coin_name}: {str(e)}"

def transfer_to_dexscreener_agent(coin_name: str) -> str:
    """Search for a token's contract address from Jupiter API."""
    print(f"Searching for {coin_name} on Jupiter API")
    try:
        # Get token list from Jupiter API
        response = requests.get("https://token.jup.ag/strict")
        response.raise_for_status()
        tokens = response.json()

        # Search for token by name or symbol (case insensitive)
        matches = []
        search_term = coin_name.lower()
        for token in tokens:
            if (search_term in token['name'].lower() or 
                search_term in token['symbol'].lower()):
                matches.append(token)

        if matches:
            # Return first match
            token = matches[0]
            return f"Contract address for {token['name']}: {token['address']}\nToken name: {token['name']}"
        else:
            # If not found in Jupiter, try DexScreener API
            url = f"https://api.dexscreener.com/latest/dex/search?q={coin_name}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                
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
            except requests.RequestException:
                return f"No results found for {coin_name}."

    except requests.RequestException as e:
        return f"An error occurred while fetching data for {coin_name}: {str(e)}"

    
def transfer_to_telegram_agent(token_address: str):
    """Query token address to telegram bot."""
    try:
        url = f"{os.environ.get('DEV_TG_BOT_URL')}/send_message"
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
        
        if "result" not in sol_data or "value" not in sol_data["result"]:
            raise ValueError("Invalid response format from RPC endpoint. Please try again.")
        sol_balance = float(sol_data["result"]["value"]) / 1e9 # Convert lamports to SOL
        
        # Get SOL price in USD
        try:
            sol_price_data = solana_get_sol_price()
            # Handle case where sol_price_data is invalid by retrying once
            try:
                sol_price = float(sol_price_data["solPrice"])
            except (TypeError, KeyError):
                # Retry getting SOL price data once
                sol_price_data = solana_get_sol_price()
                sol_price = float(sol_price_data["solPrice"]) if isinstance(sol_price_data, dict) else 0
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
                        if ':' in line and '$' in line:
                            try:
                                # Extract USD amount from string like "Token XYZ: $123.45"
                                usd_str = line.split('$')[1].strip()
                                # Remove any trailing text after the number
                                usd_str = ''.join(c for c in usd_str if c.isdigit() or c == '.')
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
        # Get prices from multiple APIs
        prices = get_token_prices_from_apis(token_addresses)

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


def get_token_prices_from_apis(token_addresses: str) -> dict:

    """Get token prices from multiple price APIs."""
    
    try:
        prices = {}
        tokens = token_addresses.split(',')

        # Try Jupiter API first
        jupiter_url = f"https://api.jup.ag/price/v2?ids={token_addresses}"
        response = requests.get(jupiter_url)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            for token in tokens:
                if token in data['data']:
                    details = data['data'][token]
                    if details and details.get('price'):
                        prices[token] = float(details['price'])

        # Try Raydium API for tokens without prices
        remaining_tokens = [t for t in tokens if t not in prices]
        if remaining_tokens:
            raydium_url = f"https://api-v3.raydium.io/mint/price?mints={','.join(remaining_tokens)}"
            response = requests.get(raydium_url)
            response.raise_for_status()
            raydium_data = response.json()
            
            if raydium_data.get('success') and raydium_data.get('data'):
                for token in remaining_tokens:
                    if token in raydium_data['data'] and raydium_data['data'][token] is not None:
                        prices[token] = float(raydium_data['data'][token])
        # Try Fluxbeam API for remaining tokens
        remaining_tokens = [t for t in tokens if t not in prices]
        if remaining_tokens:
            try:
                fluxbeam_url = f"https://data.fluxbeam.xyz/prices?ids={','.join(remaining_tokens)}"
                #fluxbeam_url = f"https://data.fluxbeam.xyz/tokens/{token}/price"
                response = requests.get(fluxbeam_url)
                response.raise_for_status()
                data = response.json()
                
                if 'data' in data:
                    for token, price in data['data'].items():
                        if price > 0:
                            prices[token] = float(price)
            except requests.RequestException:
                pass
                
        return prices
    except requests.RequestException as e:
        print(f"Error fetching token prices: {str(e)}")
        return {}


def rug_checker(token_address: str) -> str:
    """Check if a token is potentially a rug pull using rugcheck.xyz API and provide detailed token information."""
    try:
        url = f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract key information safely with defaults
        token_meta = data.get('tokenMeta') or {}
        token_data = data.get('token') or {}
        token_name = token_meta.get('name', 'Unknown')
        token_symbol = token_meta.get('symbol', 'Unknown')
        total_supply = token_data.get('supply', 0)
        decimals = token_data.get('decimals', 0)
        total_liquidity = data.get('totalMarketLiquidity', 0)
        score = data.get('score', 0)
        
        # Build response message
        response_parts = []
        
        # Token Basic Info
        response_parts.append(f"Token Information:")
        response_parts.append(f"Name: {token_name}")
        response_parts.append(f"Symbol: {token_symbol}")
        if total_supply and decimals:
            response_parts.append(f"Total Supply: {total_supply / (10 ** decimals):,.2f}")
        else:
            response_parts.append("Total Supply: Unknown")
        response_parts.append(f"Total Liquidity: ${total_liquidity:,.2f}")
        
        # Overall risk level based on score
        if score > 50000:
            risk_color = "red"
            risk_level = "High Risk"
        elif score > 20000:
            risk_color = "orange"
            risk_level = "Medium Risk"
        else:
            risk_color = "green"
            risk_level = "Low Risk"
            
        response_parts.append(f"\n<font color='{risk_color}'>Risk Assessment:")
        response_parts.append(f"Overall Risk Score: {score}")
        response_parts.append(f"Risk Level: {risk_level}</font>")
        
        # Top Holders Analysis
        top_holders = data.get('topHolders') or []
        if top_holders:
            response_parts.append("\nTop Token Holders:")
            for idx, holder in enumerate(top_holders, 1):
                if not holder:
                    continue
                pct = holder.get('pct', 0)
                amount = holder.get('uiAmount', 0)
                owner = holder.get('owner', 'Unknown')
                holder_color = "red" if pct > 20 else "orange" if pct > 10 else "green"
                response_parts.append(f"<font color='{holder_color}'>#{idx}: {owner}")
                response_parts.append(f"Amount: {amount:,.2f} ({pct:.2f}%)</font>")
        
        # Market Information
        markets = data.get('markets') or []
        if markets:
            response_parts.append("\nMarket Information:")
            for market in markets:
                if not market:
                    continue
                lp = market.get('lp') or {}
                response_parts.append(f"Market Type: {market.get('marketType', 'Unknown')}")
                response_parts.append(f"Base Price: ${lp.get('basePrice', 0):,.8f}")
                response_parts.append(f"Quote Price: ${lp.get('quotePrice', 0):,.2f}")
                response_parts.append(f"LP Providers: {data.get('totalLPProviders', 0)}")
        
        # Risk Factors
        risks = data.get('risks') or []
        if risks:
            response_parts.append("\nDetailed Risk Factors:")
            for risk in risks:
                if not risk:
                    continue
                risk_name = risk.get('name', '')
                risk_value = risk.get('value', '')
                risk_desc = risk.get('description', '')
                risk_level = risk.get('level', '')
                risk_score = risk.get('score', 0)
                
                color = "red" if risk_level == 'danger' else "orange" if risk_level == 'warn' else "green"
                
                risk_line = f"<font color='{color}'>"
                risk_line += f"• {risk_name}"
                if risk_value:
                    risk_line += f" ({risk_value})"
                risk_line += f": {risk_desc}"
                risk_line += f" [Score: {risk_score}]</font>"
                response_parts.append(risk_line)
        
        # Additional Token Metadata
        file_meta = data.get('fileMeta') or {}
        if file_meta.get('description'):
            response_parts.append(f"\nToken Description: {file_meta['description']}")
            
        return "\n".join(response_parts)
        
    except requests.RequestException as e:
        return f"Error checking token status: {str(e)}"