# Adapted from RenolY2/DebugYoshi's dolphin-memory-lib
# https://github.com/RenolY2/dolphin-memory-lib

import ctypes
import struct
from struct import pack, unpack
from ctypes import wintypes, sizeof, addressof, POINTER, pointer
from ctypes.wintypes import DWORD, ULONG, LONG, WORD
from multiprocessing import shared_memory

# Various Windows structs/enums needed for operation
NULL = 0

TH32CS_SNAPHEAPLIST = 0x00000001
TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPALL = TH32CS_SNAPHEAPLIST | TH32CS_SNAPPROCESS | TH32CS_SNAPTHREAD | TH32CS_SNAPMODULE
assert TH32CS_SNAPALL == 0xF


PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020

MEM_MAPPED = 0x40000

ULONG_PTR = ctypes.c_ulonglong


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', DWORD),
                ('cntUsage', DWORD),
                ('th32ProcessID', DWORD),
                ('th32DefaultHeapID', ctypes.POINTER(ULONG)),
                ('th32ModuleID', DWORD),
                ('cntThreads', DWORD),
                ('th32ParentProcessID', DWORD),
                ('pcPriClassBase', LONG),
                ('dwFlags', DWORD),
                ('szExeFile', ctypes.c_char * 260)]


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', DWORD),
                ('PartitionID', WORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', DWORD),
                ('Protect', DWORD),
                ('Type', DWORD)]


class PSAPI_WORKING_SET_EX_BLOCK(ctypes.Structure):
    _fields_ = [('Flags', ULONG_PTR),
                ('Valid', ULONG_PTR),
                ('ShareCount', ULONG_PTR),
                ('Win32Protection', ULONG_PTR),
                ('Shared', ULONG_PTR),
                ('Node', ULONG_PTR),
                ('Locked', ULONG_PTR),
                ('LargePage', ULONG_PTR),
                ('Reserved', ULONG_PTR),
                ('Bad', ULONG_PTR),
                ('ReservedUlong', ULONG_PTR)]


# class PSAPI_WORKING_SET_EX_INFORMATION(ctypes.Structure):
#    _fields_ = [    ( 'VirtualAddress' , ctypes.c_void_p),
#                    ( 'VirtualAttributes' , PSAPI_WORKING_SET_EX_BLOCK)]

class PSAPI_WORKING_SET_EX_INFORMATION(ctypes.Structure):
    _fields_ = [('VirtualAddress', ctypes.c_void_p),
                #( 'Flags', ULONG_PTR),
                ('Valid', ULONG_PTR, 1)]
    #( 'ShareCount', ULONG_PTR),
    #( 'Win32Protection', ULONG_PTR),
    #( 'Shared', ULONG_PTR),
    #( 'Node', ULONG_PTR),
    #( 'Locked', ULONG_PTR),
    #( 'LargePage', ULONG_PTR),
    #( 'Reserved', ULONG_PTR),
    #( 'Bad', ULONG_PTR),
    # ( 'ReservedUlong', ULONG_PTR)]

    # def print_values(self):
    #    for i,v in self._fields_:
    #        print(i, getattr(self, i))


# The find_dolphin function is based on WindowsDolphinProcess::findPID() from
# aldelaro5's Dolphin memory engine
# https://github.com/aldelaro5/Dolphin-memory-engine

