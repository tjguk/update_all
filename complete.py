#!python2
import os, sys
import pysvn

from winsys import fs
import pyodbc

SERVER_PORTS = [
    ("gldbheatooh", 10010),
    ("SVR-DB-HEAT", 1433),
    ("SRVDBHEAT", 1433),
    ("EMG-DB1-PRD", 1433),
]

db = None
for (server_name, port) in SERVER_PORTS:
    try:
        db = pyodbc.connect(driver="SQL Server", server=server_name, database="HEAT", user="heat", password="heat", port=port)
    except:
        print "Unable to connect to", server_name
        continue
    else:
        break
else:
    raise RuntimeError("Unable to connect to any HEAT database")

svn = pysvn.Client()
PREFIX_PREFIXES = {"ONHOLD", "mg"}
PREFIX_SUFFIXES = {"", " ", "."}
PREFIXES = [p + s for p in PREFIX_PREFIXES for s in PREFIX_SUFFIXES]

def call_is_closed(call_id):
    for call in db.execute(
        "SELECT CallStatus FROM CallLog WHERE CallID = ?",
        [call_id.zfill(8)]
    ):
        return call.CallStatus == 'Closed'

def go(relative_root=".", relative_release="release", relative_completed="_Completed", relative_tests="tests"):
    root = fs.dir(os.getcwd()) + relative_root
    release = fs.dir(root) + relative_release
    completed = fs.dir(root) + relative_completed
    tests = fs.dir(root) + relative_tests
    print "Starting from =>", root
    print "Release =>", release
    print "Completed =>", completed
    if tests:
        print "Tests =>", tests
    else:
        print "No tests"

    print "Updating..."
    svn.update(unicode(release), unicode(completed))

    for folder in sorted(release.dirs()):
        call_name = folder.name
        for prefix in PREFIXES:
            if folder.name.startswith(prefix):
                call_name = folder.name[len(prefix):]
                break

        heat_call = call_name.split()[0]
        if heat_call.isdigit ():
            print "HEAT Call:", heat_call
            if call_is_closed(heat_call):
                to_checkin = []
                try:
                    if tests:
                        test_folder = folder.dir("tests")
                        if test_folder:
                            tested_folder = tests + (call_name.lstrip("0"))
                            svn.copy(unicode(test_folder), unicode(tested_folder))
                            to_checkin.append(unicode(tested_folder))
                    completed_folder = base_completed_folder = completed + call_name.lstrip("0")
                    for i in range(1, 10):
                        #
                        # If the folder already exists, loop round a few possibles until we succeed
                        #
                        if not completed_folder:
                            break
                        completed_folder = fs.dir("%s - %d" % (unicode(base_completed_folder).rstrip("\\"), i))
                    else:
                        print("All versions of folder name already taken; skipping")
                        continue

                    svn.move(unicode(folder), unicode(completed_folder))
                    to_checkin.append(unicode(folder))
                    to_checkin.append(unicode(completed_folder))
                    svn.checkin(
                        to_checkin,
                        "Tidying up closed calls: #%s" % heat_call
                    )
                except pysvn.ClientError, err:
                    print "ERROR:", err
                else:
                    print "Changes committed"

    print

if __name__ == '__main__':
    go(*sys.argv[1:])
