"""Pull the latest code on a cPanel (Truehost) server.

Shared hosting has no Terminal, so run this from
cPanel -> Setup Python App -> "Execute python script":

    deploy/cpanel_update.py

Then click RESTART on the same page.

It throws away local edits inside the checkout first, because cPanel rewrites
passenger_wsgi.py whenever the Python app is saved and git refuses to pull over
it. Nothing that matters lives in tracked files: the database and the uploaded
photos are in data/ and static/uploads/, which git ignores.
"""
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def git(*args):
    out = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)
    print("$ git", " ".join(args))
    print(out.stdout.strip() or out.stderr.strip())
    if out.returncode:
        sys.exit(out.returncode)


git("checkout", "--", ".")
git("pull", "--ff-only")
print("\nDone. Now click RESTART on the Setup Python App page.")
