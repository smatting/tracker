#!/usr/bin/env python3
'''
Determine user activity by listening to X events (e.g. mouse, keyboard)
and log 5-minute-binnted activity to ~/.tracker/YYYY-MM-DD files

You can also register user activity by signalling SIGUP to the process.
'''

import datetime
import time
import os
import signal
import sys
import subprocess
import threading

# timestamp of last activity in UTC secs
t_last_activity = None

def handler(signum, frame):
    global t_last_activity
    t = time.time()
    print(t, 'registering activity')
    t_last_activity =  time.time()

def bin_time(dt):
    minute = dt.minute - dt.minute % 5
    return dt.replace(minute=minute, second=0, microsecond=0)

def bin_inc(dt):
    return dt + datetime.timedelta(seconds=60*5)

def bin_dec(dt):
    return dt - datetime.timedelta(seconds=60*5)

def secs_until_next():
    datetime.datetime.now()

def main2():
    t = time.time()
    now = datetime.datetime.now()
    print(t, now.timestamp(), t - now.timestamp())

def bin_to_string(dt):
    return dt.strftime('%H:%M')

def read_last_line(p):
    with open(p, 'r', encoding='utf8') as f:
        for line in f:
            if line != '':
                last_line = line
    return last_line

def get_pidfile():
    return os.path.expanduser('~/.tracker.pid')

def read_pidfile(p):
    try:
        with open(p) as f:
            return int(f.read())
    except FileNotFoundError:
        return None

def log_active_bin(dt):
    fn = dt.strftime('%Y-%m-%d')
    p = os.path.expanduser(f'~/.tracker/{fn}')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    dt_str = bin_to_string(dt)
    if os.path.exists(p):
        dt_last = read_last_line(p)
        if dt_last == dt_str:
            return
    with open(p, 'a', encoding='utf8') as f:
        f.write(f'{dt_str}\n')

def main():
    def listen():
        global t_last_activity
        p = subprocess.Popen(['xinput', 'test-xi2', '--root'], stdout=subprocess.PIPE)
        for line in p.stdout:
            t = time.time()
            t_last_activity = time.time()

    thread = threading.Thread(target=listen)
    thread.start()

    try:
        own_pid = os.getpid()
        pidfile = get_pidfile()
        if os.path.exists(pidfile):
            print(f'Pidfile {pidfile} already exists. Maybe already running?')
            sys.exit(1)

        with open(pidfile, 'w') as f:
            f.write(str(own_pid))

        # Set the signal handler and a 5-second alarm
        signal.signal(signal.SIGHUP, handler)
        while True:
            t = datetime.datetime.now()
            current_bin = bin_time(t)
            next_bin = bin_inc(current_bin)
            sleep = (next_bin - t).total_seconds()
            print('current_bin', bin_to_string(current_bin))
            time.sleep(sleep)
            # at the end of current_bin
            if t_last_activity is not None:
                if t_last_activity > current_bin.timestamp():
                    print('user was active during the last 5 minutes')
                    log_active_bin(current_bin)
                else:
                    print('user was inactive during the last 5 minutes')
    finally:
        try:
            os.remove(pidfile)
        except FileNotFoundError:
            pass
        thread.join()


if __name__ == '__main__':
    main()
