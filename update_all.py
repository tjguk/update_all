from __future__ import print_function
import os, sys
import fnmatch
import subprocess
import time

def svn_update(dirpath):
    basename = os.path.basename(dirpath)
    print("svn: %s" % (basename))
    os.chdir(dirpath)
    subprocess.call(["svn", "up", "--ignore-externals"])
    print("")

def hg_update(dirpath):
    print("hg: %s" % (os.path.basename(dirpath)))
    os.chdir(dirpath)
    subprocess.call(["hg", "pull", "--update", "--verbose"])
    print("")

def git_update(dirpath):
    print("git: %s" % (os.path.basename(dirpath)))
    os.chdir(dirpath)
    for bline in subprocess.check_output(["git", "status"]).splitlines():
        line = bline.decode("utf-8")
        branch_preamble = "On branch "
        if line.startswith(branch_preamble):
            branch = line[len(branch_preamble):]
            break
    else:
        branch = ""
            
    for bremote in subprocess.check_output(["git", "remote"]).splitlines():
        remote = bremote.decode("utf-8")
        if remote == "origin":
            command = "pull"
        else:
            command = "fetch"
        print(command, remote, "=>", end=" ")
        subprocess.call(["git", command, "--verbose", remote, branch])
        print("")

    print("")

def main(root="."):
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
            svn_update(dirpath)
        elif os.path.isdir(os.path.join(dirpath, ".hg")):
            hg_update(dirpath)
        elif os.path.isdir(os.path.join(dirpath, ".git")):
            git_update(dirpath)

        complete_filepath = os.path.join(dirpath, "complete.cmd")
        if os.path.isfile(complete_filepath):
            subprocess.call([complete_filepath], shell=True)
        
        test_filepath = os.path.join(dirpath, "run-tests.cmd")
        log_filepath = os.path.join(dirpath, "tests.log")
        if os.path.isfile(test_filepath):
            subprocess.call([test_filepath], shell=True)
            os.startfile(log_filepath)

    print("=" * len("FINISHED: %s" % root))
    print("FINISHED: %s at %s" % (root, time.asctime()))

if __name__ == '__main__':
    main(*sys.argv[1:])
