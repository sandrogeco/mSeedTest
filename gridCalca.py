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
t=UTCDateTime(2020,7,31,12,10)
wnd=5
sft=1

st=['BRK0','BRK1','BRK2','BRK3','BRK4']
ns=len(st)
rms=np.zeros(ns)
vpp=np.zeros(ns)

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
# for s in np.arange(0, ns):
#     traces = client.get_waveforms('LK', st[s], '', 'EHZ', t - 720, t+720)
#     traces.remove_response(client._inv)
#     traces.filter('bandpass', freqmin=3, freqmax=10, corners=2, zerophase=True)
#     rms[s] = np.sqrt(np.mean(traces[0].data ** 2))

# array([  4.78069433e-07,   6.35591108e-07,   4.16597551e-07,
#          3.34616584e-06,   5.90863776e-07])
print('base rms calculated')

while 1<2:
    tt=tt+sft
    for s in np.arange(0,ns):
        traces = client.get_waveforms('LK', st[s], '', 'EHZ', tt - 10*wnd, tt+10*wnd)
        traces.remove_response(client._inv)
        traces.filter('bandpass', freqmin=3, freqmax=10, corners=2, zerophase=True)
        rms[s]=np.sqrt(np.mean(traces[0].data ** 2))
        tr=traces.copy()
        tr.trim(tt-wnd,tt+wnd)
        vpp[s]=np.max(np.abs(tr[0].data))
        vppOffset=np.mean(np.abs(traces[0]))
    rms=rms-rmsOffset

    print(UTCDateTime(tt).strftime("%Y%m%d_%H%M%S"))
    print(str(np.max(vpp)))

    if np.max(vpp)>0.00008:
        vpp = vpp - vppOffset
        for i in np.arange(0,ns):
            for j in np.arange(i+1,ns):
                #r[i,j]=rms[j]/rms[i]#np.log(rms[i]/rms[j])
                r[i,j]=vpp[j]/vpp[i]

        e=[3]
        for i in np.arange(0, dst.shape[0]):
            for j in np.arange(0, dst.shape[1]):
                for k in np.arange(0, dst.shape[2]):
                    p = r - dst[i, j, k]

                    p[e , :] = 0
                    p[:, e ] = 0
                    result[i, j, k] =np.trace(np.dot(p.T, p))
                    p = r - dsts[i, j, k]

                    p[e, :] = 0
                    p[:, e ] = 0
                    results[i, j, k] = np.trace(np.dot(p.T, p))

        mm = np.unravel_index(np.argmin(result), result.shape)

        x = grid[0, mm[0], mm[1], mm[2]]
        y = grid[1, mm[0], mm[1], mm[2]]
        z = grid[2, mm[0], mm[1], mm[2]]
        lat, lon = utm.to_latlon(x, y, 25, 'L')
        lLat.append(lat)
        lLon.append(lLon)
        ld.append(z)
        lRmax.append(np.max(rms))
        lRmean.append(np.mean(rms))
        lResult.append(np.sqrt(result[mm]))
        mms = np.unravel_index(np.argmin(results), results.shape)
        xs = grid[0, mms[0], mms[1], mms[2]]
        ys = grid[1, mms[0], mms[1], mms[2]]
        zs = grid[2, mms[0], mms[1], mms[2]]
        lats, lons = utm.to_latlon(xs, ys, 25, 'L')
        print(e )
        print(str(z) + '  ' + str(zs))
        print(str(lat) + '  ' + str(lats))
        print(str(lon) + '  ' + str(lons))
        print(str(result[mm]) + '  ' + str(results[mms]))



        ptn = kml.newpoint(name=UTCDateTime(tt).strftime("%M%S"),
                           description='v_' + str(e) + '_' + str(z) + '_' + str(np.sqrt(result[mm])), coords=[(str(lon), str(lat))])
        ptn.style = style
        ptns = kmls.newpoint(name=UTCDateTime(tt).strftime("%M%S"),
                             description='s_' + str(e) + '_' + str(zs) + '_' + str(np.sqrt(results[mms])),
                             coords=[(str(lons), str(lats))])
        ptns.style = styles
        kml.save("kmlVa.kml")
        kmls.save("kmlSa.kml")


