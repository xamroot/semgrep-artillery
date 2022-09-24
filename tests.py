import os
import subprocess
import threading
import json
import inspect
import requests
import signal
import time

server_address = "127.0.0.1"
server_port = 5000

server_proc = None
server_output = ""
server_err = ""
tests_passed = 0
tests_failed = 0
global_data = {}

def evaluate_test(condition):
    global tests_passed
    global tests_failed
    if condition == True:
        tests_passed += 1
    else:
        tests_failed += 1
        print(f"TEST FAILED: {inspect.stack()[1].function}")

def create_test_environment():
    subprocess.Popen(["rm", "-rf", "repos/dummyrepo"])
    subprocess.Popen(["rm", "-rf", "repos/bad_test_repo"])
    subprocess.Popen(["mkdir", "repos/dummyrepo"])
    subprocess.Popen(["cp", "-r", "tests/bad_test_repo", "repos/bad_test_repo"])

def destroy_test_environment():
    global server_proc
    subprocess.Popen(["rm", "-rf", "repos/dummyrepo"])
    subprocess.Popen(["rm", "-rf", "repos/bad_test_repo"])


def await_server_start():
    server_started = False
    url = f"http://{server_address}:{server_port}/list/repos"
    while not server_started:
        try:
            res = requests.get(url)
            server_started = True
        except Exception as e:
            continue

def run_server():
    global server_proc
    global server_output
    global server_err
    server_proc = subprocess.Popen(["python3", "app.py", "--debug"], stdout=subprocess.PIPE) 
    server_output, server_err = server_proc.communicate()

def run_tests():
    global server_proc
    global tests_passed
    global tests_failed
    # start server in separate thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    # set up environment for testing
    create_test_environment()
    await_server_start()
    # call each test function here
    test_ensure_listrepos_returns_list_json()
    test_ensure_listrepos_contains_dummy_repo()
    test_newjob_should_handle_nonexistant_repo()
    test_newjob_should_handle_missing_repo_param()
    test_newjob_should_handle_missing_rules_param()
    test_newjob_should_handle_empty_rules_param()
    test_newjob_should_succeed()
    test_jobsrunning_should_reflect_new_job_after_creation()
    test_jobsqueued_should_reflect_new_job_after_many_creations()
    test_jobstatus_should_reflect_accurate_job_status()
    test_jobstatus_should_be_finished_after_processed_and_should_have_results()
    test_job_should_have_results_anytime_after_processing()
    test_jobs_list_should_show_most_recent_job_at_start()
    # tests done, kill server process and join thread
    os.kill(server_proc.pid, signal.SIGINT)
    server_thread.join()
    destroy_test_environment()
    print(f"{tests_passed} / {tests_passed + tests_failed} tests passed")

# ensure that /list/repos returns a json list
def test_ensure_listrepos_returns_list_json():
    url = f"http://{server_address}:{server_port}/list/repos"
    res = requests.get(url)
    data = json.loads(res.text)
    evaluate_test( type(data["repos"]) == type([]))

# ensure that /list/repos contains the dummy repo in it's list
def test_ensure_listrepos_contains_dummy_repo():
    url = f"http://{server_address}:{server_port}/list/repos"
    res = requests.get(url)
    data = json.loads(res.text)
    evaluate_test( "dummyrepo" in data["repos"] )

# ensure newjob catches a request with a nonexistant repo
def test_newjob_should_handle_nonexistant_repo():
    url = f"http://{server_address}:{server_port}/newjob"
    body = {
        "repo": "nonexistantrepo",
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"]
    }
    res = requests.post(url, json=body)
    data = json.loads(res.text)
    evaluate_test( "error" in data )

# ensure newjob catches a request without repo param
def test_newjob_should_handle_missing_repo_param():
    url = f"http://{server_address}:{server_port}/newjob"
    body = {
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"]
    }
    res = requests.post(url, json=body)
    data = json.loads(res.text)
    evaluate_test( "error" in data )

# ensure newjob catches a request without rules param
def test_newjob_should_handle_missing_rules_param():
    url = f"http://{server_address}:{server_port}/newjob"
    body = {
        "repo": "dummyrepo",
    }
    res = requests.post(url, json=body)
    data = json.loads(res.text)
    evaluate_test( "error" in data )

# ensure newjob catches a request empty rules param
def test_newjob_should_handle_empty_rules_param():
    url = f"http://{server_address}:{server_port}/newjob"
    body = {
        "repo": "dummyrepo",
        "rules": []
    }
    res = requests.post(url, json=body)
    data = json.loads(res.text)
    evaluate_test( "error" in data )

