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
    '''Performs bruteforce on records from provided table'''
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
        optimize=True,
        max_retries=1,
        max_success_records=None,
        max_success_primary_items=1,
        max_primary_success_records=1,
        max_multiple_primary_items=1,
        excluded_primary_items=None,
        compare_func=None,
        after_attempt=None):
        self._target = target
        self._table = table
        self._session = session
        self._connect = connect
        self._target_reached = target_reached

        self._success = success
        self._failure = failure
        self._target_error = target_error
        self._client_error = client_error

        self._optimize = optimize
        self._max_retries = max_retries

        self._compare_func = compare_func
        self._after_attempt = after_attempt


        # Dont store arguments after here.
        self._attack_type = self._create_attack_type()
        self._runner = self._perock_runner_type(
            self._attack_type,
            self._target, 
            self._table,
            self._optimize,
        )

        self.set_max_multiple_primary_items(max_multiple_primary_items)
        self.set_max_primary_success_records(max_primary_success_records)

        if max_success_records is not None:
            self.set_max_success_records(max_success_records)
        if max_success_primary_items is not None:
            self.set_max_success_primary_items(max_success_primary_items)
        if excluded_primary_items is not None:
            self.add_excluded_primary_items(excluded_primary_items)


    def _create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        class attack(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            def compare(self, value):
                return self_._compare_func(value, self._responce)

            @classmethod
            def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session != None:
                    is_function = inspect.isfunction(self_._session)
                    if is_function or inspect.ismethod(self_._session):
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
                    if self_._compare_func:
                        return self.compare(self_._target_reached)
                    else:
                        return self_._target_reached(self._responce)
                return super().target_reached()

            def success(self):
                if self_._success:
                    if self_._compare_func:
                        return self.compare(self_._success)
                    else:
                        return self_._success(self._responce)
                return super().success()

            def failure(self):
                if self_._failure:
                    if self_._compare_func:
                        return self.compare(self_._failure)
                    else:
                        return self_._failure(self._responce)
                return super().failure()

            def client_errors(self):
                if self_._client_error:
                    if self_._compare_func:
                        return self.compare(self_._client_error)
                    else:
                        return self_._client_error(self._responce)
                return super().client_errors()

            def target_errors(self):
                if self_._target_error:
                    if self_._compare_func:
                        return self.compare(self_._target_error)
                    else:
                        return self_._target_error(self._responce)
                return super().target_errors()

            def after_request(self):
                if self_._after_attempt:
                    self_._after_attempt(self._data, self._responce)
        return attack

    def set_max_success_records(self, total):
        '''Sets maximum success records to cancel/stop attack'''
        self._runner.set_max_success_records(total)

    def set_max_multiple_primary_items(self, total):
        '''Set maximum primary items to execute in parrallel'''
        self._runner.set_max_multiple_primary_items(total)

    def set_max_success_primary_items(self, total):
        '''Set maximum primary items with success record'''
        self._runner.set_max_success_primary_items(total)
    
    def set_max_primary_success_records(self, total):
        '''Set maximum success records for each primary item'''
        self._runner.set_max_primary_item_success_records(total)

    def add_excluded_primary_item(self, primary_item):
        '''Adds primary field item to be excluded'''
        self._runner.add_excluded_primary_items(primary_item)

    def add_excluded_primary_items(self, primary_items):
        '''Adds primary field items to be excluded'''
        for primary_item in primary_items:
            self.add_excluded_primary_item(primary_item)

    def remove_excluded_primary_item(self, primary_item):
        '''Removes primary field item from excluded primary field'''
        self._runner.remove_excluded_primary_items(primary_item)


    def get_excluded_primary_items(self):
        '''Gets excluded primary field items'''
        return self._runner.get_excluded_primary_items()

    def get_table(self):
        '''Gets table with records to bruteforce.'''
        return self._runner.get_table()

    def is_primary_optimised(self):
        '''Checks primary if optimations are enabled.'''
        return self._runner.is_primary_optimised()

    def session_exists(self):
        '''Checks if session exists'''
        return self._runner.session_exists()

    def set_session(self, session):
        '''Sets session object to be used with runner'''
        return self._runner.set_session(session)

    def get_session(self):
        '''Gets session object used by runner'''
        return self._runner.get_session()

    def create_session(self, *args, **kwargs):
        '''Create session exatly as runner would create it'''
        return self._runner.create_session(*args, **kwargs)

    def get_success_records(self):
        '''Gets successfuly bruteforced records'''
        return self._runner.get_success_records()

    def success_exists(self):
        '''Checks if there was success in one of records'''
        return bool(self._runner.get_success_records())


    def get_runner_time(self):
        '''Gets elapsed time of runner'''
        return self._runner.get_runner_time()

    def is_running(self):
        '''Checks if runner is currently running'''
        return self._runner.is_running()

    def started(self):
        '''Checks if runner if runner was ever started running'''
        return self._runner.started()

    def completed(self):
        '''Checks if runner if runner completed running'''
        return self._runner.completed()

    def stop(self):
        '''Stops runner and terminate any pending records.'''
        return self._runner.stop()

    def start(self):
        '''Starts bruteforce'''
        try:
            return self._runner.run()
        except KeyboardInterrupt as e:
            raise e


class basic_runner(runner):
    '''Performs bruteforce on table synchronously'''
    _perock_runner_type = RunnerBlock


class parallel_runner(runner):
    '''Performs bruteforce on table concurrenctly or in parallel'''
    _perock_runner_type = RunnerParallel

    def __init__(self, target, table, connect, max_workers=10, **kwargs):
        super().__init__(target, table, connect, **kwargs)
        # Number of workers should match number of paralel tasks.
        # This can improve performance(especially waiting for tasks)
        self._runner.set_max_workers(max_workers)
        self._runner.set_max_parallel_tasks(max_workers)


class executor_runner(parallel_runner):
    '''Performs bruteforce on table using executor'''
    _perock_runner_type = RunnerExecutor

    def set_executor(self, executor):
        '''Sets executor to use to execute tasks'''
        self._runner.set_executor(executor)


class thread_runner(executor_runner):
    '''Performs bruteforce on table using threads'''
    _perock_runner_type = RunnerThread
    

class async_runner(parallel_runner):
    '''Performs bruteforce on table using asyncronously(asyncio)'''
    _perock_attack_type = AttackAsync
    _perock_runner_type = RunnerAsync

    def __init__(self, target, table, connect, max_workers=200, **kwargs):
        super().__init__(target, table, connect, max_workers=max_workers,
        **kwargs)
        self._event_loop = None

    def _create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        cmp_func_is_async = inspect.iscoroutinefunction(self_._compare_func)
        after_attempt_async = inspect.iscoroutinefunction(
            self_._after_attempt
        )
        class attack_async(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            async def compare(self, value):
                results = self_._compare_func(value, self._responce)
                if cmp_func_is_async:
                    return await results
                else:
                    return results

            @classmethod
            async def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session != None:
                    is_function = inspect.isfunction(self_._session)
                    if is_function or inspect.ismethod(self_._session):
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
                    if self_._compare_func:
                        return await self.compare(self_._target_reached)
                    return await self_._target_reached(self._responce)
                return await super().target_reached()

            async def success(self):
                if self_._success:
                    if self_._compare_func:
                        return await self.compare(self_._success)
                    return await self_._success(self._responce)
                return await super().success()

            async def failure(self):
                if self_._failure:
                    if self_._compare_func:
                        return await self.compare(self_._failure)
                    return await self_._failure(self._responce)
                return await super().failure()

            async def client_errors(self):
                if self_._client_error:
                    if self_._compare_func:
                        return await self.compare(self_._client_error)
                    return await self_._client_error(self._responce)
                return await super().client_errors()

            async def target_errors(self):
                if self_._target_error:
                    if self_._compare_func:
                        return await self.compare(self_._target_error)
                    return await self_._target_error(self._responce)
                return await super().target_errors()  

            async def after_request(self):
                if self_._after_attempt:
                    output = self_._after_attempt(self._data, self._responce)
                    if after_attempt_async:
                        await output
        return attack_async

    def set_event_loop(self, event_loop):
        '''Sets event loop to use with .start() method'''
        self._event_loop = event_loop

    async def astart(self):
        '''Starts bruteforce(coroutine)'''
        await self._runner.run()

    def start(self):
        '''Starts bruteforce'''
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

    passwords_field = broote.field("password", lambda: range(10**10))
    usernames_field = broote.field("username", ["Marry", "John", "Ben"])

    table = broote.table()
    table.add_field(passwords_field)
    table.add_primary_field(usernames_field)

    def success(response):
        # Matches Username "Ben" and Password 1
        return ("Ben" in response) and "1" in response

    def connect(target, record):
        return "Target is '{}', record is '{}'".format(target, record)

    def after(record, responce):
        print(responce)

    runner_ = basic_runner("fake target", table, connect=connect,
    max_success_records=1, max_multiple_primary_items=3, success=success,
    optimize=True, after_attempt=after)
    runner_.start()
    print(runner_.get_success_records())
