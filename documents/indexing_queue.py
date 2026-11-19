import queue
import threading
event_queue = queue.Queue()
pending_events = set()
pending_lock = threading.Lock()


def enqueue_file(action, relative_path):
    key = relative_path.lower()

    with pending_lock:
        if key in pending_events:
            return

        pending_events.add(key)

    event_queue.put((action, relative_path))


def get_next_event():
    return event_queue.get()


def finish_event(relative_path):
    with pending_lock:
        pending_events.discard(relative_path.lower())
    
    event_queue.task_done()
