from seisLib import drumPlot
import utm
import numpy as np
from obspy import UTCDateTime
import obspy.signal.polarization
import  matplotlib.pyplot as plt
import scipy.signal as sgn
from scipy.signal import hanning
from scipy.optimize import curve_fit
import simplekml


plt.switch_backend('tKagg')

client = drumPlot('/mnt/ide/seed/')
t=UTCDateTime(2020,7,31,14,00)
wnd=10
sft=5

st=['BRK0','BRK1','BRK2','BRK3','BRK4']
ns=len(st)
rms=np.zeros(ns)
vpp=np.zeros(ns)
vppOffset=np.zeros(ns)
vppOffsetShort=np.zeros(ns)
vCh=np.zeros(ns)


r=np.zeros((ns,ns))
rs=np.zeros((ns,ns))
data=np.load('dst.npz')
dst=data['dst']
dsts=data['dsts']
grid=data['grid']
result=np.zeros(dst.shape)
results=np.zeros(dst.shape)
resultGroup=np.zeros([2,ns+1],dtype=object)
kml = simplekml.Kml()
kmls = simplekml.Kml()
style = simplekml.Style()
style.labelstyle.color = simplekml.Color.red
styles = simplekml.Style()
styles.labelstyle.color = simplekml.Color.blue
tt=t
lLat=[]
lLon=[]
ld=[]
lRmean=[]
lRmax=[]
lResult=[]


rmsOffset=0
print('base rms calculated')

def trAmpl(tr):
    r=np.sqrt(tr[0].data**2+tr[1].data**2+tr[2].data**2)
    return r

def loc(dstM,r,dec,e,lx,ly,lz):
    dst=np.zeros(dstM.shape,object)
    dst[:,:,:]=dstM[:,:,:]
    result = np.ones(dst.shape)*np.Inf
    #dst = dst[lx[0]:lx[1], ly[0]:ly[1], lz[0]:lz[1]]
    for i in np.arange(lx[0], lx[1], dec):
        for j in np.arange(ly[0], ly[1], dec):
            for k in np.arange(lz[0], lz[1], dec):
                p = r - dst[i, j, k]
                p[e, :] = 0
                p[:, e] = 0
                result[i, j, k] = np.trace(np.dot(p.T, p))
    mm = np.unravel_index(np.argmin (result), result.shape)
    m = np.min(result)
    if dec==1:

        rr={
            'min':m,
            'mPos':mm

        }
        return rr
    else:
        sx=(lx[1]-lx[0])/4
        sy= (ly[1] - ly[0])/4
        sz = (lz[1] - lz[0])/4
        lx=[np.int(np.maximum(mm[0]-sx,0)),np.int(np.minimum(mm[0]+sx,dst.shape[0]))]
        ly = [np.int(np.maximum(mm[1] -sy, 0)), np.int(np.minimum(mm[1] +sy, dst.shape[1]))]
        lz = [np.int(np.maximum(mm[2] - sz, 0)), np.int(np.minimum(mm[2] + sz, dst.shape[2]))]


        dec=np.int(dec/2)
        return loc(dst,r,dec,e,lx,ly,lz)



