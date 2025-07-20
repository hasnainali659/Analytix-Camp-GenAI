"""
ASYNC PROGRAMMING IN PYTHON: BEGINNER TO ADVANCED TUTORIAL
=========================================================

This tutorial covers async programming from basics to advanced concepts
with real-life examples and exercises for beginner students.

Table of Contents:
1. Introduction to Async Programming
2. Understanding Concurrency vs Parallelism
3. Basic Async/Await Syntax
4. Real-Life Examples
5. Error Handling in Async Code
6. Advanced Async Patterns
7. Performance and Best Practices
8. Exercises and Projects
"""

import asyncio
import aiohttp
import time
import random
from typing import List, Dict, Any
import json

# ============================================================================
# SECTION 1: INTRODUCTION TO ASYNC PROGRAMMING
# ============================================================================

"""
What is Async Programming?
--------------------------
Async programming allows your program to handle multiple tasks concurrently
without blocking the execution of other tasks. It's like multitasking!

Real-life analogy:
Imagine you're cooking dinner:
- SYNCHRONOUS (blocking): You put pasta in water, stand there and wait 10 minutes
  doing nothing, then start chopping vegetables.
- ASYNCHRONOUS (non-blocking): You put pasta in water, while it's cooking you
  chop vegetables, set the table, and prepare sauce. Much more efficient!

When to use Async Programming:
1. I/O operations (file reading, network requests, database queries)
2. Web scraping
3. API calls
4. Real-time applications (chat apps, live data feeds)
5. GUI applications (keep UI responsive)
"""

# ============================================================================
# SECTION 2: SYNCHRONOUS vs ASYNCHRONOUS COMPARISON
# ============================================================================

def synchronous_example():
    """Traditional synchronous code - blocks execution"""
    print("🔄 Synchronous Example: Making coffee step by step")
    
    def boil_water():
        print("☕ Boiling water...")
        time.sleep(2)  # Simulates 2 seconds of boiling
        print("✅ Water is ready!")
    
    def grind_coffee():
        print("☕ Grinding coffee beans...")
        time.sleep(1.5)  # Simulates 1.5 seconds of grinding
        print("✅ Coffee is ground!")
    
    def prepare_cup():
        print("☕ Preparing cup...")
        time.sleep(0.5)  # Simulates 0.5 seconds
        print("✅ Cup is ready!")
    
    start_time = time.time()
    
    # Everything happens one after another (blocking)
    boil_water()
    grind_coffee()
    prepare_cup()
    
    total_time = time.time() - start_time
    print(f"⏱️ Total time (synchronous): {total_time:.2f} seconds\n")

async def asynchronous_example():
    """Async code - allows concurrent execution"""
    print("🚀 Asynchronous Example: Making coffee efficiently")
    
    async def boil_water():
        print("☕ Boiling water...")
        await asyncio.sleep(2)  # Non-blocking sleep
        print("✅ Water is ready!")
    
    async def grind_coffee():
        print("☕ Grinding coffee beans...")
        await asyncio.sleep(1.5)  # Non-blocking sleep
        print("✅ Coffee is ground!")
    
    async def prepare_cup():
        print("☕ Preparing cup...")
        await asyncio.sleep(0.5)  # Non-blocking sleep
        print("✅ Cup is ready!")
    
    start_time = time.time()
    
    # Everything happens concurrently (non-blocking)
    await asyncio.gather(
        boil_water(),
        grind_coffee(),
        prepare_cup()
    )
    
    total_time = time.time() - start_time
    print(f"⏱️ Total time (asynchronous): {total_time:.2f} seconds\n")

# ============================================================================
# SECTION 3: BASIC ASYNC/AWAIT SYNTAX
# ============================================================================

async def basic_async_function():
    """
    Basic async function syntax:
    1. Use 'async def' to define an async function
    2. Use 'await' to wait for async operations
    3. Use 'asyncio.run()' to run async functions
    """
    print("🎯 This is an async function!")
    await asyncio.sleep(1)  # Wait 1 second without blocking
    print("✅ Async function completed!")

