"""
Memory System for Autonomous Agents

Implements multi-layer memory:
- Working Memory: Current session context
- Short-term: Recent N actions
- Long-term: Vector store for semantic search
- Episodic: Full attack chains
"""

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import hashlib


@dataclass
class MemoryEntry:
    """A single memory entry."""
    id: str
    content: str
    memory_type: str  # 'thought', 'action', 'observation', 'finding', 'goal'
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    session_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.memory_type,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id
        }


class BaseMemory(ABC):
    """Abstract base class for memory implementations."""
    
    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry."""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Search for relevant memories."""
        pass
    
    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get recent memories."""
        pass


class WorkingMemory(BaseMemory):
    """
    Working memory for current session.
    Keeps track of immediate context and recent actions.
    """
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.entries: List[MemoryEntry] = []
        self.session_id = str(uuid.uuid4())
        self.current_goal: Optional[str] = None
        self.context: Dict[str, Any] = {}
    
    async def add(self, entry: MemoryEntry) -> None:
        """Add entry to working memory."""
        entry.session_id = self.session_id
        self.entries.append(entry)
        
        # Trim if exceeds max size
        if len(self.entries) > self.max_size:
            self.entries = self.entries[-self.max_size:]
    
    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Simple text search in working memory."""
        query_lower = query.lower()
        matches = [
            e for e in self.entries
            if query_lower in e.content.lower()
        ]
        return matches[-limit:]
    
    async def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get most recent entries."""
        return self.entries[-limit:]
    
    async def get_context_window(self, n: int = 5) -> Dict[str, Any]:
        """Get the current context window for LLM."""
        recent = await self.get_recent(n)
        
        return {
            'session_id': self.session_id,
            'goal': self.current_goal,
            'context': self.context,
            'recent_actions': [e.to_dict() for e in recent],
            'memory_count': len(self.entries)
        }
    
    def set_goal(self, goal: str, context: Optional[Dict] = None):
        """Set the current goal."""
        self.current_goal = goal
        if context:
            self.context.update(context)
    
    def update_context(self, key: str, value: Any):
        """Update context information."""
        self.context[key] = value
    
    def clear(self):
        """Clear working memory."""
        self.entries = []
        self.current_goal = None
        self.context = {}


class LongTermMemory(BaseMemory):
    """
    Long-term memory with vector storage for semantic search.
    
    Uses simple embedding-based retrieval.
    In production, use ChromaDB, Pinecone, or similar.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.entries: Dict[str, MemoryEntry] = {}
        # Simple in-memory storage; replace with vector DB
    
    def _simple_hash_embedding(self, text: str) -> List[float]:
        """
        Create a simple embedding from text.
        In production, use real embeddings (OpenAI, HuggingFace, etc.)
        """
        # Simple bag-of-words style embedding
        words = text.lower().split()
        embedding = [0.0] * 128
        
        for word in words:
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = hash_val % 128
            embedding[idx] += 1.0
        
        # Normalize
        magnitude = sum(x**2 for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x**2 for x in a) ** 0.5
        magnitude_b = sum(x**2 for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    async def add(self, entry: MemoryEntry) -> None:
        """Add entry with embedding."""
        # Generate embedding if not provided
        if entry.embedding is None:
            entry.embedding = self._simple_hash_embedding(entry.content)
        
        self.entries[entry.id] = entry
        
        # Persist if storage path provided
        if self.storage_path:
            await self._persist()
    
    async def search(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """Semantic search using embeddings."""
        query_embedding = self._simple_hash_embedding(query)
        
        # Calculate similarities
        scored = []
        for entry in self.entries.values():
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                scored.append((similarity, entry))
        
        # Sort by similarity
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [entry for _, entry in scored[:limit]]
    
    async def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get most recent entries."""
        sorted_entries = sorted(
            self.entries.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )
        return sorted_entries[:limit]
    
    async def _persist(self):
        """Save to disk."""
        if not self.storage_path:
            return
        
        data = {
            k: {
                **v.to_dict(),
                'embedding': v.embedding
            }
            for k, v in self.entries.items()
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
    
    async def load(self):
        """Load from disk."""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for entry_id, entry_data in data.items():
                entry = MemoryEntry(
                    id=entry_data['id'],
                    content=entry_data['content'],
                    memory_type=entry_data['type'],
                    metadata=entry_data.get('metadata', {}),
                    timestamp=datetime.fromisoformat(entry_data['timestamp']),
                    embedding=entry_data.get('embedding'),
                    session_id=entry_data.get('session_id', '')
                )
                self.entries[entry_id] = entry
        except FileNotFoundError:
            pass


class EpisodicMemory:
    """
    Episodic memory for storing complete attack chains.
    Used for learning from past operations.
    """
    
    def __init__(self):
        self.episodes: List[Dict] = []
    
    def record_episode(
        self,
        goal: str,
        steps: List[Dict],
        outcome: str,
        success: bool,
        lessons_learned: List[str]
    ):
        """Record a complete attack episode."""
        episode = {
            'id': str(uuid.uuid4()),
            'goal': goal,
            'steps': steps,
            'outcome': outcome,
            'success': success,
            'lessons_learned': lessons_learned,
            'timestamp': datetime.now().isoformat()
        }
        
        self.episodes.append(episode)
    
    def get_similar_episodes(self, goal: str) -> List[Dict]:
        """Find episodes with similar goals."""
        # Simple keyword matching
        goal_words = set(goal.lower().split())
        
        scored = []
        for episode in self.episodes:
            episode_words = set(episode['goal'].lower().split())
            similarity = len(goal_words & episode_words) / len(goal_words | episode_words)
            scored.append((similarity, episode))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:3]]


class MemoryManager:
    """
    Unified interface for all memory systems.
    Coordinates working, long-term, and episodic memory.
    """
    
    def __init__(
        self,
        long_term_path: Optional[str] = None,
        enable_embeddings: bool = False
    ):
        self.working = WorkingMemory()
        self.long_term = LongTermMemory(long_term_path)
        self.episodic = EpisodicMemory()
        self.enable_embeddings = enable_embeddings
    
    async def add_goal(self, goal: str, context: Optional[Dict] = None):
        """Add a new goal to memory."""
        self.working.set_goal(goal, context)
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=goal,
            memory_type='goal',
            metadata={'context': context or {}}
        )
        
        await self.working.add(entry)
        await self.long_term.add(entry)
    
    async def add_experience(
        self,
        thought: Any,
        action: Any,
        observation: Any
    ):
        """Add a complete ReAct cycle to memory."""
        # Add to working memory
        thought_entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=str(thought.content) if hasattr(thought, 'content') else str(thought),
            memory_type='thought',
            metadata={'step': getattr(thought, 'step_number', 0)}
        )
        await self.working.add(thought_entry)
        
        action_entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=f"{action.type.name}: {getattr(action, 'tool_name', '')}",
            memory_type='action',
            metadata={
                'tool': getattr(action, 'tool_name', None),
                'parameters': getattr(action, 'parameters', {}),
                'step': getattr(action, 'step_number', 0)
            }
        )
        await self.working.add(action_entry)
        
        obs_content = str(observation.result) if hasattr(observation, 'result') else str(observation)
        obs_entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=obs_content[:1000],  # Truncate long outputs
            memory_type='observation',
            metadata={
                'success': getattr(observation, 'success', True),
                'step': getattr(observation, 'step_number', 0)
            }
        )
        await self.working.add(obs_entry)
        
        # Also add to long-term for important findings
        if hasattr(observation, 'result') and observation.result:
            findings = self._extract_findings(observation.result)
            for finding in findings:
                finding_entry = MemoryEntry(
                    id=str(uuid.uuid4()),
                    content=str(finding),
                    memory_type='finding',
                    metadata={'source': 'tool_execution'}
                )
                await self.long_term.add(finding_entry)
    
    async def get_relevant_context(self, query: str) -> Dict[str, Any]:
        """Get relevant context from all memory layers."""
        # Working memory context
        working_context = await self.working.get_context_window()
        
        # Long-term relevant memories
        long_term_memories = await self.long_term.search(query, limit=3)
        
        # Similar past episodes
        similar_episodes = self.episodic.get_similar_episodes(query)
        
        return {
            'current_session': working_context,
            'relevant_past': [m.to_dict() for m in long_term_memories],
            'similar_episodes': similar_episodes
        }
    
    async def search(self, query: str) -> List[MemoryEntry]:
        """Search across memory systems."""
        working_results = await self.working.search(query)
        long_term_results = await self.long_term.search(query)
        
        # Combine and deduplicate
        all_results = working_results + long_term_results
        seen = set()
        unique = []
        for r in all_results:
            if r.id not in seen:
                seen.add(r.id)
                unique.append(r)
        
        return unique
    
    async def get_findings(self) -> List[Dict]:
        """Get all security findings from memory."""
        findings = []
        
        # Search for finding-type memories
        results = await self.long_term.search('vulnerability finding exploit')
        for entry in results:
            if entry.memory_type == 'finding':
                findings.append(entry.to_dict())
        
        return findings
    
    def _extract_findings(self, result: Any) -> List[Any]:
        """Extract security findings from tool results."""
        findings = []
        
        if isinstance(result, dict):
            # Look for common finding patterns
            if 'findings' in result:
                findings.extend(result['findings'])
            if 'open_ports' in result:
                findings.extend(result['open_ports'])
            if 'vulnerabilities' in result:
                findings.extend(result['vulnerabilities'])
        
        return findings
    
    async def record_episode(self, outcome: str, success: bool):
        """Record the completion of an attack episode."""
        recent = await self.working.get_recent(100)
        
        self.episodic.record_episode(
            goal=self.working.current_goal or "Unknown",
            steps=[e.to_dict() for e in recent],
            outcome=outcome,
            success=success,
            lessons_learned=[]  # Could extract from analysis
        )
    
    async def load(self):
        """Load long-term memory from disk."""
        await self.long_term.load()
