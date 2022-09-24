import threading
import os
import zipfile

count = 0
kill = False
threads = []
repo_dir = ""

def thread_function(name):
    global kill
    global repo_dir
    while not kill:
        repos = os.listdir(repo_dir)
        for repo in repos:
            if ".zip" in repo:
                with zipfile.ZipFile(f"{repo_dir}/{repo}", 'r') as zip_ref:
                    zip_ref.extractall(f"{repo_dir}/{repo.split('.zip')[0]}")
                os.remove(f"{repo_dir}/{repo}")


def run_unzipper(_repo_dir):
    global count
    global threads
    global kill
    global repo_dir
    if count > 0:
        return False
    else:
        print("[UNZIPPER THREAD RUNNING]")
        kill = False
        repo_dir = _repo_dir
        count += 1
        newthread = threading.Thread(target=thread_function, args=(1,))
        newthread.start()
        threads.append(newthread)
        return True

def kill_unzipper():
    global threads
    global kill
    kill = True
    for thread in threads:
        thread.join()
        print("[UNZIPPER THREAD KILLED]")


# x.join()
