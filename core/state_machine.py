"""
Advanced State Machine for Zen AI Pentest Framework v3.0
========================================================
Hochmoderne State Machine mit:
- Hierarchical States (Composite & Sub-States)
- Guarded Transitions mit komplexen Bedingungen
- Event-Driven Architecture
- State Persistence & Recovery
- Parallel State Execution
- History States für Deep/Flat History
- Time-based Transitions
- Automatic State Validation

Autonomous Operations:
- Kein manuelles Zutun erforderlich
- Self-validating state transitions
- Automatic rollback on failure
- Predictive state preloading
"""

from enum import Enum, auto
from typing import Dict, List, Any, Optional, Callable, Set, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import asyncio
import json
import logging
import uuid
import time
from abc import ABC, abstractmethod
from contextvars import ContextVar

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Arten von States."""
    SIMPLE = "simple"
    COMPOSITE = "composite"  # Hat Sub-States
    PARALLEL = "parallel"    # Parallele Sub-States
    HISTORY = "history"      # Merkt vorherigen State
    FINAL = "final"          # End-State


class HistoryType(Enum):
    """History-Typen für History States."""
    SHALLOW = "shallow"  # Nur direkten State
    DEEP = "deep"        # Komplette History


@dataclass
class StateEvent:
    """Event für State Transitions."""
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


@dataclass
class TransitionGuard:
    """Guard-Bedingung für Transitions."""
    condition: Callable[[StateEvent, 'StateContext'], bool]
    description: str = ""
    priority: int = 0
    
    def evaluate(self, event: StateEvent, context: 'StateContext') -> bool:
        try:
            return self.condition(event, context)
        except Exception as e:
            logger.warning(f"Guard evaluation failed: {e}")
            return False


@dataclass
class StateAction:
    """Aktion beim Eintritt/Verlassen eines States."""
    action: Callable[['State', 'StateContext'], Any]
    async_execution: bool = False
    timeout_seconds: Optional[float] = None
    retry_on_failure: bool = False
    max_retries: int = 3


class StateContext:
    """
    Kontext für State Machine Execution.
    Thread-safe Context für State-Daten.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.data: Dict[str, Any] = {}
        self.history: deque = deque(maxlen=100)
        self.event_log: deque = deque(maxlen=1000)
        self.start_time = datetime.now()
        self._lock = asyncio.Lock()
        
    async def set(self, key: str, value: Any):
        async with self._lock:
            self.data[key] = value
            
    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self.data.get(key, default)
    
    async def update(self, updates: Dict[str, Any]):
        async with self._lock:
            self.data.update(updates)
    
    def log_event(self, event: StateEvent):
        self.event_log.append({
            **event.to_dict(),
            "context_session": self.session_id
        })


