from configs.blockchain_coordinator_agent import get_coordinator_agent
from swarm.repl import run_demo_loop

if __name__ == "__main__":
    run_demo_loop(get_coordinator_agent(), debug=True)