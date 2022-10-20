import inspect


@staticmethod
def to_coroutine_function(callable_):
    # Create asyncio version of function provided
    if inspect.iscoroutinefunction(callable_):
        return callable_
    else:
        async def wrapper_coro(*args, **kwars):
            return callable_(*args, **kwars)
        return wrapper_coro


def is_method_function(object_):
    # Checks if object is function or method
    return callable(object_)


def extract_value(object_, *args, **kwargs):
    # Extracts return value if object is method or function.
    # If method or function, original object is called.
    if is_method_function(object_):
        return object_(*args, **kwargs)
    else:
        return object_