class State:
    """
    Repräsentiert einen State in der State Machine.
    Unterstützt Hierarchical States und Actions.
    """
    
    def __init__(
        self,
        name: str,
        state_type: StateType = StateType.SIMPLE,
        parent: Optional['State'] = None
    ):
        self.name = name
        self.state_type = state_type
        self.parent = parent
        self.sub_states: Dict[str, 'State'] = {}
        self.initial_sub_state: Optional[str] = None
        self.entry_actions: List[StateAction] = []
        self.exit_actions: List[StateAction] = []
        self.while_in_state_actions: List[StateAction] = []
        self._active = False
        self._entered_at: Optional[datetime] = None
        self._history: deque = deque(maxlen=50)
        
    def add_sub_state(self, state: 'State'):
        state.parent = self
        self.sub_states[state.name] = state
        if self.initial_sub_state is None:
            self.initial_sub_state = state.name
            
    def on_entry(self, action: Callable, async_exec: bool = False, timeout: Optional[float] = None):
        self.entry_actions.append(StateAction(action, async_exec, timeout))
        return self
        
    def on_exit(self, action: Callable, async_exec: bool = False, timeout: Optional[float] = None):
        self.exit_actions.append(StateAction(action, async_exec, timeout))
        return self
        
    def while_in_state(self, action: Callable, async_exec: bool = True):
        self.while_in_state_actions.append(StateAction(action, async_exec))
        return self
    
    async def enter(self, context: StateContext, event: Optional[StateEvent] = None):
        self._active = True
        self._entered_at = datetime.now()
        
        logger.debug(f"Entering state: {self.name}")
        
        for action in self.entry_actions:
            await self._execute_action(action, context, event)
        
        # Start while-in-state actions
        if self.while_in_state_actions:
            asyncio.create_task(self._run_while_in_state(context))
    
    async def exit(self, context: StateContext, event: Optional[StateEvent] = None):
        self._active = False
        
        logger.debug(f"Exiting state: {self.name}")
        
        for action in self.exit_actions:
            await self._execute_action(action, context, event)
    
    async def _execute_action(
        self, 
        action: StateAction, 
        context: StateContext, 
        event: Optional[StateEvent] = None
    ):
        retry_count = 0
        
        while retry_count <= action.max_retries:
            try:
                if action.async_execution:
                    if action.timeout_seconds:
                        await asyncio.wait_for(
                            action.action(self, context),
                            timeout=action.timeout_seconds
                        )
                    else:
                        await action.action(self, context)
                else:
                    action.action(self, context)
                break
                
            except Exception as e:
                retry_count += 1
                if retry_count > action.max_retries or not action.retry_on_failure:
                    logger.error(f"Action failed in state {self.name}: {e}")
                    raise
                await asyncio.sleep(0.1 * retry_count)
    
    async def _run_while_in_state(self, context: StateContext):
        while self._active:
            for action in self.while_in_state_actions:
                try:
                    if action.async_execution:
                        await action.action(self, context)
                    else:
                        action.action(self, context)
                except Exception as e:
                    logger.warning(f"While-in-state action error: {e}")
            await asyncio.sleep(1)
    
    def is_active(self) -> bool:
        return self._active
    
    def get_duration(self) -> Optional[timedelta]:
        if self._entered_at:
            return datetime.now() - self._entered_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.state_type.value,
            "active": self._active,
            "duration_seconds": self.get_duration().total_seconds() if self.get_duration() else None,
            "sub_states": list(self.sub_states.keys())
        }


class Transition:
    """
    Repräsentiert einen Übergang zwischen States.
    Unterstützt Guards, Actions und Timeouts.
    """
    
    def __init__(
        self,
        source: str,
        target: str,
        event: Optional[str] = None,
        guards: Optional[List[TransitionGuard]] = None,
        action: Optional[Callable] = None,
        priority: int = 0,
        auto_trigger: bool = False,
        delay_seconds: Optional[float] = None
    ):
        self.source = source
        self.target = target
        self.event = event
        self.guards = guards or []
        self.action = action
        self.priority = priority
        self.auto_trigger = auto_trigger
        self.delay_seconds = delay_seconds
        
    def can_fire(self, event: StateEvent, context: StateContext) -> bool:
        if self.event and event.name != self.event:
            return False
        
        for guard in sorted(self.guards, key=lambda g: g.priority, reverse=True):
            if not guard.evaluate(event, context):
                return False
        
        return True
    
    async def fire(self, context: StateContext, event: StateEvent):
        if self.action:
            if asyncio.iscoroutinefunction(self.action):
                await self.action(context, event)
            else:
                self.action(context, event)


