import sys, os
INTERP = os.path.join(os.environ['HOME'], 'myprojectenv', 'bin', 'python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from myapp import app as application 
