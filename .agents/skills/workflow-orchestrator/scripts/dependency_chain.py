#!/usr/bin/env python3
"""
Dependency Chain Management

Manages execution order and data flow between workflow modules,
ensuring dependencies are resolved before execution.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("dependency_chain")


@dataclass
class DependencyNode:
    """A node in the dependency graph."""

    name: str
    module: Any
    depends_on: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    required: bool = False
    condition: Optional[Callable] = None
    input_mapper: Optional[Callable] = None
    output_mapper: Optional[Callable] = None
    fallback: Optional[Any] = None


class DependencyChain:
    """
    Manages module dependencies and execution order.

    Features:
    - Automatic dependency resolution
    - Circular dependency detection
    - Parallel execution groups
    - Data transformation between modules
    """

    def __init__(self):
        self._nodes: Dict[str, DependencyNode] = {}
        self._execution_order: Optional[List[str]] = None

    def add_step(
        self,
        name: str,
        module: Any,
        depends_on: Optional[List[str]] = None,
        required: bool = False,
        condition: Optional[Callable[[Any], bool]] = None,
        input_mapper: Optional[Callable[[Any], Dict]] = None,
        output_mapper: Optional[Callable[[Any], Dict]] = None,
        fallback: Optional[Any] = None,
    ) -> "DependencyChain":
        """
        Add a step to the dependency chain.

        Args:
            name: Unique step identifier
            module: Module instance to execute
            depends_on: List of step names this step depends on
            required: Whether this step is required for workflow success
            condition: Function to check if step should execute
            input_mapper: Function to map context to module inputs
            output_mapper: Function to map module outputs to context
            fallback: Fallback module if this step fails/returns empty

        Returns:
            Self for chaining
        """
        if name in self._nodes:
            raise ValueError(f"Step '{name}' already exists")

        # Validate dependencies exist
        for dep in depends_on or []:
            if dep not in self._nodes:
                raise ValueError(f"Dependency '{dep}' not found for step '{name}'")

        node = DependencyNode(
            name=name,
            module=module,
            depends_on=depends_on or [],
            required=required,
            condition=condition,
            input_mapper=input_mapper,
            output_mapper=output_mapper,
            fallback=fallback,
        )

        self._nodes[name] = node

        # Update dependents
        for dep in node.depends_on:
            self._nodes[dep].dependents.append(name)

        # Invalidate cached execution order
        self._execution_order = None

        logger.debug(f"Added step: {name} (depends on: {depends_on})")
        return self

    def remove_step(self, name: str) -> "DependencyChain":
        """Remove a step and its dependencies."""
        if name not in self._nodes:
            return self

        node = self._nodes[name]

        # Remove from dependents of dependencies
        for dep in node.depends_on:
            if dep in self._nodes:
                self._nodes[dep].dependents.remove(name)

        # Remove dependencies that depend on this node
        for dependent in node.dependents:
            dep_node = self._nodes[dependent]
            dep_node.depends_on.remove(name)

        del self._nodes[name]
        self._execution_order = None

        return self

    def get_execution_order(self) -> List[str]:
        """
        Get topological sorted execution order.

        Returns:
            List of step names in execution order

        Raises:
            ValueError: If circular dependency detected
        """
        if self._execution_order:
            return self._execution_order

        # Topological sort using Kahn's algorithm
        in_degree = defaultdict(int)
        graph = defaultdict(list)

        # Build graph
        for name, node in self._nodes.items():
            in_degree[name] = len(node.depends_on)
            for dep in node.depends_on:
                graph[dep].append(name)

        # Find nodes with no dependencies
        queue = deque([n for n in self._nodes if in_degree[n] == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for dependent in graph[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(result) != len(self._nodes):
            remaining = set(self._nodes.keys()) - set(result)
            raise ValueError(f"Circular dependency detected involving: {remaining}")

        self._execution_order = result
        return result

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Group steps that can be executed in parallel.

        Returns:
            List of groups, where each group contains steps
            that can run simultaneously (no inter-dependencies)
        """
        order = self.get_execution_order()

        # Track which steps have been assigned to groups
        assigned = set()
        groups = []

        while len(assigned) < len(order):
            # Find steps whose dependencies are all assigned
            group = []
            for name in order:
                if name in assigned:
                    continue
                node = self._nodes[name]
                deps_satisfied = all(d in assigned for d in node.depends_on)
                if deps_satisfied:
                    group.append(name)

            if not group:
                # Should not happen if no cycles
                raise ValueError("Unable to form parallel groups")

            groups.append(group)
            assigned.update(group)

        return groups

    def get_ready_steps(self, completed: Set[str], context: Optional[Any] = None) -> List[str]:
        """
        Get steps ready to execute based on completed steps.

        Args:
            completed: Set of completed step names
            context: Optional context for condition checking

        Returns:
            List of step names ready to execute
        """
        ready = []

        for name, node in self._nodes.items():
            if name in completed:
                continue

            # Check dependencies
            deps_met = all(dep in completed for dep in node.depends_on)
            if not deps_met:
                continue

            # Check condition
            if node.condition and context is not None:
                if not node.condition(context):
                    continue

            ready.append(name)

        return ready

    def map_inputs(self, step_name: str, context: Any) -> Dict[str, Any]:
        """
        Map context to module inputs for a step.

        Args:
            step_name: Name of the step
            context: Current workflow context

        Returns:
            Dictionary of inputs for the module
        """
        node = self._nodes.get(step_name)
        if not node:
            raise ValueError(f"Step '{step_name}' not found")

        if node.input_mapper:
            return node.input_mapper(context)

        # Default: pass through dependency outputs
        inputs = {}
        for dep in node.depends_on:
            if hasattr(context, "get_latest_result"):
                result = context.get_latest_result(dep)
                if result:
                    inputs[dep] = result.outputs

        return inputs

    def map_outputs(self, step_name: str, module_output: Dict, context: Any) -> Any:
        """
        Map module outputs to context updates.

        Args:
            step_name: Name of the step
            module_output: Raw module output
            context: Current workflow context

        Returns:
            Transformed output
        """
        node = self._nodes.get(step_name)
        if not node:
            return module_output

        if node.output_mapper:
            return node.output_mapper(module_output, context)

        return module_output

    def get_dependents(self, step_name: str) -> List[str]:
        """Get all steps that depend on a given step."""
        node = self._nodes.get(step_name)
        return node.dependents if node else []

    def get_dependencies(self, step_name: str) -> List[str]:
        """Get all dependencies for a given step."""
        node = self._nodes.get(step_name)
        return node.depends_on if node else []

    def get_required_steps(self) -> List[str]:
        """Get all required steps."""
        return [n for n, node in self._nodes.items() if node.required]

    def validate(self) -> List[str]:
        """
        Validate the dependency chain.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for missing dependencies
        for name, node in self._nodes.items():
            for dep in node.depends_on:
                if dep not in self._nodes:
                    errors.append(f"Step '{name}' depends on missing step '{dep}'")

        # Check for circular dependencies
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))

        # Check for orphaned steps
        if self._nodes:
            try:
                order = self.get_execution_order()
                orphans = set(self._nodes.keys()) - set(order)
                if orphans:
                    errors.append(f"Orphaned steps: {orphans}")
            except ValueError:
                pass  # Already caught above

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert chain to dictionary representation."""
        return {
            name: {
                "depends_on": node.depends_on,
                "dependents": node.dependents,
                "required": node.required,
                "has_condition": node.condition is not None,
                "has_input_mapper": node.input_mapper is not None,
                "has_output_mapper": node.output_mapper is not None,
                "has_fallback": node.fallback is not None,
            }
            for name, node in self._nodes.items()
        }

    def visualize(self) -> str:
        """Generate text visualization of dependency graph."""
        lines = ["Dependency Chain:", "=" * 40]

        try:
            order = self.get_execution_order()
            for i, name in enumerate(order, 1):
                node = self._nodes[name]
                deps = f" ← {', '.join(node.depends_on)}" if node.depends_on else ""
                required = " [REQUIRED]" if node.required else ""
                lines.append(f"{i}. {name}{deps}{required}")
        except ValueError as e:
            lines.append(f"ERROR: {e}")

        return "\n".join(lines)


