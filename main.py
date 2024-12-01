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

# Configure Redis and MongoDB
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
            
            # Save updated session
            await save_session(user_input.chat_id, session)

            result = {
                "content": response.messages,
                "chat_id": user_input.chat_id,
                "agent": session.agent.name
            }
            return result
    except Exception as e:
        logger.error(f"Request {request_id} - Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{chat_id}")
async def delete_session(chat_id: str):
    """Delete a session from both Redis and MongoDB"""
    redis_client.delete(f"session:{chat_id}")
    result = await sessions_collection.delete_one({"chat_id": chat_id})
    
    if result.deleted_count > 0:
        return {"status": "success", "message": f"Session {chat_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

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
