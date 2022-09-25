from flask import *
import lib.utils as artillery_utils
import lib.semgrepper as semgrepper

def newjob_get():
    return render_template("new_job.html", data="")

def newjob_post(body):
    if "repo" not in body:
        return jsonify({"status_code": 200, "error": True, "message": "no repo selected"})
    if "rules" not in body or len(body["rules"]) < 1:
        return jsonify({"status_code": 200, "error": True, "message": "no rules selected"})
    else:
        tag = "None"
        if "tag" in body:
            tag = upper(body["tag"])
        # all needed params exist, validate given params
        repo = body["repo"]
        # ensure repo exists
        if not artillery_utils.check_repo_existance(repo):
            return jsonify({"status_code": 200, "error": True, "message": "repo does not exist"})
        # all validations passed!
        else:
            # debug stuff for tests before handling as normal
            job = {"repo": body["repo"], "rules": body["rules"], "tag":tag}
            if artillery_utils.is_debug():
                if "debug_timer" in body:
                    job["debug_timer"] = body["debug_timer"]
            # queue the new job with semgrepper
            jid = semgrepper.add_semgrep_job(job)
            return jsonify({"status_code": 200, "jobid": jid, "message": "succcess"})

def jobsrunning_get():
    return jsonify({"status_code":200, "jobs": semgrepper.get_running_jobs()})

def jobsqueued_get():
    return jsonify({"status_code":200, "jobs": semgrepper.get_queued_jobs()})

def jobstatus_get(jid):
    return jsonify({"status_code":200, "job": semgrepper.get_job(jid)})

def jobresults_get(jid):
    results = semgrepper.get_job_results(jid)
    if results is not None:
        return jsonify({"status_code":200, "results":results})
    else:
        return jsonify({"status_code":200, "error":True, "message":"Job either does not exist or has not finished being processed"})

def jobs_get(index):
    PAGINATION_SIZE = 10
    pagination_start = int(index) * PAGINATION_SIZE
    pagination_end = (int(index) + 1) * PAGINATION_SIZE
    jobs = semgrepper.get_jobs(pagination_start, pagination_end)
    if jobs is not None:
        return jsonify({"status_code":200, "jobs":jobs})
    else:
        return jsonify({"status_code":200, "error":True, "message":"Something went wrong"})

def resultslist_get(index, filters):
    PAGINATION_SIZE = 10
    pagination_start = int(index) * PAGINATION_SIZE
    pagination_end = (int(index) + 1) * PAGINATION_SIZE
    results = semgrepper.get_results(int(pagination_start), int(pagination_end), filters)
    if results is not None:
        return jsonify({"status_code":200, "results":results})
    else:
        return jsonify({"status_code":200, "error":True, "message":"Something went wrong"})

