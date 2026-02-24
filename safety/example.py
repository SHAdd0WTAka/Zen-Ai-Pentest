"""
Example: Using Safety System
"""

from safety import SafetyLevel, SafetyPipeline


def example_basic_usage():
    # Initialize safety pipeline
    safety = SafetyPipeline(safety_level=SafetyLevel.STRICT, auto_correct=True)

    # Check an output
    output = """
    Found vulnerability CVE-2023-1234 on target 192.168.1.1.
    Port 80 is maybe open. This is probably critical.
    """

    result = safety.check_output(output=output, context={"target": "192.168.1.1"}, schema_name="vulnerability_report")

    print(f"Passed: {result['passed']}")
    print(f"Confidence: {result['confidence'].score} ({result['confidence'].level})")
    print(f"Issues: {result['issues']}")
    print(f"Should retry: {result['should_retry']}")

    if result["should_retry"]:
        retry_prompt = safety.get_retry_prompt("Analyze target", result)
        print(f"\nRetry prompt: {retry_prompt}")

    return result


def example_with_agent():
    """Example integration with agent"""
    from memory import MemoryManager

    # Setup
    memory = MemoryManager().create_conversation_memory("test")
    safety = SafetyPipeline(safety_level=SafetyLevel.STANDARD)

    # Agent generates output
    agent_output = "Port scan complete. Port 22 is closed."

    # Add context from memory
    context = {"scan_results": {"ports": {"22": {"state": "open"}}}, "memory_context": memory.get_recent(5)}

    # Safety check
    result = safety.check_output(agent_output, context)

    if not result["passed"]:
        print("Output failed safety check!")
        print(f"Issues: {result['issues']}")
        print(f"Corrected: {result.get('corrected_output', agent_output)}")

    return result


if __name__ == "__main__":
    print("=== Basic Safety Check ===")
    example_basic_usage()

    print("\n=== Agent Integration ===")
    example_with_agent()
