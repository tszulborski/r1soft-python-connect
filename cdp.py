# -*- coding: utf-8 -*-

# Python connector for R1Soft Server Backup Manager.
# Copyright (C) 2017 Tomasz Szulborski
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ssl, datetime
from suds.client import Client

class cdp(object):

    # Initialize base data
    def __init__(self, host, port, user, password):
        ssl._create_default_https_context = ssl._create_unverified_context
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        self.agent_client = Client('https://' + self.host + ':' + self.port + '/Agent?wsdl', username=self.user, password=self.password, timeout=300)
        self.disksafe_client = Client('https://' + self.host + ':' + self.port + '/DiskSafe?wsdl', username=self.user, password=self.password, timeout=300)
        self.recoverypoints_client = Client('https://' + self.host + ':' + self.port + '/RecoveryPoints2?wsdl', username=self.user, password=self.password, timeout=300)
        self.taskhistory_client = Client('https://' + self.host + ':' + self.port + '/TaskHistory?wsdl', username=self.user, password=self.password, timeout=300)

    # Get all agents list from the backup server
    def _get_agents(self):
        agents = self.agent_client.service.getAgents()
        return agents

    # Get agent object by description
    def _get_agent(self, name):
        agents = self._get_agents()
        for agent in agents:
            if agent['description'] == name:
                return agent

        return None

    # Get disksafe object for the agent
    def _get_disksafe(self, agent):
        return self.disksafe_client.service.getDiskSafesForAgent(agent)

    # Get recovery points for the disksafe
    def _get_recoverypoints(self, disksafe):
        return self.recoverypoints_client.service.getRecoveryPoints(disksafe['id'], True)

    # Get backup points for the server
    def get_backups(self, name):
        backups = []

        agent = self._get_agent(name)
        if not agent:
            return None

        disksafe = self._get_disksafe(agent)[0]
        recoverypoints = self._get_recoverypoints(disksafe)

        for recoverypoint in recoverypoints:

            # Pass the recoverypoint that is not available for restore
            if recoverypoint['recoveryPointState'] != "AVAILABLE":
                continue

            backup = {}
            backup['server_name'] = name
            backup['date'] = datetime.datetime.fromtimestamp(recoverypoint['createdOnTimestampInMillis']/1000)
            backup['recoverypoint_id'] = recoverypoint['recoveryPointID']
            backup['disksafe_id'] = disksafe['id']
            backups.append(backup)

        return backups

    # Get files for the recovery point and path
    def get_files(self, disksafe_id, recoverypoint_id, path):
        recoverypoint = self.recoverypoints_client.service.getRecoveryPointByID(disksafe_id, recoverypoint_id)
        directory_entries = self.recoverypoints_client.service.getDirectoryEntries(recoverypoint, path)
        return self.recoverypoints_client.service.getMultipleFileEntryInformation(recoverypoint, path, directory_entries)

    # Get databases for the recovery point
    def get_databases(self, disksafe_id, recoverypoint_id):
        instance_id = self.recoverypoints_client.service.getMySQLDatabaseInstances(disksafe_id, recoverypoint_id)[0]['id']
        return self.recoverypoints_client.service.getMySQLDatabaseNames(disksafe_id, recoverypoint_id, instance_id)

    # Start restore files process
    def restore_files(self, disksafe_id, recoverypoint_id, path, files):
        recoverypoint = self.recoverypoints_client.service.getRecoveryPointByID(disksafe_id, recoverypoint_id)

        # Restore settings
        restore_opts = self.recoverypoints_client.factory.create('fileRestoreOptions')
        restore_opts.basePath = path
        restore_opts.fileNames = files
        restore_opts.useCompression = True
        restore_opts.overwriteExistingFiles = True
        restore_opts.useOriginalHost = True
        restore_opts.restoreToAlternateLocation = False
        restore_opts.estimateRestoreSize = True

        # Start recovery process and return task id
        task = self.recoverypoints_client.service.doFileRestore(recoverypoint, restore_opts)
        if task:
            return task['id']

        return None

    # Start restore MySQL databases process
    def restore_databases(self, disksafe_id, recoverypoint_id, databases):
        instance_id = self.recoverypoints_client.service.getMySQLDatabaseInstances(disksafe_id, recoverypoint_id)[0]['id']

        # Restore settings
        restore_info = self.recoverypoints_client.factory.create('mySQLDatabaseRestore')
        restore_info.databaseNames = databases

        # Start recovery process and return task id
        task = self.recoverypoints_client.service.scheduleSimpleMySQLRestore(disksafe_id, recoverypoint_id, instance_id, restore_info)
        if task:
            return task

        return None

    # Get task status
    def task_status(self, task_id):
        return self.taskhistory_client.service.getTaskExecutionContextByID(task_id)
