# Copyright 2018 Bailey Defino
# <https://bdefino.github.io>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
__package__ = __name__

import os
import socket
import sys
import time

from lib import baseserver, conf

__doc__ = """log incoming data via TCP
Usage: python logd.py [OPTIONS]
OPTIONS
\t-a, --address=ADDRESS\taddress
\t\tdefaults to the highest IP version possible, on an OS-provided port
\t\tIPv4 example: "127.0.0.1:8888"
\t\tIPv6 example: "[::1]:8888"
\t-c, --config=PATH\tconfiguration file
\t\te.g.
\t\t\t[server] # the default IPv6 server
\t\t\taddress: [::1]:8888
\t\t\troot: .
\t-h, --help\tdisplay this text and exit
\t-r, --root=PATH\troot directory"""

class Logd(baseserver.BaseServer):
    def __init__(self, root = os.getcwd(), *args, **kwargs):
        baseserver.BaseServer.__init__(self, baseserver.event.ConnectionEvent,
            LogdHandler, *args, **kwargs)
        self.root = root

        if not os.path.exists(self.root):
            os.makedirs(self.root)
        elif not os.path.isdir(self.root):
            raise OSError("root (\"%s\") exists, and isn't a directory"
                % self.root)

class LogdHandler(baseserver.event.Handler):
    def __init__(self, *args, **kwargs):
        baseserver.event.Handler.__init__(self, *args, **kwargs)
        self.event.conn.settimeout(self.event.server.sock_config.TIMEOUT)
        self.path = os.path.join(self.event.server.root,
            baseserver.atos(self.event.remote), str(round(time.time(), 10))) \
            + ".dat"
        dir = os.path.dirname(self.path)
        
        if not os.path.exists(dir):
            os.makedirs(dir)
        elif not os.path.isdir(dir):
            raise OSError("\"%s\" exists, and isn't a directory" % dir)
        self.fp = open(self.path, "wb")
    
    def next(self):
        try:
            self.fp.write(self.event.conn.recv(
                self.event.server.sock_config.BUFLEN))
            self.fp.flush()
            os.fdatasync(self.fp.fileno())
        except socket.timeout:
            pass
        except (IOError, OSError): # also covers socket.error
            self.event.conn.close()
            raise StopIteration

if __name__ == "__main__":
    class AddressConfig(baseserver.TCPConfig):
        pass
    
    i = 1
    root = os.getcwd()

    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg.startswith("--"):
            arg = arg[2:]

            if arg == "address":
                if i == len(sys.argv) - 1:
                    print "Argument required."
                    sys.exit()

                try:
                    AddressConfig.ADDRESS = baseserver.stoa(sys.argv[i + 1])
                except:
                    print "Invalid address."
                    sys.exit()
                i += 1
            elif arg == "config":
                if i == len(sys.argv) - 1:
                    print "Argument required."
                    sys.exit()

                try:
                    config = conf.Conf(open(sys.argv[i + 1]))
                    
                    if config:
                        if "address" in config[0]:
                            AddressConfig.ADDRESS = baseserver.stoa(
                                config[0]["address"])
                        root = config[0].get("root", root)
                except:
                    print "Invalid configuration file."
                    sys.exit()
                i += 1
            elif arg == "help":
                print __doc__
                sys.exit()
            elif arg == "root":
                if i == len(sys.argv) - 1:
                    print "Argument required."
                    sys.exit()
                i += 1
                root = sys.argv[i]
            else:
                "Invalid option."
                sys.exit()
        elif arg.startswith("-"):
            for c in arg[1:]:
                if c == 'a':
                    if i == len(sys.argv) - 1:
                        print "Argument required."
                        sys.exit()

                    try:
                        AddressConfig.ADDRESS = baseserver.stoa(
                            sys.argv[i + 1])
                    except:
                        print "Invalid address."
                        sys.exit()
                    i += 1
                elif c == 'c':
                    if i == len(sys.argv) - 1:
                        print "Argument required."
                        sys.exit()

                    try:
                        config = conf.Conf(open(sys.argv[i + 1]))
                        
                        if config:
                            if "address" in config[0]:
                                AddressConfig.ADDRESS = baseserver.stoa(
                                    config[0]["address"])
                            root = os.path.realpath(os.path.join(
                                    os.path.dirname(sys.argv[i + 1]),
                                    config[0].get("root", root)))
                    except:
                        print "Invalid configuration file."
                        sys.exit()
                    i += 1
                elif c == 'h':
                    print __doc__
                    sys.exit()
                elif c == 'r':
                    if i == len(sys.argv) - 1:
                        print "Argument required."
                        sys.exit()
                    i += 1
                    root = sys.argv[i]
                else:
                    print "Invalid option."
                    sys.exit()
        i += 1
    
    #mkconfig
    
    server = Logd(root, AddressConfig)
    server.thread(baseserver.threaded.Pipelining(nthreads = 4))
    server()
