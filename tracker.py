#!/usr/bin/env python3

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

def notify_tracker(pid, pidfile):
    if pid is None:
        pid = read_pidfile(pidfile)

    try:
        if pid is not None:
            os.kill(pid, signal.SIGHUP)
    except ProcessLookupError:
        pid = read_pidfile(pidfile)

    return pid


def main_keyboard(pidfile):
    import keyboard
    pid = read_pidfile(pidfile)
    while True:
        try:
            e = keyboard.read_event()
            t = time.time()
            print(t, 'keyboard activity')
            pid = notify_tracker(pid, pidfile)
        except ImportError:
            raise
        except Exception:
            time.sleep(1)

def main_mouse():
    t_last = time.time()


    pidfile = get_pidfile()
    pid = read_pidfile(pidfile)

    def listen():
        nonlocal t_last
        p = subprocess.Popen(['xinput', 'test-xi2', '--root'], stdout=subprocess.PIPE)
        for line in p.stdout:
            t_last = time.time()

    thread = threading.Thread(target=listen)
    thread.start()

    try:
        while True:
            t = time.time()
            if t - t_last < 1.0:
                print(t, 'mouse activity')
                pid = notify_tracker(pid, pidfile)
            time.sleep(1)
    except:
        raise
    finally:
        thread.join()


def main():
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
            print('current_bin', current_bin)
            print('sleep', sleep)
            time.sleep(sleep)
            # at the end of current_bin
            if t_last_activity is not None:
                if t_last_activity > current_bin.timestamp():
                    print('logging active bin')
                    log_active_bin(current_bin)
                else:
                    print('no activity')
    finally:
        try:
            os.remove(pidfile)
        except FileNotFoundError:
            pass


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'track':
        main()
    elif cmd == 'keyboard':
        pidfile = sys.argv[2]
        main_keyboard(pidfile)
    elif cmd == 'mouse':
        main_mouse()
    else:
        print(f'Unknown command {cmd}')
        sys.exit(1)