async def downloading_files_example():
    """Real-life example: Downloading multiple files"""
    
    async def download_file(filename: str, size_mb: int):
        print(f"📥 Starting download: {filename} ({size_mb}MB)")
        # Simulate download time based on file size
        download_time = size_mb * 0.5  # 0.5 seconds per MB
        await asyncio.sleep(download_time)
        print(f"✅ Downloaded: {filename}")
        return filename
    
    print("📁 Downloading multiple files concurrently...")
    start_time = time.time()
    
    # Download files concurrently
    files = await asyncio.gather(
        download_file("document.pdf", 5),
        download_file("presentation.pptx", 8),
        download_file("spreadsheet.xlsx", 3),
        download_file("image.jpg", 2)
    )
    
    total_time = time.time() - start_time
    print(f"🎉 All files downloaded in {total_time:.2f} seconds!")
    return files

# ============================================================================
# SECTION 4: REAL-LIFE EXAMPLES
# ============================================================================

async def web_scraping_example():
    """Example: Checking multiple websites' status"""
    
    async def check_website(session, url: str):
        try:
            print(f"🌐 Checking {url}...")
            async with session.get(url, timeout=5) as response:
                status = "✅ Online" if response.status == 200 else f"⚠️ Status: {response.status}"
                print(f"{url}: {status}")
                return {"url": url, "status": response.status, "online": response.status == 200}
        except Exception as e:
            print(f"{url}: ❌ Offline ({str(e)[:50]}...)")
            return {"url": url, "status": "error", "online": False}
    
    websites = [
        "https://google.com",
        "https://github.com", 
        "https://stackoverflow.com",
        "https://python.org",
        "https://invalid-website-12345.com"  # This will fail
    ]
    
    print("🔍 Checking multiple websites concurrently...")
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            *[check_website(session, url) for url in websites],
            return_exceptions=True
        )
    
    online_count = sum(1 for r in results if isinstance(r, dict) and r.get("online"))
    print(f"\n📊 Results: {online_count}/{len(websites)} websites are online")

async def restaurant_order_system():
    """Real-life example: Restaurant order processing system"""
    
    class Order:
        def __init__(self, order_id: int, items: List[str], customer: str):
            self.order_id = order_id
            self.items = items
            self.customer = customer
            self.status = "received"
    
    async def prepare_item(item: str, prep_time: float):
        print(f"👨‍🍳 Preparing {item}...")
        await asyncio.sleep(prep_time)
        print(f"✅ {item} is ready!")
        return item
    
    async def process_order(order: Order):
        print(f"📋 Processing order #{order.order_id} for {order.customer}")
        
        # Different items take different times to prepare
        prep_times = {
            "burger": 3.0,
            "fries": 2.0,
            "salad": 1.5,
            "drink": 0.5,
            "pizza": 4.0,
            "pasta": 3.5
        }
        
        order.status = "preparing"
        
        # Prepare all items concurrently
        prepared_items = await asyncio.gather(
            *[prepare_item(item, prep_times.get(item, 2.0)) for item in order.items]
        )
        
        order.status = "ready"
        print(f"🎉 Order #{order.order_id} is ready for {order.customer}!")
        return order
    
    # Simulate multiple orders coming in
    orders = [
        Order(1, ["burger", "fries", "drink"], "Alice"),
        Order(2, ["pizza", "salad"], "Bob"),
        Order(3, ["pasta", "drink"], "Charlie"),
        Order(4, ["burger", "salad", "fries"], "Diana")
    ]
    
    print("🏪 Restaurant Order System - Processing multiple orders concurrently")
    start_time = time.time()
    
    # Process all orders concurrently
    completed_orders = await asyncio.gather(
        *[process_order(order) for order in orders]
    )
    
    total_time = time.time() - start_time
    print(f"\n⏱️ All {len(completed_orders)} orders completed in {total_time:.2f} seconds!")

# ============================================================================
# SECTION 5: ERROR HANDLING IN ASYNC CODE
# ============================================================================

