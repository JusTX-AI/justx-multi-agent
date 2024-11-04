from swarm import Agent
from configs.tools import *

class AgentCoordinator:
    def __init__(self):
        self.coordinator_agent = None
        self.initialize_coordinator()
    
    def initialize_coordinator(self):
        # Import here to avoid circular import
        from configs.blockchain_agents.solana import query_agent
        from configs.blockchain_agents.solana import transaction_agent
        
        self.coordinator_agent = Agent(
            name="Coordinator Agent",
            instructions="Some Instructions",
            functions=[
                query_agent.transfer_to_dexscreener_agent,
                transaction_agent.transfer_to_solana_send_agent,
                transaction_agent.transfer_to_solana_send_token_agent,
                transaction_agent.transfer_to_solana_create_and_delegate_stake_agent,
                transaction_agent.transfer_to_solana_create_stake_account_agent,
                transaction_agent.transfer_to_solana_delegate_stake_agent,
                transaction_agent.transfer_to_solana_deactivate_stake_agent,
                transaction_agent.transfer_to_solana_withdraw_stake_agent
            ]
        )
    
    def get_coordinator_agent(self):
        return self.coordinator_agent

coordinator_instance = AgentCoordinator()
get_coordinator_agent = coordinator_instance.get_coordinator_agent



# dexscreener_agent = Agent(
#     name="Dexscreener Agent",
#     instructions=DEXSCREENER_INSTRUCTIONS,
#     functions=[
#         transfer_to_dexscreener_agent,
#         transfer_to_coordinator_agent
#     ]
# )
