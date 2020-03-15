from flask import Flask

app = Flask(__name__)

from covid19app import routes
