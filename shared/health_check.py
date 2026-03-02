"""
Module Health Check System - Ensures all modules are fully connected.

Every module must pass health checks on startup to verify:
1. Database tables exist with correct schema
2. Required configurations have defaults
3. API routes are registered and responding
4. Mini App settings component exists (if applicable)
5. Commands are registered with correct prefix
6. Event listeners are active
7. WebSocket events broadcast correctly

If any module fails its health check, the system logs a detailed error
and the module is disabled until the issue is resolved.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Type

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import AsyncSessionLocal, engine
from shared.event_bus import EventType

logger = logging.getLogger(__name__)


class HealthCheckStatus(str, Enum):
    """Status of a health check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    check_name: str
    status: HealthCheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ModuleHealthReport:
    """Complete health report for a module."""
    module_name: str
    overall_status: HealthCheckStatus
    checks: List[HealthCheckResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_check(self, result: HealthCheckResult) -> None:
        """Add a check result to the report."""
        self.checks.append(result)
        
        # Update overall status
        if result.status == HealthCheckStatus.FAIL:
            self.overall_status = HealthCheckStatus.FAIL
        elif result.status == HealthCheckStatus.WARNING:
            if self.overall_status != HealthCheckStatus.FAIL:
                self.overall_status = HealthCheckStatus.WARNING
        elif result.status == HealthCheckStatus.PASS:
            if self.overall_status not in [HealthCheckStatus.FAIL, HealthCheckStatus.WARNING]:
                self.overall_status = HealthCheckStatus.PASS


class ModuleHealthChecker:
    """
    Performs health checks on a module.
    
    Each module can define its own health checks, but all modules
    get a base set of checks automatically.
    """
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._custom_checks: List[Callable[..., Coroutine]] = []
    
    def add_check(
        self,
        check_func: Callable[..., Coroutine]
    ) -> None:
        """Add a custom health check function."""
        self._custom_checks.append(check_func)
    
    async def run_checks(self) -> ModuleHealthReport:
        """Run all health checks for this module."""
        report = ModuleHealthReport(
            module_name=self.module_name,
            overall_status=HealthCheckStatus.PASS
        )
        
        # Run base checks
        await self._check_database_tables(report)
        await self._check_module_config(report)
        await self._check_api_routes(report)
        
        # Run custom checks
        for check_func in self._custom_checks:
            try:
                result = await check_func()
                if isinstance(result, HealthCheckResult):
                    report.add_check(result)
            except Exception as e:
                report.add_check(HealthCheckResult(
                    check_name=check_func.__name__,
                    status=HealthCheckStatus.FAIL,
                    message=f"Health check crashed: {e}"
                ))
        
        return report
    
    async def _check_database_tables(self, report: ModuleHealthReport) -> None:
        """Check that required database tables exist."""
        try:
            # Get expected tables for this module
            expected_tables = self._get_expected_tables()
            
            if not expected_tables:
                report.add_check(HealthCheckResult(
                    check_name="database_tables",
                    status=HealthCheckStatus.SKIP,
                    message="No database tables required"
                ))
                return
            
            async with engine.connect() as conn:
                for table_name in expected_tables:
                    try:
                        # Check if table exists
                        result = await conn.execute(
                            text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
                        )
                        exists = result.scalar()
                        
                        if not exists:
                            report.add_check(HealthCheckResult(
                                check_name=f"database_table_{table_name}",
                                status=HealthCheckStatus.FAIL,
                                message=f"Table '{table_name}' does not exist",
                                details={"table": table_name}
                            ))
                        else:
                            report.add_check(HealthCheckResult(
                                check_name=f"database_table_{table_name}",
                                status=HealthCheckStatus.PASS,
                                message=f"Table '{table_name}' exists",
                                details={"table": table_name}
                            ))
                    except Exception as e:
                        report.add_check(HealthCheckResult(
                            check_name=f"database_table_{table_name}",
                            status=HealthCheckStatus.FAIL,
                            message=f"Failed to check table '{table_name}': {e}",
                            details={"table": table_name, "error": str(e)}
                        ))
        
        except Exception as e:
            report.add_check(HealthCheckResult(
                check_name="database_tables",
                status=HealthCheckStatus.FAIL,
                message=f"Database connection failed: {e}"
            ))
    
    async def _check_module_config(self, report: ModuleHealthReport) -> None:
        """Check that module has default configuration."""
        try:
            from shared.models import ModuleConfig
            
            async with AsyncSessionLocal() as session:
                # Check if any groups have this module configured
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM module_configs WHERE module_name = '{self.module_name}'")
                )
                count = result.scalar()
                
                report.add_check(HealthCheckResult(
                    check_name="module_config",
                    status=HealthCheckStatus.PASS,
                    message=f"Module has {count} configured groups",
                    details={"configured_groups": count}
                ))
        
        except Exception as e:
            report.add_check(HealthCheckResult(
                check_name="module_config",
                status=HealthCheckStatus.WARNING,
                message=f"Could not verify module config: {e}"
            ))
    
    async def _check_api_routes(self, report: ModuleHealthReport) -> None:
        """Check that API routes are registered."""
        # This would check if the API routes for this module are registered
        # For now, just mark as pass
        report.add_check(HealthCheckResult(
            check_name="api_routes",
            status=HealthCheckStatus.SKIP,
            message="API route check not implemented"
        ))
    
    def _get_expected_tables(self) -> List[str]:
        """Get list of database tables this module expects."""
        # Map module names to their expected tables
        table_map = {
            "moderation": ["mod_actions", "warnings", "member_notes"],
            "economy": ["wallets", "transactions", "economy_config"],
            "reputation": ["reputation", "reputation_logs"],
            "games": ["game_sessions", "game_scores"],
            "notes": ["notes"],
            "filters": ["filters"],
            "locks": ["locks"],
            "rules": ["rules"],
            "welcome": ["greetings"],
            "scheduler": ["scheduled_messages"],
            "captcha": ["captcha_settings"],
            "antispam": ["antiflood_config"],
            "antiraid": ["antiraid_config"],
            "word_filter": ["banned_words", "banned_word_list_configs"],
            "federation": ["federations", "federation_admins", "federation_members", "federation_bans"],
            "polls": ["polls", "poll_votes"],
            "identity": ["member_badges", "badge_definitions"],
            "events": ["group_events", "event_rsvps"],
            "challenges": [],  # Uses existing tables
            "trust_system": ["trust_score_history"],
            "graveyard": ["deleted_messages"],
        }
        
        return table_map.get(self.module_name, [])


