#!/usr/bin/env python3
"""
Test Agent Client
=================

Simple test client for Agent Communication v2 WebSocket.

Usage:
    # Terminal 1: Start the server
    JWT_SECRET_KEY="test-secret" python -m api.main
    
    # Terminal 2: Run this test agent
    python test_agent_client.py
"""

import asyncio
import json
import sys
import websockets


class TestAgent:
    """Simple test agent for WebSocket communication"""
    
    def __init__(self, agent_id: str, server_url: str = "ws://localhost:8000/agents/ws"):
        self.agent_id = agent_id
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.message_count = 0
    
    async def connect(self):
        """Connect to WebSocket server"""
        print(f"🔌 Connecting to {self.server_url}...")
        
        try:
            self.websocket = await websockets.connect(self.server_url)
            
            # Send auth
            await self.websocket.send(json.dumps({
                "type": "auth",
                "agent_id": self.agent_id
            }))
            
            # Wait for auth response
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "auth_success":
                self.connected = True
                print(f"✅ Connected as {self.agent_id}")
                print(f"   Server message: {data.get('message')}")
                return True
            else:
                print(f"❌ Auth failed: {data}")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def send_message(self, recipient: str, payload: dict):
        """Send message to another agent"""
        if not self.connected:
            print("❌ Not connected")
            return
        
        await self.websocket.send(json.dumps({
            "type": "message",
            "message_id": f"msg_{self.message_count}",
            "recipient": recipient,
            "payload": payload
        }))
        
        self.message_count += 1
        print(f"📤 Sent message to {recipient}: {payload}")
    
    async def send_heartbeat(self):
        """Send heartbeat"""
        if not self.connected:
            return
        
        await self.websocket.send(json.dumps({
            "type": "heartbeat"
        }))
    
    async def receive_loop(self):
        """Receive messages from server"""
        try:
            while self.connected:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                msg_type = data.get("type")
                
                if msg_type == "message":
                    sender = data.get("sender", "unknown")
                    payload = data.get("payload", {})
                    print(f"📥 Received from {sender}: {payload}")
                
                elif msg_type == "ack":
                    print(f"✅ Message acknowledged: {data.get('message_id')}")
                
                elif msg_type == "heartbeat_ack":
                    print(f"💓 Heartbeat acknowledged")
                
                elif msg_type == "error":
                    print(f"⚠️ Error: {data.get('error')}")
                
                else:
                    print(f"📨 Received: {data}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Connection closed")
            self.connected = False
        except Exception as e:
            print(f"❌ Receive error: {e}")
            self.connected = False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "disconnect"
            }))
            await self.websocket.close()
            self.connected = False
            print(f"🔌 Disconnected")


DEFAULT_SERVER_URL = "ws://localhost:8000/agents/ws"

async def test_single_agent():
    """Test single agent connection"""
    agent = TestAgent("test-agent-1", DEFAULT_SERVER_URL)
    
    if not await agent.connect():
        return
    
    # Start receive loop in background
    receive_task = asyncio.create_task(agent.receive_loop())
    
    # Send a broadcast message
    await asyncio.sleep(1)
    await agent.send_message("broadcast", {
        "action": "test",
        "message": "Hello from test agent!"
    })
    
    # Wait a bit
    await asyncio.sleep(5)
    
    # Send heartbeat
    await agent.send_heartbeat()
    await asyncio.sleep(2)
    
    # Disconnect
    await agent.disconnect()
    receive_task.cancel()


async def test_two_agents():
    """Test communication between two agents"""
    print("\n🧪 Testing two-agent communication...\n")
    
    agent1 = TestAgent("agent-alpha", DEFAULT_SERVER_URL)
    agent2 = TestAgent("agent-beta", DEFAULT_SERVER_URL)
    
    # Connect both agents
    if not await agent1.connect():
        return
    if not await agent2.connect():
        return
    
    # Start receive loops
    task1 = asyncio.create_task(agent1.receive_loop())
    task2 = asyncio.create_task(agent2.receive_loop())
    
    # Agent 1 sends to Agent 2
    await asyncio.sleep(1)
    print("\n--- Agent Alpha sending to Agent Beta ---")
    await agent1.send_message("agent-beta", {
        "action": "ping",
        "message": "Hello Beta!"
    })
    
    await asyncio.sleep(2)
    
    # Agent 2 sends to Agent 1
    print("\n--- Agent Beta sending to Agent Alpha ---")
    await agent2.send_message("agent-alpha", {
        "action": "pong",
        "message": "Hello Alpha!"
    })
    
    await asyncio.sleep(2)
    
    # Test broadcast
    print("\n--- Testing broadcast ---")
    await agent1.send_message("broadcast", {
        "action": "announce",
        "message": "Broadcast to all agents!"
    })
    
    await asyncio.sleep(3)
    
    # Disconnect
    print("\n--- Disconnecting ---")
    await agent1.disconnect()
    await agent2.disconnect()
    
    task1.cancel()
    task2.cancel()
    
    print("\n✅ Two-agent test complete!")


