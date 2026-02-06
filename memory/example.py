"""
Example: Using Memory System with Agents
"""
from memory import MemoryManager


def example_conversation_memory():
    # Initialize memory manager
    manager = MemoryManager(storage_backend='sqlite')
    
    # Create memory for a session
    memory = manager.create_conversation_memory(
        session_id='pentest-session-001',
        max_history=20
    )
    
    # Add conversation turns
    memory.add_user_message("Scan target 192.168.1.1")
    memory.add_assistant_message("Starting port scan on 192.168.1.1...")
    memory.add_assistant_message("Found open ports: 22, 80, 443")
    
    # Get context for LLM
    context = memory.get_summary()
    print(f"Conversation context:\n{context}")
    
    # Get LangGraph format
    messages = memory.get_messages_for_langgraph()
    print(f"\nLangGraph format: {messages}")
    
    return memory


def example_working_memory():
    from memory.working import WorkingMemory
    
    # Create working memory (scratchpad)
    wm = WorkingMemory(max_items=50)
    
    # Set current task context
    wm.set_scratchpad('current_target', '192.168.1.1')
    wm.set_scratchpad('scan_status', 'in_progress')
    wm.set_scratchpad('ports_found', [22, 80, 443])
    
    # Add observations
    wm.add("Port 80 running Apache 2.4.41")
    wm.add("Port 443 has valid SSL certificate")
    
    # Get full context
    context = wm.get_current_context()
    print(f"Working context:\n{context}")
    
    return wm


if __name__ == '__main__':
    print("=== Conversation Memory Example ===")
    example_conversation_memory()
    
    print("\n=== Working Memory Example ===")
    example_working_memory()
