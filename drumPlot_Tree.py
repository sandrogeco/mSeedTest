import os
import numpy
import sys
import time
from obspy import UTCDateTime
#from obspy.clients.filesystem.sds import Client
from obspy.clients.fdsn import Client
from matplotlib.backends.backend_agg import FigureCanvasAgg


import png

import paramiko

from PIL import Image


client_root='/mnt/ide/seed'#sys.argv[1]

# network=sys.argv[2]
# station=sys.argv[3]
# channel=sys.argv[4]
# start_time=sys.argv[5]
# end_time=sys.argv[6]
# dpi=int(sys.argv[7])
# sizex=int(sys.argv[8])
# sizey=int(sys.argv[9])

dpi=100
sizex=800
sizey=600

hystType = [1440,360,180]
band={
    'low':[0.05,0.1],
    'high':[0.1,0.5]
}
rTWindow = 360



ssh_client =paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!')

#client=Client(client_root)#("/mnt/ide/seed")
client = Client("IRIS")
# tStart=UTCDateTime(start_time)#("2020-06-08T06:30:00.000")
# tEnd=UTCDateTime(end_time)#("2020-06-08T09:30:00.000")


#data=client.get_all_nslc()
data=[('IU', 'ANMO', '', 'LHZ'),('IU', 'ANMO', '', 'LH1'),('IU', 'ANMO', '', 'LH2'),
      ('IU', 'AFI', '', 'LHZ'),('IU', 'AFI', '', 'LH1'),('IU', 'AFI', '', 'LH2'),
      ('IU', 'ADK', '', 'LHZ'),('IU', 'ADK', '', 'LH1'),('IU', 'ADK', '', 'LH2'),
      ('IU', 'COR', '', 'LHZ'),('IU', 'COR', '', 'LH1'),('IU', 'COR', '', 'LH2'),
      ('IU', 'COLA', '', 'LHZ'),('IU', 'COLA', '', 'LH1'),('IU', 'COLA', '', 'LH2')]
data=[('MN', 'AQU', '', 'BHE'),('MN', 'AQU', '', 'BHN'),('MN', 'AQU', '', 'BHZ')]
data=[('MN', 'AQU', '', 'BHE')
      ]
sftp=ssh_client.open_sftp()

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

tOld=UTCDateTime.now()
test=True
while 1<2:
    time.sleep(1)
    tEnd = UTCDateTime.now()
    print(tEnd.strftime("%Y%m%d%H%M%S"))
    if test:
        for st in data:
            for b in band:
                (fileName,fileNameRT) = drum(st, tEnd, rTWindow, band[b],b)
    else:
        if (tEnd.minute %5 ==0) & (tOld.minute %5 !=0):
            for st in data:
                for b in band:
                    (fileName,fileNameRT) = drum(st, tEnd, rTWindow, band[b],b)
            #    sftp.put('tmp.png', 'uploads/RT/' + fileNameRT)


        if (tEnd.minute==0) & (tOld.minute !=0):
            for hyst in hystType:
                if tEnd.hour % int(hyst/60)==0:
                    for st in data:
                        for b in band:
                            (fileName,fileNameRT)=drum(st,tEnd,hyst,band[b], b)
                 #           sftp.put('tmp.png', 'uploads/' + fileName)

    tOld=tEnd