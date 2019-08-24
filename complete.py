#!python2
import os, sys
import pysvn

from winsys import fs
import sql

db = sql.database("heat:heat@SRVDBHEAT/HEAT")
svn = pysvn.Client()
PREFIXES = {"ONHOLD"}

def call_is_closed(call_id):
    for call in sql.fetch_query(
        db, 
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
        for prefix_prefix in PREFIXES:
            for prefix_suffix in " ", ".":
                prefix = prefix_prefix + prefix_suffix
                if folder.name.startswith(prefix):
                    call_name = folder.name[1+len(prefix):]
                
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
                    completed_folder = completed + call_name.lstrip("0")
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
