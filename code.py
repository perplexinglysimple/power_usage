from __future__ import print_function
import os
import time
import  urllib.request, json 
import git
import struct
from subprocess import Popen,PIPE

power_gain = 0

class drive:
    def __init__(self):
       self.repo = git.Repo( './' )
    def upload_file(self, file, filename):
        try:
            self.repo.git.add(filename)
            self.repo.git.commit( m= filename + ' Is the file for this day. This was sampling every 60 seconds.')
            self.repo.git.push()
            power_gain = 0
        except git.exc.GitCommandError:
            print("We done messed up")

class Power_Dict:
    def __init__(self):
        self.dict_power = {"":-1}
        self.count = 0
    def append(self, ID, data):
        self.count = self.count + 1
        if ID in self.dict_power:
           temp = self.dict_power[ID]
           self.dict_power[ID] = data
           return data - temp
        else:
           self.dict_power[ID] = data
           return 0
    def count(self):
        self._temp = self.count
        self.count = 0
        return self._temp


class RotatingFileOpener:
    def __init__(self, path, mode='a', prepend="", append=""):
        if not os.path.isdir(path):
            raise FileNotFoundError("Can't open directory '{}' for data output.".format(path))
        self._path = path
        self._prepend = prepend
        self._append = append
        self._mode = mode
        self._day = time.localtime().tm_mday
        self.drive = drive()
    def __enter__(self):
        self._filename = self._format_filename()
        self._file = open(self._filename, self._mode)
        return self
    def __exit__(self, *args):
        return getattr(self._file, '__exit__')(*args)
    def _day_changed(self):
        return self._day != time.localtime().tm_mday
    def _format_filename(self):
        return os.path.join(self._path, "{}{}{}".format(self._prepend, time.strftime("%Y%m%d"), self._append))
    def write(self, *args):
        if self._day_changed():
            self._file.close()
            self.drive.upload_file(self._file, self._filename)
            self._file = open(self._format_filename(), self.mode)
        return getattr(self._file, 'write')(*args)
    def __getattr__(self, attr):
        return getattr(self._file, attr)
    def __iter__(self):
        return iter(self._file)

def decode_data(data):
    fieldwidths = (6, 10, -1, 11, -10, 8, -45, 7)  # negative widths represent ignored padding fields
    fmtstring = ' '.join('{}{}'.format(abs(fw), 'x' if fw < 0 else 's')
                        for fw in fieldwidths)
    fieldstruct = struct.Struct(fmtstring)
    parse = fieldstruct.unpack_from
    fields = parse(data)
    test,datet,timet,IDt,consumpt = fields
    return consumpt, IDt

#https://github.com/perplexinglysimple/power_usage

dict_power = Power_Dict()
file = RotatingFileOpener('./', prepend='power_data_new-', append='.txt')
meters_file = RotatingFileOpener('./', prepend='meters_saw_new-', append='.txt')
with meters_file as logger_meters:
 with file as logger:
  #A friend wrote this code to capture our houses data and put it in a text file for latter processing.
  pipe = Popen("/home/anthony/go/bin/rtlamr", shell=True, stdout=PIPE)
  counter = time.time()
  while pipe.poll() is None:
        output=pipe.stdout.readline()
        ID=str(output)[(str(output).find('ID:')+3):(str(output).find('Type:'))]
        if int(ID) == 53228632 or int(ID) == 53236473:
             print(str(output)[0:len(str(output))-3]+'\n')
             file_write=open('/home/anthony/Sept_12_start.txt','a')
             file_write.write(str(output.decode("utf-8"))[0:len(str(output.decode("utf-8")))]+'\n')
        if(int(counter) + 1*60 <= int(time.time())):
             temp = dict_power.count
             print(str(temp) + " this is how many this time")
             meters_file.write(str(temp) + ',' + str(time.time()) + '\n')
             logger.write(str(power_gain) + "," + str(time.time()) + "\n")
             counter = time.time()
        temp = decode_data(output)
        power_gain = power_gain + dict_power.append(str(temp[1].decode("utf-8")), int(temp[0].decode("utf-8")))