class ChainBuilder:
    """Fluent builder for dependency chains."""

    def __init__(self):
        self.chain = DependencyChain()

    def add(self, name: str, module: Any, **kwargs) -> "ChainBuilder":
        """Add a step."""
        self.chain.add_step(name, module, **kwargs)
        return self

    def then(self, name: str, module: Any, **kwargs) -> "ChainBuilder":
        """Add a step that depends on the previous step."""
        # Get last added step
        last_step = list(self.chain._nodes.keys())[-1] if self.chain._nodes else None
        if last_step:
            kwargs.setdefault("depends_on", []).append(last_step)
        self.chain.add_step(name, module, **kwargs)
        return self

    def parallel(self, *steps: tuple) -> "ChainBuilder":
        """Add multiple steps that can run in parallel."""
        # Get last added step as common dependency
        last_step = list(self.chain._nodes.keys())[-1] if self.chain._nodes else None

        for name, module, *rest in steps:
            kwargs = rest[0] if rest else {}
            if last_step:
                kwargs.setdefault("depends_on", []).append(last_step)
            self.chain.add_step(name, module, **kwargs)

        return self

    def build(self) -> DependencyChain:
        """Build and return the chain."""
        errors = self.chain.validate()
        if errors:
            raise ValueError(f"Validation errors: {errors}")
        return self.chain


