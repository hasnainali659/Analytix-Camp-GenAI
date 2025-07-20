# Async in Python: A Practical Guide

Python's `asyncio` library enables asynchronous programming, allowing you to write non-blocking code that handles many tasks at once. This tutorial covers the fundamentals through advanced concepts with engaging examples and exercises.

## 1. Why Asynchronous Programming?

Traditional synchronous code executes line by line, waiting for each task to finish. When operations involve waiting—like network requests or file I/O—this can slow down your program. Asynchronous code allows the program to continue running other tasks while waiting, improving efficiency.

### Real-Life Analogy

Imagine ordering food at a restaurant. In a synchronous world, the waiter would take one person's order, wait in the kitchen until it's ready, deliver the meal, then return to take the next order. Asynchronous service lets the waiter take multiple orders, deliver meals as they're ready, and keep everyone happy and fed.

## 2. Event Loop and Coroutines

`asyncio` relies on an **event loop**, a cycle that schedules and runs tasks. Functions defined with `async def` are **coroutines**, which can pause at `await` points so other tasks can run.

```python
import asyncio

async def greet(name):
    print(f"Hello, {name}!")
    await asyncio.sleep(1)  # Simulate a pause
    print(f"Goodbye, {name}!")

async def main():
    await greet("Alice")
    await greet("Bob")

asyncio.run(main())
```

Although the sleep pauses for a second, both greetings run sequentially. We'll see how to run them concurrently next.

## 3. Running Tasks Concurrently

Use `asyncio.gather` to schedule multiple coroutines at once. The event loop switches between them whenever they hit an `await`.

```python
async def main():
    await asyncio.gather(greet("Alice"), greet("Bob"))

asyncio.run(main())
```

Now, "Goodbye" messages appear after roughly one second rather than two, because both tasks waited for the same sleep concurrently.

## 4. Practical Example: Fetching Web Pages

Let's fetch several web pages in parallel.

```python
import asyncio
import aiohttp

urls = [
    "https://example.com",
    "https://httpbin.org/delay/2",  # Simulates a slow page
    "https://python.org",
]

async def fetch(url, session):
    async with session.get(url) as response:
        print(f"Fetched {url} with status {response.status}")
        return await response.text()

async def main():
    async with aiohttp.ClientSession() as session:
        pages = await asyncio.gather(*(fetch(url, session) for url in urls))
    print(f"Downloaded {len(pages)} pages")

asyncio.run(main())
```

The program begins all downloads nearly simultaneously and reports when each finishes.

## 5. Tasks and Background Work

`asyncio.create_task` schedules coroutines in the background, letting your program continue running other code.

```python
async def periodic():
    while True:
        print("Tick")
        await asyncio.sleep(1)

async def main():
    task = asyncio.create_task(periodic())
    await asyncio.sleep(5)  # Let it tick a few times
    task.cancel()           # Stop the background task

asyncio.run(main())
```

## 6. Advanced: Synchronizing with Locks

When multiple coroutines access shared data, you may need synchronization. `asyncio.Lock` works similarly to threading locks.

```python
counter = 0
lock = asyncio.Lock()

async def add_one():
    global counter
    async with lock:
        temp = counter
        await asyncio.sleep(0.1)  # Simulate work
        counter = temp + 1

async def main():
    await asyncio.gather(*(add_one() for _ in range(100)))
    print(counter)  # Should print 100

asyncio.run(main())
```

## 7. Error Handling

Use `try`/`except` around `await` expressions to handle errors gracefully.

```python
async def safe_fetch(url, session):
    try:
        async with session.get(url) as resp:
            return await resp.text()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None
```

## 8. Exercises

1. **Concurrent API Calls**: Modify the web-fetching example to retrieve JSON from several APIs and parse a specific field from each response.
2. **Progress Indicator**: Write a coroutine that prints "." every half second while another coroutine performs a slow operation (like `asyncio.sleep(5)`). Use `asyncio.gather` to run them together.
3. **Timeouts**: Implement a wrapper that cancels a coroutine if it takes longer than a specified number of seconds.
4. **Chat Server (Advanced)**: Build a tiny chat server using `asyncio` sockets where multiple clients can send messages to each other.
5. **Async File Processing**: Use `aiofiles` to read several files concurrently and count the total lines across them.

Explore these exercises to become comfortable with asynchronous concepts!

---

Async programming lets your programs remain responsive and efficient when dealing with many I/O-bound tasks. Mastering these techniques will make your Python applications faster and more scalable.


