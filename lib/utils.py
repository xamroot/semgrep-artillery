import os

repos_dir = ""
debug_flag = False

def config(_repos_dir, _debug_flag):
    global repos_dir 
    global debug_flag
    repos_dir = _repos_dir
    debug_flag = _debug_flag

def is_debug():
    return debug_flag

def get_repos_dir():
    global repos_dir
    return repos_dir

def check_repo_existance(repo):
    if repo in os.listdir(repos_dir):
        return True
    return False

def list_repos():
    global repos_dir
    repo_contents = os.listdir(repos_dir)
    zipfiles = []
    repos = []
    for file in repo_contents:
        if file[-4:] == ".zip":
            zipfiles.append(file)
        else:
            repos.append(file)
    return {"repos": repos, "zips": zipfiles}