from random import choice
import os

from wtforms import Form, BooleanField, TextField, PasswordField, validators
from flask import render_template, redirect, url_for, abort, flash
from flask import Flask, g, request, session

""" ccp_flask.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (c) 2015 David Michael Pennington
     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.
     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.
     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.
     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""

ALL_CHARS = r"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
ALL_NUMS = r"1234567890"


def _random_secret_key():
    ## Build a random key for flask if it wasn't already specified
    return "".join(choice(ALL_CHARS + ALL_NUMS) for ii in range(48))


def run(password="", debug=False, host="127.0.0.1", port=8282):
    SECRET_KEY = os.environ.get("CCP_FLASK_KEY", False) or _random_secret_key()
    USERNAME = os.environ.get("CCP_FLASK_ADMIN_USER", False) or "admin"
    PASSWORD = password or "ciscoconfparse"
    app = Flask(__name__)
    app.config.from_object(__name__)
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run()