async def error_handling_examples():
    """How to handle errors in async code"""
    
    async def risky_task(task_id: int, fail_chance: float = 0.3):
        await asyncio.sleep(1)
        if random.random() < fail_chance:
            raise Exception(f"Task {task_id} failed!")
        return f"Task {task_id} completed successfully"
    
    print("🎲 Error Handling Example 1: Try/Except")
    try:
        result = await risky_task(1, fail_chance=0.8)  # High chance of failure
        print(f"✅ {result}")
    except Exception as e:
        print(f"❌ Caught error: {e}")
    
    print("\n🎲 Error Handling Example 2: Multiple tasks with some failures")
    tasks = [risky_task(i, fail_chance=0.4) for i in range(1, 6)]
    
    # gather with return_exceptions=True continues even if some tasks fail
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"❌ Task {i}: {result}")
        else:
            print(f"✅ Task {i}: {result}")

async def timeout_example():
    """How to handle timeouts"""
    
    async def slow_operation():
        print("🐌 Starting slow operation...")
        await asyncio.sleep(5)  # Takes 5 seconds
        return "Operation completed"
    
    print("⏰ Timeout Example:")
    try:
        # Wait maximum 2 seconds
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
        print(f"✅ {result}")
    except asyncio.TimeoutError:
        print("❌ Operation timed out after 2 seconds")

# ============================================================================
# SECTION 6: ADVANCED ASYNC PATTERNS
# ============================================================================

async def producer_consumer_example():
    """Advanced pattern: Producer-Consumer with asyncio.Queue"""
    
    async def producer(queue: asyncio.Queue, producer_id: int):
        """Produces items and puts them in queue"""
        for i in range(5):
            item = f"item-{producer_id}-{i}"
            await queue.put(item)
            print(f"📦 Producer {producer_id} produced: {item}")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Signal that this producer is done
        await queue.put(None)
        print(f"🏁 Producer {producer_id} finished")
    
    async def consumer(queue: asyncio.Queue, consumer_id: int):
        """Consumes items from queue"""
        processed = 0
        while True:
            item = await queue.get()
            if item is None:
                # Signal to stop
                await queue.put(None)  # Pass the signal to other consumers
                break
            
            print(f"⚙️ Consumer {consumer_id} processing: {item}")
            await asyncio.sleep(random.uniform(0.3, 0.8))  # Simulate processing
            processed += 1
            queue.task_done()
        
        print(f"🎯 Consumer {consumer_id} processed {processed} items")
    
    print("🏭 Producer-Consumer Pattern Example")
    queue = asyncio.Queue(maxsize=10)
    
    # Start producers and consumers
    await asyncio.gather(
        producer(queue, 1),
        producer(queue, 2),
        consumer(queue, 1),
        consumer(queue, 2),
        consumer(queue, 3)
    )
    
    print("✅ Producer-Consumer example completed!")

async def rate_limiting_example():
    """Advanced: Rate limiting with Semaphore"""
    
    # Allow maximum 3 concurrent API calls
    semaphore = asyncio.Semaphore(3)
    
    async def api_call(call_id: int):
        async with semaphore:  # Acquire semaphore
            print(f"🌐 API call {call_id} started")
            await asyncio.sleep(2)  # Simulate API call
            print(f"✅ API call {call_id} completed")
            return f"Result from call {call_id}"
    
    print("🚦 Rate Limiting Example (max 3 concurrent calls)")
    
    # Make 10 API calls, but only 3 will run concurrently
    tasks = [api_call(i) for i in range(1, 11)]
    results = await asyncio.gather(*tasks)
    
    print(f"📊 Completed {len(results)} API calls with rate limiting")

# ============================================================================
# SECTION 7: PERFORMANCE COMPARISON
# ============================================================================

async def performance_comparison():
    """Compare sync vs async performance"""
    
    def sync_io_task(task_id: int):
        """Synchronous I/O simulation"""
        time.sleep(1)  # Blocking sleep
        return f"Sync task {task_id} done"
    
    async def async_io_task(task_id: int):
        """Asynchronous I/O simulation"""
        await asyncio.sleep(1)  # Non-blocking sleep
        return f"Async task {task_id} done"
    
    num_tasks = 5
    
    # Synchronous execution
    print(f"🐌 Running {num_tasks} tasks synchronously...")
    start_time = time.time()
    sync_results = [sync_io_task(i) for i in range(num_tasks)]
    sync_time = time.time() - start_time
    print(f"⏱️ Synchronous time: {sync_time:.2f} seconds")
    
    # Asynchronous execution
    print(f"\n🚀 Running {num_tasks} tasks asynchronously...")
    start_time = time.time()
    async_results = await asyncio.gather(
        *[async_io_task(i) for i in range(num_tasks)]
    )
    async_time = time.time() - start_time
    print(f"⏱️ Asynchronous time: {async_time:.2f} seconds")
    
    speedup = sync_time / async_time
    print(f"🎯 Speedup: {speedup:.2f}x faster with async!")

