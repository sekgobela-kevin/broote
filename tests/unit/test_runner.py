from broote import _runner

import broote
import unittest


class TestMethods():
    # Defines passwprds and usernames
    _usernames = ["Ben", "Jackson", "Marry"]
    _passwords = range(5)

    # Success records
    _success_records = [
        {"username": "Ben", "password": 0},
        {"username": "Marry", "password": 1},
        {"username": "Marry", "password": 4},
        {"username": "Jackson", "password": 3}
    ]

    @classmethod
    def connector(cls, target, record, session=None):
        return record

    @classmethod
    def success(cls, response):
        return response in cls._success_records

    @classmethod
    def failure(cls, response):
        return response not in cls._success_records

    @classmethod
    def target_reached(cls, response):
        return True

    @classmethod
    def client_error(cls, response):
        return False

    @classmethod
    def target_error(cls, response):
        return False

    @classmethod
    def comparer(cls, value, response):
        return value(response)

    @classmethod
    def before_connect(cls, target, response):
        pass

    @classmethod
    def after_connect(cls, record, response):
        pass

    @classmethod
    def response_closer(cls, response):
        pass

    @classmethod
    def session_closer(cls, response):
        pass

    @classmethod
    def record_transformer(cls, record):
        return record


class BaseRunnerTest(TestMethods):
    _runner_type = _runner.runner

    @classmethod
    def setUpClass(cls) -> None:

        # Defines field to use with table to create records.
        cls._usernames_field = broote.field("username", cls._usernames)
        cls._passwords_field = broote.field("password", cls._passwords)

        # Table contains cartesian product of fields as records.
        cls._table = broote.table()
        cls._table.add_primary_field(cls._usernames_field)
        cls._table.add_field(cls._passwords_field)

        cls._target = "fake target"

    def setUp(self):
        self._runner = self._runner_type(
            self._target, 
            self._table, 
            connector=self.connector,
            success=self.success,
            target_reached=self.target_reached,
            optimize=False
        )


    def test_setUp(cls) -> None:
        pass

    def test_test_initializer(self):
        runner = self._runner_type(
            "fake target",
            self._table,
            connector=self.connector,
            target_reached=self.target_reached,
            client_error=self.client_error,
            failure=self.failure,
            success=self.success,
            max_success_records=2,
            max_success_primary_items=1,
            max_primary_success_records=2,
            max_multiple_primary_items=2,
            excluded_primary_items=[],
            comparer=self.comparer,
            before_connect=self.before_connect,
            after_connect=self.after_connect,
            response_closer=self.response_closer,
            session_closer=self.session_closer,
            record_transformer=self.record_transformer
        )
        runner.start()

    def test_test_get_table(self):
        self.assertEqual(self._runner.get_table(), self._table)

    def test_is_primary_optimised(self):
        self.assertEqual(self._runner.is_primary_optimised(), False)

    def test_session_exists(self):
        self.assertFalse(self._runner.session_exists())

    def test_set_session(self):
        self._runner.set_session(object())
        self.assertTrue(self._runner.session_exists())

    def test_get_session(self):
        session = object()
        self._runner.set_session(session)
        self.assertEqual(self._runner.get_session(), session)

    def test_get_success_records(self):
        self.assertEqual(self._runner.get_success_records(), [])
        self._runner.start()
        self.assertCountEqual(self._runner.get_success_records(), 
            self._success_records)

    def test_success_exists(self):
        self.assertFalse(self._runner.success_exists())
        self._runner.start()
        self.assertTrue(self._runner.success_exists())


    def test_get_runner_time(self):
        self.assertEqual(self._runner.get_runner_time(), 0)
        self._runner.start()
        self.assertGreaterEqual(self._runner.get_runner_time(), 0)

    def test_is_running(self):
        self.assertFalse(self._runner.is_running())
        self._runner.start()
        self.assertFalse(self._runner.is_running())

    def test_started(self):
        self.assertFalse(self._runner.started())
        self._runner.start()
        self.assertTrue(self._runner.started())

    def test_completed(self):
        self.assertFalse(self._runner.completed())
        self._runner.start()
        self.assertTrue(self._runner.started())

    def test_stop(self):
        self._runner.start()
        self._runner.stop()

    def test_start(self):
        self._runner.start()


class RunnerTest(BaseRunnerTest):
    _runner_type = _runner.basic_runner


class AsyncRunnerTest(BaseRunnerTest, unittest.IsolatedAsyncioTestCase):
    _runner_type = _runner.async_runner
    _runner_test = RunnerTest

    @classmethod
    async def connector(cls, target, record, session=None):
        return super().connector(target, record, session)

    @classmethod
    async def success(cls, response):
        return super().success(response)

    @classmethod
    async def failure(cls, response):
        return super().failure(response)

    @classmethod
    async def target_reached(cls, response):
        return super().target_reached(response)

    @classmethod
    async def client_error(cls, response):
        return super().client_error(response)

    @classmethod
    async def target_error(cls, response):
        return super().target_error(response)

    @classmethod
    async def comparer(cls, value, response):
        return await value(response)
    
class BasicRunnerTest(RunnerTest, unittest.TestCase):
    _runner_type = _runner.basic_runner

class ThreadRUnnerTest(RunnerTest, unittest.TestCase):
    _runner_type = _runner.thread_runner


if __name__ == "__main__":
    unittest.main()