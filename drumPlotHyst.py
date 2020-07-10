import os
import numpy
import sys
import time
from obspy import UTCDateTime
from obspy.clients.filesystem.sds import Client
from obspy.clients.fdsn import Client
from matplotlib.backends.backend_agg import FigureCanvasAgg
# from obspy.clients.seedlink.basic_client import Client
from obspy.clients.seedlink.easyseedlink import create_client
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.stream import Stream
from obspy import read
import matplotlib.pyplot as plt
plt.switch_backend('agg')
from obspy import read_inventory

import threading
from threading import Thread

thread=Thread()

import png

import paramiko

from PIL import Image

dpi = 100
sizex = 800
sizey = 600
yRange = 0.1

hystType = [1440, 360, 180, 60]

band = {
    'low': [1, 20],
    'high': [20, 50]
}

rTWindow = 360
rtSft = 2

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!')
sftp = ssh_client.open_sftp()
inv = read_inventory("metadata/Braskem_metadata.xml")




class MyClient(EasySeedLinkClient):
    _traces =Stream()
    _inv = inv
    _rtSft = rtSft
    _lastData = UTCDateTime.now()
    _traces = Stream()
    _appTrace = Stream()
    _rTWindow = rTWindow

    def __init__(self,ip):
        EasySeedLinkClient.__init__(self,ip)
        #self.hyDr = drThread('H')
        #self.rtDr =drThread('RT')

    def plotDrum(self, filename='tmp.png'):
        try:
            self._appTrace.data = self._appTrace.data * 1000
            im = self._appTrace.plot(type='dayplot',
                                     dpi=dpi,
                                     x_labels_size=int(8 * 100 / int(dpi)),
                                     y_labels_size=int(8 * 100 / int(dpi)),
                                     title_size=int(1000 / int(dpi)),
                                     size=(sizex, sizey),
                                     color=('#AF0000', '#00AF00', '#0000AF'),
                                     # right_vertical_labels=True,

                                     vertical_scaling_range=yRange,
                                     # transparent=True,
                                     handle=True,
                                     time_offset=-3,
                                     data_unit='mm/s'
                                     # bgcolor='black',
                                     # grid_color='white',
                                     # face_color='black',+
                                     # show_y_UTC_label=False,
                                     # outfile='tmp.png'
                                     )
            im.savefig(filename)
            plt.close(im)

            return True
        except:
            print('ops,something wrong in plotting!!')
            return False

    def realTimeDrumPlot(self):

        for tr in self._traces:
            id = tr.get_id()
            print('rt '+id)
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]
            for b in band:
                fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(b) + '.png'
                self._appTrace = tr.copy()
                bb = band[b]
                self._appTrace.trim(UTCDateTime.now() - self._rTWindow * 60, UTCDateTime.now())
                self._appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                if self.plotDrum():
                    sftpMkdirs(sftp, '/RT/', 'uploads')
                    sftp.put('tmp.png', 'uploads/RT/' + fileNameRT)
                #print(fileNameRT)

    def hystDrumPlot(self):

        for tr in self._traces:
            id = tr.get_id()
            print('hyst '+id)
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]
            tEnd = UTCDateTime.now()

            for h in hystType:

                if tEnd.hour % int(h / 60) == 0:
                    for b in band:
                        tStart = tEnd - h * 60
                        p = network + '/' + station + '/' + channel + '/' + str(tEnd.year) + '/' + str(
                            tEnd.month) + '/' + str(
                            tEnd.day) + '/' + str(h) + '/' + str(b)

                        fileName = p + '/' + tStart.strftime("%Y%m%d%H%M%S") + '_' + tEnd.strftime(
                            "%Y%m%d%H%M%S") + '.png'

                        self._appTrace = tr.copy()
                        bb = band[b]
                        self._appTrace.trim(tStart, tEnd)
                        self._appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        if self.plotDrum('tmpH.png'):
                            sftpMkdirs(sftp, p, 'uploads')
                            sftp.put('tmpH.png', 'uploads/' + fileName)
                        #print(fileName)

    def align(self):
        if os.path.exists('traces.mseed'):
            self._traces = read('traces.mseed')

    def save(self):
        print('saving')
        self._traces.write('traces.mseed')
        print('saved')

    def on_data(self, traces):
        # if len(traces)==0:
        #     for trace in traces:
        #         trace
        tEnd = UTCDateTime.now()
        traces.remove_response(self._inv)
        self._traces += traces
        self._traces.merge(fill_value=0)
        self._traces.trim(tEnd - 1440 * 60, tEnd)
        print(tEnd)
        #print(self._traces)
        if (tEnd.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
        #if (tEnd.second % 30 == 0): #& (self._lastData.minute % self._rtSft != 0):
            # self.realTimeDrumPlot
            #self.rtDr.start(self._traces)
            #self.realTimeDrumPlot()

            rtThread = Thread(target=self.realTimeDrumPlot)
            rtThread.start()
            sThread=Thread(target=self.save)
            sThread.start()

        if (tEnd.minute == 0) & (self._lastData.minute != 0):
            #self.hyDr.start(self._traces)
            #self.hystDrumPlot()
            hyThread = Thread(target=self.hystDrumPlot)
            hyThread.start()
            # self.hystDrumPlot()
        self._lastData = tEnd


client = MyClient('172.16.8.10')



def sftpExist(p, path):
    try:
        p.stat(path)
        return True

    except IOError:
        return False


def sftpMkdirs(p, path, basePath):
    dirs = path.split('/')
    parPath = basePath
    for dir in dirs:
        parPath += '/' + dir
        if not sftpExist(p, parPath):
            p.mkdir(parPath)


client.select_stream('LK', 'BRK?', 'E??')
client.align()
client.run()
