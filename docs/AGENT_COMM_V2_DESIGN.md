# Phase 1.3: Agent Communication v2 - Design

## Current State Analysis

### Existing Components
```
agents/
├── agent_base.py          # BaseAgent with asyncio.Queue
├── agent_orchestrator.py  # Central message router
├── react_agent.py         # ReAct pattern agent
└── *.py                   # Specialized agents
```

### Current Message Flow
```
Agent A ──[AgentMessage]──> Orchestrator ──[route_message()]──> Agent B
                              │
                              └──> shared_context
                              └──> message_history
```

### Limitations
1. **No persistence** - Messages lost on restart
2. **No authentication** - Any agent can connect
3. **No encryption** - Messages in plain text
4. **No delivery guarantees** - Fire-and-forget
5. **No scaling** - Single process only

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│              (Auth, Rate Limiting, TLS termination)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    Message Queue (Redis/RabbitMQ)               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │ Agent Events │ │ Tasks Queue  │ │ Results Queue            ││
│  │  pub/sub     │ │  (work)      │ │  (responses)             ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────┐  ┌───────▼──────┐ ┌─────▼─────┐
│  Research   │  │   Analysis   │ │  Exploit  │
│    Agent    │  │    Agent     │ │   Agent   │
│  (Container)│  │  (Container) │ │ (Container)│
└─────────────┘  └──────────────┘ └───────────┘
```

## Components to Build

### 1. Secure Message Protocol
```python
class SecureAgentMessage:
    message_id: str          # UUID v4
    sender_id: str           # Agent identity
    recipient_id: str        # Target agent
    timestamp: datetime      # UTC
    payload: bytes           # Encrypted content
    signature: bytes         # Ed25519 signature
    message_type: str        # task/result/event/heartbeat

class MessageEncryption:
    # X25519 key exchange + AES-256-GCM
    def encrypt(payload: bytes, recipient_pubkey: bytes) -> EncryptedMessage
    def decrypt(encrypted: EncryptedMessage, private_key: bytes) -> bytes
```

### 2. Agent Authentication
```python
class AgentAuthenticator:
    # API Key based authentication
    def authenticate_agent(api_key: str) -> AgentIdentity
    def generate_agent_credentials(role: AgentRole) -> (AgentID, APIKey, Secret)
    def rotate_agent_keys(agent_id: str) -> NewCredentials
```

### 3. Message Queue Integration
```python
class AgentMessageQueue:
    # Redis Streams or RabbitMQ
    def publish(channel: str, message: SecureAgentMessage)
    def subscribe(channels: List[str], handler: Callable)
    def acknowledge(message_id: str)  # Delivery guarantee
    def retry_failed(max_retries: int = 3)
```

### 4. Real-time Event Streaming
```python
class EventStreamer:
    # WebSocket for real-time updates
    async def stream_events(agent_id: str) -> AsyncIterator[Event]
    async def broadcast(event: Event, filter: Filter)
```

## Implementation Plan

### 1.3.1 Message Protocol (2h)
- Define message schema
- Implement encryption layer
- Add signing/verification

### 1.3.2 Agent Authentication (2h)
- API key generation
- Agent registration endpoint
- Credential rotation

### 1.3.3 Message Queue (3h)
- Redis integration
- Pub/sub channels
- Persistence layer

### 1.3.4 Event Streaming (2h)
- WebSocket endpoint
- Event broadcasting
- Client connections

### 1.3.5 Integration (2h)
- Update BaseAgent
- Connect to orchestrator
- Migration path

### 1.3.6 Tests (1h)
- Unit tests
- Integration tests
- Security tests

## API Design

### Agent Registration
```http
POST /api/v1/agents/register
Authorization: Bearer <admin_token>

{
  "name": "research-agent-1",
  "role": "researcher",
  "allowed_channels": ["recon", "targets"]
}

Response:
{
  "agent_id": "agt_abc123",
  "api_key": "zen_key_xxx",
  "api_secret": "sec_yyy",  # Only shown once
  "public_key": "..."       # For encryption
}
```

### Send Message
```python
# Agent SDK usage
from zen_agents import AgentClient

agent = AgentClient(
    agent_id="agt_abc123",
    api_key="zen_key_xxx",
    api_secret="sec_yyy"
)

await agent.connect()

await agent.send_message(
    recipient="analyst-agent-1",
    msg_type="task",
    payload={"target": "example.com", "scan_type": "nmap"}
)

# Receive messages
async for msg in agent.receive_messages():
    print(f"Received: {msg.payload}")
```

### WebSocket Events
```javascript
// Client connection
const ws = new WebSocket('wss://api.zen-pentest.local/agents/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    api_key: 'zen_key_xxx',
    signature: '...'
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(msg.type, msg.payload);
};
```

## Security Considerations

1. **Mutual TLS** - Agents verify server, server verifies agents
2. **End-to-end encryption** - Messages encrypted between agents
3. **API key rotation** - Automatic key rotation every 90 days
4. **Audit logging** - All messages logged for compliance
5. **Rate limiting** - Prevent message flooding
6. **Sandboxing** - Agents run in isolated containers

## Files to Create

```
agents/v2/
├── __init__.py
├── secure_message.py      # Encryption & signing
├── agent_client.py        # Agent SDK
├── message_queue.py       # Redis/RabbitMQ wrapper
├── event_stream.py        # WebSocket handler
└── auth_manager.py        # Agent authentication

api/routes/
└── agents_v2.py           # REST endpoints

tests/agents/
└── test_comm_v2.py        # Tests
```

## Success Criteria

- [ ] Agents can authenticate with API keys
- [ ] Messages are encrypted end-to-end
- [ ] Message delivery is guaranteed (ack/nack)
- [ ] Real-time event streaming works
- [ ] 20+ messages/second throughput
- [ ] <100ms latency for same-datacenter agents
