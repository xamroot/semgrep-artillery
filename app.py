from flask import *

UPLOAD_FOLDER = './repos'
ALLOWED_EXTENSIONS = {"zip"}

app = Flask(__name__)
app.secret_key = 'super secret key'

secret = "FAKE_SECRET_KEY_LULZ"
users = {}
sessions = {}

semgrep_rules = [
    "r/csharp.dotnet.security.audit.ldap-injection.ldap-injection",
    "r/csharp.lang.security.injections.os-command.os-command-injection",
    "r/csharp.dotnet.security.audit.mass-assignment.mass-assignment"
]


@app.route('/')
def index():
    print(request)
    return render_template('index.html', data="")

@app.route("/list/rules")
def listrules():
    return jsonify({"rules": semgrep_rules})

@app.route("/list/repos")
def listrepos():
    return jsonify({"repos": []})

@app.route('/repos', methods=["GET", "POST"])
def repos():
    if request.method == "GET":
        return render_template(
            'repos.html'
            )
    elif request.method == "POST":
        print("HIT")
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return "fail"
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return "success"

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

app.run()