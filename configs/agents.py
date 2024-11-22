from swarm import Agent
#from configs.tools import *
from data.routines.prompts import COORDINATOR_INSTRUCTIONS, DEXSCREENER_INSTRUCTIONS, SOLANA_SEND_TOKEN_INSTRUCTIONS, SOLANA_WITHDRAW_STAKE_INSTRUCTIONS, SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS, SOLANA_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS, SOLANA_SEND_SOL_INSTRUCTIONS, SOLANA_COORDINATOR_INSTRUCTIONS, SOLANA_SWAP_INSTRUCTIONS, TELEGRAM_INSTRUCTIONS, SOLANA_BALANCE_INSTRUCTIONS, SOLANA_VALIDATOR_INSTRUCTIONS
from configs.blockchain_agents.solana.query_agent import *
from configs.blockchain_agents.solana.transaction_agent import *

#Coordinator Agent Transfer Functions : Used to transfer to the correct coordinator agent
def transfer_to_coordinator_agent():
    """Transfer to coordinator agent immediately."""
    return coordinator_agent

#Solana Agents Transfer Functions : Used to transfer to their respective Solana agent

def transfer_to_solana_send_sol_agent():
    """Transfer to send solana agent immediately."""
    return solana_send_solana_agent

def transfer_to_solana_send_token_agent():
    """Transfer to send token agent immediately."""
    return solana_send_token_agent

def transfer_to_solana_create_and_delegate_stake_agent():
    """Transfer to create and delegate stake agent immediately."""
    return solana_create_and_delegate_stake_agent

def transfer_to_solana_create_stake_account_agent():
    """Transfer to create stake account agent immediately."""
    return solana_create_stake_account_agent

def transfer_to_solana_delegate_stake_agent():
    """Transfer to delegate stake agent immediately."""
    return solana_delegate_stake_agent

def transfer_to_solana_deactivate_stake_agent():
    """Transfer to deactivate stake agent immediately."""
    return solana_deactivate_stake_agent

def transfer_to_solana_withdraw_stake_agent():
    """Transfer to withdraw stake agent immediately."""
    return solana_withdraw_stake_agent

def transfer_to_solana_coordinator_agent():
    """Transfer to solana coordinator agent immediately."""
    return solana_coordinator_agent

def transfer_to_solana_swap_agent():
    """Transfer to solana swap agent immediately."""
    return solana_swap_agent

# def transfer_to_solana_balance_agent():
#     """Transfer to solana balance agent immediately."""
#     return solana_balance_agent

def transfer_to_solana_validator_agent():
    """Transfer to solana validator agent immediately."""
    return solana_validator_agent


#Coordinator Agent
coordinator_agent = Agent(
    name="Coordinator Agent",
    instructions=COORDINATOR_INSTRUCTIONS,
    functions=[
        transfer_to_solana_coordinator_agent,
        transfer_to_dexscreener_agent,
        transfer_to_telegram_agent,
    ]
)