# ============================================================================
# SECTION 8: EXERCISES AND PROJECTS
# ============================================================================

"""
EXERCISE 1: Weather Checker 🌤️
------------------------------
Create an async function that checks weather for multiple cities concurrently.
Use a mock API that takes random time to respond.

YOUR TASK:
Write an async function that:
1. Takes a list of cities
2. Simulates API calls for each city (random delay 1-3 seconds)
3. Returns weather data for all cities
4. Measures total time taken

SOLUTION BELOW (try to solve first!):
"""

async def exercise_1_weather_checker():
    """Exercise 1: Weather Checker"""
    
    async def get_weather(city: str):
        """Simulate weather API call"""
        print(f"🌤️ Fetching weather for {city}...")
        delay = random.uniform(1, 3)  # Random delay 1-3 seconds
        await asyncio.sleep(delay)
        
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Windy"]
        temperature = random.randint(-10, 35)
        condition = random.choice(weather_conditions)
        
        result = {
            "city": city,
            "temperature": f"{temperature}°C",
            "condition": condition,
            "fetched_in": f"{delay:.2f}s"
        }
        print(f"✅ Weather for {city}: {temperature}°C, {condition}")
        return result
    
    cities = ["New York", "London", "Tokyo", "Sydney", "Mumbai", "São Paulo"]
    
    print("🌍 Exercise 1: Weather Checker")
    start_time = time.time()
    
    # YOUR CODE HERE: Use asyncio.gather to fetch weather for all cities
    weather_data = await asyncio.gather(
        *[get_weather(city) for city in cities]
    )
    
    total_time = time.time() - start_time
    print(f"\n📊 Got weather for {len(cities)} cities in {total_time:.2f} seconds!")
    return weather_data

"""
EXERCISE 2: File Processing Pipeline 📁
---------------------------------------
Create a pipeline that processes multiple files concurrently.

YOUR TASK:
1. Create async functions for: read_file, process_file, save_file
2. Each function should have random delays
3. Process multiple files through the pipeline
4. Use asyncio.Queue for the pipeline

SOLUTION BELOW:
"""

async def exercise_2_file_pipeline():
    """Exercise 2: File Processing Pipeline"""
    
    async def read_file(filename: str):
        """Simulate reading a file"""
        print(f"📖 Reading {filename}...")
        await asyncio.sleep(random.uniform(0.5, 1.5))
        content = f"Content of {filename}" + "x" * random.randint(100, 1000)
        print(f"✅ Read {filename} ({len(content)} chars)")
        return {"filename": filename, "content": content}
    
    async def process_file(file_data: dict):
        """Simulate processing file content"""
        filename = file_data["filename"]
        print(f"⚙️ Processing {filename}...")
        await asyncio.sleep(random.uniform(1, 2))
        
        # Simulate processing (word count, compression, etc.)
        processed_content = file_data["content"].upper()
        word_count = len(file_data["content"].split())
        
        print(f"✅ Processed {filename} ({word_count} words)")
        return {
            "filename": filename,
            "processed_content": processed_content,
            "word_count": word_count
        }
    
    async def save_file(processed_data: dict):
        """Simulate saving processed file"""
        filename = processed_data["filename"]
        print(f"💾 Saving processed_{filename}...")
        await asyncio.sleep(random.uniform(0.3, 0.8))
        print(f"✅ Saved processed_{filename}")
        return f"processed_{filename}"
    
    files = ["report.txt", "data.csv", "notes.md", "config.json", "readme.txt"]
    
    print("📁 Exercise 2: File Processing Pipeline")
    start_time = time.time()
    
    # Process files through the pipeline
    read_tasks = [read_file(f) for f in files]
    file_data = await asyncio.gather(*read_tasks)
    
    process_tasks = [process_file(data) for data in file_data]
    processed_data = await asyncio.gather(*process_tasks)
    
    save_tasks = [save_file(data) for data in processed_data]
    saved_files = await asyncio.gather(*save_tasks)
    
    total_time = time.time() - start_time
    print(f"\n🎉 Processed {len(files)} files in {total_time:.2f} seconds!")
    return saved_files