lta=10
sta=1
sl=1.2
ttL=tt
readLta=True
traces=np.zeros(ns,object)
tr=np.zeros(ns,object)
while 1<2:
    print('sta from ' + UTCDateTime(tt - sta * wnd).strftime("%Y%m%d_%H%M%S") + ' to ' + UTCDateTime(
        tt + sta * wnd).strftime("%Y%m%d_%H%M%S"))
    if tt > ttL + lta * wnd-sta*wnd:
        ttL = tt
        readLta=True
    if readLta:
        for s in np.arange(0, ns):
            traces[s] = client.get_waveforms('LK', st[s], '', 'EH?', ttL - lta * wnd, ttL + lta * wnd)
            traces[s].remove_response(client._inv)
            traces[s].filter('bandpass', freqmin=3, freqmax=10, corners=2, zerophase=True)

            vppOffset[s] = np.mean(trAmpl(traces[s])) #np.mean(np.abs(traces[s].data))

    for s in np.arange(0, ns):
        tr[s] = traces[s].copy()
        tr[s].trim(tt - sta * wnd, tt + sta * wnd)
        vpp[s] =np.max(trAmpl(tr[s])) #np.max(np.abs(tr[s].data))
        vppOffsetShort[s] =np.mean(trAmpl(tr[s]))# np.mean(np.abs(tr[s].data))



    readLta = False
    #vCh=(vppOffsetShort/vppOffset)>sl
    vCh=vpp>0.000005
    #vCh[3]=False
    vOffset=np.dot(vppOffset,vCh)/np.sum(vCh)
    print(vpp)
    print(vCh)


    if (np.sum(vCh))>=3:
        print('vpp')
        print(vpp)
        print('vOffset')
        print(vppOffset)
        print('vOffsetShort')
        print(vppOffsetShort)
        print('vCh')
        print(vCh)
        print('vo')
        print(vOffset)
        #vpp = vpp - vOffset
        for i in np.arange(0,ns):
            for j in np.arange(i+1,ns):
                r[i,j]=vpp[j]/vpp[i]


        e=np.where(vCh == False)
        # for i in np.arange(0, dst.shape[0]):
        #     for j in np.arange(0, dst.shape[1]):
        #         for k in np.arange(0, dst.shape[2]):
        #             p = r - dst[i, j, k]
        #
        #             p[e , :] = 0
        #             p[:, e ] = 0
        #             result[i, j, k] =np.trace(np.dot(p.T, p))
        #             p = r - dsts[i, j, k]
        #
        #             p[e, :] = 0
        #             p[:, e ] = 0
        #             results[i, j, k] = np.trace(np.dot(p.T, p))
        #
        # mm = np.unravel_index(np.argmin(result), result.shape)
        aVol = loc(dst, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
        #aSup= loc
        mm = aVol['mPos']
        m = aVol['min']
        # if aVol['min']<aSup['min']:
        #     mm=aVol['mPos']
        #     m=aVol['min']
        # else:
        #     mm = aSup['mPos']
        #     m = aSup['min']
        x = grid[0, mm[0], mm[1], mm[2]]
        y = grid[1, mm[0], mm[1], mm[2]]
        z = grid[2, mm[0], mm[1], mm[2]]
        lat, lon = utm.to_latlon(x, y, 25, 'L')
        lat=lat+(np.random.rand()*2-1)/10000
        lon=lon+(np.random.rand()*2-1)/10000
        ttt=UTCDateTime(tt)
        #ttt.day=UTCDateTime.now().day
        #ttt.month = UTCDateTime.now().month
        ev = {
            'id': UTCDateTime(ttt).strftime("%Y%m%d%H%M%S"),
            'time': UTCDateTime(ttt),
           # 'text': 'SWARM ev. mag' + str(pp[5]),
            'lat': lat,
            'lon': lon,
            'dpt': z,
            'mag': 1.5,#np.log(np.max(vpp)/0.000001),
            'note':'error '+str(m)
        }
        client.pushIntEv(ev)

        # aVol = loc(dsts, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
        # # aSup= loc
        # mm = aVol['mPos']
        # m = aVol['min']
        # # if aVol['min']<aSup['min']:
        # #     mm=aVol['mPos']
        # #     m=aVol['min']
        # # else:
        # #     mm = aSup['mPos']
        # #     m = aSup['min']
        # x = grid[0, mm[0], mm[1], mm[2]]
        # y = grid[1, mm[0], mm[1], mm[2]]
        # z = grid[2, mm[0], mm[1], mm[2]]
        # lat, lon = utm.to_latlon(x, y, 25, 'L')
        # lat = lat + (np.random.rand() * 2 - 1) / 10000
        # lon = lon + (np.random.rand() * 2 - 1) / 10000
        # ttt = UTCDateTime(tt)
        # # ttt.day=UTCDateTime.now().day
        # # ttt.month = UTCDateTime.now().month
        # ev = {
        #     'id': UTCDateTime(ttt).strftime("%Y%m%d%H%M%S"),
        #     'time': UTCDateTime(ttt),
        #     # 'text': 'SWARM ev. mag' + str(pp[5]),
        #     'lat': lat,
        #     'lon': lon,
        #     'dpt': z,
        #     'mag': 1.5,  # np.log(np.max(vpp)/0.000001),
        #     'note': 'error ' + str(m)
        # }
        #
        # client.pushIntEv(ev,'seismic.events_casp','id_casp')


        #
        # lLat.append(lat)
        # lLon.append(lLon)
        # ld.append(z)
        # lRmax.append(np.max(rms))
        # lRmean.append(np.mean(rms))
        # lResult.append(np.sqrt(a['min']))
        #
        # ptn = kml.newpoint(name=UTCDateTime(tt).strftime("%M%S"),
        #                    description='v_' + str(e) + '_' + str(z) + '_' + str(np.sqrt(result[mm])), coords=[(str(lon), str(lat))])
        # ptn.style = style
        #
        # kml.save("kmlVa01_18_3a.kml")
        #
        # a = loc(dsts, r, 8, e, [0, dst.shape[0]], [0, dst.shape[1]], [0, dst.shape[2]])
        # mm = a['mPos']
        # x = grid[0, mm[0], mm[1], mm[2]]
        # y = grid[1, mm[0], mm[1], mm[2]]
        # z = grid[2, mm[0], mm[1], mm[2]]
        # lat, lon = utm.to_latlon(x, y, 25, 'L')
        #
        # ptns = kmls.newpoint(name=UTCDateTime(tt).strftime("%M%S"),
        #                    description='v_' + str(e) + '_' + str(z) + '_' + str(np.sqrt(result[mm])),
        #                    coords=[(str(lon), str(lat))])
        # ptns.style = styles
        #
        # kmls.save("kmlVa01_18_3as.kml")

    tt = tt + sft


