"""Async DAG executor with bounded parallelism."""

from __future__ import annotations

import asyncio

from plug.core.models import Plan, Task, TaskResult, TaskStatus
from plug.providers.base import ProviderRequest
from plug.providers.registry import ProviderRegistry


class AsyncExecutor:
    def __init__(self, providers: ProviderRegistry, max_concurrency: int = 4) -> None:
        if isinstance(max_concurrency, bool) or not isinstance(max_concurrency, int) or max_concurrency < 1:
            raise ValueError("max_concurrency must be a positive integer")
        self.providers = providers
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def _run_task(self, task: Task) -> TaskResult:
        async with self._semaphore:
            try:
                provider = self.providers.get(task.provider)
                response = await provider.complete(ProviderRequest(prompt=task.prompt))
                return TaskResult(task.id, TaskStatus.SUCCEEDED, output=response.text)
            except Exception as exc:
                # Do not persist exception messages; they may contain credentials or prompts.
                return TaskResult(task.id, TaskStatus.FAILED, error_type=type(exc).__name__)

    async def execute(self, plan: Plan, *, fail_fast: bool = False) -> dict[str, TaskResult]:
        results: dict[str, TaskResult] = {}
        for layer in plan.layers():
            runnable: list[Task] = []
            for task in layer:
                failed_dependency = any(
                    results[dep].status is not TaskStatus.SUCCEEDED
                    for dep in task.dependencies
                )
                if failed_dependency:
                    results[task.id] = TaskResult(task.id, TaskStatus.BLOCKED)
                else:
                    runnable.append(task)
            if runnable:
                completed = await asyncio.gather(*(self._run_task(task) for task in runnable))
                results.update((item.task_id, item) for item in completed)
            if fail_fast and any(item.status is TaskStatus.FAILED for item in results.values()):
                for later in plan.tasks:
                    if later.id not in results:
                        results[later.id] = TaskResult(later.id, TaskStatus.BLOCKED)
                break
        return results
