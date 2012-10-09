# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Functions for testing. Used by the unit tests, but also useful for
manual testing.
"""

import os
import sqlalchemy
import json
from sqlalchemy.sql import select
from bmm import model
from bmm import data
from bmm import config

inventory_id = 1

def create_sqlite_db(path, schema=False):
    config.set_config(db_engine = "sqlite:///" + path)
    if not os.path.isfile(path) or schema:
        create_db_schema()
    # reset the local "fake" stuff too
    global inventory_id
    inventory_id = 1

def create_db_schema():
    data.get_conn()
    model.metadata.create_all(data.engine)

def add_server(hostname):
    """
    Configure data for a server running at |hostname|.
    """
    data.get_conn().execute(model.imaging_servers.insert(), fqdn=hostname)

def add_board(board, server="server", state="offline",
              log=[], config={}, relayinfo=""):
    global inventory_id
    conn = data.get_conn()
    id = conn.execute(select([model.imaging_servers.c.id],
                              model.imaging_servers.c.fqdn==server)).fetchone()[0]
    if id is None:
        raise data.NotFound
    conn.execute(model.boards.insert(),
                 name=board,
                 fqdn=board, #XXX
                 inventory_id=inventory_id,
                 status=state,
                 mac_address='000000000000',
                 imaging_server_id=id,
                 relay_info=relayinfo,
                 boot_config=json.dumps(config))
    inventory_id += 1

def add_bootimage(name, version=1, description="Boot image",
                  pxe_config_filename="/path/to/image"):
    data.get_conn().execute(model.images.insert(), name=name,
                            version=version, description=description,
                            pxe_config_filename=pxe_config_filename)