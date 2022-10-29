

class Response():
    def __init__(
        self, 
        target_reached=False,
        target_error=False,
        client_error=False,
        failure=False,
        success=False,
        denied=False,
        ) -> None:
        self.target_not_connected_msg = "Target not connected"
        self.target_not_reached_msg = "Target not reached"
        self.target_error_msg = "Target has experienced errors"
        self.client_error_msg = "Something is wrong with client request"
        self.denied_error_msg = "Access to target was denied"
        self.success_message = "Logged in to system"
        self.failure_message = "Provided credentials are not valid"

        #self.target_connected = target_connected
        self.target_error = target_error
        self.target_reached = target_reached
        self.client_error = client_error
        self.target_error = target_error
        self.denied_error = denied
        self.failure = failure
        self.success = success

        self.closed = False

    def message(self):
        if self.client_error:
            return self.client_error_msg
        elif self.denied_error:
            return self.denied_error_msg
        elif self.target_error:
            return self.target_error_msg
        elif self.success:
            return self.success_message
        elif self.failure:
            return self.failure_message
        elif self.self.target_not_reached_msg:
            return self.target

    def close(self):
        self.closed = True

    async def aclose(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()



class BaseSession():
    def __init__(self, *args, **kwargs) -> None:
        self.closed = False

    def connect(self, **kwargs):
        if not self.closed:
            return Response(**kwargs)
        raise RuntimeError("Session closed")


class Session(BaseSession):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AsyncSession(BaseSession):
    async def aclose(self):
        self.close()

    async def connect(self, **kwargs):
        return super().connect(**kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
