from swarm import Agent
from configs.tools import *
from data.routines.prompts import COORDINATOR_INSTRUCTIONS, DEXSCREENER_INSTRUCTIONS, SOLANA_SEND_TOKEN_INSTRUCTIONS, SOLANA_WITHDRAW_STAKE_INSTRUCTIONS, SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS, SOLANA_DELEGATE_STAKE_INSTRUCTIONS, SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS, SOLANA_SEND_SOL_INSTRUCTIONS
from configs.blockchain_agents.solana.query_agent import *
from configs.blockchain_agents.solana.transaction_agent import *

def transfer_to_coordinator_agent():
    """Transfer to coordinator agent immediately."""
    return coordinator_agent

dexscreener_agent = Agent(
    name="Dexscreener Agent",
    instructions=DEXSCREENER_INSTRUCTIONS,
    functions=[
        transfer_to_dexscreener_agent,
        transfer_to_coordinator_agent
    ]
)

coordinator_agent = Agent(
    name="Coordinator Agent",
    instructions=COORDINATOR_INSTRUCTIONS,
    functions=[
        transfer_to_dexscreener_agent,
        transfer_to_solana_send_agent,
        transfer_to_solana_send_token_agent,
        transfer_to_solana_create_and_delegate_stake_agent,
        transfer_to_solana_create_stake_account_agent,
        transfer_to_solana_delegate_stake_agent,
        transfer_to_solana_deactivate_stake_agent,
        transfer_to_solana_withdraw_stake_agent
    ]
)

solana_send_solana_agent = Agent(
    name="Solana Send Sol Agent",
    instructions=SOLANA_SEND_SOL_INSTRUCTIONS,
    functions=[
        solana_send_solana,
        transfer_to_coordinator_agent
        
    ]
)
solana_send_token_agent = Agent(
    name="Solana Send Token Agent",
    instructions=SOLANA_SEND_TOKEN_INSTRUCTIONS,
    functions=[
        solana_send_token,
        transfer_to_coordinator_agent
    ]
)
solana_create_and_delegate_stake_agent = Agent(
    name="Solana Create and Delegate Stake Agent",
    instructions=SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_create_and_delegate_stake,
        transfer_to_coordinator_agent
    ]
)
solana_create_stake_account_agent = Agent(
    name="Solana Create Stake Account Agent",
    instructions=SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS,
    functions=[
        solana_create_stake_account,
        transfer_to_coordinator_agent
    ]
)

solana_delegate_stake_agent = Agent(
    name="Solana Delegate Stake Agent",
    instructions=SOLANA_DELEGATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_delegate_stake,
        transfer_to_coordinator_agent
    ]
)

solana_deactivate_stake_agent = Agent(
    name="Solana Deactivate Stake Agent",
    instructions=SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS,
    functions=[
        solana_deactivate_stake,
        transfer_to_coordinator_agent
    ]
)

solana_withdraw_stake_agent = Agent(
    name="Solana Withdraw Stake Agent",
    instructions=SOLANA_WITHDRAW_STAKE_INSTRUCTIONS,
    functions=[
        solana_withdraw_stake,
        transfer_to_coordinator_agent
    ]
)
