import threading
import os
import zipfile
import queue
import time
import uuid
import json
import subprocess
import lib.utils as artillery_utils

WORKER_COUNT = 5

count = 0
kill = False
daemon = None
workers = []
job_queue = queue.Queue()
processing_jobs_queue = queue.Queue()
inspectable_job_queue = []
finished_job_queue = queue.Queue()
jobs = {}

# job data type should look like
# { "repo": "repo_name", ... }

class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True
        self.busy = False
        self.curr_job = None
    
    def update_busy(self, flag):
        self.busy = flag

    def get_busy(self):
        return self.busy
    
    def stop(self):
        self.running = False
    
    def build_semgrep_cmd(self):
        repo = self.curr_job["repo"]
        rules = self.curr_job["rules"]
        cmd = ["semgrep", "--json"]
        # populate cmd with all requested semgrep rules
        for rule in rules:
            cmd.append("--config")
            cmd.append(rule)
        cmd.append(f"{artillery_utils.get_repos_dir()}/{repo}")
        return cmd

    def get_current_job(self):
        return self.curr_job
    
    def process_job(self, semgrep_cmd):
        global jobs
        if self.curr_job is not None:
            # check for debug stuff, only used if --debug is passed 
            # when running app.py it is used for tests
            if artillery_utils.is_debug():
                if "debug_timer" in self.curr_job:
                    time.sleep(self.curr_job["debug_timer"])
                    return
            # double check repo existance
            if (artillery_utils.check_repo_existance(self.curr_job["repo"])):
                # run semgrep subprocess
                repo = self.curr_job["repo"]
                p = subprocess.Popen(semgrep_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, err = p.communicate()
                # update job entry with findings
                jobs[self.curr_job["jid"]]["results"] = json.loads(output.decode())

    def run(self):
        global job_queue
        global processing_jobs_queue
        global finished_job_queue
        while self.running:
            self.curr_job = None
            if job_queue.qsize() > 0:
                try:
                    self.curr_job = job_queue.get_nowait()
                except:
                    continue
                self.update_busy(True)
                processing_jobs_queue.put(self.curr_job)
                self.process_job(self.build_semgrep_cmd())
                finished_job_queue.put(self.curr_job)
                self.update_busy(False)
                
                

def semgrepper_daemon():
    global kill
    global workers
    global job_queue
    global finished_job_queue
    global processing_jobs_queue
    running = True
    prev_queue_size = 0
    while running:
        if kill:
            running = False
            [ worker.stop() for worker in workers ]
            [ worker.join() for worker in workers ]
        else:
            # check for new job being processed and update
            # inspectable queue
            job_being_processed = None
            try:
                job_being_processed = processing_jobs_queue.get_nowait()
            except Exception as e:
                pass
            if job_being_processed is not None:
                update_job_state(job_being_processed["jid"], "RUNNING")
            # check for new job finished and update list of 
            # finished jobs
            new_finished_job = None
            try:
                new_finished_job = finished_job_queue.get_nowait()
            except Exception as e:
                pass
            if new_finished_job is not None:
                update_job_state(new_finished_job["jid"], "FINISHED")

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

def update_job_state(jid, new_state):
    job_entry = jobs[jid]
    job_entry["state"] = new_state

def add_semgrep_job(job):
    global job_queue
    global jobs
    global inspectable_job_queue
    new_jid = str(uuid.uuid4())
    # give the job a job id
    job["jid"] = new_jid
    # give the job a timestamp
    job["timestamp"] = time.time()
    # add job to work queue
    job_queue.put(job)
    # add new job to jobs dictionary
    jobs[job["jid"]] = job
    # give job a state
    jobs[job["jid"]]["state"] = "QUEUED"
    return job["jid"]

def get_job(jid):
    if jid in jobs:
        return jobs[jid]
    return {}

def get_queued_jobs():
    global jobs
    ret = {}
    for jid in jobs:
        job_entry = jobs[jid]
        if job_entry["state"] == "QUEUED":
            ret[jid] = job_entry
    return ret

def get_running_jobs():
    global jobs
    ret = {}
    for jid in jobs:
        job_entry = jobs[jid]
        if job_entry["state"] == "RUNNING":
            ret[jid] = job_entry
    return ret

def get_jobs(pagination_start, pagination_end):
    global jobs
    jobs_list = list(jobs.values())
    jobs_list.sort(key = lambda x:x["timestamp"], reverse=True)
    return jobs_list[pagination_start: pagination_end]

def get_results(jid):
    global jobs
    if jid not in jobs:
        return None
    else:
        job_entry = jobs[jid]
        if job_entry["state"] != "FINISHED":
            return None
        return job_entry["results"]