"""
EXERCISE 3: Chat Room Simulator 💬
----------------------------------
Simulate a chat room with multiple users sending messages concurrently.

YOUR TASK:
Create a chat room where:
1. Multiple users send messages at random intervals
2. Messages are processed and broadcasted
3. Simulate network delays
4. Handle user connections/disconnections
"""

async def exercise_3_chat_room():
    """Exercise 3: Chat Room Simulator"""
    
    class ChatRoom:
        def __init__(self):
            self.messages = []
            self.users = set()
        
        async def add_user(self, username: str):
            self.users.add(username)
            await self.broadcast(f"🟢 {username} joined the chat", "SYSTEM")
        
        async def remove_user(self, username: str):
            self.users.discard(username)
            await self.broadcast(f"🔴 {username} left the chat", "SYSTEM")
        
        async def broadcast(self, message: str, sender: str):
            """Simulate message broadcasting"""
            await asyncio.sleep(0.1)  # Network delay
            timestamp = time.strftime("%H:%M:%S")
            formatted_msg = f"[{timestamp}] {sender}: {message}"
            self.messages.append(formatted_msg)
            print(formatted_msg)
    
    async def user_session(chat_room: ChatRoom, username: str, session_duration: int):
        """Simulate a user's chat session"""
        await chat_room.add_user(username)
        
        messages = [
            "Hello everyone! 👋",
            "How's everyone doing?",
            "Anyone working on interesting projects?",
            "Love this async programming!",
            "Python is awesome! 🐍",
            "See you later!"
        ]
        
        message_count = random.randint(2, len(messages))
        selected_messages = random.sample(messages, message_count)
        
        for message in selected_messages:
            # Random delay between messages
            await asyncio.sleep(random.uniform(1, 3))
            await chat_room.broadcast(message, username)
        
        await chat_room.remove_user(username)
    
    print("💬 Exercise 3: Chat Room Simulator")
    chat_room = ChatRoom()
    
    users = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
    
    # Start user sessions concurrently
    await asyncio.gather(
        *[user_session(chat_room, user, random.randint(5, 10)) for user in users]
    )
    
    print(f"\n📊 Chat session ended. Total messages: {len(chat_room.messages)}")

# ============================================================================
# SECTION 9: BEST PRACTICES AND COMMON MISTAKES
# ============================================================================

"""
BEST PRACTICES FOR ASYNC PROGRAMMING 🌟
=======================================

1. Use async/await for I/O operations:
   ✅ Good: await aiohttp.get(url)
   ❌ Bad: requests.get(url) in async function

2. Don't block the event loop:
   ✅ Good: await asyncio.sleep(1)
   ❌ Bad: time.sleep(1) in async function

3. Handle exceptions properly:
   ✅ Good: Use try/except with await
   ❌ Bad: Ignore exceptions in async functions

4. Use asyncio.gather() for concurrent execution:
   ✅ Good: await asyncio.gather(*tasks)
   ❌ Bad: for task in tasks: await task

5. Close resources properly:
   ✅ Good: async with aiohttp.ClientSession() as session:
   ❌ Bad: session = aiohttp.ClientSession() (without closing)

6. Use timeouts for external calls:
   ✅ Good: await asyncio.wait_for(operation(), timeout=5)
   ❌ Bad: await operation() (without timeout)

COMMON MISTAKES TO AVOID ⚠️
===========================

1. Forgetting 'await':
   async def bad_example():
       asyncio.sleep(1)  # Missing await!
   
   async def good_example():
       await asyncio.sleep(1)  # Correct!

2. Using blocking calls in async functions:
   async def bad_example():
       time.sleep(1)  # Blocks the event loop!
   
   async def good_example():
       await asyncio.sleep(1)  # Non-blocking!

3. Not handling exceptions:
   async def bad_example():
       await risky_operation()  # What if this fails?
   
   async def good_example():
       try:
           await risky_operation()
       except Exception as e:
           print(f"Error: {e}")

4. Creating too many concurrent tasks:
   # Bad: Can overwhelm system
   tasks = [make_request(url) for url in 10000_urls]
   await asyncio.gather(*tasks)
   
   # Good: Use semaphore to limit concurrency
   semaphore = asyncio.Semaphore(100)
   async def limited_request(url):
       async with semaphore:
           return await make_request(url)
"""

