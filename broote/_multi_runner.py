from concurrent import futures
import asyncio


__all__ = [
    "multi_runner",
    "multi_basic_runner",
    "multi_parallel_runner",
    "multi_executor_runner",
    "multi_thread_runner",
    "multi_async_runner"
]


class multi_runner():
    def __init__(self, runners):
        self._runners = tuple(runners)
        self._max_workers = len(self._runners)

    def get_success_records(self):
        records = []
        for runner in self._runners:
            records.extend(runner.get_success_records())
        return records

    @staticmethod
    def is_parallel_runner(runner):
        return isinstance(runner, parallel_runner)

    @staticmethod
    def is_async_runner(runner):
        return isinstance(runner, async_runner)

    @staticmethod
    def grouped_runners_by_runner_type(runners):
        # Creates map with key being runner class and value(objects)
        runners_map = {}
        for runner in runners:
            runner_type = type(runner)
            runners_map[runner_type] = runners_map.get(runners_map, [])
            runners_map[runner_type].append(runner)
        return runners_map


class multi_basic_runner(multi_runner):
    def start(self):
        # Runs each runners one after the other(non parallel)
        for runner in self._runners:
            runner.start()

class multi_parallel_runner(multi_runner):
    pass

class multi_executor_runner(multi_parallel_runner):
    _executor_type = futures.Executor

    def __init__(self, runners, executor=None):
        super().__init__(runners)
        self._executor = executor

    def set_executor(self, executor):
        self._executor = executor

    def start(self):
        # Rus each runners in their individual threads.
        if self._executor:
            runners_executor = self._executor
        else:
            runners_executor = self._executor_type(self._max_workers)
        
        # Creates futures from executor(thread pool executor)
        futures = []
        for runner in self._runners:
            future = runners_executor.submit(runner.start)
            futures.append(future)

        # Waits for for futures to complete.
        for future in futures:
            future.result()
        
        # Shutsdown executor if it was created within method.
        if not self._executor:
            runners_executor.shutdown()


class multi_thread_runner(multi_executor_runner):
    _executor_type = futures.ThreadPoolExecutor


class multi_async_runner(multi_parallel_runner):
    def __init__(self, runners, event_loop=None):
        super().__init__(runners)
        self._event_loop = event_loop

    def set_event_loop(self, event_loop):
        self._event_loop = event_loop

    async def astart(self):
        # Runs each runners in their individual threads.        
        tasks = []
        for runner in self._runners:
            if isinstance(runner, async_runner):
                awaitable = asyncio.ensure_future(runner.astart())
            else:
                awaitable = asyncio.to_thread(runner.start)
            tasks.append(asyncio.ensure_future(awaitable))

        # Waits for for futures to complete.
        await asyncio.gather(*tasks, return_exceptions=False)

    def start(self):
        if self._event_loop:
            loop = self._event_loop
        else:
            loop = asyncio.new_event_loop()
        # Runs coroutine/future until it completes.
        loop.run_until_complete(self.astart())

        # Event loop created in this method is closed.
        if not self._event_loop:
            loop.close()



if __name__ == "__main__":
    import broote
    from broote._runner import *

    passwords_field = broote.field("password", lambda: range(10**10))
    usernames_field = broote.field("username", ["Marry", "John", "Ben"]*50)

    table = broote.table()
    table.add_field(passwords_field)
    table.add_primary_field(usernames_field)

    async def success(response):
        # Matches Username "Ben" and Password 1
        return ("Ben" in response) and " 1" in response

    async def success_2(response):
        # Matches Username "Ben" and Password 1
        return ("Marry" in response) and " 1" in response

    async def connect(target, record):
        return "Target is '{}', record is '{}'".format(target, record)

    runner_1 = async_runner("fake target", table, connect=connect,
    max_success_records=1, max_multiple_primary_items=3, success=success,
    max_workers=3)

    runner_2 = async_runner("fake target", table, connect=connect,
    max_success_records=1, max_multiple_primary_items=3, success=success_2,
    max_workers=3)
    
    multi_runner = multi_thread_runner([runner_1, runner_2])
    multi_runner.start()
    print(multi_runner.get_success_records())
