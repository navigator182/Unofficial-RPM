#/******************************************************************************
#* Portions Copyright (C) 2007 Novell, Inc. All rights reserved.
#*
#* Redistribution and use in source and binary forms, with or without
#* modification, are permitted provided that the following conditions are met:
#*
#*  - Redistributions of source code must retain the above copyright notice,
#*    this list of conditions and the following disclaimer.
#*
#*  - Redistributions in binary form must reproduce the above copyright notice,
#*    this list of conditions and the following disclaimer in the documentation
#*    and/or other materials provided with the distribution.
#*
#*  - Neither the name of Novell, Inc. nor the names of its
#*    contributors may be used to endorse or promote products derived from this
#*    software without specific prior written permission.
#*
#* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
#* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#* IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#* ARE DISCLAIMED. IN NO EVENT SHALL Novell, Inc. OR THE CONTRIBUTORS
#* BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#* CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#* SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#* INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#* CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#* ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#* POSSIBILITY OF SUCH DAMAGE.
#*
#* Author: Brad Nicholes (bnicholes novell.com)
#******************************************************************************/

import os

OBSOLETE_POPEN = False
try:
    import subprocess
except ImportError:
    import popen2
    OBSOLETE_POPEN = True

import threading
import time

_WorkerThread = None  # Worker thread object
_glock = threading.Lock()   # Synchronization lock
_refresh_rate = 30  # Refresh rate of the netstat data

#Global dictionary storing the counts of the last connection state
# read from the netstat output
_conns = {'udp_established': 0,
        'udp_unconnected': 0,
        'udp_unknown': 0}


def UDP_Connections(name):
    '''Return the requested connection type status.'''
    global _WorkerThread

    if _WorkerThread is None:
        print 'Error: No netstat data gathering thread created for metric %s' % name
        return 0

    if not _WorkerThread.running and not _WorkerThread.shuttingdown:
        try:
            _WorkerThread.start()
        except (AssertionError, RuntimeError):
            pass

    #Read the last connection total for the state requested. The metric
    # name passed in matches the dictionary slot for the state value.
    _glock.acquire()
    ret = int(_conns[name])
    _glock.release()
    return ret

#Metric descriptions
_descriptors = [{'name': 'udp_established',
        'call_back': UDP_Connections,
        'time_max': 20,
        'value_type': 'uint',
        'units': 'Sockets',
        'slope': 'both',
        'format': '%u',
        'description': 'Total number of established UDP connections',
        'groups': 'network',
        },
    {'name': 'udp_unconnected',
        'call_back': UDP_Connections,
        'time_max': 20,
        'value_type': 'uint',
        'units': 'Sockets',
        'slope': 'both',
        'format': '%u',
        'description': 'Total number of unconnected UDP connections',
        'groups': 'network',
        },
    {'name': 'udp_unknown',
        'call_back': UDP_Connections,
        'time_max': 20,
        'value_type': 'uint',
        'units': 'Sockets',
        'slope': 'both',
        'format': '%u',
        'description': 'Total number of unknown UDP connections',
        'groups': 'network',
        }]


class NetstatThread(threading.Thread):
    '''This thread continually gathers the current states of the udp socket
    connections on the machine.  The refresh rate is controlled by the
    RefreshRate parameter that is passed in through the gmond.conf file.'''

    def __init__(self):
        threading.Thread.__init__(self)
        self.running = False
        self.shuttingdown = False
        self.popenChild = None

    def shutdown(self):
        self.shuttingdown = True
        if self.popenChild != None:
            try:
                self.popenChild.wait()
            except OSError, e:
                if e.errno == 10:  # No child processes
                    pass

        if not self.running:
            return
        self.join()

    def run(self):
        global _conns, _refresh_rate

        #Array positions for the connection type and state data
        # acquired from the netstat output.
        udp_at = 0
        udp_state_at = 0

        #Make a temporary copy of the udp connecton dictionary.
        tempconns = _conns.copy()

        #Set the state of the running thread
        self.running = True

        #Continue running until a shutdown event is indicated
        while not self.shuttingdown:
            if self.shuttingdown:
                break

            #Zero out the temporary connection state dictionary.
            for conn in tempconns:
                tempconns[conn] = 0

            #Call the netstat utility and split the output into separate lines
            if not OBSOLETE_POPEN:
                self.popenChild = subprocess.Popen(["/usr/sbin/ss", '-u', '-a', '-n'], stdout=subprocess.PIPE)
                lines = self.popenChild.communicate()[0].split('\n')
            else:
                self.popenChild = popen2.Popen3("/usr/sbin/ss -u -a -n")
                lines = self.popenChild.fromchild.readlines()

            try:
                self.popenChild.wait()
            except OSError, e:
                if e.errno == 10:  # No child process
                    continue

            #Iterate through the netstat output looking for the 'udp' keyword in the udp_at
            # position and the state information in the udp_state_at position. Count each
            # occurance of each state.
            for udp in lines:
                # skip empty lines
                if udp == '':
                    continue

                line = udp.split()
                if line[udp_at] != 'State':
                    if line[udp_state_at] == 'ESTAB':
                        tempconns['udp_established'] += 1
                    elif line[udp_state_at] == 'UNCONN':
                        tempconns['udp_unconnected'] += 1
                    elif line[udp_state_at] == 'UNKNOWN':
                        tempconns['udp_unknown'] += 1

            #Acquire a lock and copy the temporary connection state dictionary
            # to the global state dictionary.
            _glock.acquire()
            for conn in _conns:
                _conns[conn] = tempconns[conn]
            _glock.release()

            #Wait for the refresh_rate period before collecting the netstat data again.
            if not self.shuttingdown:
                time.sleep(_refresh_rate)

        #Set the current state of the thread after a shutdown has been indicated.
        self.running = False


def metric_init(params):
    '''Initialize the udp connection status module and create the
    metric definition dictionary object for each metric.'''
    global _refresh_rate, _WorkerThread

    #Read the refresh_rate from the gmond.conf parameters.
    if 'RefreshRate' in params:
        _refresh_rate = int(params['RefreshRate'])

    #Start the worker thread
    _WorkerThread = NetstatThread()

    #Return the metric descriptions to Gmond
    return _descriptors


def metric_cleanup():
    '''Clean up the metric module.'''

    #Tell the worker thread to shutdown
    _WorkerThread.shutdown()


#This code is for debugging and unit testing
if __name__ == '__main__':
    params = {'Refresh': '20'}
    metric_init(params)
    while True:
        try:
            for d in _descriptors:
                v = d['call_back'](d['name'])
                print 'value for %s is %u' % (d['name'],  v)
            time.sleep(5)
        except KeyboardInterrupt:
            os._exit(1)
