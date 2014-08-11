#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import time
import sys

debug = 10
info = 20
warn = 30
error = 40
critical = 50
off = 100

lvldata = {10: ['DEBUG', '\033[1;97m'],
           20: ['INFO', '\033[1;92m'],
           30: ['WARN', '\033[1;94m'],
           40: ['ERROR', '\033[1;91m'],
           50: ['CRITICAL', '\033[1;95m'],
}

count = 0

logfile = "/var/log/ratnav/service.log"
verbosity = {'global': debug,
             'file': off,
             'console': debug}

start = time.time()


def log(*what, **kwargs):
    if 'lvl' in kwargs:
        lvl = kwargs['lvl']
        if lvl < verbosity['global']:
            return
    else:
        lvl = info

    global count
    global start
    count += 1

    now = time.time() - start
    msg = "[%s] : %5s : %.5f : %5i :" % (time.asctime(),
                                         lvldata[lvl][0],
                                         now,
                                         count)

    for thing in what:
        msg += " "
        msg += str(thing)

    if lvl >= verbosity['file']:
        try:
            f = open(logfile, "a")
            f.write(msg)
            f.flush()
            f.close()
        except IOError:
            print("Can't open logfile for writing!")
            sys.exit(23)

    if lvl >= verbosity['console']:
        print(lvldata[lvl][1], str(msg), '\033[0m')