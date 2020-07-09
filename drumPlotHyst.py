import os
import numpy
import sys
import time
from obspy import UTCDateTime
#from obspy.clients.filesystem.sds import Client
from obspy.clients.fdsn import Client
from matplotlib.backends.backend_agg import FigureCanvasAgg
#from obspy.clients.seedlink.basic_client import Client
from obspy.clients.seedlink.easyseedlink import create_client
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.stream import Stream
import matplotlib.pyplot as plt


import png

import paramiko

from PIL import Image



dpi=100
sizex=800
sizey=600

hystType = [1440,360,180]

band={
    'low':[0.05,0.1],
    'high':[0.1,0.5]
}

rTWindow = 360
rtSft=2


ssh_client =paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!')
sftp=ssh_client.open_sftp()



class MyClient(EasySeedLinkClient):
    _traces = Stream()
    _lastData=UTCDateTime.now()
    _rTWindow=rTWindow
    _rtSft=rtSft

    def plotDrum(self,tr):

        try:
            im=tr.plot(type='dayplot',
                    dpi=dpi,
                    x_labels_size=int(8 * 100 / int(dpi)),
                    y_labels_size=int(8 * 100 / int(dpi)),
                    title_size=int(1000 / int(dpi)),
                    size=(sizex, sizey),
                    color=('#AF0000', '#00AF00', '#0000AF'),
                    # transparent=True,
                    handle=True
                    # bgcolor='black',
                    # grid_color='white',
                    # face_color='black',+
                    # show_y_UTC_label=False,
                    #outfile='tmp.png'
                    )
            im.savefig('tmp.png')
            plt.close(im)

            return True
        except:
            print('ops,something wrong in plotting!!')
            return False

    def realTimeDrumPlot(self,b):
        for tr in self._traces:
            id=tr.get_id()
            spl=id.split('.')
            network=spl[0]
            station=spl[1]
            channel=spl[3]
            for band in b:
                fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(band) + '.png'
                trApp=tr.copy()
                bb=b[band]
                trApp.trim(UTCDateTime.now()-self._rTWindow*60,UTCDateTime.now())
                trApp.filter('bandpass',freqmin=bb[0],freqmax=bb[1],corners=2,zerophase=True)
                if self.plotDrum(trApp):
                    sftp.put('tmp.png', 'uploads/RT/' + fileNameRT)
                print(fileNameRT)



    def on_data(self,traces):
        # if len(traces)==0:
        #     for trace in traces:
        #         trace
        tEnd=UTCDateTime.now()
        self._traces+=traces
        self._traces.merge()
        self._traces.trim(tEnd-1440*60,tEnd)
        print(self._traces)
        if (tEnd.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
            self.realTimeDrumPlot(band)
        self._lastData = tEnd





client= MyClient('172.16.8.10')

# data=[('IU', 'ANMO', '', 'LHZ'),('IU', 'ANMO', '', 'LH1'),('IU', 'ANMO', '', 'LH2'),
#       ('IU', 'AFI', '', 'LHZ'),('IU', 'AFI', '', 'LH1'),('IU', 'AFI', '', 'LH2'),
#       ('IU', 'ADK', '', 'LHZ'),('IU', 'ADK', '', 'LH1'),('IU', 'ADK', '', 'LH2'),
#       ('IU', 'COR', '', 'LHZ'),('IU', 'COR', '', 'LH1'),('IU', 'COR', '', 'LH2'),
#       ('IU', 'COLA', '', 'LHZ'),('IU', 'COLA', '', 'LH1'),('IU', 'COLA', '', 'LH2')]
# data=[('MN', 'AQU', '', 'BHE'),('MN', 'AQU', '', 'BHN'),('MN', 'AQU', '', 'BHZ')]
data=[('LK', 'BRK0', 'EHE'),('LK', 'BRK0', 'EHN'),('LK', 'BRK0', 'EHZ'),
      ('LK', 'BRK1', 'EHE'),('LK', 'BRK1', 'EHN'),('LK', 'BRK1', 'EHZ')]


def sftpExist(p,path):
    try:
        p.stat(path)
        return True

    except IOError:
        return False


def sftpMkdirs(p,path,basePath):
    dirs=path.split('/')
    parPath=basePath
    for dir in dirs:
        parPath+='/'+dir
        if not sftpExist(p,parPath):
            p.mkdir(parPath)


hst=True


def drum(st,tEnd,hyst,band,b):
    network = st[0]
    station = st[1]
    channel = st[3]

    tStart = tEnd - hyst * 60
    p = network + '/' + station + '/' + channel + '/' + str(tEnd.year) + '/' + str(tEnd.month) + '/' + str(
        tEnd.day) + '/' + str(hyst)+'/'+str(b)

    sftpMkdirs(sftp, p, 'uploads')
    sftpMkdirs(sftp, '/RT/', 'uploads')

    traces = client.get_waveforms(network, station, "*", channel, tStart, tEnd)
    for tr in traces:
        trId = tr.get_id()

        fileName = p + '/' + tStart.strftime("%Y%m%d%H%M%S") + '_' + tEnd.strftime("%Y%m%d%H%M%S") + '.png'
        fileNameRT='RT_'+ network + '_' + station + '_' + channel + '_' + str(b)+'.png'

        tr.filter('bandpass',freqmin=band[0],freqmax=band[1],corners=2,zerophase=True)
        tr.plot(type='dayplot',
                dpi=dpi,
                x_labels_size=int(8 * 100 / int(dpi)),
                y_labels_size=int(8 * 100 / int(dpi)),
                title_size=int(1000 / int(dpi)),
                size=(sizex, sizey),
                color=('#AF0000', '#00AF00', '#0000AF'),
                #transparent=True,
                #handle=True
                # bgcolor='black',
                # grid_color='white',
                # face_color='black',+
                # show_y_UTC_label=False,
                outfile='tmpmpl.png'
                )
        im = Image.open('tmpmpl.png')
        #Image.fromarray(numpy.fromstring(imM.canvas.tostring_rgb(), dtype=numpy.uint8).reshape(lst)).convert('P', palette=Image.AFFINE).save('tmp.png', format='PNG',optimization=True)
  #      Image.fromarray(X,'RGBA').convert('P', palette=Image.AFFINE).save('tmp.png', format='PNG',optimization=True)
        im.convert('RGBA').convert('P', palette=Image.AFFINE).save('tmp.png', format='PNG',optimization=True)
        print(fileNameRT+' '+fileName)
        return (fileName,fileNameRT)



def readTraces(tr,traces,tStart,tEnd):
    i=0
    for id in tr:
        traces[i]=client.get_waveforms(id[0],id[1],'*',id[2],tStart,tEnd).append(traces[i])
        i+=1


tOld=UTCDateTime.now()
test=True
#traces=client.get_waveforms(data[0],data[1],'*',data[2],tOld-rtSft*60,tOld)
traces={}

client.select_stream('LK','BRK?','E??')
client.run()
