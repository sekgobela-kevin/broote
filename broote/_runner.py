from perock.attack import *
from perock.runner import *

import inspect
import asyncio
from concurrent import futures



__all__ = [
    "runner",
    "basic_runner",
    "parallel_runner",
    "executor_runner",
    "thread_runner",
    "async_runner"
]


class runner():
    _perock_attack_type = Attack
    _perock_runner_type = RunnerBase

    def __init__(    
        self,
        target,
        table,
        connect,
        session=None,
        target_reached=None,
        success=None,
        failure=None,
        target_error=None,
        client_error=None,
        opitimize=True,
        max_retries=1,
        max_success_records=None,
        max_multiple_primary_items=1):
        self._target = target
        self._table = table
        self._session = session
        self._connect = connect
        self._target_reached = target_reached

        self._success = success
        self._failure = failure
        self._target_error = target_error
        self._client_error = client_error

        self._opitimize = opitimize
        self._max_retries = max_retries

        self._attack_type = self.__create_attack_type()
        self._runner = self._perock_runner_type(
            self._attack_type,
            self._target, 
            self._table,
            self._opitimize,
        )

        self._runner.set_max_multiple_primary_items(
            max_multiple_primary_items
        )

        if max_success_records != None:
            self._runner.set_max_success_records(max_success_records)


    def __create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        class attack(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            @classmethod
            def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session != None:
                    is_function = inspect.isfunction(self_._session)
                    if is_function and inspect.ismethod(self_._session):
                        return self_._session()
                    return self_._session
                return super().create_session()

            def request(self):
                if self._session != None:
                    responce = self_._connect(self_._target, self._data,
                    self._session)
                else:
                    responce = self_._connect(self_._target, self._data)
                return responce
            
            def target_reached(self):
                if self_._target_reached:
                    return self_._target_reached(self._responce)
                return super().target_reached()

            def success(self):
                if self_._success:
                    return self_._success(self._responce)
                return super().success()

            def failure(self):
                if self_._failure:
                    return self_._failure(self._responce)
                return super().failure()

            def client_errors(self):
                if self_._client_error:
                    return self_._client_error(self._responce)
                return super().client_errors()

            def target_errors(self):
                if self_._target_error:
                    return self_._target_error(self._responce)
                return super().target_errors()  
        return attack

    def get_success_records(self):
        return self._runner.get_success_records()

    def success_exists(self):
        return bool(self._runner.get_success_records())

    def start(self):
        return self._runner.run()
    

class basic_runner(runner):
    _perock_runner_type = RunnerBlock


class parallel_runner(runner):
    _perock_runner_type = RunnerParallel

    def __init__(self, target, table, connect, max_workers=10, **kwargs):
        super().__init__(target, table, connect, **kwargs)
        # Number of workers should match number of paralel tasks.
        # This can improve performance(especially waiting for tasks)
        self._runner.set_max_workers(max_workers)
        self._runner.set_max_parallel_tasks(max_workers)


class executor_runner(parallel_runner):
    _perock_runner_type = RunnerExecutor

    def set_executor(self, executor):
        '''Sets executor to use to execute tasks'''
        self._runner.set_executor(executor)


class thread_runner(executor_runner):
    _perock_runner_type = RunnerThread
    

class async_runner(parallel_runner):
    _perock_attack_type = AttackAsync
    _perock_runner_type = RunnerAsync

    def __init__(self, target, table, connect, max_workers=200, **kwargs):
        super().__init__(target, table, connect, max_workers=max_workers,
        **kwargs)
        self._event_loop = None

    def __create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        class attack_async(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            @classmethod
            async def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session != None:
                    is_function = inspect.isfunction(self_._session)
                    if is_function and inspect.ismethod(self_._session):
                        return await self_._session()
                    return self_._session
                return await super().create_session()

            async def request(self):
                if self._session != None:
                    responce = await self_._connect(self_._target, 
                    self._data, self._session)
                else:
                    responce = await self_._connect(self_._target, self._data)
                return responce
            
            async def target_reached(self):
                if self_._target_reached:
                    return await self_._target_reached(self._responce)
                return await super().target_reached()

            async def success(self):
                if self_._success:
                    return await self_._success(self._responce)
                return await super().success()

            async def failure(self):
                if self_._failure:
                    return await self_._failure(self._responce)
                return await super().failure()

            async def client_errors(self):
                if self_._client_error:
                    return await self_._client_error(self._responce)
                return await super().client_errors()

            async def target_errors(self):
                if self_._target_error:
                    return await self_._target_error(self._responce)
                return await super().target_errors()  
        return attack_async

    def set_event_loop(self, event_loop):
        self._event_loop = event_loop

    async def astart(self):
        await self._runner.run()

    def start(self):
        if self._event_loop:
            loop = self._event_loop
        else:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                new_loop = True
                loop = asyncio.new_event_loop()    
        loop.run_until_complete(self._runner.run())
        if not self._event_loop:
            loop.close()



if __name__ == "__main__":
    import broote

    passwords_field = broote.field("password", lambda: range(10**10))
    usernames_field = broote.field("username", ["Marry", "John", "Ben"]*50)

    table = broote.table()
    table.add_field(passwords_field)
    table.add_primary_field(usernames_field)

    async def success(response):
        # Matches Username "Ben" and Password 1
        return ("Ben" in response) and " 1" in response

    async def connect(target, record):
        return "Target is '{}', record is '{}'".format(target, record)

    runner_ = async_runner("fake target", table, connect=connect,
    max_success_records=1, max_multiple_primary_items=3, success=success,
    max_workers=10)
    runner_.start()
    print(runner_.get_success_records())
