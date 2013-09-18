import os, sys
import fnmatch
import subprocess
import win32api

private_key_filepath = os.path.expandvars(r"%HOME%\.ssh\20120811.ppk")

def svn_update (dirpath):
  basename = os.path.basename (dirpath)
  print ("svn: %s" % (basename))
  os.chdir (dirpath)
  subprocess.call (["svn", "up", "--ignore-externals"])
  if os.path.isdir (os.path.join (dirpath, ".hg")):
    subprocess.call (["hg", "commit", "-m", '"svn up"'], shell=True)
  print

def hg_update (dirpath):
  print ("hg: %s" % (os.path.basename (dirpath)))
  os.chdir (dirpath)
  subprocess.call (["hg", "pull --update --rebase"])
  print

def git_update (dirpath):
  print ("git: %s" % (os.path.basename (dirpath)))
  os.chdir (dirpath)
  subprocess.call (["git", "pull"])
  print

def main (root="."):
  os.startfile(private_key_filepath)
  root = os.path.abspath (root)
  noupdate_filepath = os.path.join(root, ".noupdate")
  update_filepath = os.path.join (root, ".update")
  dirs = []
  if os.path.isfile (update_filepath):
    dirs = [i.strip () for i in open (update_filepath).read ().splitlines () if not i.startswith ("#")]
  if dirs == []:
    dirs = ["*"]
  matching_dirs = []
  for dir in dirs:
    matching_dirs.extend (
      d for d in os.listdir (root)
        if fnmatch.fnmatch (d, dir)
        and not d.endswith (".noupdate")
        and not os.path.isfile(os.path.join(d, ".noupdate"))
    )

  print ("UPDATING: %s" % root)
  print ("=" * len ("UPDATING: %s" % root))
  for dir in matching_dirs:
    dirpath = os.path.join (root, dir)
    update_filepath = os.path.join (dirpath, ".update")
    if os.path.isfile (update_filepath):
      main (dirpath)
    elif os.path.isdir (os.path.join (dirpath, ".svn")):
      svn_update (dirpath)
    elif os.path.isdir (os.path.join (dirpath, ".hg")):
      hg_update (dirpath)
    elif os.path.isdir (os.path.join (dirpath, ".git")):
      git_update (dirpath)
  print ("=" * len ("FINISHED: %s" % root))
  print ("FINISHED: %s" % root)

if __name__ == '__main__':
  main (*sys.argv[1:])
