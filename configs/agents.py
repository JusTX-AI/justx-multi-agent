from swarm import Agent
from configs.tools import *
from data.routines.prompts import COORDINATOR_INSTRUCTIONS, DEXSCREENER_INSTRUCTIONS, SOLANA_SEND_TOKEN_INSTRUCTIONS, SOLANA_WITHDRAW_STAKE_INSTRUCTIONS, SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS, SOLANA_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS, SOLANA_SEND_SOL_INSTRUCTIONS

def transfer_to_coordinator_agent():
    """Transfer to coordinator agent immediately."""
    return coordinator_agent

def transfer_to_send_sol_agent():
    """Transfer to send sol agent immediately."""
    return solana_send_sol_agent

def transfer_to_send_token_agent():
    """Transfer to send token agent immediately."""
    return solana_send_token_agent

def transfer_to_create_and_delegate_stake_agent():
    """Transfer to create and delegate stake agent immediately."""
    return solana_create_and_delegate_stake_agent

def transfer_to_create_stake_account_agent():
    """Transfer to create stake account agent immediately."""
    return solana_create_stake_account_agent

def transfer_to_delegate_stake_agent():
    """Transfer to delegate stake agent immediately."""
    return solana_delegate_stake_agent

def transfer_to_deactivate_stake_agent():
    """Transfer to deactivate stake agent immediately."""
    return solana_deactivate_stake_agent

def transfer_to_withdraw_stake_agent():
    """Transfer to withdraw stake agent immediately."""
    return solana_withdraw_stake_agent

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
        transfer_to_send_sol_agent,
        transfer_to_send_token_agent,
        transfer_to_create_and_delegate_stake_agent,
        transfer_to_create_stake_account_agent,
        transfer_to_delegate_stake_agent,
        transfer_to_deactivate_stake_agent,
        transfer_to_withdraw_stake_agent
    ]
)
dexscreener_agent = Agent(
    name="Dexscreener Agent",
    instructions=DEXSCREENER_INSTRUCTIONS,
    functions=[
        transfer_to_coordinator_agent,
    ]
)
solana_send_sol_agent = Agent(
    name="Solana Send Sol Agent",
    instructions=SOLANA_SEND_SOL_INSTRUCTIONS,
    functions=[
        send_sol,
        transfer_to_coordinator_agent
        
    ]
)
solana_send_token_agent = Agent(
    name="Solana Send Token Agent",
    instructions=SOLANA_SEND_TOKEN_INSTRUCTIONS,
    functions=[
        send_token,
        transfer_to_coordinator_agent
    ]
)
solana_create_and_delegate_stake_agent = Agent(
    name="Solana Create and Delegate Stake Agent",
    instructions=SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        create_and_delegate_stake,
        transfer_to_coordinator_agent
    ]
)
solana_create_stake_account_agent = Agent(
    name="Solana Create Stake Account Agent",
    instructions=SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS,
    functions=[
        create_stake_account,
        transfer_to_coordinator_agent
    ]
)

solana_delegate_stake_agent = Agent(
    name="Solana Delegate Stake Agent",
    instructions=SOLANA_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        delegate_stake,
        transfer_to_coordinator_agent
    ]
)

solana_deactivate_stake_agent = Agent(
    name="Solana Deactivate Stake Agent",
    instructions=SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS,
    functions=[
        deactivate_stake,
        transfer_to_coordinator_agent
    ]
)

solana_withdraw_stake_agent = Agent(
    name="Solana Withdraw Stake Agent",
    instructions=SOLANA_WITHDRAW_STAKE_INSTRUCTIONS,
    functions=[
        withdraw_stake,
        transfer_to_coordinator_agent
    ]
)
