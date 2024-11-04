from swarm import Agent
from data.routines.prompts import (
    SOLANA_SEND_TOKEN_INSTRUCTIONS,
    SOLANA_WITHDRAW_STAKE_INSTRUCTIONS,
    SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS,
    SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS,
    SOLANA_DELEGATE_STAKE_INSTRUCTIONS,
    SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS,
    SOLANA_SEND_SOL_INSTRUCTIONS,
)
from configs.tools import *


def transfer_to_coordinator_agent():
    from configs.blockchain_coordinator_agent import get_coordinator_agent
    """Transfer to coordinator agent immediately."""
    return get_coordinator_agent()


def transfer_to_solana_send_agent():
    """Transfer to send sol agent immediately."""
    return Agent(
        name="Solana Send Sol Agent",
        instructions=SOLANA_SEND_SOL_INSTRUCTIONS,
        functions=[solana_send_solana, transfer_to_coordinator_agent],
    )


def transfer_to_solana_send_token_agent():
    """Transfer to send token agent immediately."""
    return Agent(
        name="Solana Send Token Agent",
        instructions=SOLANA_SEND_TOKEN_INSTRUCTIONS,
        functions=[solana_send_token, transfer_to_coordinator_agent],
    )


def transfer_to_solana_create_and_delegate_stake_agent():
    """Transfer to create and delegate stake agent immediately."""
    return Agent(
        name="Solana Create and Delegate Stake Agent",
        instructions=SOLANA_CREATE_AND_DELEGATE_STAKE_INSTRUCTIONS,
        functions=[solana_create_and_delegate_stake, transfer_to_coordinator_agent],
    )


def transfer_to_solana_create_stake_account_agent():
    """Transfer to create stake account agent immediately."""
    return Agent(
        name="Solana Create Stake Account Agent",
        instructions=SOLANA_CREATE_STAKE_ACCOUNT_INSTRUCTIONS,
        functions=[solana_create_stake_account, transfer_to_coordinator_agent],
    )


def transfer_to_solana_delegate_stake_agent():
    """Transfer to delegate stake agent immediately."""
    return Agent(
        name="Solana Delegate Stake Agent",
        instructions=SOLANA_DELEGATE_STAKE_INSTRUCTIONS,
        functions=[solana_delegate_stake, transfer_to_coordinator_agent],
    )


def transfer_to_solana_deactivate_stake_agent():
    """Transfer to deactivate stake agent immediately."""
    return Agent(
        name="Solana Deactivate Stake Agent",
        instructions=SOLANA_DEACTIVATE_STAKE_INSTRUCTIONS,
        functions=[solana_deactivate_stake, transfer_to_coordinator_agent],
    )


def transfer_to_solana_withdraw_stake_agent():
    """Transfer to withdraw stake agent immediately."""
    return Agent(
        name="Solana Withdraw Stake Agent",
        instructions=SOLANA_WITHDRAW_STAKE_INSTRUCTIONS,
        functions=[solana_withdraw_stake, transfer_to_coordinator_agent],
    )
