from configs.agents import coordinator_agent, solana_coordinator_agent
from swarm import Swarm, Agent
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

client = Swarm()
app = FastAPI()

class InputData(BaseModel):
    user_input: str

@app.post('/run')
async def run_agent(input_data: InputData):
    try:
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        logger.info(f"Request {request_id} received with input: {input_data}")

        messages = [{"role": "user", "content": input_data.user_input}]
        logger.debug(f"Request {request_id} - Formatted messages: {json.dumps(messages)}")

        logger.info(f"Request {request_id} - Running Solana coordinator agent")
        result = client.run(agent=solana_coordinator_agent, messages=messages)
        
        response = result.messages[-1]["content"]
        responding_agent = "Unknown"
        
        # Try to determine which agent provided the response
        for message in result.messages:
            if message.get("tool_name"):
                responding_agent = message["tool_name"]
                break
        
        logger.info(f"Request {request_id} - Successfully processed request. Response from agent: {responding_agent}")
        logger.debug(f"Request {request_id} - Full response: {json.dumps(result.messages)}")
        
        return response

    except Exception as e:
        logger.error(f"Request {request_id} - Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host='0.0.0.0', port=5002)
