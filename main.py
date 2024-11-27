from configs.agents import coordinator_agent, solana_coordinator_agent
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from swarm import Swarm, Agent
import json
import logging
from datetime import datetime
from sse_starlette.sse import EventSourceResponse

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

app = FastAPI()

# Define request models
class UserInput(BaseModel):
    chat_id: str
    user_input: str
    stream: Optional[bool] = False
    debug: Optional[bool] = False

# Store session state
sessions = {}

class SessionState:
    def __init__(self, agent: Agent):
        self.messages: List[Dict] = []
        self.agent = agent

# Initialize the Swarm client
client = Swarm()

def process_streaming_chunk(chunk: str) -> str:
    """Process a streaming chunk and format it for SSE"""
    try:
        if chunk.strip():
            return json.dumps({"content": chunk})
    except Exception as e:
        return json.dumps({"error": str(e)})
    return ""

async def stream_generator(response):
    """Generate streaming response chunks"""
    try:
        async for chunk in response:
            if chunk:
                yield f"data: {process_streaming_chunk(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"

@app.post("/run")
async def run_agent(user_input: UserInput):
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"Request {request_id} received with input: {user_input}")

    # Get or create session state
    session = sessions.get(user_input.chat_id)
    if not session:
        # Start with the solana coordinator agent if no session exists
        session = SessionState(solana_coordinator_agent)
        sessions[user_input.chat_id] = session

    # Update session state
    session.messages.append({"role": "user", "content": user_input.user_input})

    try:
        if user_input.stream:
            # Handle streaming response
            response = client.run(
                agent=session.agent,
                messages=session.messages,
                stream=True,
                debug=user_input.debug,
            )
            return EventSourceResponse(stream_generator(response))
        else:
            # Handle regular response
            response = client.run(
                agent=session.agent,
                messages=session.messages,
                stream=False,
                debug=user_input.debug,
            )
            
            # Update session with response
            session.messages.extend(response.messages)
            session.agent = response.agent

            result = {
                "content": response.messages,
                "chat_id": user_input.chat_id,
                "agent": session.agent.name
            }
            print(result)
            return result
    except Exception as e:
        logger.error(f"Request {request_id} - Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{chat_id}")
async def delete_session(chat_id: str):
    """Delete a session and its associated state"""
    if chat_id in sessions:
        del sessions[chat_id]
        return {"status": "success", "message": f"Session {chat_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/session/{chat_id}/history")
async def get_session_history(chat_id: str):
    """Get the message history for a session"""
    if chat_id in sessions:
        session = sessions[chat_id]
        return {
            "chat_id": chat_id,
            "messages": session.messages,
            "agent_name": session.agent.name
        }
    raise HTTPException(status_code=404, detail="Session not found")

@app.get("/health")
async def health_check():
    """API endpoint to check service health and uptime"""
    try:
        # Basic health check - verify we can access the sessions dict
        _ = len(sessions)
        
        return {
            "status": "healthy",
            "message": "Service is running",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Service is unhealthy"
        )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)


# from configs.agents import coordinator_agent, solana_coordinator_agent
# from swarm import Swarm, Agent
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import logging
# import json
# from datetime import datetime

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('app.log'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# client = Swarm()
# app = FastAPI()

# class InputData(BaseModel):
#     user_input: str
#     chat_id: str

# @app.post('/run')
# async def run_agent(input_data: InputData):
#     try:
#         chat_id = input_data.chat_id
#         print(f"Chat ID: {chat_id}")

#         request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
#         logger.info(f"Request {request_id} received with input: {input_data}")

#         # Parse the user_input as JSON if it's a string containing messages
#         try:
#             messages = json.loads(input_data.user_input)
#         except json.JSONDecodeError:
#             messages = [{"role": "user", "content": input_data.user_input}]
            
#         logger.debug(f"Request {request_id} - Formatted messages: {json.dumps(messages)}")

#         logger.info(f"Request {request_id} - Running Solana coordinator agent")
#         result = client.run(agent=solana_coordinator_agent, messages=messages)
        
#         response = result.messages[-1]["content"]
#         responding_agent = "Unknown"
        
#         # Try to determine which agent provided the response
#         for message in result.messages:
#             if message.get("tool_name"):
#                 responding_agent = message["tool_name"]
#                 break
        
#         logger.info(f"Request {request_id} - Successfully processed request. Response from agent: {responding_agent}")
#         logger.debug(f"Request {request_id} - Full response: {json.dumps(result.messages)}")
        
#         return {
#             "content": response,
#             "agent": responding_agent
#         }

#     except Exception as e:
#         logger.error(f"Request {request_id} - Error processing request: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == '__main__':
#     import uvicorn
#     logger.info("Starting FastAPI server")
#     uvicorn.run(app, host='0.0.0.0', port=5002)
