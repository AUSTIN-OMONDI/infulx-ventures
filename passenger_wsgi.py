"""Entry point for cPanel / Passenger hosting (Truehost, HostPinnacle and similar).

cPanel's "Setup Python App" looks for this file in the application root and
imports `application` from it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "infulx")

# the shop package lives in the infulx/ folder
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app as application  # noqa: E402

if __name__ == "__main__":
    application.run()
