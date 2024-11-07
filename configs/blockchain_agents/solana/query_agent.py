import requests
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
    