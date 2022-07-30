# -*- coding: utf-8 -*-


from engineio.async_drivers import threading
from flask import Flask
from flask_apscheduler import APScheduler
from flask_socketio import SocketIO, emit

from bp import api_files, api_lift

socketio = SocketIO()
scheduler = APScheduler()


def init_app():
    '''Initialize the core application.'''
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')

    with app.app_context():

        # Routes
        from . import events, routes, tasks

        # Blueprints
        app.register_blueprint(api_lift)
        app.register_blueprint(api_files)

        # Config
        app.cfg_mtime = None
        app.cfg = {}

        # Status
        app.is_busy = False

        # Socketio
        socketio.init_app(app, async_mode='threading')

        # Scheduler
        scheduler.init_app(app)
        scheduler.start()

        # Initial
        tasks.sync_config()
        tasks.sync_workspace()

        return app
