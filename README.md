# 🫏 mule

**Add a stubborn streak to your code.**

Mule is a powerful, lightweight Python library for implementing robust retry logic with comprehensive control over attempt patterns, waiting strategies, and lifecycle hooks. Unlike other retry libraries, mule provides fine-grained control over every aspect of the retry process while maintaining simplicity for common use cases.

## ✨ Why Choose Mule?

- **🎯 Precise Control**: Fine-grained control over retry conditions, timing, and behavior
- **🔧 Flexible Usage**: Supports both sync and async functions and code blocks
- **🪝 Plugable Lifecycle Hooks**: Monitor and react to every phase of the retry lifecycle
- **🧩 Composable Conditions**: Combine stop conditions with logical operators (`&`, `|`, `~`)
- **⚡ Minimal Dependencies**: Only requires `typing-extensions`
- **🔒 Type Safe**: Full type hints with `mypy` and `pyright` compatibility

## 🚀 Quick Start

### Installation

```bash
pip install mule-lib
```

### Basic Usage

```python
import requests
from mule import retry
from mule.stop_conditions import AttemptsExhausted

@retry(until=AttemptsExhausted(3))
def unreliable_api_call():
    # This will retry up to 3 times on any exception
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()

result = unreliable_api_call()
```

## 📚 Core Concepts

### Stop Conditions

Stop conditions determine when to stop retrying. Mule provides several built-in conditions:

#### `AttemptsExhausted(max_attempts)`
Stop after a fixed number of attempts:

```python
import random
from mule import retry
from mule.stop_conditions import AttemptsExhausted

@retry(until=AttemptsExhausted(5))
def flaky_function():
    # Will retry up to 5 times
    if random.random() < 0.7:
        raise ValueError("Random failure")
    return "success"
```

#### `ExceptionMatches(exception_type)`
Stop when a specific exception type is raised:

```python
from mule import retry
from mule.stop_conditions import ExceptionMatches

def should_fail_critically():
    return False  # Example implementation

def should_fail_temporarily():
    return True  # Example implementation

@retry(until=ExceptionMatches(ValueError))
def critical_operation():
    # Stops immediately if ValueError is raised
    # Continues retrying for other exceptions
    if should_fail_critically():
        raise ValueError("Critical error - don't retry")
    elif should_fail_temporarily():
        raise ConnectionError("Temporary error - will retry")
    return "success"
```

#### `NoException()`
Stop when no exception is raised (used by default):

```python
import random
from mule import retry

@retry
def eventually_succeeds():
    # Retries indefinitely until success
    if random.random() < 0.9:
        raise Exception("Still failing")
    return "finally worked!"
```

### Composable Stop Conditions

Combine conditions using logical operators:

```python
from mule import retry
from mule.stop_conditions import AttemptsExhausted, ExceptionMatches

# Stop if we've tried 5 times OR if we get a ValueError
@retry(until=AttemptsExhausted(5) | ExceptionMatches(ValueError))
def complex_retry():
    pass

# Stop if we get a ValueError AND we've tried at least 3 times
@retry(until=ExceptionMatches(ValueError) & AttemptsExhausted(3))
def another_example():
    pass

# Retry as long as we DON'T get a ValueError (inversion with ~)
@retry(until=~ExceptionMatches(ValueError))
def invert_example():
    pass
```

### Wait Strategies

Control the delay between retry attempts:

#### Fixed Wait Time

```python
import datetime
from mule import retry
from mule.stop_conditions import AttemptsExhausted

# Wait 5 seconds between attempts
@retry(until=AttemptsExhausted(3), wait=5)
def with_fixed_wait():
    pass

# Using timedelta for more precision
@retry(until=AttemptsExhausted(3), wait=datetime.timedelta(seconds=2.5))
def with_timedelta_wait():
    pass
```

#### Dynamic Wait Strategies

```python
from mule import retry
from mule.stop_conditions import AttemptsExhausted

# Exponential backoff
def exponential_backoff(prev_state, next_state):
    return min(2 ** (next_state.attempt - 1), 60)  # Cap at 60 seconds

@retry(until=AttemptsExhausted(5), wait=exponential_backoff)
def with_exponential_backoff():
    pass

# Linear backoff
def linear_backoff(prev_state, next_state):
    return next_state.attempt * 2  # 2s, 4s, 6s, 8s...

@retry(until=AttemptsExhausted(4), wait=linear_backoff)
def with_linear_backoff():
    pass

# Fibonacci backoff
def fibonacci_backoff(prev_state, next_state):
    a, b = 1, 1
    for _ in range(next_state.attempt - 1):
        a, b = b, a + b
    return a

@retry(until=AttemptsExhausted(8), wait=fibonacci_backoff)
def with_fibonacci_backoff():
    pass
```

