import random
import signal
import threading
import time

exit_event = threading.Event()


def bg_thread():
    for i in range(1,30):
        print(f"{i} of 30 iter...")
        time.sleep(random.random())
        if exit_event.is_set():
            break
    print(f'{i} iter completed before exiting')


def signal_handler(signum, frame):
    exit_event.set()

signal.signal(signal.SIGINT, signal_handler)

th = threading.Thread(target=bg_thread)
th.start()
th.join()