#Solana Agents
solana_coordinator_agent = Agent(
    name="Solana Coordinator Agent",
    instructions=SOLANA_COORDINATOR_INSTRUCTIONS,
    functions=[
        transfer_to_coordinator_agent,
        transfer_to_solana_send_token_agent,
        transfer_to_solana_send_sol_agent,
        transfer_to_solana_create_and_delegate_stake_agent,
        transfer_to_solana_create_stake_account_agent,
        transfer_to_solana_delegate_stake_agent,
        transfer_to_solana_deactivate_stake_agent,
        transfer_to_solana_withdraw_stake_agent,
        transfer_to_dexscreener_agent,
        transfer_to_solana_swap_agent,
        transfer_to_telegram_agent,
        solana_balance_checker
        
    ]
)
solana_send_solana_agent = Agent(
    name="Solana Send Sol Agent",
    instructions=SOLANA_SEND_SOL_INSTRUCTIONS,
    functions=[
        solana_send_solana,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_validator_agent,
        transfer_to_solana_create_and_delegate_stake_agent,
        solana_balance_checker
    ]
)
solana_send_token_agent = Agent(
    name="Solana Send Token Agent",
    instructions=SOLANA_SEND_TOKEN_INSTRUCTIONS,
    functions=[
        solana_send_token,
        transfer_to_solana_coordinator_agent,
        solana_balance_checker,
        transfer_to_dexscreener_agent,
        transfer_to_telegram_agent,
        transfer_to_solana_validator_agent,
        transfer_to_solana_create_and_delegate_stake_agent
    ]
)
solana_create_and_delegate_stake_agent = Agent(
    name="Solana Create and Delegate Stake Agent",
    instructions=SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_create_and_delegate_stake,
        transfer_to_solana_coordinator_agent,
        transfer_to_telegram_agent,
        transfer_to_solana_validator_agent,
        solana_balance_checker
    ]
)
solana_create_stake_account_agent = Agent(
    name="Solana Create Stake Account Agent",
    instructions=SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS,
    functions=[
        solana_create_stake_account,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_validator_agent,
        solana_balance_checker
    ]
)
solana_delegate_stake_agent = Agent(
    name="Solana Delegate Stake Agent",
    instructions=SOLANA_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_delegate_stake,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_validator_agent,
        solana_balance_checker
    ]
)
solana_deactivate_stake_agent = Agent(
    name="Solana Deactivate Stake Agent",
    instructions=SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_deactivate_stake,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_validator_agent,
        solana_balance_checker
    ]
)
solana_withdraw_stake_agent = Agent(
    name="Solana Withdraw Stake Agent",
    instructions=SOLANA_WITHDRAW_STAKE_INSTRUCTIONS,
    functions=[
        solana_withdraw_stake,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_validator_agent,
        solana_balance_checker
    ]
)
solana_swap_agent = Agent(
    name="Solana Swap Agent",
    instructions=SOLANA_SWAP_INSTRUCTIONS,
    functions=[
        solana_swap,
        transfer_to_solana_coordinator_agent,
        transfer_to_telegram_agent,
        solana_balance_checker
    ]
)

# solana_balance_agent = Agent(
#     name="Solana Balance Agent",
#     instructions=SOLANA_BALANCE_INSTRUCTIONS,
#     functions=[
#         solana_balance,
#         transfer_to_solana_coordinator_agent,
#         transfer_to_telegram_agent,
#         transfer_to_solana_send_sol_agent,
#         transfer_to_solana_send_token_agent,
#         transfer_to_solana_create_and_delegate_stake_agent,
#         transfer_to_solana_create_stake_account_agent,
#         transfer_to_solana_delegate_stake_agent,
#         transfer_to_solana_deactivate_stake_agent,
#         transfer_to_solana_withdraw_stake_agent,
#         transfer_to_solana_swap_agent
#     ]
# )

solana_validator_agent = Agent(
    name="Solana Validator Agent",
    instructions=SOLANA_VALIDATOR_INSTRUCTIONS,
    functions=[
        solana_fetch_validators,
        transfer_to_solana_coordinator_agent,
        transfer_to_solana_create_and_delegate_stake_agent,
        transfer_to_solana_create_stake_account_agent,
        transfer_to_solana_delegate_stake_agent,
        transfer_to_solana_deactivate_stake_agent,
        transfer_to_solana_withdraw_stake_agent,
        solana_balance_checker
    ]
)

#Dexscreener Agent
dexscreener_agent = Agent(
    name="Dexscreener Agent",
    instructions=DEXSCREENER_INSTRUCTIONS,
    functions=[
        transfer_to_dexscreener_agent,
        transfer_to_coordinator_agent,
        transfer_to_telegram_agent
    ]
)

telegram_agent = Agent(
   name="Telegram Agent",
   instructions=TELEGRAM_INSTRUCTIONS,
   functions=[
       transfer_to_telegram_agent,
       transfer_to_coordinator_agent
   ]
)