# ============================================================================
# SECTION 10: MAIN EXECUTION AND MENU
# ============================================================================

async def main_menu():
    """Interactive menu to run different examples and exercises"""
    
    menu_options = {
        "1": ("Basic Sync vs Async Comparison", [synchronous_example, asynchronous_example]),
        "2": ("Downloading Files Example", downloading_files_example),
        "3": ("Web Scraping Example", web_scraping_example),
        "4": ("Restaurant Order System", restaurant_order_system),
        "5": ("Error Handling Examples", error_handling_examples),
        "6": ("Timeout Example", timeout_example),
        "7": ("Producer-Consumer Pattern", producer_consumer_example),
        "8": ("Rate Limiting Example", rate_limiting_example),
        "9": ("Performance Comparison", performance_comparison),
        "10": ("Exercise 1: Weather Checker", exercise_1_weather_checker),
        "11": ("Exercise 2: File Pipeline", exercise_2_file_pipeline),
        "12": ("Exercise 3: Chat Room", exercise_3_chat_room),
        "13": ("Run All Examples", "all")
    }
    
    print("=" * 60)
    print("🐍 ASYNC PROGRAMMING IN PYTHON - TUTORIAL MENU")
    print("=" * 60)
    
    for key, (title, _) in menu_options.items():
        print(f"{key:>2}. {title}")
    
    print("\nEnter choice (1-13) or 'exit' to quit:")
    
    # For demonstration, let's run a few key examples
    print("\n🚀 Running demo examples...\n")
    
    # Run basic comparison
    print("=" * 60)
    synchronous_example()
    await asynchronous_example()
    
    # Run downloading example
    print("=" * 60)
    await downloading_files_example()
    
    # Run exercise 1
    print("\n" + "=" * 60)
    await exercise_1_weather_checker()
    
    print("\n🎉 Demo completed! To run specific examples, call them individually.")
    print("📚 Read through the code comments to learn more about async programming!")

# ============================================================================
# FINAL PROJECTS FOR ADVANCED LEARNERS
# ============================================================================

"""
FINAL PROJECTS 🚀
=================

1. Web Crawler:
   Build an async web crawler that:
   - Crawls multiple websites concurrently
   - Respects robots.txt
   - Implements rate limiting
   - Handles errors gracefully
   - Saves data to files

2. Real-time Data Monitor:
   Create a system that:
   - Monitors multiple APIs/websites
   - Processes data in real-time
   - Sends notifications on changes
   - Uses WebSockets for real-time updates

3. Async Web Server:
   Build a web server using FastAPI or aiohttp that:
   - Handles multiple requests concurrently
   - Connects to async database
   - Implements WebSocket endpoints
   - Has proper error handling

4. File Processing System:
   Create a system that:
   - Watches directories for new files
   - Processes files concurrently
   - Transforms data (resize images, convert formats)
   - Uploads results to cloud storage

5. Chat Application:
   Build a real-time chat app with:
   - Multiple chat rooms
   - User authentication
   - Message persistence
   - Real-time notifications
   - File sharing

Remember: Start small, build incrementally, and always handle errors!
"""

# Run the tutorial
if __name__ == "__main__":
    print("🐍 Welcome to Async Programming in Python Tutorial!")
    print("This tutorial covers async programming from beginner to advanced level.")
    print("\nTo run the examples:")
    print("python async.py")
    print("\nOr run specific functions in an interactive Python session:")
    print("await main_menu()")
    
    # Uncomment the line below to run the demo
    # asyncio.run(main_menu())