"""
MIT License
Copyright (c) 2017 aldelaro5
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


class Dolphin(object):
    def __init__(self):
        self.pid = -1
        self.memory = None

    def reset(self):
        self.pid = -1
        self.memory = None

    def find_dolphin(self, skip_pids=[]):
        entry = PROCESSENTRY32()

        entry.dwSize = sizeof(PROCESSENTRY32)
        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(
            TH32CS_SNAPPROCESS, NULL)
        print(addressof(entry), hex(addressof(entry)))
        a = ULONG(addressof(entry))

        self.pid = -1

        if ctypes.windll.kernel32.Process32First(snapshot, pointer(entry)):
            if entry.th32ProcessID not in skip_pids and entry.szExeFile in (b"Dolphin.exe", b"DolphinQt2.exe", b"DolphinWx.exe"):
                self.pid = entry.th32ProcessID
            else:
                while ctypes.windll.kernel32.Process32Next(snapshot, pointer(entry)):
                    if entry.th32ProcessID in skip_pids:
                        continue
                    if entry.szExeFile in (b"Dolphin.exe", b"DolphinQt2.exe", b"DolphinWx.exe"):
                        self.pid = entry.th32ProcessID

        ctypes.windll.kernel32.CloseHandle(snapshot)

        if self.pid == -1:
            return False

        return True

    def init_shared_memory(self):
        try:
            self.memory = shared_memory.SharedMemory(
                'dolphin-emu.'+str(self.pid))
            return True
        except FileNotFoundError:
            return False

    def read_ram(self, offset, size):
        return self.memory.buf[offset:offset+size]

    def write_ram(self, offset, data):
        self.memory.buf[offset:offset+len(data)] = data

    def read_uint32(self, addr):
        assert addr >= 0x80000000
        value = self.read_ram(addr-0x80000000, 4)

        return unpack(">I", value)[0]

    def write_uint32(self, addr, val):
        assert addr >= 0x80000000
        return self.write_ram(addr - 0x80000000, pack(">I", val))

    def read_float(self, addr):
        assert addr >= 0x80000000
        value = self.read_ram(addr - 0x80000000, 4)

        return unpack(">f", value)[0]

    def write_float(self, addr, val):
        assert addr >= 0x80000000
        return self.write_ram(addr - 0x80000000, pack(">f", val))


"""with open("ctypes.txt", "w") as f:
    for a in ctypes.__dict__:
        f.write(str(a))
        f.write("\n")"""


def ms_to_time(ms):
    import math
    mins = str(math.floor(ms / 1000 / 60))
    ms = ms % 60000
    seconds = math.floor(ms / 1000)
    seconds = str.rjust(str(seconds), 2, '0')
    ms = str.rjust(str(ms % 1000), 3, '0')
    return mins + ':' + seconds + '.' + ms


if __name__ == "__main__":
    import time
    from constants import course_ids, course_index
    dolphin = Dolphin()

    if dolphin.find_dolphin():
        print("Found Dolphin!")
    else:
        print("Didn't find Dolphin")

    print(dolphin.pid)

    dolphin.init_shared_memory()
    if dolphin.init_shared_memory():
        print("Found MEM1 and/or MEM2!")
    else:
        print("Didn't find MEM1 and/or MEM2")

    # these values may be different for you
    p1_timer_address = 0x810A33F0
    p3_timer_address = 0x810B4B80
    # p3_timer_address = 0x810D6758 # this is another address that seems to store the same value
    current_track_address = 0x803CB6A8

    track_order = []
    times1 = [0] * 16
    times2 = [0] * 16
    track = 0x24  # Luigi Circuit
    track_order.append(course_ids[track])

    # wait for first track to start
    RACE_STARTED = 5999999
    while dolphin.read_uint32(p1_timer_address) != RACE_STARTED and dolphin.read_uint32(p3_timer_address) != RACE_STARTED:
        time.sleep(1)

    print("Grand Prix started")
    while len(track_order) <= 16:
        if dolphin.read_uint32(p1_timer_address) != RACE_STARTED and dolphin.read_uint32(p3_timer_address) != RACE_STARTED:
            p1_time = ms_to_time(dolphin.read_uint32(p1_timer_address))
            p3_time = ms_to_time(dolphin.read_uint32(p3_timer_address))
            times1[course_index[course_ids[track]]] = p1_time
            times2[course_index[course_ids[track]]] = p3_time
            if len(track_order) < 16:
                while dolphin.read_uint32(current_track_address) == track:
                    time.sleep(5)
                track = dolphin.read_uint32(current_track_address)
                track_order.append(course_ids[track])
                print(times1)
                print(times2)
                print("Next Track: " + course_ids[track])
        time.sleep(1)

    print('track order')
    print('["' + '", "'.join(track_order) + '"]')
    print('p1 times')
    print(','.join(times1))
    print('p3 times')
    print(','.join(times2))
