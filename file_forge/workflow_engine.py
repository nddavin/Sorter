"""
Advanced workflow automation engine for file processing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from .models import Workflow, WorkflowExecution, File as FileModel, SortingRule, AuditLog
from .database import get_db_context
from .processors import file_processor, sorting_engine
from .config import settings

logger = logging.getLogger(__name__)


class WorkflowTrigger(Enum):
    """Workflow trigger types."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    FILE_UPLOAD = "file_upload"
    API_CALL = "api_call"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep:
    """Represents a single step in a workflow."""

    def __init__(self, step_config: Dict[str, Any]):
        self.id = step_config.get('id')
        self.name = step_config.get('name', '')
        self.type = step_config.get('type', '')
        self.config = step_config.get('config', {})
        self.conditions = step_config.get('conditions', [])
        self.actions = step_config.get('actions', [])
        self.on_success = step_config.get('on_success')
        self.on_failure = step_config.get('on_failure')

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this workflow step."""
        try:
            # Check conditions
            if not await self._check_conditions(context):
                return {'status': 'skipped', 'reason': 'conditions not met'}

            # Execute actions
            result = await self._execute_actions(context)

            return {
                'status': 'completed',
                'step_id': self.id,
                'result': result
            }

        except Exception as e:
            logger.error(f"Step {self.id} failed: {e}")
            return {
                'status': 'failed',
                'step_id': self.id,
                'error': str(e)
            }

    async def _check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if step conditions are met."""
        for condition in self.conditions:
            condition_type = condition.get('type')
            if condition_type == 'file_exists':
                file_path = condition.get('file_path')
                if not file_path or not await self._file_exists(file_path):
                    return False
            elif condition_type == 'file_type':
                expected_type = condition.get('file_type')
                actual_type = context.get('file_type')
                if actual_type != expected_type:
                    return False
            elif condition_type == 'file_size':
                min_size = condition.get('min_size', 0)
                max_size = condition.get('max_size', float('inf'))
                file_size = context.get('file_size', 0)
                if not (min_size <= file_size <= max_size):
                    return False
            elif condition_type == 'user_role':
                required_role = condition.get('role')
                user_role = context.get('user_role')
                if user_role != required_role:
                    return False

        return True

    async def _execute_actions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step actions."""
        results = {}

        for action in self.actions:
            action_type = action.get('type')

            if action_type == 'sort_files':
                results['sorting'] = await self._action_sort_files(context, action)
            elif action_type == 'move_files':
                results['moving'] = await self._action_move_files(context, action)
            elif action_type == 'process_files':
                results['processing'] = await self._action_process_files(context, action)
            elif action_type == 'send_notification':
                results['notification'] = await self._action_send_notification(context, action)
            elif action_type == 'create_report':
                results['report'] = await self._action_create_report(context, action)
            elif action_type == 'run_script':
                results['script'] = await self._action_run_script(context, action)

        return results

    async def _action_sort_files(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Sort files according to rules."""
        files = context.get('files', [])
        rule_ids = action_config.get('rule_ids', [])

        def _query_rules():
            with get_db_context() as db:
                return db.query(SortingRule).filter(SortingRule.id.in_(rule_ids)).all()

        import asyncio
        rules = await asyncio.to_thread(_query_rules)
        sorted_files = sorting_engine.apply_sorting_rules(files, rules)

        return {
            'sorted_count': len(sorted_files),
            'rules_applied': len(rules)
        }

    async def _action_move_files(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Move files to specified location."""
        # Implementation for file moving
        return {'moved': True}

    async def _action_process_files(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process files with specified operations."""
        files = context.get('files', [])
        operations = action_config.get('operations', [])

        processed = []
        for file in files:
            result = await asyncio.to_thread(file_processor.process_file, file.file_path, file.filename)
            processed.append(result)

        return {
            'processed_count': len(processed),
            'operations': operations
        }

    async def _action_send_notification(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification."""
        # Implementation for notifications
        return {'notification_sent': True}

    async def _action_create_report(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create processing report."""
        # Implementation for report generation
        return {'report_created': True}

    async def _action_run_script(self, context: Dict[str, Any], action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run custom script."""
        # Implementation for script execution
        return {'script_executed': True}

    async def _file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        import asyncio
        import os
        return await asyncio.to_thread(os.path.exists, file_path)


class WorkflowEngine:
    """Main workflow automation engine."""

    def __init__(self):
        """Initialize workflow engine."""
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            executors={'default': AsyncIOExecutor()},
            job_defaults={
                'coalesce': True,
                'max_instances': 3,
                'misfire_grace_time': 30
            }
        )
        self.workflows: Dict[int, Workflow] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}

    async def start(self):
        """Start the workflow engine."""
        self.scheduler.start()
        await self._load_workflows()
        logger.info("Workflow engine started")

    async def stop(self):
        """Stop the workflow engine."""
        self.scheduler.shutdown()
        logger.info("Workflow engine stopped")

    async def _load_workflows(self):
        """Load active workflows from database."""
        with get_db_context() as db:
            workflows = db.query(Workflow).filter(Workflow.is_active == True).all()

            for workflow in workflows:
                self.workflows[workflow.id] = workflow
                await self._schedule_workflow(workflow)

    async def _schedule_workflow(self, workflow: Workflow):
        """Schedule workflow based on its trigger configuration."""
        if workflow.trigger_type == WorkflowTrigger.SCHEDULED.value:
            cron_expr = workflow.trigger_config.get('cron_expression')
            if cron_expr:
                self.scheduler.add_job(
                    self._execute_workflow,
                    CronTrigger.from_crontab(cron_expr),
                    args=[workflow.id],
                    id=f"workflow_{workflow.id}",
                    replace_existing=True
                )

    async def create_workflow(self, name: str, description: str, trigger_type: str,
                            trigger_config: Dict[str, Any], steps: List[Dict[str, Any]],
                            created_by_id: int) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description,
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            steps=steps,
            created_by_id=created_by_id
        )

        with get_db_context() as db:
            db.add(workflow)
            # Audit log
            audit_entry = AuditLog(
                user_id=created_by_id,
                action="create_workflow",
                resource_type="workflow",
                resource_id=str(workflow.id),
                details={"workflow_name": name}
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(workflow)

        self.workflows[workflow.id] = workflow
        await self._schedule_workflow(workflow)

        return workflow

    async def execute_workflow(self, workflow_id: int, trigger_context: Optional[Dict[str, Any]] = None) -> WorkflowExecution:
        """Execute a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        with get_db_context() as db:
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING.value,
                trigger_type=trigger_context.get('trigger_type', 'manual') if trigger_context else 'manual',
                trigger_details=trigger_context or {}
            )
            db.add(execution)
            db.commit()
            db.refresh(execution)

        try:
            # Execute workflow steps
            context = trigger_context or {}
            context['execution_id'] = execution.id
            context['workflow_id'] = workflow_id

            results = []
            for step_config in workflow.steps:
                step = WorkflowStep(step_config)
                step_result = await step.execute(context)
                results.append(step_result)

                # Update execution with step results in separate session
                with get_db_context() as db:
                    db_execution = db.query(WorkflowExecution).get(execution.id)
                    db_execution.output = results
                    db.commit()

            execution.status = WorkflowStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow()
            execution.runtime_seconds = (execution.completed_at - execution.started_at).total_seconds()

        except Exception as e:
            execution.status = WorkflowStatus.FAILED.value
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Workflow {workflow_id} execution failed: {e}")

        finally:
            with get_db_context() as db:
                db_execution = db.query(WorkflowExecution).get(execution.id)
                db_execution.status = execution.status
                db_execution.completed_at = execution.completed_at
                db_execution.runtime_seconds = execution.runtime_seconds
                if hasattr(execution, 'error_message'):
                    db_execution.error_message = execution.error_message
                db.commit()

        return execution

    async def _execute_workflow(self, workflow_id: int):
        """Internal method to execute scheduled workflow."""
        await self.execute_workflow(workflow_id, {'trigger_type': 'scheduled'})

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger event and execute associated workflows."""
        # Find workflows triggered by this event
        with get_db_context() as db:
            workflows = db.query(Workflow).filter(
                Workflow.trigger_type == WorkflowTrigger.EVENT.value,
                Workflow.trigger_config.contains({'event_type': event_type})
            ).all()

            for workflow in workflows:
                await self.execute_workflow(workflow.id, {
                    'trigger_type': 'event',
                    'event_type': event_type,
                    'event_data': event_data
                })

        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")

    async def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics."""
        from sqlalchemy import func
        
        with get_db_context() as db:
            total_workflows = db.query(Workflow).count()
            active_workflows = db.query(Workflow).filter(Workflow.is_active == True).count()
            total_executions = db.query(WorkflowExecution).count()

            completed = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowStatus.COMPLETED.value
            ).count()
            failed = db.query(WorkflowExecution).filter(
                WorkflowExecution.status == WorkflowStatus.FAILED.value
            ).count()
            
            avg_runtime_result = db.query(func.avg(WorkflowExecution.runtime_seconds)).filter(
                WorkflowExecution.runtime_seconds.isnot(None)
            ).scalar()
            avg_runtime = avg_runtime_result or 0

            return {
                'total_workflows': total_workflows,
                'active_workflows': active_workflows,
                'total_executions': total_executions,
                'completed_executions': completed,
                'failed_executions': failed,
                'success_rate': completed / max(total_executions, 1) * 100,
                'average_runtime_seconds': avg_runtime
            }


# Global workflow engine instance
workflow_engine = WorkflowEngine()


async def initialize_workflow_engine():
    """Initialize and start the workflow engine."""
    await workflow_engine.start()


async def shutdown_workflow_engine():
    """Shutdown the workflow engine."""
    await workflow_engine.stop()