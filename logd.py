#!/bin/python
import os
import socket
import sys
import time
import traceback

__doc__ = """logd - UDP log daemon
Usage: ./logd.py [-d DIR] [IFACE[:PORT]]
DIR
	output directory
IFACE
	listening interface (defaults to "" wildcard)
PORT
	listening port (defaults to 55555)"""

UDP_CAPACITY = 65536
UDP_DATA_CAPACITY = UDP_CAPACITY - 8 # remove header length

class LogD:
    def __init__(self, addr, _dir = os.getcwd()):
        self.addr = addr
        self.dir = _dir

    def __call__(self):
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        _sock.settimeout(0.1)
        _sock.bind(self.addr)

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        elif not os.path.isdir(self.dir):
            _sock.close()
            raise OSError("\"%s\" exists and isn't a directory" % self.dir)
        print "[*] Running LogD on %s:%u in \"%s\"" % (self.addr[0], self.addr[1], self.dir)

        try:
            while 1:
                time.sleep(0.1) # not REALLY necessary, but we don't want to overuse the CPU

                try:
                    data, remote = _sock.recvfrom(UDP_DATA_CAPACITY)
                except socket.timeout:
                    continue
                path = os.path.realpath(os.path.join(self.dir, remote[0], str(remote[1]), "%f" % time.time()))
                _dir = os.path.dirname(path)
                print "[+] Received %u octets from %s:%u into \"%s\"" % (len(data), remote[0], remote[1], path)

                if not os.path.exists(_dir):
                    os.makedirs(_dir)
                elif not os.path.isdir(_dir):
                    raise OSError("\"%s\" exists, and isn't a directory" % _dir)

                with open(path, "wb") as fp:
                    fp.write(data)
                    os.fdatasync(fp.fileno())
                del data, remote
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print >> sys.stderr, "[!] LogD encountered fatal error:"
            print >> sys.stderr, traceback.format_exc(e)
        finally:
            print "[*] Closing LogD on %s:%u..." % self.addr
            _sock.close()
            print "[*] Closed LogD."

if __name__ == "__main__":
    addr = ['', 55555]
    argv = sys.argv[1:]
    _dir = os.getcwd()
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg == "-d":
            if i + 1 >= len(argv):
                print "Argument required."
                print __doc__
                sys.exit(1)
            _dir = argv[i + 1]
            i += 1
        else:
            if ':' in arg:
                addr =  arg.rsplit(':', 1)

                try:
                    port = int(port)
                except:
                    print "Expected integer."
                    print __doc__
                    sys.exit(1)
            else:
                addr[0] = arg
        i += 1
    LogD(tuple(addr), _dir)()