## 🔄 Async Support

Mule provides identical functionality for async functions:

```python
import asyncio
import httpx
from mule import retry
from mule.stop_conditions import AttemptsExhausted

@retry(until=AttemptsExhausted(3), wait=1)
async def async_api_call():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        response.raise_for_status()
        return response.json()

result = asyncio.run(async_api_call())
```

## 🔁 Retrying Code Blocks

When you need to retry code that depends on external context or state, the `@retry` decorator can be limiting. Mule provides `attempting` and `attempting_async` to retry arbitrary code blocks while preserving access to local variables, instance state, and complex control flow:

### Access External Context with `attempting`

```python
import random
from mule import attempting
from mule.stop_conditions import AttemptsExhausted

# Example: Retry with access to local variables and external state
user_id = 12345
session_token = "abc123"
max_retries = 3

for attempt in attempting(until=AttemptsExhausted(max_retries), wait=1):
    with attempt:
        # Full access to external context
        if not session_token:
            raise ValueError("No session token")
            
        # Complex logic that needs external state
        if random.random() < 0.7:
            raise ConnectionError(f"Failed to process user {user_id}")
        
        result = f"Processed user {user_id} with token {session_token}"
        attempt.result = result
        break

print(f"Final result: {result}")
```

### Retry Within Class Methods

```python
import json
import sqlite3
from mule import attempting
from mule.stop_conditions import AttemptsExhausted, ExceptionMatches

class UserManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.retry_count = 0
    
    def get_user_count(self):
        # Retry while accessing instance variables
        for attempt in attempting(
            until=AttemptsExhausted(3) | ExceptionMatches(ValueError), 
            wait=2
        ):
            with attempt:
                self.retry_count += 1  # Modify instance state
                
                # Use instance variables
                conn = sqlite3.connect(self.db_path)
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                
                if count < 0:
                    raise ValueError("Invalid count")
                
                attempt.result = count
                conn.close()
                return count

manager = UserManager("users.db")
count = manager.get_user_count()
print(f"User count: {count}, Retries: {manager.retry_count}")
```

### Async Code Blocks with External Context

```python
import asyncio
import random
import httpx
from mule import attempting_async
from mule.stop_conditions import AttemptsExhausted

async def fetch_user_data(user_id: int, api_key: str):
    # Retry with access to function parameters and local variables
    headers = {"Authorization": f"Bearer {api_key}"}
    retries_made = 0
    
    async for attempt in attempting_async(until=AttemptsExhausted(3), wait=1):
        async with attempt:
            retries_made += 1  # Modify local variable
            
            async with httpx.AsyncClient() as client:
                if random.random() < 0.6:
                    raise httpx.ConnectError(f"Connection failed for user {user_id}")
                
                # Use external context (parameters, headers)
                response = await client.get(
                    f"https://api.example.com/users/{user_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                data["retries_made"] = retries_made
                attempt.result = data
                return data

# Usage with external context
user_id = 123
api_key = "secret-key"
result = asyncio.run(fetch_user_data(user_id, api_key))
```

### Complex Control Flow

```python
import random
from mule import attempting
from mule.stop_conditions import AttemptsExhausted

def process_batch(items: list, batch_size: int = 10):
    processed = []
    
    # Retry processing batches with complex control flow
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        for attempt in attempting(until=AttemptsExhausted(3), wait=1):
            with attempt:
                # Process batch with access to loop variables
                batch_result = []
                
                for item in batch:
                    if random.random() < 0.1:  # 10% failure rate
                        raise Exception(f"Failed to process item {item}")
                    
                    batch_result.append(f"processed_{item}")
                
                # Success - add to main list
                processed.extend(batch_result)
                break  # Exit retry loop, continue with next batch
    
    return processed

items = list(range(25))
result = process_batch(items, batch_size=5)
print(f"Processed {len(result)} items")
```

## 🪝 Lifecycle Hooks

Monitor and react to retry lifecycle events:

