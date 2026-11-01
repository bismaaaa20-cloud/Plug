import asyncio
import unittest
from plug.core.executor import AsyncExecutor
from plug.core.models import Plan, Task, TaskStatus
from plug.providers.base import ProviderResponse
from plug.providers.registry import ProviderRegistry

class FakeProvider:
    name = "fake"
    async def complete(self, request):
        return ProviderResponse(self.name, f"done: {request.prompt}")
    async def health(self):
        return True

class ExecutorTests(unittest.TestCase):
    def test_dependency_execution(self):
        registry = ProviderRegistry()
        registry.register(FakeProvider())
        plan = Plan((Task("one", "first", "fake"), Task("two", "second", "fake", ("one",))))
        results = asyncio.run(AsyncExecutor(registry).execute(plan))
        self.assertEqual(results["one"].status, TaskStatus.SUCCEEDED)
        self.assertEqual(results["two"].status, TaskStatus.SUCCEEDED)
    def test_unknown_provider_fails_without_leaking_message(self):
        plan = Plan((Task("one", "first", "missing"),))
        results = asyncio.run(AsyncExecutor(ProviderRegistry()).execute(plan))
        self.assertEqual(results["one"].status, TaskStatus.FAILED)
        self.assertEqual(results["one"].error_type, "UnknownProviderError")
