# -*- coding: utf-8 -*-


from tbs import const as CONST
from version import stop_apps_on_port

from turboshaft import init_app, socketio

app = init_app()

if __name__ == '__main__':
    port = CONST.APP_PORT

    # Stop all app on port
    stop_apps_on_port(port)

    # Start app
    socketio.run(app, host='0.0.0.0', port=port)
