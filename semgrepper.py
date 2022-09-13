import threading
import os
import zipfile
import queue

WORKER_COUNT = 5

count = 0
kill = False
daemon = None
workers = []
job_queue = queue.Queue()

class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.busy = False
    
    def update_busy(self, flag):
        self.busy = flag

    def get_busy(self):
        return self.busy
    
    def stop(self):
        self.running = False

    def run(self):
        global job_queue
        while self.running:
            curr_job = None
            if job_queue.qsize() > 0:
                try:
                    curr_job = job_queue.get()
                except:
                    pass
                self.update_busy(True)
                self.update_busy(False)
                
                

def semgrepper_daemon():
    global kill
    global workers
    global job_queue
    running = True
    prev_queue_size = 0
    while running:
        if kill:
            running = False
            [ worker.stop() for worker in workers ]
            [ worker.join() for worker in workers ]
        else:
            curr_queue_size = job_queue.qsize()
            if curr_queue_size != prev_queue_size:
                prev_queue_size = curr_queue_size
                print(f"QUEUE UPDATED {prev_queue_size}")


'''
def thread_function(name):
    global kill
    while not kill:
        repos = os.listdir("repos")
        for repo in repos:
            if ".zip" in repo:
                with zipfile.ZipFile(f"./repos/{repo}", 'r') as zip_ref:
                    zip_ref.extractall(f"./repos/{repo.split('.zip')[0]}")
                os.remove(f"./repos/{repo}")
'''

def start_semgrepper_daemon():
    daemon = threading.Thread(target=semgrepper_daemon, args=())
    daemon.start()
    return daemon

def start_semgrepper_workers(n):
    workers = [WorkerThread() for i in range(n)]
    [ worker.start() for worker in workers ]
    return workers

def run_semgrepper():
    global count
    global kill
    global daemon
    global workers
    if count > 0:
        return False
    else:
        kill = False
        count += 1
        # start up semgrepper daemon
        daemon = start_semgrepper_daemon()
        # start up semgrepper workers
        workers = start_semgrepper_workers(2)
        print("[SEMGREPPER THREAD RUNNING]")
        return True

def kill_semgrepper():
    global daemon
    global kill
    kill = True
    daemon.join()
    print("[SEMGREPPER THREAD KILLED]")

def add_semgrep_job(repo):
    global job_queue
    job_queue.put(repo)