# ensure newjob can successfully create a semgrep job
def test_newjob_should_succeed():
    url = f"http://{server_address}:{server_port}/newjob"
    body = {
        "repo": "dummyrepo",
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"]
    }
    res = requests.post(url, json=body)
    data = json.loads(res.text)
    evaluate_test( "error" not in data and "succcess" in data["message"] )

# ensure newjob can successfully create a semgrep job
def test_jobsrunning_should_reflect_new_job_after_creation():
    # create a new job with a debug timer
    url = f"http://{server_address}:{server_port}/newjob"
    job = {
        "repo": "dummyrepo",
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"],
        "debug_timer":2
    }
    jid = ""
    for i in range(5):
        res = requests.post(url, json=job)
        if len(jid) < 1:
            jid = json.loads(res.text)["jobid"]
    # now check /jobs/running
    url = f"http://{server_address}:{server_port}/jobs/running"
    res = requests.get(url)
    data = json.loads(res.text)
    evaluate_test( len(jid) > 0 and jid in data["jobs"] )

# ensure inspectable queue accurately reflects the real queue
# when many requests are waiting
def test_jobsqueued_should_reflect_new_job_after_many_creations():
    # create a new job with a debug timer
    url = f"http://{server_address}:{server_port}/newjob"
    job = {
        "repo": "dummyrepo",
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"],
        "debug_timer":2
    }
    jid = ""
    for i in range(5):
        res = requests.post(url, json=job)
        jid = json.loads(res.text)["jobid"]
    # now check /jobs/queued
    url = f"http://{server_address}:{server_port}/jobs/queued"
    res = requests.get(url)
    data = json.loads(res.text)
    evaluate_test( len(jid) > 0 and jid in data["jobs"] )

# after creating a new job should be able to inspect it's status
# status should either be queued or running
def test_jobstatus_should_reflect_accurate_job_status():
    # create a new job with a debug timer
    url = f"http://{server_address}:{server_port}/newjob"
    job = {
        "repo": "dummyrepo",
        "rules": ["r/csharp.dotnet.security.audit.ldap-injection.ldap-injection"],
    }
    res = requests.post(url, json=job)
    jid = json.loads(res.text)["jobid"]
    # now check /job/<jid>
    url = f"http://{server_address}:{server_port}/job/{jid}"
    res = requests.get(url)
    data = json.loads(res.text)["job"]
    evaluate_test( data["state"] == "QUEUED" or data["state"] == "RUNNING")


# job state should be set to finished after done being
# processed by semgrepper
def test_jobstatus_should_be_finished_after_processed_and_should_have_results():
    global global_data
    # create a new job with a debug timer
    url = f"http://{server_address}:{server_port}/newjob"
    job = {
        "repo": "bad_test_repo",
        "rules": ["r/csharp.lang.security.insecure-deserialization.binary-formatter.insecure-binaryformatter-deserialization"],
    }
    res = requests.post(url, json=job)
    jid = json.loads(res.text)["jobid"]
    # update global_data for use in later tests
    global_data["finished_jid"] = jid
    # now wait for job status to be finished
    job_state = ""
    max_loops = 10
    loops = 0
    while job_state != "FINISHED" and loops <= max_loops:
        url = f"http://{server_address}:{server_port}/job/{jid}"
        res = requests.get(url)
        job_state = json.loads(res.text)["job"]["state"]
        loops += 1
        time.sleep(2)
    evaluate_test( job_state == "FINISHED" )
    # now get results for job
    url = f"http://{server_address}:{server_port}/job/{jid}/results"
    res = requests.get(url)
    results = json.loads(res.text)["results"]["results"]
    evaluate_test( len(results) > 0 )

# should be able to view a jobs results at any point after the job
# is finished running
def test_job_should_have_results_anytime_after_processing():
    global global_data
    jid = global_data["finished_jid"]
    # now get results for job
    url = f"http://{server_address}:{server_port}/job/{jid}/results"
    res = requests.get(url)
    results = json.loads(res.text)["results"]["results"]
    evaluate_test( len(results) > 0 )

# should be able to see most recent job as the first item of 
# the jobs list
def test_jobs_list_should_show_most_recent_job_at_start():
    global global_data
    jid = global_data["finished_jid"]
    # now get results for job
    url = f"http://{server_address}:{server_port}/jobs/list/0"
    res = requests.get(url)
    results = json.loads(res.text)
    evaluate_test( results["jobs"][0]["jid"] == jid)


try:
    run_tests()
except Exception as e:
    print(f"ERROR OCCURRED! \n{e}")
    print(server_proc)
    if server_proc is not None:
        server_proc.terminate()