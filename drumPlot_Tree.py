import os
import sys
from obspy import UTCDateTime
from obspy.clients.filesystem.sds import Client
import paramiko


client_root=sys.argv[1]
network=sys.argv[2]
station=sys.argv[3]
channel=sys.argv[4]
start_time=sys.argv[5]
end_time=sys.argv[6]
dpi=int(sys.argv[7])
sizex=int(sys.argv[8])
sizey=int(sys.argv[9])

hystType = [1440,360,60,5 ]




ssh_client =paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname='80.211.98.179', username='braskem', password='Geoapp2020!')

client=Client(client_root)#("/mnt/ide/seed")
tStart=UTCDateTime(start_time)#("2020-06-08T06:30:00.000")
tEnd=UTCDateTime(end_time)#("2020-06-08T09:30:00.000")

data=client.get_all_nslc()

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



for hyst in hystType:
    for st in data:
        network=st[0]
        station=st[1]
        channel=st[3]

        p=network+'/'+station+'/'+channel+'/'+str(tEnd.year)+'/'+str(tEnd.month)+'/'+str(tEnd.day)+'/'+str(hyst)
        sftpMkdirs(sftp,p,'uploads')
        tStart=tEnd-hyst*60
        traces = client.get_waveforms(network, station, "*", channel, tStart, tEnd)

        for tr in traces:
            trId=tr.get_id()
            fileName=p+'/'+tStart.strftime("%Y%m%d%H%M%S")+'_'+tEnd.strftime("%Y%m%d%H%M%S")+'.jpg'

            if not sftpExist(sftp,'uploads/'+fileName):
                tr.plot(type='dayplot',
                        dpi=dpi,
                        x_labels_size=int(8*100/int(dpi)),
                        y_labels_size=int(8*100/int(dpi)),
                        title_size=int(1000/int(dpi)),
                        size=(sizex, sizey),
                        #bgcolor='black',
                        #grid_color='white',
                        #face_color='black',
                        # show_y_UTC_label=False,
                        outfile='tmp.jpg')
                sftp.put('tmp.jpg','uploads/'+fileName)
                print(fileName)
