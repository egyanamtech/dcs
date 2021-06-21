import os
import shutil
import stat
import subprocess
import sys


class DCScaffold:
    """DCScaffold is the container class for the Docker-Compose Scaffold commands
    This can be used along with a CLI generation library such as click
    """

    DOCKER_USER = None
    FRONTEND_DIR = None
    BACKEND_DIR = None
    CLONE = None
    REPO_BASE = None
    FRONTEND_REPO = None
    BACKEND_REPO = None
    BACKEND_PATH = None
    FRONTEND_PATH = None
    CWD = None
    DIRNAME = None

    def __init__(self, d_user, f_dir, b_dir, f_repo, b_repo, cwd, clone, repo_base):
        """The class constructor for the DCScaffold Class

        :param d_user: The docker User, in case you specify the user in docker-compose.yml
        :type d_user: string
        :param f_dir: The directory where the frontend service will be cloned
        :type f_dir: string
        :param b_dir: The directory where the backend service will be cloned
        :type b_dir: string
        :param f_repo: The repo where the frontend service is hosted
        :type f_repo: string
        :param b_repo: The repo where the frontend service is hosted
        :type b_repo: string
        :param cwd: The directory where the services will be saved
        :type cwd: string
        :param clone: The command to clone the repositories
        :type clone: string
        :param repo_base: The base of the repos
        :type repo_base: string
        """
        self.DOCKER_USER = d_user
        self.FRONTEND_DIR = f_dir
        self.BACKEND_DIR = b_dir
        self.FRONTEND_REPO = f_repo
        self.BACKEND_REPO = b_repo
        self.CWD = cwd
        self.CLONE = clone
        self.REPO_BASE = repo_base
        self.BACKEND_PATH = os.path.join(self.CWD, self.BACKEND_DIR)
        self.FRONTEND_PATH = os.path.join(self.CWD, self.FRONTEND_DIR)
        self.DIRNAME = os.path.basename(self.CWD)

    def _remove_readonly(self, func, path, _):
        """Clear the readonly bit and reattempt the removal
        :param func: The function to run
        :type func: function
        :param path: The path
        :type path: string
        :param _: [description]
        :type _: [type]
        """
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def remove_folders(self, only_tag, frontend_tag, frontend_branch, backend_branch, backend_tag):
        """Remove the service folders if specified"""
        dir_list = []
        if only_tag:
            if frontend_branch:
                dir_list.append(self.FRONTEND_PATH)
            elif frontend_tag:
                dir_list.append(self.FRONTEND_PATH)
            elif backend_branch:
                dir_list.append(self.BACKEND_PATH)
            elif backend_tag:
                dir_list.append(self.BACKEND_PATH)
        else:
            dir_list.append(self.FRONTEND_PATH)
            dir_list.append(self.BACKEND_PATH)

        subprocess.run(f"{self.DOCKER_USER} docker-compose down", shell=True)
        for x in dir_list:
            try:
                shutil.rmtree(x, onerror=self._remove_readonly)
            except FileNotFoundError:
                print("No folder to delete.")
            except Exception as e:
                print("Exception :", e)
                print("You cannot proceed to run script")
                sys.exit(-1)

    def clone_backend_frontend(self, BRANCH_DATA, REPO, DIR, PATH):

        clone_command = f"{self.CLONE} --single-branch --depth=1 {BRANCH_DATA} {self.REPO_BASE}{REPO} {DIR}"
        fr_isdir = os.path.isdir(PATH)
        if fr_isdir:
            print("Repos already cloned")
        else:
            print("cloning")
            res = subprocess.run(clone_command, shell=True, capture_output=True)
            a = str(res.stderr)
            if res.returncode == 128:
                error = a[:-3].endswith("not found in upstream origin")
                if error:
                    print(
                        f"ERROR: The {DIR[5:]} branch/tag '{BRANCH_DATA}' not avaialable to origin"
                    )
                else:
                    print("You may have slow internet or NO internet.\n", res.stderr)
                sys.exit(-1)

    def clone_repos(self, frontend_branch, backend_branch, frontend_tag, backend_tag, only_tag, remove):
        """Clones the repos specified, with the specified branch or tag.
        Only one of tag or branch is allowed for each service

        :param frontend_branch: The branch to clone for the frontend branch
        :type frontend_branch: string
        :param backend_branch: The branch to clone for the backend branch
        :type backend_branch: string
        :param frontend_tag: The tag to clone for the frontend branch
        :type frontend_tag: string
        :param backend_tag: The tag to clone for the backend branch
        :type backend_tag: string
        """
        if only_tag:
            branches_to_check = [frontend_branch, frontend_tag, backend_tag, backend_branch]
            actual_sum = sum(map(bool, branches_to_check))

            if actual_sum != 1:
                # continue processing if sum == 1
                print("you must specify one, and only one of the following for using the --only flag:")
                print("--frontend-branch")
                print("--frontend-tag")
                print("--backend-branch")
                print("--backend-tag")
                sys.exit(-1)

        if remove:
            self.remove_folders(only_tag, frontend_tag, frontend_branch, backend_branch, backend_tag)
            print("in remove")
        subprocess.run("git config --global credential.helper store", shell=True)
        F_BRANCH_DATA = ""
        B_BRANCH_DATA = ""

        if frontend_branch:
            F_BRANCH_DATA = f"-b {frontend_branch}"
        elif frontend_tag:
            F_BRANCH_DATA = f"-b {frontend_tag}"
        if only_tag:
            if F_BRANCH_DATA != "":
                self.clone_backend_frontend(F_BRANCH_DATA, self.FRONTEND_REPO, self.FRONTEND_DIR, self.FRONTEND_PATH)

        else:
            self.clone_backend_frontend(F_BRANCH_DATA, self.FRONTEND_REPO, self.FRONTEND_DIR, self.FRONTEND_PATH)

        if backend_branch:
            B_BRANCH_DATA = f"-b {backend_branch}"

        elif backend_tag:
            B_BRANCH_DATA = f"-b {backend_tag}"
        if only_tag:
            if B_BRANCH_DATA != "":
                self.clone_backend_frontend(B_BRANCH_DATA, self.BACKEND_REPO, self.BACKEND_DIR, self.BACKEND_PATH)

        else:
            self.clone_backend_frontend(B_BRANCH_DATA, self.BACKEND_REPO, self.BACKEND_DIR, self.BACKEND_PATH)

        subprocess.run("git config --global --unset credential.helper", shell=True)

    def docker_sql_commands(self, sql_file):
        print("docker sql commands")

        # Builds, (re)creates, starts, and attaches to containers for a service in (-d) Detached mode: Run containers in the background.
        # Services of frontend,backend and database will be started and attached to the container.
        subprocess.run(f"{self.DOCKER_USER} docker-compose up  -d ", shell=True)

        # step 1, copy the sql_file to the container
        # The docker cp utility copies the contents of SRC_PATH to the DEST_PATH.
        # You can copy from the container’s file system to the local machine or the reverse, from the local filesystem to the container
        # sql_file copied into database container(i.e. into parham_docker_db_1)
        sql1 = f"{self.DOCKER_USER} docker cp {sql_file} {self.DIRNAME}_db_1:/tmp"
        subprocess.run(sql1, shell=True)

        # step 2, import the sql file
        # It will import the sql file into container, data of the sql_file will come under operation/process for frontend and backend.
        sql2 = f"{self.DOCKER_USER} docker exec -it  {self.DIRNAME}_db_1 psql -U postgres postgres -f /tmp/{sql_file}"
        subprocess.run(sql2, shell=True)

        # # step 3, delete the sql file from the container
        # After importing sql file into container again no need to keep the sql file in the container.
        # So command will delete the sql file from the container.
        sql3 = f"{self.DOCKER_USER} docker exec -it  {self.DIRNAME}_db_1 rm /tmp/{sql_file}"
        subprocess.run(sql3, shell=True)

    def show_logs(self, app, outfile, follow_logs):
        """displays/generates logs of specified app and stores in file"""
        pipe_into = ""
        if outfile:
            pipe_into = f"| tee {outfile}"
        f_log = ""
        if follow_logs:
            f_log = "-f"
        subprocess.run(
            f"{self.DOCKER_USER} docker-compose logs {f_log} {app} {pipe_into}",
            shell=True,
        )

    def rebuild_cont(self, flags):
        if flags:
            print(flags)
        cmd = f"{self.DOCKER_USER} docker-compose build {flags}"
        print("cmd", cmd)
        subprocess.run(f"{self.DOCKER_USER} docker-compose down", shell=True)
        subprocess.run(cmd, shell=True)
        subprocess.run(f"{self.DOCKER_USER} docker-compose up -d ", shell=True)

    def run_djangoshell(self):
        """opens interactive django shell directly"""
        print("Django Shell")
        subprocess.run(
            f"{self.DOCKER_USER} docker exec -it {self.DIRNAME}_backend_1 python manage.py shell",
            shell=True,
        )

    def run_dumpdb(self, sql_file):
        """creates backup of current DB and dumps new DB file in docker"""
        print("Dumping db into docker")
        shutil.copyfile(
            os.path.join(self.CWD, sql_file), os.path.join(self.CWD, f"{sql_file}.bak")
        )
        subprocess.run(
            f"{self.DOCKER_USER} docker exec -t {self.DIRNAME}_db_1 pg_dump -U postgres -O -x postgres > {sql_file}",
            shell=True,
        )
        print("Done")

    def run_test(self, section):
        """runs the test suites for specified section."""
        print("Checking tests...")
        res = section[1:]
        if section[0] == "frontend":
            command = f"docker-compose exec frontend npm run test {' '.join(res)}"

        if section[0] == "backend":
            command = f"docker-compose exec backend pytest {' '.join(res)}"

        print(command)
        subprocess.run(command, shell=True)

    def run_up(self):
        """starts the containers for docker services.\n
        Builds, (re)creates, starts, and attaches to containers for a service."""
        print("Starting the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose up  -d ", shell=True)

    def run_down(self):
        """stops containers and removes containers created by up """
        print("Stopping the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose down", shell=True)

    def run_ps(self):
        """shows all running containers by default """
        print("Checking the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose ps -a", shell=True)

    def run_restart(self):
        """restarts the containers for docker services"""
        print("Restarting the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose restart", shell=True)

    def run_stop(self):
        """stops the containers without down-ing them"""
        print("Stopping the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose stop", shell=True)

    def run_start(self):
        """starts the stopped the containers """
        print("Stopping the services...")
        subprocess.run(f"{self.DOCKER_USER} docker-compose start", shell=True)

    def run_restart_app(self, app):
        """restarts the specified app/service container"""
        basepath = os.path.basename(self.CWD)
        print(f"Restarting the service: {app}")
        subprocess.run(
            f"{self.DOCKER_USER} docker restart {basepath}_{app}_1", shell=True
        )

    def test_docker(self):
        result = subprocess.run(
            f"{self.DOCKER_USER} docker ps", capture_output=True, shell=True
        )
        if result.stdout:
            print("Docker is running.")
        if result.stderr:
            print("Docker is not running. Please start your docker.")
            sys.exit(-1)
