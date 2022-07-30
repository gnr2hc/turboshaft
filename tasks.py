# -*- coding: utf-8 -*-

import os
from pathlib import Path

import version
from tbs import Config, TurboLIFT, Workspace

from . import scheduler, socketio

config = Config()
lift = TurboLIFT()


@scheduler.task(
    "interval",
    id="sync_config",
    seconds=5,
    max_instances=1,
)
def task_sync_config():
    sync_config()
    sync_workspace()


@scheduler.task(
    "interval",
    id="sync_lift",
    seconds=3,
    max_instances=1,
)
def task_sync_lift():
    sync_liftstatus()


@scheduler.task(
    "interval",
    id="check_version",
    seconds=60,
    max_instances=1,
)
def task_check_version():
    check_expired()


def check_expired():
    with scheduler.app.app_context():
        is_expired = version.is_expired()
        scheduler.app.cfg.update({'is_expired': is_expired})
        if is_expired:
            socketio.emit('version_expired', namespace='/tbs')


def sync_config():
    # Check config file
    with scheduler.app.app_context():
        mtime = os.path.getmtime(config.file_config)

        if scheduler.app.cfg_mtime is None or scheduler.app.cfg_mtime != mtime:
            data = config.get_config()

            # Broadcast change
            broadcast_config_changed(data)

#check commit
def sync_workspace():
    # Check workspace
    with scheduler.app.app_context():
        data = {}
        try:
            directory = scheduler.app.cfg.get('projectDir')
            workspace = Workspace(directory)

            # Git branch
            gitBranchNameOptions = workspace.get_branches()
            gitActiveBranch = workspace.get_active_branch()
            gitBranchName = gitBranchNameOptions.get(gitActiveBranch)

            data = {
                'swVariantOptions': workspace.get_variants(),

                'gitBranchNameOptions': gitBranchNameOptions,
                'gitBranchName': gitBranchName,

                'testlist': workspace.get_testlists(),

                'tsRepo': workspace.get_testscript_data(),
            }

            # Variant data
            variant = scheduler.app.cfg.get('swVariant')
            variant_config = workspace.get_variant_config(variant)

            if variant_config != {}:
                crash_options = {v: k for k, v in variant_config.get('MappingCrashcode', {}).items()}

                # Update data
                data.update({
                    'swSADOptions': workspace.get_sads(variant),
                    'swCrashcodeOptions': crash_options,
                })
            else:
                data.update({
                    'swVariant': None,

                    'swSAD': None,
                    'swCrashcode': None,

                    'swSADOptions': {},
                    'swCrashcodeOptions': {},
                })

                info = {
                    'swVariant': None,
                    'swSAD': None,
                    'swCrashcode': None,
                }
                config.save_config(info)

        except Exception as e:
            scheduler.app.logger.exception(e)

        finally:
            # Broadcast change
            broadcast_config_changed(data)


def sync_liftstatus():
    with scheduler.app.app_context():
        data = {}
        try:
            # LIFT status
            status = lift.get_running_status()
            isBusy = status.get('pid') != None

            isBusy = isBusy or scheduler.app.cfg.get('is_reserving') is True

            data.update({
                'isBusy': isBusy
            })

            # LIFT latest report
            dir_project = scheduler.app.cfg.get('projectDir')
            dir_report = Path(dir_project).joinpath('reports')

            report = lift.get_latest_report(dir_report)
            report.update({
                'isBusy': isBusy,
                'token': scheduler.app.cfg.get('token')
            })

            data.update({
                'report': report
            })

        except Exception as e:
            scheduler.app.logger.exception(e)

        finally:
            # Broadcast change
            broadcast_config_changed(data)


def broadcast_config_changed(data):
    with scheduler.app.app_context():

        # Get the changed info
        updated_info = {k: v for k, v in data.items()
                        if scheduler.app.cfg.get(k) != v}

        if updated_info:
            if ('isBusy' in updated_info):
                updated_info.update({
                    'token': scheduler.app.cfg.get('token')
                })

            socketio.emit('config_changed', updated_info, namespace='/tbs')

        # Update data to context
        scheduler.app.cfg.update(data)
