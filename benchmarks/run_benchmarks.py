"""
Zen-AI-Pentest Benchmark CLI Runner

Command-line interface for running benchmarks, viewing results,
and generating comparison reports.
"""

import asyncio
from datetime import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List

# Rich for beautiful CLI output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Matplotlib for charts
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from .benchmark_engine import (
    BenchmarkEngine, BenchmarkConfig, BenchmarkReport,
    BenchmarkStatus
)
from .scenarios import (
    list_all_scenarios, ScenarioType, DifficultyLevel, ALL_SCENARIOS
)
from .ci_benchmark import CIBenchmarkRunner, CIConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Console for output
console = Console() if RICH_AVAILABLE else None


class BenchmarkCLI:
    """Command-line interface for benchmark operations."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        self.engine = BenchmarkEngine(output_dir=output_dir)
        self.output_dir = Path(output_dir)
        
        if RICH_AVAILABLE:
            console.print(
                Panel.fit(
                    "[bold blue]Zen-AI-Pentest Benchmark Framework[/bold blue]\n"
                    "[dim]Security Testing Performance Evaluation[/dim]",
                    border_style="blue"
                )
            )
    
    def list_scenarios(
        self,
        scenario_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        tag: Optional[str] = None
    ) -> None:
        """List available benchmark scenarios."""
        
        scenarios = list_all_scenarios()
        
        # Apply filters
        if scenario_type:
            scenarios = [s for s in scenarios if s.get("type") == scenario_type]
        if difficulty:
            scenarios = [s for s in scenarios if s.get("difficulty") == difficulty]
        if tag:
            scenarios = [s for s in scenarios if tag in s.get("tags", [])]
        
        if RICH_AVAILABLE:
            table = Table(
                title="Available Benchmark Scenarios",
                box=box.ROUNDED
            )
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("Type", style="blue")
            table.add_column("Difficulty", style="yellow")
            table.add_column("Duration", justify="right")
            table.add_column("Vulns", justify="right")
            
            for s in scenarios:
                diff_color = {
                    "easy": "green",
                    "medium": "yellow",
                    "hard": "red",
                    "expert": "magenta"
                }.get(s.get("difficulty", ""), "white")
                
                table.add_row(
                    s.get("id", ""),
                    s.get("name", ""),
                    s.get("type", ""),
                    f"[{diff_color}]{s.get('difficulty', '')}[/{diff_color}]",
                    f"{s.get('estimated_duration_minutes', 0)}m",
                    str(s.get('expected_vulnerabilities_count', 0))
                )
            
            console.print(table)
            console.print(f"\n[dim]Total: {len(scenarios)} scenarios[/dim]")
        else:
            # Plain text output
            print("\nAvailable Benchmark Scenarios:")
            print("-" * 100)
            print(f"{'ID':<25} {'Name':<30} {'Type':<12} {'Difficulty':<10} {'Duration':<10}")
            print("-" * 100)
            
            for s in scenarios:
                print(
                    f"{s.get('id', ''):<25} "
                    f"{s.get('name', '')[:28]:<30} "
                    f"{s.get('type', ''):<12} "
                    f"{s.get('difficulty', ''):<10} "
                    f"{s.get('estimated_duration_minutes', 0)}m"
                )
            
            print(f"\nTotal: {len(scenarios)} scenarios")
    
    async def run_benchmark(
        self,
        scenarios: Optional[List[str]] = None,
        scenario_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        name: Optional[str] = None,
        concurrent: int = 1,
        timeout: int = 3600,
        compare: bool = False,
        competitors: Optional[List[str]] = None
    ) -> BenchmarkReport:
        """Run benchmark with specified configuration."""
        
        # Build configuration
        config = BenchmarkConfig(
            benchmark_name=name or f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            scenarios=scenarios or [],
            tags=tags,
            max_concurrent=concurrent,
            timeout_per_scenario=timeout,
            enable_competitor_comparison=compare,
            competitors=competitors or []
        )
        
        # Add type filter
        if scenario_type:
            try:
                config.scenario_types = [ScenarioType(scenario_type)]
            except ValueError:
                logger.warning(f"Unknown scenario type: {scenario_type}")
        
        # Add difficulty filter
        if difficulty:
            try:
                config.difficulty_levels = [DifficultyLevel(difficulty)]
            except ValueError:
                logger.warning(f"Unknown difficulty: {difficulty}")
        
        if RICH_AVAILABLE:
            console.print(f"\n[bold]Starting Benchmark:[/bold] {config.benchmark_name}")
            console.print(f"[dim]ID: {config.benchmark_id}[/dim]\n")
        else:
            print(f"\nStarting Benchmark: {config.benchmark_name}")
            print(f"ID: {config.benchmark_id}\n")
        
        # Run benchmark
        report = await self.engine.run_benchmark(config)
        
        # Display results
        self._display_results(report)
        
        return report
    
    def _display_results(self, report: BenchmarkReport) -> None:
        """Display benchmark results."""
        
        if RICH_AVAILABLE:
            console.print("\n[bold]Benchmark Results:[/bold]\n")
            
            # Summary panel
            summary_text = (
                f"[bold]Duration:[/bold] {report.duration_seconds:.1f}s\n"
                f"[bold]Scenarios:[/bold] {len(report.scenario_results)}\n"
                f"[bold]Passed:[/bold] {report.scenarios_passed} ✅\n"
                f"[bold]Failed:[/bold] {report.scenarios_failed} ❌\n"
                f"[bold]Success Rate:[/bold] {report.success_rate:.1f}%"
            )
            console.print(Panel(summary_text, title="Summary", border_style="green"))
            
            # Results table
            table = Table(title="Scenario Results", box=box.ROUNDED)
            table.add_column("Scenario", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Duration", justify="right")
            table.add_column("Precision", justify="right")
            table.add_column("Recall", justify="right")
            table.add_column("F1-Score", justify="right")
            table.add_column("Overall", justify="right")
            
            for result in report.scenario_results:
                status_color = {
                    BenchmarkStatus.COMPLETED: "green",
                    BenchmarkStatus.FAILED: "red",
                    BenchmarkStatus.TIMEOUT: "yellow",
                    BenchmarkStatus.CANCELLED: "magenta"
                }.get(result.status, "white")
                
                if result.metrics:
                    scores = result.metrics.calculate_aggregate_scores()
                    table.add_row(
                        result.scenario_id,
                        f"[{status_color}]{result.status.name}[/{status_color}]",
                        f"{result.duration_seconds:.1f}s",
                        f"{scores.get('precision', 0):.3f}",
                        f"{scores.get('recall', 0):.3f}",
                        f"{scores.get('f1_score', 0):.3f}",
                        f"[bold]{scores.get('overall', 0):.3f}[/bold]"
                    )
                else:
                    table.add_row(
                        result.scenario_id,
                        f"[{status_color}]{result.status.name}[/{status_color}]",
                        f"{result.duration_seconds:.1f}s",
                        "N/A", "N/A", "N/A", "N/A"
                    )
            
            console.print(table)
            
            # Aggregate metrics
            if report.aggregate_metrics:
                console.print("\n[bold]Aggregate Metrics:[/bold]")
                metrics_text = ""
                for key, value in report.aggregate_metrics.items():
                    if isinstance(value, float):
                        metrics_text += f"[bold]{key}:[/bold] {value:.3f}\n"
                    else:
                        metrics_text += f"[bold]{key}:[/bold] {value}\n"
                console.print(Panel(metrics_text, border_style="blue"))
            
            # Output location
            output_path = self.output_dir / report.benchmark_id
            console.print(f"\n[dim]Results saved to: {output_path}[/dim]")
            
        else:
            # Plain text output
            print("\n" + "="*60)
            print("BENCHMARK RESULTS")
            print("="*60)
            print(f"Duration: {report.duration_seconds:.1f}s")
            print(f"Scenarios: {len(report.scenario_results)}")
            print(f"Passed: {report.scenarios_passed}")
            print(f"Failed: {report.scenarios_failed}")
            print(f"Success Rate: {report.success_rate:.1f}%")
            print("-"*60)
            
            for result in report.scenario_results:
                print(f"\n{result.scenario_id}:")
                print(f"  Status: {result.status.name}")
                print(f"  Duration: {result.duration_seconds:.1f}s")
                
                if result.metrics:
                    scores = result.metrics.calculate_aggregate_scores()
                    print(f"  Precision: {scores.get('precision', 0):.3f}")
                    print(f"  Recall: {scores.get('recall', 0):.3f}")
                    print(f"  F1-Score: {scores.get('f1_score', 0):.3f}")
                    print(f"  Overall: {scores.get('overall', 0):.3f}")
    
    def view_report(self, benchmark_id: str) -> None:
        """View a specific benchmark report."""
        
        report_path = self.output_dir / benchmark_id / "report.json"
        
        if not report_path.exists():
            if RICH_AVAILABLE:
                console.print(f"[red]Report not found: {benchmark_id}[/red]")
            else:
                print(f"Report not found: {benchmark_id}")
            return
        
        try:
            with open(report_path) as f:
                data = json.load(f)
            
            if RICH_AVAILABLE:
                console.print(f"\n[bold]Benchmark Report:[/bold] {benchmark_id}")
                
                # Display as tree
                tree = Tree(f"[bold]{data.get('benchmark_name', benchmark_id)}[/bold]")
                
                summary = data.get('summary', {})
                summary_branch = tree.add("[blue]Summary[/blue]")
                summary_branch.add(f"Total: {summary.get('total_scenarios', 0)}")
                summary_branch.add(f"Passed: {summary.get('passed', 0)}")
                summary_branch.add(f"Failed: {summary.get('failed', 0)}")
                summary_branch.add(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
                
                if 'aggregate_metrics' in data and data['aggregate_metrics']:
                    metrics_branch = tree.add("[green]Aggregate Metrics[/green]")
                    for key, value in data['aggregate_metrics'].items():
                        if isinstance(value, float):
                            metrics_branch.add(f"{key}: {value:.3f}")
                        else:
                            metrics_branch.add(f"{key}: {value}")
                
                console.print(tree)
            else:
                print(json.dumps(data, indent=2))
                
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error loading report: {e}[/red]")
            else:
                print(f"Error loading report: {e}")
    
    def list_history(self, limit: int = 10) -> None:
        """List benchmark history."""
        
        history = self.engine.get_benchmark_history(limit=limit)
        
        if not history:
            if RICH_AVAILABLE:
                console.print("[yellow]No benchmark history found[/yellow]")
            else:
                print("No benchmark history found")
            return
        
        if RICH_AVAILABLE:
            table = Table(title="Benchmark History", box=box.ROUNDED)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Date", style="dim")
            table.add_column("Scenarios", justify="right")
            table.add_column("Success Rate", justify="right")
            table.add_column("F1-Score", justify="right")
            
            for entry in history:
                metrics = entry.get('aggregate_metrics', {})
                table.add_row(
                    entry.get('benchmark_id', '')[:12],
                    entry.get('timestamp', '')[:19],
                    str(len(entry.get('scenarios', []))),
                    f"{entry.get('success_rate', 0):.1f}%",
                    f"{metrics.get('avg_f1_score', 0):.3f}"
                )
            
            console.print(table)
        else:
            print("\nBenchmark History:")
            print("-" * 80)
            for entry in history:
                metrics = entry.get('aggregate_metrics', {})
                print(
                    f"{entry.get('benchmark_id', '')[:12]} | "
                    f"{entry.get('timestamp', '')[:19]} | "
                    f"Scenarios: {len(entry.get('scenarios', [])):<3} | "
                    f"Success: {entry.get('success_rate', 0):.1f}% | "
                    f"F1: {metrics.get('avg_f1_score', 0):.3f}"
                )
    
    def compare_reports(
        self, 
        benchmark_id1: str, 
        benchmark_id2: str
    ) -> None:
        """Compare two benchmark reports."""
        
        path1 = self.output_dir / benchmark_id1 / "report.json"
        path2 = self.output_dir / benchmark_id2 / "report.json"
        
        if not path1.exists() or not path2.exists():
            if RICH_AVAILABLE:
                console.print("[red]One or both reports not found[/red]")
            else:
                print("One or both reports not found")
            return
        
        try:
            with open(path1) as f:
                data1 = json.load(f)
            with open(path2) as f:
                data2 = json.load(f)
            
            metrics1 = data1.get('aggregate_metrics', {})
            metrics2 = data2.get('aggregate_metrics', {})
            
            if RICH_AVAILABLE:
                console.print(f"\n[bold]Comparing Benchmarks:[/bold]")
                console.print(f"  [cyan]{benchmark_id1}[/cyan] vs [cyan]{benchmark_id2}[/cyan]\n")
                
                table = Table(box=box.ROUNDED)
                table.add_column("Metric", style="bold")
                table.add_column(benchmark_id1[:15], justify="right")
                table.add_column(benchmark_id2[:15], justify="right")
                table.add_column("Change", justify="right")
                
                for key in metrics1.keys():
                    if key in metrics2:
                        val1 = metrics1[key]
                        val2 = metrics2[key]
                        
                        if isinstance(val1, float) and isinstance(val2, float):
                            change = val2 - val1
                            change_pct = (change / val1 * 100) if val1 != 0 else 0
                            
                            change_color = "green" if change > 0 else "red"
                            change_str = f"{change:+.3f} ({change_pct:+.1f}%)"
                            
                            table.add_row(
                                key,
                                f"{val1:.3f}",
                                f"{val2:.3f}",
                                f"[{change_color}]{change_str}[/{change_color}]"
                            )
                
                console.print(table)
            else:
                print(f"\nComparing: {benchmark_id1} vs {benchmark_id2}")
                print("-" * 60)
                for key in metrics1.keys():
                    if key in metrics2:
                        val1 = metrics1[key]
                        val2 = metrics2[key]
                        if isinstance(val1, float):
                            change = val2 - val1
                            print(f"{key}: {val1:.3f} → {val2:.3f} ({change:+.3f})")
                        
        except Exception as e:
            if RICH_AVAILABLE:
                console.print(f"[red]Error comparing reports: {e}[/red]")
            else:
                print(f"Error comparing reports: {e}")
    
    def generate_chart(self, benchmark_id: Optional[str] = None) -> None:
        """Generate visualization charts."""
        
        if not MATPLOTLIB_AVAILABLE:
            if RICH_AVAILABLE:
                console.print("[yellow]Matplotlib not available. Install with: pip install matplotlib[/yellow]")
            else:
                print("Matplotlib not available")
            return
        
        if benchmark_id:
            # Single benchmark chart
            report_path = self.output_dir / benchmark_id / "report.json"
            if not report_path.exists():
                if RICH_AVAILABLE:
                    console.print(f"[red]Report not found: {benchmark_id}[/red]")
                else:
                    print(f"Report not found: {benchmark_id}")
                return
            
            with open(report_path) as f:
                data = json.load(f)
            
            self._create_benchmark_chart(data, benchmark_id)
        else:
            # Historical trend chart
            history = self.engine.get_benchmark_history(limit=20)
            if not history:
                if RICH_AVAILABLE:
                    console.print("[yellow]No history available for trend chart[/yellow]")
                else:
                    print("No history available")
                return
            
            self._create_trend_chart(history)
    
    def _create_benchmark_chart(self, data: dict, benchmark_id: str) -> None:
        """Create chart for single benchmark."""
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle(f'Benchmark Results: {benchmark_id}', fontsize=14, fontweight='bold')
        
        scenario_results = data.get('scenario_results', [])
        
        # 1. Scores by scenario
        ax1 = axes[0, 0]
        scenarios = [r['scenario_id'] for r in scenario_results if r.get('metrics')]
        scores_data = []
        
        for r in scenario_results:
            if r.get('metrics'):
                scores = r['metrics'].get('aggregate_scores', {})
                scores_data.append({
                    'precision': scores.get('precision', 0),
                    'recall': scores.get('recall', 0),
                    'f1': scores.get('f1_score', 0)
                })
        
        if scenarios and scores_data:
            x = range(len(scenarios))
            width = 0.25
            
            ax1.bar([i - width for i in x], [s['precision'] for s in scores_data], 
                   width, label='Precision', alpha=0.8)
            ax1.bar(x, [s['recall'] for s in scores_data], 
                   width, label='Recall', alpha=0.8)
            ax1.bar([i + width for i in x], [s['f1'] for s in scores_data], 
                   width, label='F1-Score', alpha=0.8)
            
            ax1.set_xlabel('Scenario')
            ax1.set_ylabel('Score')
            ax1.set_title('Scores by Scenario')
            ax1.set_xticks(x)
            ax1.set_xticklabels(scenarios, rotation=45, ha='right')
            ax1.legend()
            ax1.set_ylim(0, 1)
        
        # 2. Duration by scenario
        ax2 = axes[0, 1]
        durations = [r['duration_seconds'] for r in scenario_results]
        statuses = [r['status'] for r in scenario_results]
        colors = ['green' if s == 'COMPLETED' else 'red' for s in statuses]
        
        ax2.barh(scenarios, durations, color=colors, alpha=0.7)
        ax2.set_xlabel('Duration (seconds)')
        ax2.set_title('Scenario Duration')
        
        # 3. Severity distribution
        ax3 = axes[1, 0]
        all_severities = {}
        for r in scenario_results:
            if r.get('metrics'):
                sev_dist = r['metrics'].get('severity_distribution', {})
                for sev, count in sev_dist.items():
                    all_severities[sev] = all_severities.get(sev, 0) + count
        
        if all_severities:
            colors_sev = {'critical': '#d32f2f', 'high': '#f57c00', 
                         'medium': '#fbc02d', 'low': '#388e3c', 'info': '#1976d2'}
            sev_colors = [colors_sev.get(s, '#757575') for s in all_severities.keys()]
            ax3.pie(all_severities.values(), labels=all_severities.keys(), 
                   colors=sev_colors, autopct='%1.1f%%')
            ax3.set_title('Findings by Severity')
        
        # 4. Aggregate metrics
        ax4 = axes[1, 1]
        metrics = data.get('aggregate_metrics', {})
        metric_names = []
        metric_values = []
        
        for key in ['avg_precision', 'avg_recall', 'avg_f1_score', 'avg_accuracy']:
            if key in metrics:
                metric_names.append(key.replace('avg_', '').title())
                metric_values.append(metrics[key])
        
        if metric_values:
            bars = ax4.bar(metric_names, metric_values, color='steelblue', alpha=0.7)
            ax4.set_ylabel('Score')
            ax4.set_title('Aggregate Metrics')
            ax4.set_ylim(0, 1)
            
            # Add value labels on bars
            for bar, val in zip(bars, metric_values):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{val:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        
        output_path = self.output_dir / benchmark_id / "chart.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        if RICH_AVAILABLE:
            console.print(f"[green]Chart saved:[/green] {output_path}")
        else:
            print(f"Chart saved: {output_path}")
    
    def _create_trend_chart(self, history: list) -> None:
        """Create historical trend chart."""
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        dates = [h.get('timestamp', '')[:10] for h in history]
        
        metrics_to_plot = {
            'F1-Score': [h.get('aggregate_metrics', {}).get('avg_f1_score', 0) for h in history],
            'Precision': [h.get('aggregate_metrics', {}).get('avg_precision', 0) for h in history],
            'Recall': [h.get('aggregate_metrics', {}).get('avg_recall', 0) for h in history],
            'Accuracy': [h.get('aggregate_metrics', {}).get('avg_accuracy', 0) for h in history],
        }
        
        for label, values in metrics_to_plot.items():
            ax.plot(dates, values, marker='o', label=label, linewidth=2)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Score')
        ax.set_title('Benchmark Performance Trends')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        output_path = self.output_dir / "trend_chart.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        if RICH_AVAILABLE:
            console.print(f"[green]Trend chart saved:[/green] {output_path}")
        else:
            print(f"Trend chart saved: {output_path}")
    
    async def run_ci(
        self,
        benchmark_type: str = "quick",
        output_format: str = "all",
        fail_on_gate: bool = False,
        fail_on_regression: bool = False
    ) -> None:
        """Run CI/CD benchmark pipeline."""
        
        config = CIConfig(
            output_format=output_format,
            fail_on_gate_failure=fail_on_gate,
            fail_on_critical_regression=fail_on_regression
        )
        
        runner = CIBenchmarkRunner(
            engine=self.engine,
            config=config,
            output_dir=str(self.output_dir)
        )
        
        result = await runner.run_ci_pipeline(benchmark_type)
        
        if RICH_AVAILABLE:
            if result["should_fail"]:
                console.print(f"\n[red]❌ Build Failed: {result['fail_reason']}[/red]")
            else:
                console.print("\n[green]✅ All Checks Passed[/green]")
            
            console.print(f"\n[bold]Results:[/bold]")
            console.print(f"  Success Rate: {result['success_rate']:.1f}%")
            console.print(f"  Gates Passed: {result['gates_passed']}/{result['gates_total']}")
            console.print(f"  Regressions: {result['regressions']}")
        else:
            if result["should_fail"]:
                print(f"\nBuild Failed: {result['fail_reason']}")
            else:
                print("\nAll Checks Passed")
            print(f"Success Rate: {result['success_rate']:.1f}%")
        
        if result["should_fail"]:
            sys.exit(1)


def main():
    """Main CLI entry point."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(
        description="Zen-AI-Pentest Benchmark Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all scenarios
  %(prog)s list
  
  # Run quick benchmark
  %(prog)s run --scenarios dvwa juice-shop
  
  # Run full benchmark suite
  %(prog)s run --all
  
  # Run by difficulty
  %(prog)s run --difficulty easy
  
  # View report
  %(prog)s view <benchmark-id>
  
  # Compare two reports
  %(prog)s compare <id1> <id2>
  
  # Generate charts
  %(prog)s chart --benchmark <id>
  
  # Run CI pipeline
  %(prog)s ci --type quick
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available scenarios")
    list_parser.add_argument("--type", help="Filter by scenario type")
    list_parser.add_argument("--difficulty", help="Filter by difficulty")
    list_parser.add_argument("--tag", help="Filter by tag")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run benchmark")
    run_parser.add_argument("--scenarios", nargs="+", help="Specific scenarios to run")
    run_parser.add_argument("--all", action="store_true", help="Run all scenarios")
    run_parser.add_argument("--type", help="Filter by scenario type")
    run_parser.add_argument("--difficulty", help="Filter by difficulty")
    run_parser.add_argument("--tags", nargs="+", help="Filter by tags")
    run_parser.add_argument("--name", help="Benchmark name")
    run_parser.add_argument("--concurrent", type=int, default=1, help="Max concurrent scenarios")
    run_parser.add_argument("--timeout", type=int, default=3600, help="Timeout per scenario (seconds)")
    run_parser.add_argument("--compare", action="store_true", help="Compare with competitors")
    run_parser.add_argument("--competitors", nargs="+", help="Competitors to compare")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View benchmark report")
    view_parser.add_argument("benchmark_id", help="Benchmark ID")
    
    # History command
    history_parser = subparsers.add_parser("history", help="View benchmark history")
    history_parser.add_argument("--limit", type=int, default=10, help="Number of entries")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two benchmarks")
    compare_parser.add_argument("benchmark_id1", help="First benchmark ID")
    compare_parser.add_argument("benchmark_id2", help="Second benchmark ID")
    
    # Chart command
    chart_parser = subparsers.add_parser("chart", help="Generate visualization charts")
    chart_parser.add_argument("--benchmark", help="Benchmark ID (or omit for trend)")
    
    # CI command
    ci_parser = subparsers.add_parser("ci", help="Run CI/CD benchmark pipeline")
    ci_parser.add_argument("--type", choices=["quick", "full"], default="quick")
    ci_parser.add_argument("--format", choices=["json", "junit", "markdown", "all"], default="all")
    ci_parser.add_argument("--fail-on-gate", action="store_true", help="Fail on gate failure")
    ci_parser.add_argument("--fail-on-regression", action="store_true", help="Fail on regression")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = BenchmarkCLI()
    
    if args.command == "list":
        cli.list_scenarios(
            scenario_type=args.type,
            difficulty=args.difficulty,
            tag=args.tag
        )
    
    elif args.command == "run":
        scenarios = None
        if args.all:
            scenarios = list(ALL_SCENARIOS.keys())
        elif args.scenarios:
            scenarios = args.scenarios
        
        asyncio.run(cli.run_benchmark(
            scenarios=scenarios,
            scenario_type=args.type,
            difficulty=args.difficulty,
            tags=args.tags,
            name=args.name,
            concurrent=args.concurrent,
            timeout=args.timeout,
            compare=args.compare,
            competitors=args.competitors
        ))
    
    elif args.command == "view":
        cli.view_report(args.benchmark_id)
    
    elif args.command == "history":
        cli.list_history(limit=args.limit)
    
    elif args.command == "compare":
        cli.compare_reports(args.benchmark_id1, args.benchmark_id2)
    
    elif args.command == "chart":
        cli.generate_chart(args.benchmark)
    
    elif args.command == "ci":
        asyncio.run(cli.run_ci(
            benchmark_type=args.type,
            output_format=args.format,
            fail_on_gate=args.fail_on_gate,
            fail_on_regression=args.fail_on_regression
        ))


if __name__ == "__main__":
    main()
