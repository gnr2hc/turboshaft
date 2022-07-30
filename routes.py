# -*- coding: utf-8 -*-


import os
from datetime import datetime
from pathlib import Path

import htmlmin
from flask import abort
from flask import current_app as app
from flask import (jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_cors import cross_origin
from tbs import const as CONST


@app.route('/')
@app.route('/index.html')
def index():
    return redirect(url_for('pages', page='test-execution.html'))


@app.route('/<page>')
def pages(page):
    try:
        projectBaseName = app.cfg.get('projectDir', '').split('/')[-1]
        data = {
            'sidebar': request.cookies.get('sidebar'),
            'projectBaseName': projectBaseName,
            'projectName': projectBaseName.replace('_', ' '),
            'swVariant': app.cfg.get('swVariant'),
            'version': CONST.APP_VERSION,
        }
        html = render_template(page, **data)

        return htmlmin.minify(html, remove_comments=True, remove_all_empty_space=True)

    except Exception as e:
        app.logger.exception(e)


@app.route('/raw/reports/')
@app.route('/raw/reports/<path:basepath>')
def raw_report(basepath=''):
    try:
        dir_project = app.cfg.get('projectDir', '')
        dir_report = Path(dir_project).joinpath('reports')

        path = dir_report.joinpath(basepath)

        if path.is_file():

            return send_from_directory(dir_report, basepath)

        else:
            dirpath = '/raw/reports/{basepath}'.format(basepath=basepath)
            lstChild = get_list_files(path, basepath)

            data = {
                'directory': dirpath,
                'sidebar': 'collapsed',
                'lstChild': lstChild,
                'hideMenu': 1
            }

            return render_template('files.html', **data)

    except Exception as e:
        app.logger.exception(e)


@app.route('/img/variants/<image>', methods=['GET'])
def image_variants(image):
    try:
        dir_project = app.cfg.get('projectDir')
        directory = Path(dir_project).joinpath('Variants', 'Images')
        if directory.joinpath(image).is_file():
            return send_from_directory(directory, image)

    except Exception as e:
        app.logger.exception(e)


@app.route('/api/lab/info', methods=['GET'])
@cross_origin()
def lab_info():
    try:
        response = {}
        status = 200

        lst_key = ['projectDir', 'swVariant', 'swSAD', 'swCrashcode', 'testbenchOpt', 'gitBranchName', 'isBusy']
        for key in lst_key:
            response.update({key: app.cfg.get(key)})

    except Exception as e:
        app.logger.exception(e)

    finally:
        return jsonify(response), status


def get_list_files(dirpath, basepath):
    '''Get list files from directory to render index page.

    Args:
        dirpath (str): path to directory
        basepath (str): basepath url

    Returns:
        list: list of files
            {name: name, url: url}
    '''
    lstChild = [{'name': '../', 'url': '..'}]

    lst_path = sorted(Path(dirpath).iterdir(),
                      key=os.path.getmtime, reverse=True)

    for item in lst_path:

        name = item.name
        name = name if item.is_file() else '{0}/'.format(name)

        url = '/raw/reports/{0}/{1}'.format(basepath, name)
        url = url.replace('//', '/')

        timestamp = item.lstat().st_mtime
        modified = datetime.fromtimestamp(timestamp)
        modified = modified.strftime("%Y-%m-%d %H:%M:%S")

        dct = {
            'name': name,
            'url': url,
            'modified': modified
        }

        lstChild.append(dct)

    return lstChild
