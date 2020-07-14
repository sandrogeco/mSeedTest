

#sudo ./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

#openvpn --config clientBRASKEM__GEOAPP.con
#
# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/
import os
from obspy import UTCDateTime
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.stream import Stream
from obspy import read
import matplotlib.pyplot as plt
plt.switch_backend('agg')
from obspy import read_inventory

from threading import Thread

import json

import time
import paramiko


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

#inv = read_inventory("metadata/Braskem_metadata.xml")




class drumPlot(EasySeedLinkClient):
    _traces =Stream()
    _inv = read_inventory("metadata/Braskem_metadata.xml")
    _rtSft = rtSft
    _lastData = UTCDateTime.now()
    _traces = Stream()
    _appTrace = Stream()
    _drTrace =Stream()
    _drHTrace = Stream()
    _rTWindow = rTWindow
    _tEnd=UTCDateTime.now()
    _tNow = UTCDateTime.now()
    _rtRunning=False
    _hyRunning=False
    _saving=False
    _status={}

    def statusCalc(self):
        for tr in self._traces:
            id=tr.get_id()
            l=int(UTCDateTime.now()-tr.stats['endtime'])
            station=id.split('.')[1]
            self._status[station]={}
            self._status[station]["Noise Level"]="---"
            self._status[station]["Latency"]= str(l)+'s'
            self._status[station]["Voltage"]="---"
            self._status[station]["Color"]= "#FF0000"
        with open('geophone_network_status.json', 'w') as fp:
             json.dump(self._status, fp)
        sftp.put('geophone_network_status.json', 'uploads/RT/' + 'geophone_network_status.json')

    def singleStatusCalc(self,tr):
        id = tr.get_id()
        station = id.split('.')[1]
        l = int(UTCDateTime.now() - tr.stats['endtime'])
        self._status[station] = {}
        self._status[station]["Noise Level"] = "---"
        self._status[station]["Latency"] = str(l) + 's'
        self._status[station]["Voltage"] = "---"
        self._status[station]["Color"] = "#FF0000"

    def plotDrum(self, trace,filename='tmp.png'):
        #trace.resample(50)
        try:
            #self._appTrace.data = self._appTrace.data * 1000#/3.650539e+08
            trace.data=trace.data*1000
            im = trace.plot(type='dayplot',
                                     dpi=dpi,
                                     x_labels_size=int(8 * 100 / int(dpi)),
                                     y_labels_size=int(8 * 100 / int(dpi)),
                                     title_size=int(1000 / int(dpi)),
                                     title=self._tEnd.strftime("%Y/%m/%d"),
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
        print('start ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        appTrace=Stream()
        self._rtRunning=True
        for tr in self._traces:
            id = tr.get_id()
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]
            l = int(self._tEnd - tr.stats['endtime'])
            self._status[station] = {}
            self._status[station]["Noise Level"] = "---"
            self._status[station]["Latency"] = str(l) + 's'
            self._status[station]["Voltage"] = "---"
            self._status[station]["Color"] = "#FF0000"

            for b in band:
                fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(b) + '.png'
                appTrace = tr.copy()
                bb = band[b]
                appTrace.trim(self._tEnd - self._rTWindow * 60, self._tEnd,pad=True,fill_value=0)
                appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                if self.plotDrum(appTrace):
                    sftpMkdirs(sftp, '/RT/', 'uploads')
                    sftp.put('tmp.png', 'uploads/RT/' + fileNameRT)
                #print(fileNameRT)
        with open('geophone_network_status.json', 'w') as fp:
             json.dump(self._status, fp)
        sftp.put('geophone_network_status.json', 'uploads/RT/' + 'geophone_network_status.json')
        print('end '+UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._rtRunning=False

    def hystDrumPlot(self):
        print('Hyststart ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        appTrace=Stream()
        self._hyRunning=True

        for tr in self._traces:
            id = tr.get_id()
            #print('hyst '+id)
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]


            for h in hystType:

                if self._tEnd.hour % int(h / 60) == 0:
                    for b in band:
                        tStart = self._tEnd - h * 60
                        p = network + '/' + station + '/' + channel + '/' + str(self._tEnd.year) + '/' + str(
                            self._tEnd.month) + '/' + str(
                            self._tEnd.day) + '/' + str(h) + '/' + str(b)

                        fileName = p + '/' + tStart.strftime("%Y%m%d%H%M") + '_' + self._tEnd.strftime(
                            "%Y%m%d%H%M") + '.png'

                        appTrace = tr.copy()
                        bb = band[b]
                        appTrace.trim(tStart, self._tEnd,pad=True,fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        if self.plotDrum(appTrace,'tmpH.png'):
                            sftpMkdirs(sftp, p, 'uploads')
                            sftp.put('tmpH.png', 'uploads/' + fileName)
                        #print(fileName)
        print('Hystend ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._hyRunning=False

    def align(self):
        if os.path.exists('traces.mseed'):
            self._traces = read('traces.mseed')
        return True

    def save(self):
        self._saving=True
        tr=self._traces.copy()
        print('saving')
        tr.write('traces.mseed')
        print('saved')
        self._saving=False

    def on_data(self,traces):
        self._tNow = UTCDateTime.now()
        traces.remove_response(self._inv)
        #traces.resample(125)
        self._traces += traces
        self._traces.merge(fill_value=0)

        # print(self._tNow.strftime(("%Y-%m-%d %H:%M:%S")) +' rtThread'+str(self._rtRunning))


        if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
            self._tEnd=self._tNow
            self._traces.trim(self._tEnd - 720 * 60, self._tNow)
            print(self._traces)
            if not self._rtRunning:
                rtThread = Thread(target=self.realTimeDrumPlot)
                rtThread.start()
            if not self._saving:
                sThread=Thread(target=self.save)
                sThread.start()

        if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
            self._tEnd = self._tNow
            if not self._hyRunning:
                hyThread = Thread(target=self.hystDrumPlot)
                hyThread.start()
        #     # self.hystDrumPlot()

        self._lastData = self._tNow


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



ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!',timeout=5)
sftp = ssh_client.open_sftp()
client = drumPlot('172.16.8.10')
client.select_stream('LK', 'BRK?', 'E??')
client.align()
client.run()
