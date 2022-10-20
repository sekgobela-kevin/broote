from perock import attack as attack_mod
from perock import runner as runner_mod
from broote import _util

import asyncio



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
    _perock_attack_type = attack_mod.Attack
    _perock_runner_type = runner_mod.RunnerBase

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
        max_retries=None,
        max_success_records=None,
        max_success_primary_items=None,
        max_primary_success_records=None,
        max_multiple_primary_items=None,
        excluded_primary_items=None,
        compare_func=None,
        before_connect=None,
        after_attempt=None,
        after_connect=None,
        response_closer=None,
        session_closer=None,
        record_tranformer=None):
        self._target = target
        self._table = table
        self._session = session
        self._connector = connect
        self._target_reached = target_reached

        self._success = success
        self._failure = failure
        self._target_error = target_error
        self._client_error = client_error

        self._optimize = optimize
        self._max_retries = max_retries if max_retries is not None else 0

        self._before_connect = before_connect
        self._after_connect = after_connect or after_attempt
        self._response_closer = response_closer
        self._session_closer = session_closer

        self._record_tranformer = record_tranformer
        self._comparer = compare_func


        # Dont store arguments after here.
        self._attack_type = self._create_attack_type()
        self._runner = self._perock_runner_type(
            self._attack_type,
            self._target, 
            self._table,
            self._optimize,
        )

        if max_multiple_primary_items is not None:
            self.set_max_multiple_primary_items(max_multiple_primary_items)
        if max_primary_success_records is not None:
            self.set_max_primary_success_records(max_primary_success_records)

        if max_success_records is not None:
            self.set_max_success_records(max_success_records)
        if max_success_primary_items is not None:
            self.set_max_success_primary_items(max_success_primary_items)
        if excluded_primary_items is not None:
            self.add_excluded_primary_items(excluded_primary_items)


        # Performs transformation on some attributes
        if self._session is not None:
            if not _util.is_method_function(self._session):
                self._session = lambda: self._session

        if success is None and failure is None:
            err_msg = "'Success' or 'Failure' is required by runner"
            raise ValueError(err_msg)


    def _create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        class attack(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            def compare(self, value):
                # Defines how argument like success get compared to response
                return self_._comparer(value, self._responce)

            @classmethod
            def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session is not None:
                    return _util.extract_value(self_._session)

            def request(self):
                # Peforms connection to target returning response
                if self._session is not None:
                    responce = self_._connector(self_._target, self._data,
                    self._session)
                else:
                    responce = self_._connector(self_._target, self._data)
                return responce
            
            def target_reached(self):
                # Checks if target was reached
                if self_._target_reached:
                    if self_._comparer:
                        return self.compare(self_._target_reached)
                    else:
                        return self_._target_reached(self._responce)
                # Tries to guess if target was reached.
                return super().target_reached()

            def success(self):
                # Checks if there was success
                if self_._success:
                    if self_._comparer:
                        return self.compare(self_._success)
                    else:
                        return self_._success(self._responce)
                else:
                    # Tries to guess if there is success.
                    if self.target_reached():
                        return not (self.target_errors() or self.failure())
                    else:
                        return False

            def failure(self):
                # Checks if there was failure(opposite of success)
                if self_._failure:
                    if self_._comparer:
                        return self.compare(self_._failure)
                    else:
                        return self_._failure(self._responce)
                return super().failure()

            def client_errors(self):
                # Checks if there was client error(likely exception)
                if self_._client_error:
                    if self_._comparer:
                        return self.compare(self_._client_error)
                    else:
                        return self_._client_error(self._responce)
                return super().client_errors()

            def target_errors(self):
                # Checks if there was error after target was reached
                if self_._target_error:
                    if self_._comparer:
                        return self.compare(self_._target_error)
                    else:
                        return self_._target_error(self._responce)
                return super().target_errors()

            def before_request(self):
                # Method called before connecting to target.
                super().before_request()
                if self_._record_tranformer is not None:
                    # Avoid tranforming record multiple times
                    token = "__trans_tok_attria"
                    if not hasattr(self, token):
                        # Data/record is replaced by transformed one.
                        self._data = self_._record_tranformer(self._data)
                        setattr(self, token, False)
                if self_._before_connect is not None:
                    self_._before_connect(self._data, self._responce)

            def after_request(self):
                # Method called after connecting to target.
                super().after_request()
                if self_._after_connect:
                    self_._after_connect(self._data, self._responce)

            @classmethod
            def close_session(cls, session):
                # Closes session object to free resources
                if self_._session_closer is not None:
                    self_._session_closer(session)

            @classmethod
            def close_responce(cls, response):
                # Closes response object to free resources
                if self_._response_closer is not None:
                    self_._response_closer(response)

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
        self._runner.set_max_primary_success_records(total)

    def add_excluded_primary_item(self, primary_item):
        '''Adds primary field item to be excluded'''
        self._runner.add_excluded_primary_item(primary_item)

    def add_excluded_primary_items(self, primary_items):
        '''Adds primary field items to be excluded'''
        self._runner.add_excluded_primary_items(primary_items)

    def remove_excluded_primary_item(self, primary_item):
        '''Removes primary field item from excluded primary items'''
        self._runner.remove_excluded_primary_item(primary_item)

    def remove_excluded_primary_items(self, primary_items):
        '''Removes primary field items from excluded primary items'''
        self._runner.remove_excluded_primary_items(primary_items)


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
    _perock_runner_type = runner_mod.RunnerBlock


class parallel_runner(runner):
    '''Performs bruteforce on table concurrenctly or in parallel'''
    _perock_runner_type = runner_mod.RunnerParallel
    _default_max_workers = 15

    def __init__(self, target, table, connect, max_workers=None, **kwargs):
        super().__init__(target, table, connect, **kwargs)
        # Setups max-workers incase it was not provided.
        if max_workers is None:
            max_workers = self._default_max_workers
        # Number of workers should match number of paralel tasks.
        # This can improve performance(especially waiting for tasks)
        self._runner.set_max_workers(max_workers)
        self._runner.set_max_parallel_tasks(max_workers)


class executor_runner(parallel_runner):
    '''Performs bruteforce on table using executor'''
    _perock_runner_type = runner_mod.RunnerExecutor

    def set_executor(self, executor):
        '''Sets executor to use to execute tasks'''
        self._runner.set_executor(executor)


class thread_runner(executor_runner):
    '''Performs bruteforce on table using threads'''
    _perock_runner_type = runner_mod.RunnerThread
    

class async_runner(parallel_runner):
    '''Performs bruteforce on table using asyncronously(asyncio)'''
    _perock_attack_type = attack_mod.AttackAsync
    _perock_runner_type = runner_mod.RunnerAsync

    def __init__(self, target, table, connect, **kwargs):
        if kwargs.get("max_workers", None) is None:
            kwargs["max_workers"] = 400
        super().__init__(target, table, connect, **kwargs)
        
        # Ensures that callable attributes are awaitable.
        # Some callables may not be awaitable but they need to.
        if _util.is_method_function(self._after_connect):
            self._after_connect = _util.to_coroutine_function(
                self._after_connect)

        if _util.is_method_function(self._before_connect):
            self._before_connect = _util.to_coroutine_function(
                self._before_connect)

        if _util.is_method_function(self._session):
            self._session = _util.to_coroutine_function(self._session)

        if _util.is_method_function(self._comparer):
            self._comparer = _util.to_coroutine_function(
                self._comparer)

        if _util.is_method_function(self._session_closer):
            self._session_closer = _util.to_coroutine_function(
                self._session_closer)

        if _util.is_method_function(self._response_closer):
            self._response_closer = _util.to_coroutine_function(
                self._response_closer)

        if _util.is_method_function(self._record_tranformer):
            self._record_tranformer = _util.to_coroutine_function(
                self._record_tranformer)

        self._event_loop = None


    def _create_attack_type(self):
        # Creates attack class from corresponding perock attack class.
        self_ = self # Stores runner instance to use within attack.
        class attack_async(self_._perock_attack_type):
            def __init__(self, target, record) -> None:
                super().__init__(target, record, self_._max_retries)

            async def compare(self, value):
                # Defines how argument like success get compared to response
                return await self_._comparer(value, self._responce)

            @classmethod
            async def create_session(cls):
                # Creates session object to use when connecting with target
                if self_._session is not None:
                    return await self_._session()

            async def request(self):
                # Connects to target and returns response.
                if self._session is not None:
                    responce = await self_._connector(self_._target, 
                    self._data, self._session)
                else:
                    responce = await self_._connector(self_._target, self._data)
                return responce
            
            async def target_reached(self):
                # Checks if target was reached.
                if self_._target_reached is not None:
                    if self_._comparer:
                        return await self.compare(self_._target_reached)
                    return await self_._target_reached(self._responce)
                return await super().target_reached()

            async def success(self):
                # Checks if there was success.
                if self_._success is not None:
                    if self_._comparer:
                        return await self.compare(self_._success)
                    return await self_._success(self._responce)
                else:
                    # Tries to guess if there was success.
                    # .failure() should not use .success()(avoid recursion)
                    if await self.target_reached():
                        if await self.failure():
                            return False
                        elif await self.target_errors():
                            return False
                    return False

            async def failure(self):
                # Checks if target was failure(opposite of success)
                if self_._failure is not None:
                    if self_._comparer:
                        return await self.compare(self_._failure)
                    return await self_._failure(self._responce)
                return await super().failure()

            async def client_errors(self):
                # Checks if there client error(likely exception response).
                if self_._client_error is not None:
                    if self_._comparer:
                        return await self.compare(self_._client_error)
                    return await self_._client_error(self._responce)
                return await super().client_errors()

            async def target_errors(self):
                # Checks if there was error after reaching target.
                if self_._target_error is not None:
                    if self_._comparer:
                        return await self.compare(self_._target_error)
                    return await self_._target_error(self._responce)
                return await super().target_errors()  

            async def before_request(self):
                # Checks if there was error after reaching target.
                await super().before_request()
                if self_._record_tranformer is not None:
                    # Avoid tranforming record multiple times
                    token = "__trans_tok_attria"
                    if not hasattr(self, token):
                        # Data/record is replaced by transformed one.
                        self._data = await self_._record_tranformer(
                            self._data)
                        setattr(self, token, False)
                if self_._before_connect is not None:
                    # Realise that record/data is overiden.
                    await self_._before_connect(self._data)

            async def after_request(self):
                # Method called after connecting to target.
                await super().after_request()
                if self_._after_connect is not None:
                   await self_._after_connect(self._data, self._responce)

            @classmethod
            async def close_session(cls, session):
                if self_._session_closer is not None:
                    await self_._session_closer(session)

            @classmethod
            async def close_responce(cls, response):
                if self_._response_closer is not None:
                    await self_._response_closer(response)
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
        print(record)

    def record_transformer(record):
        return tuple(record.values())

    runner_ = basic_runner("fake target", table, connect=connect,
    max_success_records=1, max_multiple_primary_items=3, success=success,
    optimize=True, after_attempt=after, record_tranformer=record_transformer)
    runner_.start()
    print(runner_.get_success_records())
