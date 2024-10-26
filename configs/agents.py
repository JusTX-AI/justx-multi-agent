from swarm import Agent
from configs.tools import *
from data.routines.prompts import COORDINATOR_INSTRUCTIONS, DEXSCREENER_INSTRUCTIONS, SOLANA_SEND_TOKEN_INSTRUCTIONS

def transfer_to_coordinator_agent():
    """Transfer to coordinator agent immediately."""
    return coordinator_agent

def transfer_to_send_sol_agent():
    """Transfer to send sol agent immediately."""
    return solana_send_token_agent

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

coordinator_agent = Agent(
    name="Coordinator Agent",
    instructions=COORDINATOR_INSTRUCTIONS,
    functions=[
        transfer_to_dexscreener_agent,
        transfer_to_send_sol_agent
    ]
)

dexscreener_agent = Agent(
    name="Dexscreener Agent",
    instructions=DEXSCREENER_INSTRUCTIONS,
    functions=[
        transfer_to_coordinator_agent,
    ]
)

solana_send_token_agent = Agent(
    name="Solana Send Token Agent",
    instructions=SOLANA_SEND_TOKEN_INSTRUCTIONS,
    functions=[
        transfer_to_coordinator_agent,
        send_sol
    ]
)
