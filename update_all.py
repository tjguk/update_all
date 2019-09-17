from __future__ import print_function
import os, sys
import argparse
import fnmatch
import glob
import subprocess
import time

def which(command):
    paths = ["."] + os.environ.get ("PATH", "").split (";")
    exts = [e.lower () for e in os.environ.get ("PATHEXT", ".exe").split (";")]

    base, ext = os.path.splitext(command)
    if ext: exts = [ext]

    for path in paths:
        for ext in exts:
            filepath = os.path.join(path, "%s%s" % (base, ext))
            for filename in glob.glob(filepath):
                return filename

SVN_COMMAND = which("svn")
if SVN_COMMAND:
    print("Subversion:", SVN_COMMAND)
else:
    print("Subversion not found")

HG_COMMAND = which("hg")
if HG_COMMAND:
    print("Mercurial:", HG_COMMAND)
else:
    print("Mercurial not found")

GIT_COMMAND = which("git")
if GIT_COMMAND:
    print("Git:", GIT_COMMAND)
else:
    print("Git not found")

def svn_update(dirpath):
    basename = os.path.basename(dirpath)
    print("svn: %s" % (basename))
    os.chdir(dirpath)
    subprocess.call([SVN_COMMAND, "up", "--ignore-externals"])
    print("")

def hg_update(dirpath):
    print("hg: %s" % (os.path.basename(dirpath)))
    os.chdir(dirpath)
    subprocess.call([HG_COMMAND, "pull", "--update", "--verbose"])
    print("")

def git_update(dirpath):
    print("git: %s" % (os.path.basename(dirpath)))
    os.chdir(dirpath)
    for bline in subprocess.check_output([GIT_COMMAND, "status"]).splitlines():
        line = bline.decode("utf-8")
        branch_preamble = "On branch "
        if line.startswith(branch_preamble):
            branch = line[len(branch_preamble):]
            break
    else:
        branch = ""

    for bremote in subprocess.check_output([GIT_COMMAND, "remote"]).splitlines():
        remote = bremote.decode("utf-8")
        if remote == "origin":
            command = "pull"
        else:
            command = "fetch"
        print(command, remote, "=>", end=" ")
        subprocess.call([GIT_COMMAND, command, "--verbose", remote, branch])
        print("")

    print("")

def main(root=".", do_tests=True, do_complete=True):
    no_tests = not do_tests
    no_complete = not do_complete

    root = os.path.abspath(root)
    noupdate_filepath = os.path.join(root, ".noupdate")
    update_filepath = os.path.join(root, ".update")
    dirs = []
    if os.path.isfile(update_filepath):
        dirs = [i.strip() for i in open(update_filepath).read().splitlines() if not i.startswith("#")]
    if dirs == []:
        dirs = ["*"]
    matching_dirs = []
    for dir in dirs:
        matching_dirs.extend(
            d for d in os.listdir(root)
                if fnmatch.fnmatch(d, dir)
                and not d.endswith(".noupdate")
                and not os.path.isfile(os.path.join(d, ".noupdate"))
        )

    print("UPDATING: %s at %s" % (root, time.asctime()))
    print("=" * len("UPDATING: %s" % root))

    already_seen = set()
    for dir in matching_dirs:
        dirpath = os.path.join(root, dir)
        if dirpath in already_seen:
            continue
        else:
            already_seen.add(dirpath)

        update_filepath = os.path.join(dirpath, ".update")
        if os.path.isfile(update_filepath):
            main(dirpath)
        elif os.path.isdir(os.path.join(dirpath, ".svn")):
            if SVN_COMMAND:
                svn_update(dirpath)
        elif os.path.isdir(os.path.join(dirpath, ".hg")):
            if HG_COMMAND:
                hg_update(dirpath)
        elif os.path.isdir(os.path.join(dirpath, ".git")):
            if GIT_COMMAND:
                git_update(dirpath)

        if not no_complete:
            complete_filepath = os.path.join(dirpath, "complete.cmd")
            if os.path.isfile(complete_filepath):
                subprocess.call([complete_filepath], shell=True)

        if not no_tests:
            test_filepath = os.path.join(dirpath, "run-tests.cmd")
            log_filepath = os.path.join(dirpath, "tests.log")
            if os.path.isfile(test_filepath):
                subprocess.call(["start", test_filepath], shell=True)

    print("=" * len("FINISHED: %s" % root))
    print("FINISHED: %s at %s" % (root, time.asctime()))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--no-tests", dest="tests", action="store_const", const=False, default=True)
    parser.add_argument("--no-complete", dest="complete", action="store_const", const=False, default=True)
    args = parser.parse_args()

    main(args.root, args.tests, args.complete)
