import os
import sys
from obspy import UTCDateTime
from obspy.clients.filesystem.sds import Client

client_root=sys.argv[1]
network=sys.argv[2]
station=sys.argv[3]
channel=sys.argv[4]
start_time=sys.argv[5]
end_time=sys.argv[6]
# print(sys.argv[1])
# print(sys.argv[2])
# print(sys.argv[3])
# print(sys.argv[4])
# print(sys.argv[5])
# print(sys.argv[6])
# print(sys.argv[7])
# print(sys.argv[8])
# print(sys.argv[9])
# exit(0)
dpi=int(sys.argv[7])
sizex=int(sys.argv[8])
sizey=int(sys.argv[9])





client=Client(client_root)#("/mnt/ide/seed")
tStart=UTCDateTime(start_time)#("2020-06-08T06:30:00.000")
tEnd=UTCDateTime(end_time)#("2020-06-08T09:30:00.000")

traces=client.get_waveforms(network, station, "*", channel, tStart,tEnd)

for tr in traces:
    trId=tr.get_id()

    fileName='out_'+trId+'.png'
    #os.remove('out_'+trId+'.png')#TODO non li cancella, problema di permessi
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
            outfile=fileName)
    print(fileName)
