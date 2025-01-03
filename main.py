from configs.agents import coordinator_agent, solana_coordinator_agent
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from swarm import Swarm, Agent
import json
import logging
from datetime import datetime, timedelta
from sse_starlette.sse import EventSourceResponse
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis
import pickle
import os
from configs.blockchain_agents.solana.transaction_agent import solana_swap

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

#Configure Redis and MongoDB
redis_client = Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD')
)
mongo_client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))

db = mongo_client.justx_db
sessions_collection = db.sessions

REDIS_EXPIRY = 3600  # 1 hour cache expiry

# Define request models
class UserInput(BaseModel):
    chat_id: str
    user_input: str
    stream: Optional[bool] = False
    debug: Optional[bool] = False

class SessionState:
    def __init__(self, agent: Agent):
        self.messages: List[Dict] = []
        self.agent = agent
        self.last_updated = datetime.utcnow()

    def to_dict(self):
        return {
            'messages': self.messages,
            'agent_name': self.agent.name,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: dict, agent: Agent):
        session = cls(agent)
        session.messages = data['messages']
        session.last_updated = data['last_updated']
        return session
    



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

async def get_session(chat_id: str) -> Optional[SessionState]:
    """Get session from Redis or MongoDB"""
    # Try Redis first
    session_data = redis_client.get(f"session:{chat_id}")
    if session_data:
        session_dict = pickle.loads(session_data)
        return SessionState.from_dict(session_dict, solana_coordinator_agent)

    # Try MongoDB if not in Redis
    session_doc = await sessions_collection.find_one({"chat_id": chat_id})
    if session_doc:
        session = SessionState.from_dict(session_doc, solana_coordinator_agent)
        # Cache in Redis
        redis_client.setex(
            f"session:{chat_id}",
            REDIS_EXPIRY,
            pickle.dumps(session.to_dict())
        )
        return session
    return None

async def save_session(chat_id: str, session: SessionState):
    """Save session to both Redis and MongoDB"""
    session_dict = session.to_dict()
    
    # Save to Redis
    redis_client.setex(
        f"session:{chat_id}",
        REDIS_EXPIRY,
        pickle.dumps(session_dict)
    )
    
    # Save to MongoDB
    await sessions_collection.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                **session_dict,
                "chat_id": chat_id,
                "last_updated": datetime.utcnow()
            }
        },
        upsert=True
    )

@app.post("/run")
async def run_agent(user_input: UserInput):
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.info(f"Request {request_id} received with input: {user_input}")
    print(user_input)

    # Get or create session state
    session = await get_session(user_input.chat_id)
    if not session:
        session = SessionState(solana_coordinator_agent)

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
              #  model_override="gpt-4o-mini"
            )
            return EventSourceResponse(stream_generator(response))
        else:
            # Handle regular response
            response = client.run(
                agent=session.agent,
                messages=session.messages,
                stream=False,
                debug=user_input.debug,
             #   model_override="gpt-4o-mini"
            )
            
            # Update session with response
            session.messages.extend(response.messages)
            session.agent = response.agent
            
            # Save updated session
            await save_session(user_input.chat_id, session)

            result = {
                "content": response.messages,
                "chat_id": user_input.chat_id,
                "agent": session.agent.name
            }
            # Check if response contains solana_swap parameters
            # Only execute swap if response contains valid solana_swap parameters
            last_message = response.messages[-1]
            swap_params = None
            
            def extract_json_from_text(text):
                try:
                    # Find anything that looks like JSON using regex
                    import re
                    json_pattern = r'\{(?:[^{}]|(?R))*\}'
                    potential_jsons = re.finditer(json_pattern, text)
                    
                    for match in potential_jsons:
                        try:
                            parsed = json.loads(match.group())
                            if "solana_swap" in str(parsed).lower():
                                return parsed
                        except:
                            continue
                    return None
                except:
                    return None

            # Get content in various formats
            if isinstance(last_message, dict):
                content = last_message.get("content", "")
            else:
                content = str(last_message)

            # Multiple attempts to find swap parameters
            try:
                # Attempt 1: Direct JSON parsing if content is string
                if isinstance(content, str):
                    try:
                        # Remove markdown code block syntax if present
                        content = content.replace("```json", "").replace("```", "").strip()
                        parsed_content = json.loads(content)
                        if isinstance(parsed_content, dict):
                            content = parsed_content
                    except:
                        # If direct parsing fails, try to extract JSON from text
                        extracted = extract_json_from_text(content)
                        if extracted:
                            content = extracted

                # Attempt 2: Check dictionary format
                if isinstance(content, dict):
                    if content.get("name") == "solana_swap":
                        swap_params = content.get("parameters")
                    elif "solana_swap" in str(content).lower():
                        # Check various possible parameter locations
                        possible_params = [
                            content.get("parameters"),
                            content.get("solana_swap"),
                            content.get("params"),
                            content
                        ]
                        for params in possible_params:
                            if isinstance(params, dict) and all(key in params for key in ["input_token_address", "output_token_address", "amount"]):
                                swap_params = params
                                break

                # Attempt 3: Search in nested structures
                if not swap_params and isinstance(content, str):
                    extracted = extract_json_from_text(content)
                    if extracted:
                        if extracted.get("name") == "solana_swap":
                            swap_params = extracted.get("parameters")
                        elif isinstance(extracted, dict):
                            swap_params = extracted

                # Attempt 4: Search through all messages if not found yet
                if not swap_params:
                    for msg in response.messages:
                        if isinstance(msg, dict) and msg.get("content"):
                            try:
                                msg_content = msg["content"].replace("```json", "").replace("```", "").strip()
                                parsed = json.loads(msg_content)
                                if parsed.get("name") == "solana_swap":
                                    swap_params = parsed.get("parameters")
                                    break
                            except:
                                continue

            except Exception as e:
                logger.error(f"Error parsing swap parameters: {str(e)}")
                # Continue execution even if parsing fails
                pass

            # Final validation of swap_params
            if swap_params and isinstance(swap_params, dict):
                required_keys = ["input_token_address", "output_token_address", "amount"]
                if not all(key in swap_params for key in required_keys):
                    swap_params = None

            if swap_params:
                # Execute swap with parameters
                swap_result = solana_swap(
                    input_token=swap_params["input_token_address"],
                    output_token=swap_params["output_token_address"], 
                    amount=swap_params["amount"],
                    slippage=swap_params["slippage"]
                )
                if "transaction_functions" not in result:
                    result["transaction_functions"] = {}
                result["transaction_functions"]["solana_swap"] = swap_result
                print(swap_result)
###################################@

            print(session.agent.name)
            print(result)
            return result
    except Exception as e:
        logger.error(f"Request {request_id} - Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# @app.delete("/session/{chat_id}")
# async def delete_session(chat_id: str):
#     """Delete a session from both Redis and MongoDB"""
#     redis_client.delete(f"session:{chat_id}")
#     result = await sessions_collection.delete_one({"chat_id": chat_id})
    
#     if result.deleted_count > 0:
#         return {"status": "success", "message": f"Session {chat_id} deleted"}
#     raise HTTPException(status_code=404, detail="Session not found")

@app.get("/session/{chat_id}/history")
async def get_session_history(chat_id: str):
    """Get the message history for a session"""
    session = await get_session(chat_id)
    if session:
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
