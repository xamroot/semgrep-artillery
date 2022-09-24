from flask import *
from werkzeug import *
import os
import shutil
import signal
import sys
import json
import argparse
import lib.endpoints as endpoint
import lib.utils as artillery_utils
import lib.unzipper as unzipper
import lib.semgrepper as semgrepper


UPLOAD_FOLDER = './repos'
ALLOWED_EXTENSIONS = {"zip"}
secret = "FAKE_SECRET_KEY_LULZ"
debug = False

template_dir = os.path.abspath('./templates')
repos_dir = os.path.abspath('./repos')

users = {}
sessions = {}
semgrep_processes = {}
semgrep_rules = [
    "r/csharp.dotnet.security.audit.ldap-injection.ldap-injection",
    "r/csharp.lang.security.injections.os-command.os-command-injection",
    "r/csharp.dotnet.security.audit.mass-assignment.mass-assignment",
    "r/csharp.lang.security.insecure-deserialization.binary-formatter.insecure-binaryformatter-deserialization"
]

# parse args
parser = argparse.ArgumentParser(description="Collaborative semgrep interface for team based engagements to standardize semgrep output and centralize the storage of output data")
parser.add_argument('--debug', 
                    action=argparse.BooleanOptionalAction, 
                    help='a debug flag for running tests')
args = vars(parser.parse_args())
if args["debug"] == True:
    debug = True

# set up utility config
artillery_utils.config(repos_dir, debug)

app = Flask(__name__,template_folder=template_dir)
app.secret_key = secret

def signal_handler(sig, frame):
    unzipper.kill_unzipper()
    semgrepper.kill_semgrepper()
    sys.exit(0)

@app.route('/')
def index():
    return render_template('index.html', data="")

@app.route("/list/rules")
def listrules():
    return jsonify({"rules": semgrep_rules})

@app.route("/list/repos")
def listrepos():
    return jsonify(artillery_utils.list_repos())

@app.route('/repos', methods=["GET", "POST", "DELETE"])
def repos():
    if request.method == "GET":
        return render_template(
            'repos.html'
            )
    elif request.method == "POST":
        print(request.files["file"])
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return "fail"
        # file uploaded exists, run checks should be a new a zip file
        # then save zip file (will be unzipped by unzipper thread)
        if file:
            filename = file.filename
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            unzipped_filepath = filepath.split(".zip")[0]
            # check whether zip already exists or has been unzipped 
            if os.path.exists(unzipped_filepath) or os.path.exists(filepath):
                return "repo already exists"
            # save repo and return success
            else:
                file.save(filepath)
                return "success"
    elif request.method == "DELETE":
        filename = request.data.decode()
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(filepath):
            if filename in semgrep_processes:
                return jsonify({"error": "repo in use by semgrep"})
            else:
                shutil.rmtree(filepath)
                return jsonify({"message": "success"})
        else:
            return jsonify({"error": "repo does not exist"})


@app.route('/stats', methods=["GET"])
def stats():
    if request.method == "GET":
        return render_template(
            'status.html'
            )

@app.route('/newjob', methods=["GET", "POST"])
def newjob():
    if request.method == "GET":
        return endpoint.newjob_get()
    elif request.method == "POST":
        body = json.loads(request.get_data().decode())
        return endpoint.newjob_post(body)


@app.route('/jobs/running', methods=["GET"])
def jobs_running():
    if request.method == "GET":
        return endpoint.jobsrunning_get()

@app.route('/jobs/queued', methods=["GET"])
def jobs_queued():
    if request.method == "GET":
        return endpoint.jobsqueued_get()

@app.route('/jobs/list/<index>', methods=["GET"])
def jobs_list(index):
    PAGINATION_SIZE = 10
    if request.method == "GET":
        index = int(index)
        end_index = index+1
        return endpoint.jobs_get(index*PAGINATION_SIZE, end_index*PAGINATION_SIZE)

@app.route("/job/<jid>", methods=["GET"])
def job_status(jid):
    if request.method == "GET":
        return endpoint.jobstatus_get(jid)

@app.route("/job/<jid>/results", methods=["GET"])
def job_results(jid):
    if request.method == "GET":
        return endpoint.jobresults_get(jid)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template(
            'login.html', 
            form_title="Log In",
            submit_path="/login",
            submit_button_title="login",
            )
    elif request.method == "POST":
        return "success"

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template(
            'signup.html', 
            form_title="Sign Up",
            submit_path="/signup",
            submit_button_title="signup",
            )
    elif request.method == "POST":
        return "success"


# finish set up
signal.signal(signal.SIGINT, signal_handler)
# begin helper threads
unzipper.run_unzipper(repos_dir)
semgrepper.run_semgrepper()
# run app
app.run()