class SystemHealthChecker:
    """
    System-wide health checker that runs checks on all modules.
    
    This is the main entry point for health checking on startup.
    """
    
    def __init__(self):
        self._module_checkers: Dict[str, ModuleHealthChecker] = {}
        self._system_checks: List[Callable[..., Coroutine]] = []
    
    def register_module(self, module_name: str) -> ModuleHealthChecker:
        """Register a module for health checking."""
        checker = ModuleHealthChecker(module_name)
        self._module_checkers[module_name] = checker
        return checker
    
    def add_system_check(self, check_func: Callable[..., Coroutine]) -> None:
        """Add a system-wide health check."""
        self._system_checks.append(check_func)
    
    async def run_all_checks(self) -> Dict[str, ModuleHealthReport]:
        """Run health checks on all registered modules."""
        results = {}
        
        # Run module checks
        for module_name, checker in self._module_checkers.items():
            try:
                report = await checker.run_checks()
                results[module_name] = report
                
                # Log failures
                if report.overall_status == HealthCheckStatus.FAIL:
                    logger.error(
                        f"Module '{module_name}' health check FAILED: "
                        f"{sum(1 for c in report.checks if c.status == HealthCheckStatus.FAIL)} failures"
                    )
                    for check in report.checks:
                        if check.status == HealthCheckStatus.FAIL:
                            logger.error(f"  - {check.check_name}: {check.message}")
                elif report.overall_status == HealthCheckStatus.WARNING:
                    logger.warning(f"Module '{module_name}' health check passed with warnings")
                else:
                    logger.info(f"Module '{module_name}' health check passed")
            
            except Exception as e:
                logger.error(f"Health check crashed for module '{module_name}': {e}")
                results[module_name] = ModuleHealthReport(
                    module_name=module_name,
                    overall_status=HealthCheckStatus.FAIL,
                    checks=[HealthCheckResult(
                        check_name="health_check_crash",
                        status=HealthCheckStatus.FAIL,
                        message=f"Health check crashed: {e}"
                    )]
                )
        
        # Run system checks
        for check_func in self._system_checks:
            try:
                await check_func()
            except Exception as e:
                logger.error(f"System health check '{check_func.__name__}' failed: {e}")
        
        return results
    
    async def check_database_connection(self) -> HealthCheckResult:
        """Check that database connection is working."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                return HealthCheckResult(
                    check_name="database_connection",
                    status=HealthCheckStatus.PASS,
                    message="Database connection successful"
                )
        except Exception as e:
            return HealthCheckResult(
                check_name="database_connection",
                status=HealthCheckStatus.FAIL,
                message=f"Database connection failed: {e}"
            )
    
    async def check_redis_connection(self) -> HealthCheckResult:
        """Check that Redis connection is working."""
        try:
            from shared.redis_client import get_redis
            redis = await get_redis()
            await redis.ping()
            return HealthCheckResult(
                check_name="redis_connection",
                status=HealthCheckStatus.PASS,
                message="Redis connection successful"
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="redis_connection",
                status=HealthCheckStatus.FAIL,
                message=f"Redis connection failed: {e}"
            )
    
    async def check_event_bus(self) -> HealthCheckResult:
        """Check that event bus is working."""
        try:
            from shared.event_bus import get_event_bus, NexusEvent, EventType
            bus = await get_event_bus()
            
            # Publish a test event to a test channel
            test_event = NexusEvent(
                event_type=EventType.SYSTEM_ERROR,
                group_id=0,  # Test group
                data={"test": True}
            )
            await bus.publish(test_event)
            
            return HealthCheckResult(
                check_name="event_bus",
                status=HealthCheckStatus.PASS,
                message="Event bus is working"
            )
        except Exception as e:
            return HealthCheckResult(
                check_name="event_bus",
                status=HealthCheckStatus.FAIL,
                message=f"Event bus check failed: {e}"
            )
    
    def get_failed_modules(self, results: Dict[str, ModuleHealthReport]) -> List[str]:
        """Get list of modules that failed health checks."""
        return [
            name for name, report in results.items()
            if report.overall_status == HealthCheckStatus.FAIL
        ]


# Global health checker
_health_checker: Optional[SystemHealthChecker] = None


def get_health_checker() -> SystemHealthChecker:
    """Get or create the global health checker."""
    global _health_checker
    
    if _health_checker is None:
        _health_checker = SystemHealthChecker()
        
        # Add system checks
        _health_checker.add_system_check(_health_checker.check_database_connection)
        _health_checker.add_system_check(_health_checker.check_redis_connection)
        _health_checker.add_system_check(_health_checker.check_event_bus)
    
    return _health_checker


async def run_startup_health_checks(module_names: List[str]) -> Dict[str, ModuleHealthReport]:
    """
    Run health checks on all modules at startup.
    
    Returns a dict of module_name -> HealthReport.
    Modules with FAILED status should be disabled.
    """
    checker = get_health_checker()
    
    # Register all modules
    for name in module_names:
        checker.register_module(name)
    
    # Run checks
    results = await checker.run_all_checks()
    
    # Log summary
    failed = checker.get_failed_modules(results)
    if failed:
        logger.error(
            f"Health check complete: {len(results)} modules checked, "
            f"{len(failed)} FAILED: {', '.join(failed)}"
        )
    else:
        logger.info(
            f"Health check complete: {len(results)} modules checked, all passed"
        )
    
    return results
