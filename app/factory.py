"""
Application Factory

Creates and configures the FastAPI application with all components.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all our components
try:
    from orchestrator import ZenOrchestrator, OrchestratorConfig
    from scheduler import TaskScheduler, ScheduleConfig
    from dashboard import DashboardManager, DashboardConfig
    from audit import AuditLogger
    from analysis_bot import AnalysisBot
    from core.secure_input_validator import SecureInputValidator
except ImportError as e:
    logging.warning(f"Some components not available: {e}")
    ZenOrchestrator = None
    TaskScheduler = None
    DashboardManager = None
    AuditLogger = None
    AnalysisBot = None
    SecureInputValidator = None

# Import API routes
try:
    from api.routes.analysis import router as analysis_router
    from api.routes.audit import router as audit_router
    from api.routes.orchestrator import router as orchestrator_router
    from api.routes.scheduler import router as scheduler_router
    from api.routes.dashboard import router as dashboard_router
except ImportError:
    analysis_router = None
    audit_router = None
    orchestrator_router = None
    scheduler_router = None
    dashboard_router = None


logger = logging.getLogger(__name__)


class ApplicationFactory:
    """
    Factory for creating the Zen-AI-Pentest application

    Creates and wires together all components:
    - Orchestrator
    - Scheduler
    - Dashboard
    - Audit Logger
    - Analysis Bot

    Example:
        factory = ApplicationFactory()
        app = factory.create()
    """

    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.app: Optional[FastAPI] = None

    def create(
        self,
        debug: bool = False,
        enable_docs: bool = True
    ) -> FastAPI:
        """
        Create and configure the FastAPI application

        Args:
            debug: Enable debug mode
            enable_docs: Enable Swagger UI docs

        Returns:
            Configured FastAPI application
        """
        # Create FastAPI app
        self.app = FastAPI(
            title="Zen-AI-Pentest API",
            description="Autonomous AI-powered penetration testing framework",
            version="2.4.0",
            debug=debug,
            docs_url="/docs" if enable_docs else None,
            redoc_url="/redoc" if enable_docs else None,
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup lifespan (startup/shutdown)
        self.app.router.lifespan_context = self._lifespan

        # Register routes
        self._register_routes()

        # Add health check endpoint
        self._add_health_endpoint()

        logger.info("Application factory created")
        return self.app

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """Application lifespan manager (startup/shutdown)"""
        # Startup
        logger.info("=" * 60)
        logger.info("Starting Zen-AI-Pentest Application...")
        logger.info("=" * 60)

        try:
            # Initialize components
            await self._initialize_components(app)

            logger.info("✅ Application startup complete")
            logger.info("=" * 60)

            yield

        finally:
            # Shutdown
            logger.info("=" * 60)
            logger.info("Shutting down Zen-AI-Pentest Application...")
            logger.info("=" * 60)

            await self._shutdown_components()

            logger.info("✅ Application shutdown complete")

    async def _initialize_components(self, app: FastAPI) -> None:
        """Initialize all application components"""

        # 1. Secure Validator (always needed)
        if SecureInputValidator:
            self.components["validator"] = SecureInputValidator()
            logger.info("✅ Secure Validator initialized")

        # 2. Audit Logger
        if AuditLogger:
            try:
                from audit.config import AuditConfig
                audit_config = AuditConfig.default()
                audit_logger = AuditLogger(audit_config)
                await audit_logger.start()
                self.components["audit_logger"] = audit_logger
                logger.info("✅ Audit Logger initialized")
            except Exception as e:
                logger.warning(f"⚠️ Audit Logger initialization failed: {e}")

        # 3. Analysis Bot
        if AnalysisBot:
            try:
                self.components["analysis_bot"] = AnalysisBot()
                logger.info("✅ Analysis Bot initialized")
            except Exception as e:
                logger.warning(f"⚠️ Analysis Bot initialization failed: {e}")

        # 4. Task Scheduler
        if TaskScheduler:
            try:
                scheduler_config = ScheduleConfig(persistence_enabled=True)
                scheduler = TaskScheduler(scheduler_config)
                await scheduler.start()
                self.components["scheduler"] = scheduler
                logger.info("✅ Task Scheduler initialized")
            except Exception as e:
                logger.warning(f"⚠️ Task Scheduler initialization failed: {e}")

        # 5. Dashboard Manager
        if DashboardManager:
            try:
                dashboard_config = DashboardConfig()
                dashboard = DashboardManager(dashboard_config)
                await dashboard.start()
                self.components["dashboard"] = dashboard
                logger.info("✅ Dashboard Manager initialized")
            except Exception as e:
                logger.warning(f"⚠️ Dashboard Manager initialization failed: {e}")

        # 6. ZenOrchestrator (main coordinator)
        if ZenOrchestrator:
            try:
                orch_config = OrchestratorConfig.production()
                orchestrator = ZenOrchestrator(orch_config)

                # Inject dependencies
                if "validator" in self.components:
                    orchestrator.validator = self.components["validator"]
                if "audit_logger" in self.components:
                    orchestrator.audit_logger = self.components["audit_logger"]
                if "analysis_bot" in self.components:
                    orchestrator.analysis_bot = self.components["analysis_bot"]

                await orchestrator.start()
                self.components["orchestrator"] = orchestrator
                logger.info("✅ ZenOrchestrator initialized")
            except Exception as e:
                logger.warning(f"⚠️ ZenOrchestrator initialization failed: {e}")

        # Wire up integrations
        await self._wire_integrations()

        # Store components in app state
        app.state.components = self.components

    async def _wire_integrations(self) -> None:
        """Wire up component integrations"""

        # Connect Dashboard to Orchestrator
        if "dashboard" in self.components and "orchestrator" in self.components:
            dashboard = self.components["dashboard"]
            orchestrator = self.components["orchestrator"]
            dashboard.connect_orchestrator(orchestrator)
            logger.info("🔗 Dashboard connected to Orchestrator")

        # Connect Dashboard to Scheduler
        if "dashboard" in self.components and "scheduler" in self.components:
            dashboard = self.components["dashboard"]
            scheduler = self.components["scheduler"]
            dashboard.connect_scheduler(scheduler)
            logger.info("🔗 Dashboard connected to Scheduler")

        # Register task callbacks with Scheduler
        if "scheduler" in self.components:
            scheduler = self.components["scheduler"]

            # Register a generic task callback
            async def generic_task_callback(task_data):
                """Execute task via orchestrator"""
                if "orchestrator" in self.components:
                    orch = self.components["orchestrator"]
                    # Submit to orchestrator
                    task_id = await orch.submit_task(task_data)
                    return {"task_id": task_id, "status": "submitted"}
                return {"error": "Orchestrator not available"}

            scheduler.register_callback("vulnerability_scan", generic_task_callback)
            scheduler.register_callback("subdomain_enum", generic_task_callback)
            scheduler.register_callback("port_scan", generic_task_callback)
            logger.info("🔗 Task callbacks registered with Scheduler")

    async def _shutdown_components(self) -> None:
        """Gracefully shutdown all components"""

        shutdown_order = [
            "orchestrator",  # Stop orchestrator first
            "dashboard",     # Then dashboard
            "scheduler",     # Then scheduler
            "audit_logger",  # Then audit logger
        ]

        for name in shutdown_order:
            component = self.components.get(name)
            if component and hasattr(component, 'stop'):
                try:
                    await component.stop()
                    logger.info(f"✅ {name} stopped")
                except Exception as e:
                    logger.error(f"❌ Error stopping {name}: {e}")

    def _register_routes(self) -> None:
        """Register all API routes"""

        routers = [
            (analysis_router, "/api/v1/analysis"),
            (audit_router, "/api/v1/audit"),
            (orchestrator_router, "/api/v1/orchestrator"),
            (scheduler_router, "/api/v1/scheduler"),
            (dashboard_router, "/api/v1/dashboard"),
        ]

        for router, prefix in routers:
            if router:
                self.app.include_router(router, prefix=prefix)
                logger.debug(f"Registered routes: {prefix}")

    def _add_health_endpoint(self) -> None:
        """Add health check endpoint"""

        @self.app.get("/health")
        async def health_check():
            """Comprehensive health check"""
            checks = {}

            for name, component in self.components.items():
                try:
                    if hasattr(component, 'health_check'):
                        if asyncio.iscoroutinefunction(component.health_check):
                            checks[name] = await component.health_check()
                        else:
                            checks[name] = component.health_check()
                    else:
                        checks[name] = {"healthy": True}
                except Exception as e:
                    checks[name] = {"healthy": False, "error": str(e)}

            all_healthy = all(
                c.get("healthy", False) if isinstance(c, dict) else c
                for c in checks.values()
            )

            return {
                "status": "healthy" if all_healthy else "degraded",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.app.get("/ready")
        async def readiness_check():
            """Readiness probe for Kubernetes"""
            orchestrator = self.components.get("orchestrator")
            if orchestrator and orchestrator._running:
                return {"ready": True}
            return {"ready": False}

        @self.app.get("/live")
        async def liveness_check():
            """Liveness probe for Kubernetes"""
            return {"alive": True}

    def get_component(self, name: str) -> Optional[Any]:
        """Get a component by name"""
        return self.components.get(name)


def create_app(
    debug: bool = False,
    enable_docs: bool = True
) -> FastAPI:
    """
    Convenience function to create the application

    Args:
        debug: Enable debug mode
        enable_docs: Enable Swagger UI

    Returns:
        Configured FastAPI application
    """
    factory = ApplicationFactory()
    return factory.create(debug=debug, enable_docs=enable_docs)