```python
import random
from mule import retry
from mule.stop_conditions import AttemptsExhausted
from mule._attempts.dataclasses import AttemptState

@retry(until=AttemptsExhausted(3), wait=1)
def monitored_function():
    if random.random() < 0.7:
        raise Exception("Random failure")
    return "success"

@monitored_function.before_attempt
def log_attempt_start(state: AttemptState):
    print(f"Starting attempt {state.attempt}")

@monitored_function.on_failure
def log_failure(state: AttemptState):
    print(f"Attempt {state.attempt} failed: {state.exception}")

@monitored_function.on_success
def log_success(state: AttemptState):
    print(f"Success on attempt {state.attempt}! Result: {state.result}")

@monitored_function.before_wait
def log_wait_start(state: AttemptState):
    print(f"Waiting {state.wait_seconds}s before attempt {state.attempt}")

@monitored_function.after_wait
def log_wait_end(state: AttemptState):
    print(f"Finished waiting, starting attempt {state.attempt}")

result = monitored_function()
```

### Async Hooks

Hooks can be async functions too, and they work seamlessly with both sync and async decorated functions:

```python
from mule import retry
from mule.stop_conditions import AttemptsExhausted

async def some_async_logging(state):
    pass  # Example implementation

async def notify_monitoring_system(exception):
    pass  # Example implementation

@retry(until=AttemptsExhausted(3))
def sync_function():
    return "result"

@sync_function.on_success
async def async_hook(state):
    # This async hook works with the sync function
    await some_async_logging(state)

# Also works with async functions
@retry(until=AttemptsExhausted(3))
async def async_function():
    return "result"

@async_function.on_failure
async def async_failure_hook(state):
    await notify_monitoring_system(state.exception)
```

## 🎯 Advanced Examples

### Database Operations with Retry

```python
import sqlite3
from mule import retry
from mule.stop_conditions import AttemptsExhausted, ExceptionMatches

@retry(
    until=AttemptsExhausted(3) | ExceptionMatches(sqlite3.IntegrityError),
    wait=0.5
)
def insert_user(name: str, email: str):
    conn = sqlite3.connect("users.db")
    try:
        conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (name, email)
        )
        conn.commit()
    except sqlite3.OperationalError:
        # Retry on operational errors (database locked, etc.)
        conn.close()
        raise
    except sqlite3.IntegrityError:
        # Don't retry on integrity errors (duplicate email, etc.)
        conn.close()
        raise
    finally:
        conn.close()
```

### HTTP Client with Circuit Breaker Pattern

```python
import requests
from mule import retry
from mule.stop_conditions import AttemptsExhausted, ExceptionMatches

class CircuitBreakerOpen(Exception):
    pass

failure_count = 0
max_failures = 5

@retry(until=AttemptsExhausted(3) | ExceptionMatches(CircuitBreakerOpen))
def api_call_with_circuit_breaker(url: str):
    global failure_count
    
    if failure_count >= max_failures:
        raise CircuitBreakerOpen("Circuit breaker is open")
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        failure_count = 0  # Reset on success
        return response.json()
    except requests.RequestException:
        failure_count += 1
        raise

@api_call_with_circuit_breaker.on_failure
def track_failures(state):
    print(f"API call failed {failure_count} times")

@api_call_with_circuit_breaker.on_success
def track_success(state):
    print("API call succeeded, circuit breaker reset")
```

### File Operations with Exponential Backoff

```python
import os
import random
from mule import retry
from mule.stop_conditions import AttemptsExhausted

def smart_backoff(prev_state, next_state):
    # Exponential backoff with jitter
    base_delay = 2 ** (next_state.attempt - 1)
    jitter = random.uniform(0.1, 0.3) * base_delay
    return min(base_delay + jitter, 30)  # Cap at 30 seconds

@retry(until=AttemptsExhausted(5), wait=smart_backoff)
def save_important_file(data: str, filepath: str):
    try:
        with open(filepath, 'w') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
    except (OSError, IOError) as e:
        print(f"Failed to save file: {e}")
        raise

@save_important_file.before_attempt
def log_attempt(state):
    if state.attempt > 1:
        print(f"Retrying file save (attempt {state.attempt})")

@save_important_file.on_success
def log_success(state):
    print(f"File saved successfully on attempt {state.attempt}")
```

## 🤝 Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
