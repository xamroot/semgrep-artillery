import threading
import os
import zipfile

count = 0
kill = False
threads = []

def thread_function(name):
    global kill
    while not kill:
        repos = os.listdir("repos")
        for repo in repos:
            if ".zip" in repo:
                with zipfile.ZipFile(f"./repos/{repo}", 'r') as zip_ref:
                    zip_ref.extractall(f"./repos/{repo.split('.zip')[0]}")
                os.remove(f"./repos/{repo}")


def run_unzipper():
    global count
    global threads
    global kill
    if count > 0:
        return False
    else:
        print("[UNZIPPER THREAD RUNNING]")
        kill = False
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
