from flask import *
from werkzeug import *
import os
import shutil
import unzipper
import signal
import sys

UPLOAD_FOLDER = './repos'
ALLOWED_EXTENSIONS = {"zip"}

app = Flask(__name__)
app.secret_key = 'super secret key'

secret = "FAKE_SECRET_KEY_LULZ"
users = {}
sessions = {}

semgrep_processes = {}

semgrep_rules = [
    "r/csharp.dotnet.security.audit.ldap-injection.ldap-injection",
    "r/csharp.lang.security.injections.os-command.os-command-injection",
    "r/csharp.dotnet.security.audit.mass-assignment.mass-assignment"
]

def signal_handler(sig, frame):
    unzipper.kill_unzipper()
    sys.exit(0)

@app.route('/')
def index():
    print(request)
    return render_template('index.html', data="")

@app.route("/list/rules")
def listrules():
    return jsonify({"rules": semgrep_rules})

@app.route("/list/repos")
def listrepos():
    repo_contents = os.listdir("./repos")
    zipfiles = []
    repos = []
    for file in repo_contents:
        if file[-4:] == ".zip":
            zipfiles.append(file)
        else:
            repos.append(file)
    return jsonify({"repos": repos, "zips": zipfiles})

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


@app.route('/newjob', methods=["GET", "POST"])
def newjob():
    if request.method == "GET":
        return render_template(
            'new_job.html', 
            form_title="New Job",
            submit_path="/newjob",
            submit_button_title="run job",
            rules=semgrep_rules
            )
    elif request.method == "POST":
        print(request.form)
        return "success"

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

signal.signal(signal.SIGINT, signal_handler)

unzipper.run_unzipper()
app.run()