async def interactive_mode():
    """Interactive mode for testing"""
    agent_id = input("Enter agent ID: ").strip() or "interactive-agent"
    agent = TestAgent(agent_id, DEFAULT_SERVER_URL)
    
    if not await agent.connect():
        return
    
    # Start receive loop in background
    receive_task = asyncio.create_task(agent.receive_loop())
    
    print("\nCommands:")
    print("  send <recipient> <message>  - Send message")
    print("  broadcast <message>         - Broadcast to all")
    print("  heartbeat                   - Send heartbeat")
    print("  quit                        - Exit\n")
    
    try:
        while agent.connected:
            command = await asyncio.get_event_loop().run_in_executor(
                None, input, "> "
            )
            
            parts = command.strip().split(maxsplit=1)
            if not parts:
                continue
            
            cmd = parts[0].lower()
            
            if cmd == "quit":
                break
            
            elif cmd == "heartbeat":
                await agent.send_heartbeat()
            
            elif cmd == "send" and len(parts) > 1:
                # Format: send <recipient> <message>
                msg_parts = parts[1].split(maxsplit=1)
                if len(msg_parts) >= 2:
                    recipient = msg_parts[0]
                    message = msg_parts[1]
                    await agent.send_message(recipient, {"text": message})
                else:
                    print("Usage: send <recipient> <message>")
            
            elif cmd == "broadcast" and len(parts) > 1:
                await agent.send_message("broadcast", {"text": parts[1]})
            
            else:
                print(f"Unknown command: {cmd}")
    
    except KeyboardInterrupt:
        print("\nInterrupted")
    
    finally:
        await agent.disconnect()
        receive_task.cancel()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Agent Client")
    parser.add_argument("--mode", choices=["single", "dual", "interactive"], 
                        default="single", help="Test mode")
    parser.add_argument("--server", default="ws://localhost:8000/agents/ws",
                        help="WebSocket server URL")
    
    args = parser.parse_args()
    
    # Update global server URL for test functions
    global DEFAULT_SERVER_URL
    DEFAULT_SERVER_URL = args.server
    
    print("=" * 60)
    print("Zen-AI-Pentest Agent Communication Test Client")
    print("=" * 60)
    print(f"Server: {args.server}")
    print(f"Mode: {args.mode}")
    print("=" * 60 + "\n")
    
    try:
        if args.mode == "single":
            await test_single_agent_with_url(args.server)
        elif args.mode == "dual":
            await test_two_agents_with_url(args.server)
        elif args.mode == "interactive":
            await interactive_mode_with_url(args.server)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_single_agent_with_url(server_url: str):
    """Test single agent with custom URL"""
    agent = TestAgent("test-agent-1", server_url)
    
    if not await agent.connect():
        return
    
    receive_task = asyncio.create_task(agent.receive_loop())
    
    await asyncio.sleep(1)
    await agent.send_message("broadcast", {
        "action": "test",
        "message": "Hello from test agent!"
    })
    
    await asyncio.sleep(5)
    await agent.send_heartbeat()
    await asyncio.sleep(2)
    
    await agent.disconnect()
    receive_task.cancel()


async def test_two_agents_with_url(server_url: str):
    """Test two agents with custom URL"""
    print("\n🧪 Testing two-agent communication...\n")
    
    agent1 = TestAgent("agent-alpha", server_url)
    agent2 = TestAgent("agent-beta", server_url)
    
    if not await agent1.connect():
        return
    if not await agent2.connect():
        return
    
    task1 = asyncio.create_task(agent1.receive_loop())
    task2 = asyncio.create_task(agent2.receive_loop())
    
    await asyncio.sleep(1)
    print("\n--- Agent Alpha sending to Agent Beta ---")
    await agent1.send_message("agent-beta", {"action": "ping", "message": "Hello Beta!"})
    
    await asyncio.sleep(2)
    
    print("\n--- Agent Beta sending to Agent Alpha ---")
    await agent2.send_message("agent-alpha", {"action": "pong", "message": "Hello Alpha!"})
    
    await asyncio.sleep(2)
    
    print("\n--- Testing broadcast ---")
    await agent1.send_message("broadcast", {"action": "announce", "message": "Broadcast!"})
    
    await asyncio.sleep(3)
    
    print("\n--- Disconnecting ---")
    await agent1.disconnect()
    await agent2.disconnect()
    
    task1.cancel()
    task2.cancel()
    
    print("\n✅ Two-agent test complete!")


async def interactive_mode_with_url(server_url: str):
    """Interactive mode with custom URL"""
    agent_id = input("Enter agent ID: ").strip() or "interactive-agent"
    agent = TestAgent(agent_id, server_url)
    
    if not await agent.connect():
        return
    
    receive_task = asyncio.create_task(agent.receive_loop())
    
    print("\nCommands: send <recipient> <message> | broadcast <message> | heartbeat | quit\n")
    
    try:
        while agent.connected:
            command = await asyncio.get_event_loop().run_in_executor(None, input, "> ")
            parts = command.strip().split(maxsplit=1)
            if not parts:
                continue
            
            cmd = parts[0].lower()
            
            if cmd == "quit":
                break
            elif cmd == "heartbeat":
                await agent.send_heartbeat()
            elif cmd == "send" and len(parts) > 1:
                msg_parts = parts[1].split(maxsplit=1)
                if len(msg_parts) >= 2:
                    await agent.send_message(msg_parts[0], {"text": msg_parts[1]})
                else:
                    print("Usage: send <recipient> <message>")
            elif cmd == "broadcast" and len(parts) > 1:
                await agent.send_message("broadcast", {"text": parts[1]})
    
    except KeyboardInterrupt:
        pass
    finally:
        await agent.disconnect()
        receive_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
