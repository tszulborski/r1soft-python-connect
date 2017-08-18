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

from cdp import cdp

# SET THIS
host = "XXXXX"
port = "9443"
username = "XXXXX"
password = "XXXXX"

# Connect to backup server
server = cdp(host, port, username, password)

# Get available backup points
backups = server.get_backups("u1")

# Display files from backup root directory
print server.get_files(backups[0]['disksafe_id'], backups[0]['recoverypoint_id'], '/')

# Display MySQL databases
print server.get_databases(backups[0]['disksafe_id'], backups[0]['recoverypoint_id'])
