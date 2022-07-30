# -*- coding: utf-8 -*-


import re
import time

from flask import current_app as app
from flask_socketio import emit
from tbs import Workspace
from tbs import const as CONST

from . import socketio, tasks


@socketio.on('connect', namespace='/tbs')
def connect():
    # Check authorize
    if (app.cfg.get('is_expired') == True):
        socketio.emit('version_expired', namespace='/tbs')


@socketio.on('config_init', namespace='/tbs')
def config_init():
    emit('config_init', app.cfg)


@socketio.on('config_update', namespace='/tbs')
def config_update(info):
    if 'projectDir' in info:
        info.update({
            'swVariant': None,
        })

    if 'swVariant' in info:
        info.update({
            'swSAD': None,
            'swCrashcode': None,
        })

    if app.cfg.get('isBusy') or app.cfg.get('is_reserving'):
        emit('config_update_failed', {})

    else:
        tasks.config.save_config(info)
        emit('config_update_success', {})

        tasks.sync_config()
        tasks.sync_workspace()


@socketio.on('branch_change', namespace='/tbs')
def branch_change(branch):
    dir_project = app.cfg.get('projectDir')

    workspace = Workspace(dir_project)
    workspace.switch_branch(branch)

    emit('branch_change_success', {})

    tasks.sync_config()
    tasks.sync_workspace()


@socketio.on('lift_sync_status', namespace='/tbs')
def lift_update():
    tasks.sync_liftstatus()


@socketio.on('log_sync', namespace='/tbs')
def log_sync(data):

    while True:

        try:
            response = get_lift_log(data.get('lastLine', 0), data.get('oldestLine', -500))
            if (response.get('lastLine', 0) > data.get('lastLine', 0)):
                emit('log_sync_data', response)

            data.update({'lastLine': response.get('lastLine', 0)})

        except Exception as e:
            app.logger.exception(e)

        time.sleep(1)


def get_lift_log(line_number, oldest_line):
    '''Get TurboLIFT running console.

    Args:
        line (int): from line number

    Returns:
        dict: console log content
            text (str) from line to end
            line (int) line number
    '''
    def strip_ansi(text):
        ansi_escape3 = re.compile(
            r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]', flags=re.IGNORECASE)
        text = ansi_escape3.sub('', text)
        return text

    filepath = CONST.LIFT_PATH_LOG
    lst = []
    with open(filepath) as fp:
        count = 0
        for line in fp:
            count += 1
            if count < line_number + 1:
                continue

            lst.append(line)

    text = ''.join(lst)
    text = strip_ansi(text) + '\n'

    data = {
        'text': text,
        'lastLine': count
    }

    return data
