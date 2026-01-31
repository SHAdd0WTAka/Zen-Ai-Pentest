# ADR 0003: LLM Backend Routing Strategy

## Status
Accepted

## Context
Different LLM backends have different characteristics:
- Cost (free vs paid)
- Quality (accuracy, reasoning)
- Rate limits
- Availability
- Context window size

## Decision
Implement intelligent routing based on task requirements:

### Routing Logic
```python
if task.complexity == 'high' and requires_reasoning:
    use = 'claude' or 'chatgpt'
elif task == 'reconnaissance' and free_tier_available:
    use = 'duckduckgo'
else:
    use = 'openrouter' (cost-optimized)
```

### Supported Backends
1. **DuckDuckGo AI** - Free, rate-limited, good for simple tasks
2. **OpenRouter** - Unified API, cost-effective
3. **ChatGPT Direct** - High quality, requires API key
4. **Claude Direct** - Best reasoning, requires API key

### Fallback Strategy
- Primary fails → Try secondary
- All paid fail → Fallback to free tier
- Queue and retry with exponential backoff

## Consequences

### Positive
- Cost optimization
- High availability
- Best quality for complex tasks
- Graceful degradation

### Negative
- Complex routing logic
- Different response formats to normalize
- State management across backends

## Metrics
- Cost per 1000 requests: Target <$0.50
- Success rate: Target >95%
- Average latency: Target <2s

## References
- [OpenRouter Docs](https://openrouter.ai/docs)
- [DuckDuckGo AI](https://duckduckgo.com/duckai)
