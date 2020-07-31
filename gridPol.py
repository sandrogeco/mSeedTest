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
wnd=720
sft=5

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
a=[]
for s in np.arange(0, ns):
    traces = client.get_waveforms('LK', st[s], '', 'EH?', tt - wnd, tt + wnd)
    traces.remove_response(client._inv)
    traces.filter('bandpass', freqmin=3, freqmax=10, corners=2, zerophase=True)
    a.append(obspy.signal.polarization.polarization_analysis(traces, stime=tt,etime=tt+wnd,frqlow=3,frqhigh=10,win_len=3, win_frac=.2, method='flinn'))
    print(str(s))
print('a')