import threading
import time
import os

def task1():
    start_time = time.time()
    print(f"The start time for thread 1 is {start_time}")
    thread_name = threading.current_thread().name
    print(f"Task1 assigned to thread {thread_name}")
    print(f"The process if for running task 1 {os.getpid()}")
    time.sleep(10)

def task2():
    start_time = time.time()
    print(f"The start time for thread 2 is {start_time}")
    thread_name = threading.current_thread().name
    print(f"Task1 assigned to thread {thread_name}")
    print(f"The process if for running task 2 {os.getpid()}")
    time.sleep(5)

if __name__ == "__main__":

    start_time = time.time()

    print(f"Id for main process is {os.getpid()}")
    print(f"Main thread name {threading.current_thread().name}")

    t1 = threading.Thread(target=task1, name='t1')
    t2 = threading.Thread(target=task2, name='t2')

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    end_time = time.time()

    print(f"The complete execution time is {end_time-start_time}")
