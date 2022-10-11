# broote
Broote is general purpose python bruteforce library built on top of 
[perock](https://github.com/sekgobela-kevin/perock). It aims to make
bruteforcing with python easier and more enjoyable with less code. Everything
will be handled internally with perock letting you focus on what matters.

No more long loops, managing threads or calculating cartesian product
to generate bruteforce data. 
Broote does a good job in handling them without having to worry.  

Steps for using broote library:
- Define bruteforce data e.g passwords or usernames.
- Specify target to bruteforce e.g url, webpage form or file with password.
- Define how to interact/communicate with target(creates responce).
- Define what is considered success, failure or error based on responce.
- Start bruteforce and wait for results.
 
Broote does not create passwords or usernames but they can be generated
with [Brute](https://github.com/rdegges/brute).  
See [perock](https://github.com/sekgobela-kevin/perock) for little more 
about broote library.

> Dont expect broote to perform better than manually written code.


### Install
Broote can be installed with pip in your command-line application.
```bash
pip install broote
```

### Usage
Bruteforce data in broote is represented with fields, records and table.  
```python 
import broote

usernames_field = broote.field("username", ["Ben", "Jackson", "Marry"])
passwords_field = broote.field("password", range(10))

table = broote.table()
table.add_primary_field(usernames_field)
broote.add_field(passwords_field)
```
> See [forcetable](https://github.com/sekgobela-kevin/forcetable) library for 
more about fields, records and table.  

Forcetable library was integrated into broote but can be used directly 
without problems. 

Primary field is important for making bruteforce much
faster. As above, username is expected to be tried with password until 
there is success or run out of passwords.

> Always provide primary field to improve performance.


Target in broote can be anything that points to the system to be 
bruteforced. That can be url to webpage, file path or any type of object. 
What matters is being able to use target to perform bruteforce.

Here how we can connect/interact with target pointed by url and then
return responce.
```python
import requests

def connect_webpage(target, record):
    # target - url to webpage.
    # record - Dict like object with data to pass to request
    return requests.post(target, data=record)

def connect_webpage(target, record, session=None):
    # Session may be valuable to make things faster or share data.
    # session - optional session object.
    return session.post(target, data=record)
```

Let define success and failure functions to define what is considered
successful or failed bruteforce.
```python
import requests

def success(responce):
    return b"logged in as " in responce.content

def failure(responce):
    return b"Username and password does not match" in responce.content
```

Runner is used to execute bruteforce and merge everything together. There
arre different runners some of which are concurrent others running one 
after the other.

`thread_runner` is used to connect/log to website to make things faster.
```python
import broote
import requests

# Defines field to use with table to create records.
usernames_field = broote.field("username", ["Ben", "Jackson", "Marry"])
passwords_field = broote.field("password", range(10))

# Table contains cartesian product of fields as records.
table = broote.table()
table.add_primary_field(usernames_field)
broote.add_field(passwords_field)


def connect_webpage(target, record, session=None):
    # target - url to webpage.
    # record - Dict with data to pass to request.
    # session - optional session object provided by runner.
    return requests.post(target, data=record)

def success(responce):
    return b"logged in as " in responce.content

def failure(responce):
    return b"Username and password does not match" in responce.content


# Creates runner executing in multiple threads.
target = "https://example.com/login"
runner = broote.thread_runner(target, table, connect=connect_webpage,success=success, failure=failure)

# Starts bruteforce into target as defined by connect_webpage().
runner.start()
runner.get_success_records() # [{'username': 'Marry', 'password': 8}]
```
> The url used '[https://example.com/login](https://example.com/login)' does 
not exists.


Runner is too strict when it comes to `target_reached()`, `success()`, 
`failure()` and `target_error()` functions.  

#### Here is what they mean.
```
Target reached - Determines if target was reached after connecting.
Success - Determines if there was success.
Failure - Determines if attempt failed(e.g wrong password)
Target error - Determines if there was error after reaching target.  
             - Target  needs to be reached as this error originates from 
               target.
Client error - Determines if there was error before reaching target.   
             - Target should not be reached and respose should be exception 
             object.
Error - Determines if there was error when connecting to target.  
      - It should satisfy 'target error' and 'client error'.
```


> Responce of `None` wont be allowed and exception object will be taken as 
`client error`.


This shows runner with more functions like `target_reached()` and 
`target_error()` which are also important.
```python
def connect_webpage(target, record):
    # Target - url to webpage.
    # Record - Dict with data to pass to request.
    return requests.post(target, data=record)

def target_reached(responce):
    return self._responce.status_code == 200

def target_error(response):
    return b"denied" in responce.content

def success(responce):
    return b"logged in as " in responce.content

def failure(responce):
    return b"username and password does not match" in responce.content


# Creates runner executing in multiple threads.
target = "https://example.com/login"
runner = broote.thread_runner(
    target, 
    table, 
    connect=connect_webpage,
    target_reached=target_reached, 
    success=success, 
    failure=failure, 
    target_error=target_errror
)

# Starts bruteforce into target as defined by connect_webpage().
runner.start()
runner.get_success_records() # [{'username': 'Marry', 'password': 8}]
```


There are other arguments that can be passed to runner including session
or setting maximum success record.

```
optimize: Bool - Enables optimisations, default True.
               - It makes things faster(better leave it as True)

session: Callable | Any - Callable that creates session or any object
                          to use as session.
                        - If callable then it should be method or function.
                        - It may sometimes be better to share certain
                          object e.g session for web request.

max_retries: int - Sets retries when target is not reached, default 1.
max_success_records: int - Maximum records to match, default None.
max_primary_success_records: int - Not currently used.

max_multiple_primary_items: int - Allows multiple primary items to be be 
                                  tried at same time.
                                - Performs tricks on top of cartesian product
                                  results.
                                - That means multiple usernames tried at
                                  same time.
                                - Becareful if using file field with 
                                  'read_all' argument being False.

compare_func: Callable - Influences how argumnets like 'success' gets
                         intepreted against responce.
                       - It makes it possible to treat the as other objects
                         other than just functions.
                       - e.g lambda: value, responce: value(responce)

after_attempt: Callable - Function called after every attempt.
                        - Great performing something after connecting to
                          target including creating logs.
                        - e.g lambda: record, responce: success(respoce)


# Arguments here are available to some runners.
max_workers: int - Sets maximum workers execute bruteforce, default=10.
                 - Only supported by concurrent runners.
```


This simple code shows ways of using `compare_func` and `after_attempt`
arguments of runner.
```python
def connect_webpage(target, record):
    return requests.post(target, data=record)

def compare_function(value, responce):
    return value in responce.content

def after_attack_function(record, responce):
    if b"logged in as " in responce.content:
        username = record.get_item("username")
        password = record.get_item("password")
        print("Logged in as '{}' with '{}'".format(username, password))

# Creates runner executing in multiple threads.
target = "https://example.com/login"
runner = broote.thread_runner(
    target, 
    table, 
    connect=connect_webpage,
    target_reached=b"example.com", 
    success=b"logged in as ", 
    failure=b"username and password does not match", 
    target_error=b"denied",
    compare_func=compare_function
)
``` 


Here is another example not using requests library with responce being
string created from record.
```python
def success(responce):
    # Matches Username "Ben" and Password 1
    return "John" in responce and "1" in response

def connect(target, record):
    return "Target is '{}', record is '{}'".format(target, record)

def after(record, responce):
    if success((responce):
        print("Success:", record)

runner = broote.basic_runner(
    None, 
    table, 
    connect=connect_webpage,
    success=success,
    after_attack=after
)
```
> `broote.basic_runner` is not concurrent(attempts wait for each other).

Asyncio version is just similar to thread version but difference is that
the functions passed need to be awaitable.
```python
async def success(responce):
    # Matches Username "Ben" and Password 1
    return "John" in responce and "1" in response

async def connect(target, record):
    return "Target is '{}', record is '{}'".format(target, record)


runner = broote.async_runner(
    None, 
    table, 
    connect=connect_webpage,
    success=success,
    max_workers=400
)

# Async runner can be started just like thread runner.
runner.start()
# runner.astart() is awaitable compared to runner.start().
asyncio.run(runner.astart())
```


Broote has capability to execute multiple runner using multi runners.  

That allows multiple different runners to be executed at the same time not
matter the type of runner.

Each multi runner may do things differenly than the others.
`multi_async_runner` will execute runners using asyncio or different 
async thread if runner is not async.
```python
import broote

async_runner = broote.async_runner(...)
thread_runner = broote.basic_runner(...)

multi_runner = multi_async_runner([async_runner, thread_runner])
multi_runner.start()
```
Type of runner does not matter to multi runners. `multi_basic_runner`
can execute `thread_runner` or `async_runner` without problems. Multi
runner can also be used with other multi runner just like regular runner.

Multi ordinary runner is not runner and may not contain some features of 
ordinary runner.

> Remember that each runner runs independent of the others.


### Influenced by:
- [perock](https://github.com/sekgobela-kevin/perock)
- [forcetable](https://github.com/sekgobela-kevin/forcetable)

### Similar to broote
- [instaBrute](https://github.com/chinoogawa/instaBrute)
- [Brute_Force](https://github.com/Matrix07ksa/Brute_Force)
- [Instagram Bruter](https://github.com/Bitwise-01/Instagram-)
- [python-bruteForce](https://github.com/Antu7/python-bruteForce)
- [Multi-Threaded-BruteForcer](https://github.com/nasbench/Multi-Threaded-BruteForcer)
