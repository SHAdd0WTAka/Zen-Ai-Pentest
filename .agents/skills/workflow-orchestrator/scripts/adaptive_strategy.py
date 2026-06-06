#!/usr/bin/env python3
"""
Adaptive Strategy Management

Implements fallback and adaptation logic for workflow modules
when initial results are empty or unsuccessful.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("adaptive_strategy")


class AdaptationTrigger(Enum):
    """Conditions that trigger adaptations."""

    EMPTY_RESULT = auto()
    ERROR = auto()
    TIMEOUT = auto()
    BLOCKED = auto()
    PARTIAL_RESULT = auto()
    HIGH_FALSE_POSITIVE = auto()


class AdaptationAction(Enum):
    """Possible adaptation actions."""

    FALLBACK_MODULE = auto()
    RETRY_WITH_CONFIG = auto()
    INCREASE_INTENSITY = auto()
    DECREASE_INTENSITY = auto()
    SWITCH_TECHNIQUE = auto()
    PARALLEL_ALTERNATIVES = auto()
    SKIP_REMAINING = auto()
    ABORT_WORKFLOW = auto()


@dataclass
class AdaptationRule:
    """A rule for adapting workflow behavior."""

    trigger: AdaptationTrigger
    condition: Optional[Callable[[Any], bool]]
    action: AdaptationAction
    config: Dict[str, Any]
    priority: int = 0


@dataclass
class AdaptationDecision:
    """Result of an adaptation decision."""

    original_module: str
    trigger: AdaptationTrigger
    action: AdaptationAction
    new_module: Optional[str]
    config_changes: Dict[str, Any]
    reason: str


class AdaptiveStrategy:
    """
    Manages adaptive behavior for workflow execution.

    Features:
    - Configurable fallback modules
    - Dynamic intensity adjustment
    - Technique switching
    - Retry with modified parameters
    """

    def __init__(self):
        self._rules: Dict[str, List[AdaptationRule]] = {}
        self._fallbacks: Dict[str, Any] = {}
        self._adaptation_history: List[AdaptationDecision] = []

    def add_fallback(
        self, module_name: str, fallback_module: Any, trigger: AdaptationTrigger = AdaptationTrigger.EMPTY_RESULT
    ):
        """
        Register a fallback module.

        Args:
            module_name: Original module name
            fallback_module: Module to use as fallback
            trigger: Condition to trigger fallback
        """
        if module_name not in self._fallbacks:
            self._fallbacks[module_name] = {}

        self._fallbacks[module_name][trigger] = fallback_module
        logger.debug(f"Registered fallback for {module_name} on {trigger.name}")

    def add_rule(
        self,
        module_name: str,
        trigger: AdaptationTrigger,
        action: AdaptationAction,
        config: Optional[Dict] = None,
        condition: Optional[Callable[[Any], bool]] = None,
        priority: int = 0,
    ):
        """
        Add an adaptation rule.

        Args:
            module_name: Module to apply rule to
            trigger: Condition that triggers adaptation
            action: Action to take
            config: Configuration for the action
            condition: Additional condition function
            priority: Rule priority (higher = first)
        """
        rule = AdaptationRule(trigger=trigger, condition=condition, action=action, config=config or {}, priority=priority)

        if module_name not in self._rules:
            self._rules[module_name] = []

        self._rules[module_name].append(rule)

        # Sort by priority
        self._rules[module_name].sort(key=lambda r: r.priority, reverse=True)

        logger.debug(f"Added rule for {module_name}: {trigger.name} -> {action.name}")

    async def decide(
        self, module_name: str, result: Any, context: Optional[Any] = None, error: Optional[Exception] = None
    ) -> Optional[AdaptationDecision]:
        """
        Decide on adaptation based on result.

        Args:
            module_name: Module that produced result
            result: Module execution result
            context: Workflow context
            error: Exception if execution failed

        Returns:
            Adaptation decision or None if no adaptation needed
        """
        # Determine trigger
        trigger = self._determine_trigger(result, error)

        if not trigger:
            return None

        logger.info(f"Adaptation triggered for {module_name}: {trigger.name}")

        # Check for specific rules
        if module_name in self._rules:
            for rule in self._rules[module_name]:
                if rule.trigger == trigger:
                    # Check additional condition
                    if rule.condition and not rule.condition(result):
                        continue

                    # Build decision
                    decision = self._build_decision(module_name, trigger, rule, result, context)
                    self._adaptation_history.append(decision)
                    return decision

        # Check for fallback module
        if module_name in self._fallbacks:
            fallbacks = self._fallbacks[module_name]
            if trigger in fallbacks:
                decision = AdaptationDecision(
                    original_module=module_name,
                    trigger=trigger,
                    action=AdaptationAction.FALLBACK_MODULE,
                    new_module=fallbacks[trigger],
                    config_changes={},
                    reason=f"Fallback triggered by {trigger.name}",
                )
                self._adaptation_history.append(decision)
                return decision

        return None

    def _determine_trigger(self, result: Any, error: Optional[Exception]) -> Optional[AdaptationTrigger]:
        """Determine which trigger applies."""
        if error:
            if isinstance(error, asyncio.TimeoutError):
                return AdaptationTrigger.TIMEOUT
            return AdaptationTrigger.ERROR

        # Check result content
        if result is None:
            return AdaptationTrigger.EMPTY_RESULT

        if hasattr(result, "is_empty"):
            if result.is_empty:
                return AdaptationTrigger.EMPTY_RESULT
        elif hasattr(result, "findings"):
            if not result.findings:
                return AdaptationTrigger.EMPTY_RESULT
        elif isinstance(result, (list, dict)):
            if not result:
                return AdaptationTrigger.EMPTY_RESULT

        if hasattr(result, "status"):
            if result.status.name == "FAILED":
                return AdaptationTrigger.ERROR

        if hasattr(result, "was_blocked"):
            if result.was_blocked:
                return AdaptationTrigger.BLOCKED

        return None

    def _build_decision(
        self, module_name: str, trigger: AdaptationTrigger, rule: AdaptationRule, result: Any, context: Optional[Any]
    ) -> AdaptationDecision:
        """Build an adaptation decision from a rule."""
        new_module = None
        config_changes = rule.config.copy()

        if rule.action == AdaptationAction.FALLBACK_MODULE:
            if module_name in self._fallbacks:
                new_module = self._fallbacks[module_name].get(trigger)

        elif rule.action == AdaptationAction.RETRY_WITH_CONFIG:
            config_changes["retry"] = True
            config_changes["previous_error"] = str(result.errors) if hasattr(result, "errors") else None

        elif rule.action == AdaptationAction.INCREASE_INTENSITY:
            config_changes["intensity"] = "high"
            config_changes["threads"] = config_changes.get("threads", 10) * 2

        elif rule.action == AdaptationAction.DECREASE_INTENSITY:
            config_changes["intensity"] = "low"
            config_changes["threads"] = max(1, config_changes.get("threads", 10) // 2)

        elif rule.action == AdaptationAction.SWITCH_TECHNIQUE:
            techniques = config_changes.get("techniques", ["default"])
            current = config_changes.get("current_technique", techniques[0])
            if current in techniques:
                idx = techniques.index(current)
                if idx + 1 < len(techniques):
                    config_changes["current_technique"] = techniques[idx + 1]

        return AdaptationDecision(
            original_module=module_name,
            trigger=trigger,
            action=rule.action,
            new_module=new_module,
            config_changes=config_changes,
            reason=f"Rule matched: {trigger.name} -> {rule.action.name}",
        )

    def get_adaptation_history(self, module_name: Optional[str] = None) -> List[AdaptationDecision]:
        """Get history of adaptations."""
        if module_name:
            return [d for d in self._adaptation_history if d.original_module == module_name]
        return self._adaptation_history.copy()

    def clear_history(self):
        """Clear adaptation history."""
        self._adaptation_history.clear()


class StrategyTemplates:
    """Pre-configured adaptive strategies."""

    @staticmethod
    def web_scanning_strategy() -> AdaptiveStrategy:
        """Strategy for web scanning workflows."""
        strategy = AdaptiveStrategy()

        # Empty results fallback
        strategy.add_rule(
            "nuclei", AdaptationTrigger.EMPTY_RESULT, AdaptationAction.FALLBACK_MODULE, config={"fallback": "dirbuster"}
        )

        # Blocked by WAF
        strategy.add_rule(
            "nuclei",
            AdaptationTrigger.BLOCKED,
            AdaptationAction.SWITCH_TECHNIQUE,
            config={"techniques": ["aggressive", "stealth", "manual"]},
            priority=10,
        )

        # SQLMap timeout
        strategy.add_rule(
            "sqlmap", AdaptationTrigger.TIMEOUT, AdaptationAction.DECREASE_INTENSITY, config={"threads": 5, "risk": 1}
        )

        return strategy

    @staticmethod
    def network_scanning_strategy() -> AdaptiveStrategy:
        """Strategy for network scanning workflows."""
        strategy = AdaptiveStrategy()

        # No ports found - try full scan
        strategy.add_rule(
            "nmap_quick", AdaptationTrigger.EMPTY_RESULT, AdaptationAction.FALLBACK_MODULE, config={"fallback": "nmap_full"}
        )

        # Service enumeration error
        strategy.add_rule(
            "service_enum", AdaptationTrigger.ERROR, AdaptationAction.RETRY_WITH_CONFIG, config={"timeout": 60, "retries": 2}
        )

        return strategy

    @staticmethod
    def api_testing_strategy() -> AdaptiveStrategy:
        """Strategy for API testing workflows."""
        strategy = AdaptiveStrategy()

        # No spec found - try discovery
        strategy.add_rule(
            "openapi_scan",
            AdaptationTrigger.EMPTY_RESULT,
            AdaptationAction.FALLBACK_MODULE,
            config={"fallback": "api_discovery"},
        )

        # Auth bypass failed - try alternative methods
        strategy.add_rule(
            "auth_bypass",
            AdaptationTrigger.ERROR,
            AdaptationAction.SWITCH_TECHNIQUE,
            config={"techniques": ["jwt", "session", "header", "parameter"]},
        )

        return strategy

    @staticmethod
    def aggressive_strategy() -> AdaptiveStrategy:
        """Aggressive strategy that retries and escalates."""
        strategy = AdaptiveStrategy()

        # Always retry on empty
        strategy.add_rule(
            "*",  # All modules
            AdaptationTrigger.EMPTY_RESULT,
            AdaptationAction.INCREASE_INTENSITY,
            config={"retries": 2},
            priority=1,
        )

        # Retry errors with fallback
        strategy.add_rule(
            "*", AdaptationTrigger.ERROR, AdaptationAction.RETRY_WITH_CONFIG, config={"retries": 1, "fallback_on_fail": True}
        )

        return strategy


class FallbackRouter:
    """Routes execution to fallback modules."""

    def __init__(self):
        self._fallback_modules: Dict[str, Dict[AdaptationTrigger, Any]] = {}

    def register(self, original: str, trigger: AdaptationTrigger, fallback: Any):
        """Register a fallback module."""
        if original not in self._fallback_modules:
            self._fallback_modules[original] = {}
        self._fallback_modules[original][trigger] = fallback

    def get_fallback(self, original: str, trigger: AdaptationTrigger) -> Optional[Any]:
        """Get fallback module for original."""
        fallbacks = self._fallback_modules.get(original, {})
        return fallbacks.get(trigger)

    def has_fallback(self, original: str, trigger: AdaptationTrigger) -> bool:
        """Check if fallback exists."""
        return trigger in self._fallback_modules.get(original, {})


if __name__ == "__main__":
    # Test adaptive strategy
    async def test():
        # Create mock result
        class MockResult:
            def __init__(self, empty=False, errors=None):
                self.is_empty = empty
                self.errors = errors or []
                self.findings = []

        strategy = StrategyTemplates.web_scanning_strategy()

        # Test with empty result
        result = MockResult(empty=True)
        decision = await strategy.decide("nuclei", result)

        if decision:
            print(f"Decision: {decision.action.name}")
            print(f"Reason: {decision.reason}")

        # Test with error
        result = MockResult(errors=["Connection timeout"])
        decision = await strategy.decide("sqlmap", result, error=Exception("timeout"))

        if decision:
            print(f"\nDecision: {decision.action.name}")
            print(f"Config changes: {decision.config_changes}")

        # Print history
        print(f"\nTotal adaptations: {len(strategy.get_adaptation_history())}")

    asyncio.run(test())
