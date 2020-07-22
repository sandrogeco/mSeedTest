# start 10.30

# sudo ./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# openvpn --config clientBRASKEM__GEOAPP.con
#
# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/
import os
from obspy import UTCDateTime
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.stream import Stream
from obspy import read
from obspy.clients.filesystem.sds import Client
import matplotlib.pyplot as plt
import sys
plt.switch_backend('agg')
from obspy import read_inventory

from threading import Thread

import json

import time
import paramiko
import numpy as np

dpi = 100
sizex = 800
sizey = 600
yRange = 0.1

hystType = [1440, 360, 180, 60]

basePath = '/mnt/geoAppServer/'  # '/home/sandro/Documents/mSeedTest/'#'#
band = {
    'low': [1, 20],
    'high': [20, 50]
}

rTWindow = 360
rtSft = 2


# inv = read_inventory("metadata/Braskem_metadata.xml")


class drumPlot(Client):
    _file = 'tr.mseed'  # 'traces.mseed'
    _traces = Stream()
    _inv = read_inventory("metadata/Braskem_metadata.xml")
    _rtSft = rtSft
    _lastData = UTCDateTime.now()
    _traces = Stream()
    _appTrace = Stream()
    _drTrace = Stream()
    _drHTrace = Stream()
    _rTWindow = rTWindow
    _tEnd = UTCDateTime.now()
    _tNow = UTCDateTime.now()
    _rtRunning = False
    _hyRunning = False
    _saving = False
    _elRunning = False
    _status = {}
    _elab = {}
    _elabHyst={}

    def statusCalc(self):
        for tr in self._traces:
            id = tr.get_id()
            l = int(UTCDateTime.now() - tr.stats['endtime'])
            station = id.split('.')[1]
            self._status[station] = {}
            self._status[station]["Noise Level"] = "---"
            self._status[station]["Latency"] = str(l) + 's'
            self._status[station]["Voltage"] = "---"
            self._status[station]["Color"] = "#FF0000"
        with open('geophone_network_status.json', 'w') as fp:
            json.dump(self._status, fp)
            fp.close()
        sftp.put('geophone_network_status.json', 'uploads/RT/' + 'geophone_network_status.json')

    def singleStatusCalc(self, tr):
        id = tr.get_id()
        station = id.split('.')[1]
        l = int(UTCDateTime.now() - tr.stats['endtime'])
        self._status[station] = {}
        self._status[station]["Noise Level"] = "---"
        self._status[station]["Latency"] = str(l) + 's'
        self._status[station]["Voltage"] = "---"
        self._status[station]["Color"] = "#FF0000"

    def plotDrum(self, trace, filename='tmp.png'):
        print(trace.get_id())
        try:
            trace.data = trace.data * 1000 / 3.650539e+08

            im = trace.plot(type='dayplot',
                            dpi=dpi,
                            x_labels_size=int(8 * 100 / int(dpi)),
                            y_labels_size=int(8 * 100 / int(dpi)),
                            title_size=int(1000 / int(dpi)),
                            title=self._tEnd.strftime("%Y/%m/%d %H:%M:%S"),
                            size=(sizex, sizey),
                            color=('#AF0000', '#00AF00', '#0000AF'),
                            vertical_scaling_range=yRange,
                            handle=True,
                            time_offset=-3,
                            data_unit='mm/s'
                            )
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            im.savefig(filename)
            plt.close(im)

            return True
        except:
            print('ops,something wrong in plotting!!')
            return False

    def realTimeDrumPlot(self):
        print('start ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        appTrace = Stream()
        self._rtRunning = True
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
                appTrace.trim(self._tEnd - self._rTWindow * 60, self._tEnd, pad=True, fill_value=0)
                appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                self.plotDrum(appTrace, basePath + 'RT/' + fileNameRT)

        with open(basePath + 'RT/geophone_network_status.json', 'w') as fp:
            json.dump(self._status, fp)
            fp.close()

        print('end ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._rtRunning = False

    def hystDrumPlot(self):
        print('Hyststart ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        appTrace = Stream()
        self._hyRunning = True

        for tr in self._traces:
            id = tr.get_id()
            # print('hyst '+id)
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
                        appTrace.trim(tStart, self._tEnd, pad=True, fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        self.plotDrum(appTrace, basePath + fileName)

        print('Hystend ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._hyRunning = False

    def hystElab(self):

        for e in self._elabHyst:
            p = e.split('_')
            network = p[0]
            station = p[1]
            p = basePath + network + '/' + station + '/' + 'ELAB' + '/' + str(self._tEnd.year) + '/' + str(
                self._tEnd.month) + '/' + str(
                self._tEnd.day) + '/ELAB_' + e + '.json'
            if not os.path.exists(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            el = self._elabHyst[e]
            with open(p, 'w') as fp:
                json.dump(el, fp)
                fp.close()
            self._elabHyst[e]={}

    def elab(self):
        print('tremorStart ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        s = np.asarray(self.get_all_nslc())
        appTrace = Stream()
        stTrace = Stream()
        self._elRunning = True
        for network in np.unique(s[:, 0]):
            for station in np.unique(s[:, 1]):

                stTrace = self._traces.select(network, station)
                elab = {
                    'ts': np.long(self._tEnd.strftime("%Y%m%d%H%M%S"))

                }
                # TREMOR
                for tr in stTrace:
                    rms = {}
                    id = tr.get_id()
                    spl = id.split('.')
                    channel = spl[3]
                    elab[channel] = {}
                    tStart = self._tEnd - 60
                    appTrace = tr.copy()
                    appTrace.trim(tStart, self._tEnd)
                    appTrace.remove_response(self._inv)

                    for b in band:
                        bb = band[b]
                        trF = appTrace.copy()
                        trF.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        rms[b] = np.sqrt(np.mean(trF.data ** 2))
                        # print(id+' '+str(b)+' '+str(rms))
                        elab[channel]['rms_' + b] = rms[b]
                nTr=network + '_' + station
                try:
                    self._elab[nTr][elab['ts']]=elab
                    self._elabHyst[nTr][elab['ts']] = elab
                except:
                    self._elab[nTr]={}
                    self._elab[nTr][elab['ts']] = elab
                    self._elabHyst[nTr] = {}
                    self._elabHyst[nTr][elab['ts']] = elab

                #pulisco e slavo
                m=np.long((self._tEnd-1440*60).strftime("%Y%m%d%H%M%S"))
                mm=np.min(list(self._elab[nTr].keys()))
                if mm<m:
                    self._elab[nTr].pop(mm)
                for e in self._elab:
                    filename = basePath + 'RT/ELAB_' + e + '.json'

                    with open(filename, 'w') as fp:
                        json.dump(list(self._elab[e].values()), fp)
                        fp.close()
        #np.savez('elSave',h=self._elabHyst,e=self._elab)
        self._elRunning = False

    def run(self, network, station, channel):
        r=False
        try:
            data=np.load('elSave.npz')
        except:
            pass

        while 1 < 2:
            time.sleep(5)
            self._tNow = UTCDateTime.now()
            print(self._tNow)
            if self._tNow.second < self._lastData.second:
                self._tEnd = self._tNow
                self._traces = self.get_waveforms(network, station, '', channel, self._tEnd - 720 * 60,
                                                  UTCDateTime.now())
                print(self._traces)

                if not self._elRunning:
                    elThread = Thread(target=self.elab)
                    elThread.start()


                if self._tNow.hour<self._lastData.hour:
                    elSave = Thread(target=self.hystElab())
                    elSave.start()

                if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
                    if not self._rtRunning:
                        rtThread = Thread(target=self.realTimeDrumPlot)
                        rtThread.start()

                if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
                    if not self._hyRunning:
                        hyThread = Thread(target=self.hystDrumPlot)
                        hyThread.start()

            self._lastData = self._tNow

    def on_data(self, traces):

        self._tNow = UTCDateTime.now()
        print(self._tNow)

        # traces.remove_response(self._inv)
        # self._traces += traces
        # self._traces.merge(fill_value=0)
        # if (self._tEnd.minute != self._lastData.minute):
        #     if not self._trRunning:
        #         trThread = Thread(target=self.tremor)
        #         trThread.start()

        if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
            self._tEnd = self._tNow
            self._traces.trim(self._tEnd - 720 * 60, self._tNow)
            print(self._traces)
            if not self._rtRunning:
                rtThread = Thread(target=self.realTimeDrumPlot)
                rtThread.start()
            if not self._saving:
                sThread = Thread(target=self.save)
                sThread.start()

        if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
            self._tEnd = self._tNow

            if not self._hyRunning:
                hyThread = Thread(target=self.hystDrumPlot)
                hyThread.start()
        #     # self.hystDrumPlot()

        self._lastData = self._tNow

    def expt(self,start,end,st,ch):

        tr = client.get_waveforms('LK', st, '', ch, UTCDateTime.strptime(start,"%Y%m%dT%H%M%S"), UTCDateTime.strptime(end,"%Y%m%dT%H%M%S"))
        tr.remove_response(self._inv)
        tr.write('../../../../mnt/ide/traces.mseed')


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


# ssh_client = paramiko.SSHClient()
# ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!',timeout=5)
# sftp = ssh_client.open_sftp()
client = drumPlot('/mnt/ide/seed/')
# client.select_stream('LK', 'BRK?', 'E??')
# client.align()
start=sys.argv[1]
end=sys.argv[2]
#st=sys.argv[3]
#ch=sys.argv[4]
#client.run('LK', 'BRK?', 'E??')
st='BRK?'
ch='E??'
print (start)
print(end)
client.expt(start,end,st,ch)
