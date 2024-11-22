from configs.agents import coordinator_agent, solana_coordinator_agent
from swarm import Swarm, Agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# from swarm.repl import run_demo_loop
# if __name__ == "__main__":
#     run_demo_loop(coordinator_agent, debug=True)

client = Swarm()
app = FastAPI()

class InputData(BaseModel):
    # Define your input data structure here
    user_input: str  # Example field

@app.post('/run')
async def run_agent(input_data: InputData):
    try:
        # Process input data if necessary
        #result = run_demo_loop(coordinator_agent, debug=True)
        print(input_data)
        messages = [{"role": "user", "content": input_data.user_input}]
        result = client.run(agent=solana_coordinator_agent, messages=messages)
        #result = client.run(agent=coordinator_agent, messages=messages)
        print(result)
        return result.messages[-1]["content"]  # FastAPI automatically converts to JSON
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5002)