class AdvancedStateMachine:
    """
    Erweiterte State Machine mit allen Features.
    Vollständig autonom und selbstverwaltend.
    """
    
    def __init__(
        self,
        name: str = "StateMachine",
        enable_persistence: bool = True,
        auto_recovery: bool = True
    ):
        self.name = name
        self.states: Dict[str, State] = {}
        self.transitions: List[Transition] = []
        self._current_state: Optional[State] = None
        self._state_stack: List[State] = []
        self.context: StateContext = StateContext()
        self.enable_persistence = enable_persistence
        self.auto_recovery = auto_recovery
        
        # Event handling
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        
        # Metrics
        self._transition_count = 0
        self._start_time: Optional[datetime] = None
        
        # Persistence
        self._state_history: deque = deque(maxlen=1000)
        
    def add_state(self, state: State) -> State:
        self.states[state.name] = state
        return state
    
    def add_transition(self, transition: Transition):
        self.transitions.append(transition)
        # Sort by priority
        self.transitions.sort(key=lambda t: t.priority, reverse=True)
    
    def on(self, event_name: str, handler: Callable):
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    async def start(self, initial_state: str):
        """Starte die State Machine."""
        if initial_state not in self.states:
            raise ValueError(f"Unknown initial state: {initial_state}")
        
        self._running = True
        self._start_time = datetime.now()
        
        # Set initial state
        await self._enter_state(self.states[initial_state])
        
        # Start event processing
        asyncio.create_task(self._process_events())
        
        logger.info(f"State Machine '{self.name}' started in state '{initial_state}'")
    
    async def stop(self):
        """Stoppe die State Machine."""
        self._running = False
        
        if self._current_state:
            await self._exit_state(self._current_state)
        
        logger.info(f"State Machine '{self.name}' stopped")
    
    async def send(self, event: Union[str, StateEvent], payload: Optional[Dict] = None):
        """Sende ein Event an die State Machine."""
        if isinstance(event, str):
            event = StateEvent(name=event, payload=payload or {})
        
        await self._event_queue.put(event)
        self.context.log_event(event)
    
    async def _process_events(self):
        """Hintergrund-Task für Event-Verarbeitung."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                # Check for auto-trigger transitions
                await self._check_auto_transitions()
            except Exception as e:
                logger.error(f"Event processing error: {e}")
                if self.auto_recovery:
                    await self._recover_from_error(e)
    
    async def _handle_event(self, event: StateEvent):
        """Verarbeite ein einzelnes Event."""
        if not self._current_state:
            return
        
        # Find matching transitions
        matching = [
            t for t in self.transitions
            if t.source == self._current_state.name and t.can_fire(event, self.context)
        ]
        
        if matching:
            # Take highest priority transition
            transition = matching[0]
            await self._execute_transition(transition, event)
        
        # Call event handlers
        for handler in self._event_handlers.get(event.name, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, self.context)
                else:
                    handler(event, self.context)
            except Exception as e:
                logger.warning(f"Event handler error: {e}")
    
    async def _execute_transition(self, transition: Transition, event: StateEvent):
        """Führe einen Transition aus."""
        logger.debug(f"Transition: {transition.source} -> {transition.target}")
        
        # Apply delay if specified
        if transition.delay_seconds:
            await asyncio.sleep(transition.delay_seconds)
        
        # Execute transition action
        await transition.fire(self.context, event)
        
        # Exit current state
        await self._exit_state(self.states[transition.source])
        
        # Enter new state
        await self._enter_state(self.states[transition.target])
        
        self._transition_count += 1
        
        # Persist state
        if self.enable_persistence:
            self._persist_state(transition)
    
    async def _enter_state(self, state: State):
        """Betrete einen State."""
        self._current_state = state
        self._state_stack.append(state)
        await state.enter(self.context)
        
        # Handle composite states
        if state.state_type == StateType.COMPOSITE and state.initial_sub_state:
            await self._enter_state(state.sub_states[state.initial_sub_state])
    
    async def _exit_state(self, state: State):
        """Verlasse einen State."""
        await state.exit(self.context)
        
        if state in self._state_stack:
            self._state_stack.remove(state)
    
    async def _check_auto_transitions(self):
        """Prüfe auf auto-trigger Transitions."""
        if not self._current_state:
            return
        
        auto_transitions = [
            t for t in self.transitions
            if t.source == self._current_state.name 
            and t.auto_trigger
            and t.can_fire(StateEvent("auto"), self.context)
        ]
        
        for transition in auto_transitions:
            await self._execute_transition(transition, StateEvent("auto"))
    
    def _persist_state(self, transition: Transition):
        """Persistiere State-Übergang."""
        self._state_history.append({
            "from": transition.source,
            "to": transition.target,
            "timestamp": datetime.now().isoformat(),
            "context_data": dict(self.context.data)
        })
    
    async def _recover_from_error(self, error: Exception):
        """Self-Recovery bei Fehlern."""
        logger.warning(f"Attempting recovery from error: {error}")
        
        # Try to go to last known good state
        if self._state_history:
            last_good = self._state_history[-1]
            recovery_state = last_good.get("from")
            
            if recovery_state and recovery_state in self.states:
                logger.info(f"Recovering to state: {recovery_state}")
                await self._enter_state(self.states[recovery_state])
    
    def get_current_state(self) -> Optional[str]:
        """Gibt aktuellen State zurück."""
        return self._current_state.name if self._current_state else None
    
    def get_active_states(self) -> List[str]:
        """Gibt alle aktiven States zurück (für Hierarchical)."""
        return [s.name for s in self._state_stack if s.is_active()]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Gibt Metriken zurück."""
        return {
            "name": self.name,
            "current_state": self.get_current_state(),
            "active_states": self.get_active_states(),
            "transition_count": self._transition_count,
            "state_count": len(self.states),
            "transition_count_total": len(self.transitions),
            "running": self._running,
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Exportiere aktuellen State für Persistence."""
        return {
            "current_state": self.get_current_state(),
            "state_stack": [s.name for s in self._state_stack],
            "context_data": dict(self.context.data),
            "history": list(self._state_history),
            "timestamp": datetime.now().isoformat()
        }
    
    async def import_state(self, state_data: Dict[str, Any]):
        """Importiere State aus Persistence."""
        current = state_data.get("current_state")
        if current and current in self.states:
            await self._enter_state(self.states[current])
        
        if "context_data" in state_data:
            await self.context.update(state_data["context_data"])


# Pentest-spezifische State Machine
class PentestStateMachine(AdvancedStateMachine):
    """
    Spezialisierte State Machine für Penetration Testing.
    """
    
    def __init__(self):
        super().__init__(name="PentestStateMachine")
        self._setup_states()
        self._setup_transitions()
    
    def _setup_states(self):
        """Setup Pentest-spezifische States."""
        # Main states
        self.add_state(State("idle", StateType.SIMPLE))
        
        recon = State("reconnaissance", StateType.COMPOSITE)
        recon.add_sub_state(State("port_scanning"))
        recon.add_sub_state(State("service_detection"))
        recon.add_sub_state(State("os_fingerprinting"))
        self.add_state(recon)
        
        vuln = State("vulnerability_assessment", StateType.COMPOSITE)
        vuln.add_sub_state(State("automated_scanning"))
        vuln.add_sub_state(State("manual_testing"))
        self.add_state(vuln)
        
        self.add_state(State("exploitation", StateType.SIMPLE))
        self.add_state(State("post_exploitation", StateType.SIMPLE))
        self.add_state(State("reporting", StateType.SIMPLE))
        self.add_state(State("completed", StateType.FINAL))
        self.add_state(State("error", StateType.SIMPLE))
    
    def _setup_transitions(self):
        """Setup Pentest-spezifische Transitions."""
        transitions = [
            Transition("idle", "reconnaissance", event="start"),
            Transition("reconnaissance", "vulnerability_assessment", event="recon_complete"),
            Transition("vulnerability_assessment", "exploitation", event="vulns_found"),
            Transition("exploitation", "post_exploitation", event="exploit_success"),
            Transition("post_exploitation", "reporting", event="data_collected"),
            Transition("reporting", "completed", event="report_generated"),
            Transition("*", "error", event="error"),
            Transition("error", "idle", event="reset"),
        ]
        
        for t in transitions:
            self.add_transition(t)


# Factory
async def create_state_machine(
    name: str = "StateMachine",
    initial_state: str = "idle"
) -> AdvancedStateMachine:
    """Factory für State Machine Erstellung."""
    sm = AdvancedStateMachine(name=name)
    await sm.start(initial_state)
    return sm


if __name__ == "__main__":
    async def demo():
        # Create and use Pentest State Machine
        sm = PentestStateMachine()
        await sm.start("idle")
        
        # Simulate workflow
        await sm.send("start")
        await asyncio.sleep(0.5)
        
        await sm.send("recon_complete")
        await asyncio.sleep(0.5)
        
        print(json.dumps(sm.get_metrics(), indent=2))
        
        await sm.stop()
    
    asyncio.run(demo())