# Predefined chain templates


class PentestChainTemplates:
    """Templates for common penetration testing workflows."""

    @staticmethod
    def standard_web() -> DependencyChain:
        """Standard web application pentest chain."""
        builder = ChainBuilder()

        # Phase 1: Reconnaissance
        builder.add("dns_enum", "DNSEnumerator", required=True)
        builder.then("port_scan", "NmapScanner", required=True)
        builder.then("service_enum", "ServiceEnumerator", depends_on=["port_scan"])

        # Phase 2: Web Scanning
        builder.then("web_discovery", "WebDiscovery", condition=lambda ctx: ctx.has_open_port([80, 443]))
        builder.then("tech_fingerprint", "WhatWeb", depends_on=["web_discovery"])

        # Phase 3: Vulnerability Scanning
        builder.parallel(
            ("vuln_scan", "NucleiScanner"),
            ("dir_busting", "FfufScanner"),
        )

        # Phase 4: Targeted Testing
        builder.then("sql_testing", "SQLMapTester", condition=lambda ctx: ctx.has_finding("sql_injection"))
        builder.then("xss_testing", "XSSTester", condition=lambda ctx: ctx.has_finding("xss"))

        return builder.build()

    @staticmethod
    def network_only() -> DependencyChain:
        """Network-focused pentest chain."""
        builder = ChainBuilder()

        builder.add("port_scan", "NmapScanner", required=True)
        builder.then("service_deep", "ServiceDeepScan")
        builder.then("vuln_scan", "NucleiNetworkScanner")

        return builder.build()

    @staticmethod
    def api_focused() -> DependencyChain:
        """API-focused pentest chain."""
        builder = ChainBuilder()

        builder.add("discovery", "APIDiscovery", required=True)
        builder.then("spec_analysis", "OpenAPIScanner", fallback="ManualAPITesting")
        builder.then("auth_testing", "APIAuthTester")
        builder.then("fuzzing", "APIFuzzer")

        return builder.build()


if __name__ == "__main__":
    # Test dependency chain
    chain = DependencyChain()

    # Build a simple chain
    chain.add_step("a", "ModuleA")
    chain.add_step("b", "ModuleB", depends_on=["a"])
    chain.add_step("c", "ModuleC", depends_on=["a"])
    chain.add_step("d", "ModuleD", depends_on=["b", "c"], required=True)

    print(chain.visualize())
    print("\nParallel groups:")
    for i, group in enumerate(chain.get_parallel_groups(), 1):
        print(f"  Group {i}: {group}")

    # Test builder
    print("\n\nUsing ChainBuilder:")
    builder = ChainBuilder()
    chain2 = (
        builder.add("recon", "ReconModule")
        .then("scan", "ScanModule")
        .parallel(("web", "WebModule"), ("service", "ServiceModule"))
        .build()
    )
    print(chain2.visualize())
