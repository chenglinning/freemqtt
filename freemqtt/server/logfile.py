# Copyright (C) ben-ning@163.com
# All rights reserved
#
import os
LOG_FILE_MAXIM_SIZE = 2097152 # 2*1024*1024

class LogFile(object):
    def __init__(self, fname):
        self.total = 0
        self.fname = fname
        self.file = open(fname, 'w')
        path = os.getcwd()
        log_path = f"{path}/log"
        file_list = [f for f in os.listdir(log_path) if os.path.isfile(f)]
        fnum = len(file_list) % 10
        self.fnum = fnum if fnum>0 else 1

    def write(self, text):
        if self.total >= LOG_FILE_MAXIM_SIZE:
            self.close()
            backup_log_file = f"{self.fname}.{self.fnum}"
            fnum = (self.fnum + 1) % 10
            self.fnum = fnum if fnum>0 else 1
            if os.path.exists(backup_log_file):
                os.remove(backup_log_file)
            os.rename(self.fname, backup_log_file)
            self.file = open(self.fname, 'w')
            self.total = 0

        self.file.write(text)
        self.flush()
        self.total += len(text)

    def flush(self):
        self.file.flush()

    def fileno(self):
        return self.file.fileno()

    def close(self):
        self.file.close()
