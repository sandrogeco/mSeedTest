import os
import logging
from obspy import UTCDateTime
from obspy.clients.seedlink.easyseedlink import EasySeedLinkClient
from obspy.core.stream import Stream
from obspy import read
from obspy.clients.filesystem.sds import Client
import matplotlib.pyplot as plt
import multiprocessing
import obspy.signal.polarization
from obspy import read_inventory

from threading import Thread

import json
from json import encoder
import psycopg2



import time
import paramiko
import numpy as np


plt.switch_backend('agg')
dpi = 100
sizex = 800
sizey = 600
yRange = 0.1

hystType = [360, 180, 60]

band = {
    'low': [1, 20],
    'high': [20, 50]
}

rTWindow = 360
rtSft = 2

class alert():
    _a={
        'id_alert':'',
        'utc_time':'',
        'utc_time_str':'',
        'event_type':'',
        'station':'',
        'channel':'',
        'amplitude':'',
        'linearity':'',
        'az':'',
        'tkoff':'',
        'freq':'',
        'lat':'',
        'lon':'',
        'note':''
    }
    _table='seismic.alerts'

    def insert(self,clause=''):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        sql="INSERT INTO "+self._table+" (".join(str(s)+"," for s in self._a.keys())
        sql=sql[0:-1]
        sql+=") VALUES (".join(str(s)+"," for s in self._a.values())
        sql = sql[0:-1]
        sql+=") " +clause+" ;"
        connection.cursor().execute(sql)
        connection.commit()
        connection.close()


    def getLastSta(self,station,evType):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        sql="SELECT max(utc_time) from "+self._table+" WHERE station="+station+" AND event_type="+evType+" ;"
        cursor = connection.cursor()
        cursor.execute(sql)
        p = cursor.fetchall()
        connection.close()
        return p[0]


class drumPlot(Client):


    _file = 'tr.mseed'  # 'traces.mseed'
    _traces = Stream()
    _inv = read_inventory("metadata/Braskem_metadata.xml")
    _rtSft = rtSft
    _lastData = UTCDateTime.now()
    _traces = Stream()
    _2minRTraces=Stream()
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
    _events = []
    _polAn={
        'polWinLen':3,
        'polWinFr':.1,
        'fLow':4,
        'fHigh':12,
        'plTh':0.7
    }
    _polAnResult=[]





    def plotDrum(self, trace, filename='tmp.png'):
        print(trace.get_id())
        try:
            trace.data = trace.data * 1000 / 3.650539e+08
            #im,ax=plt.subplots()
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))

            #im=
            trace.plot(type='dayplot',
                            dpi=dpi,
                            x_labels_size=int(8 * 100 / int(dpi)),
                            y_labels_size=int(8 * 100 / int(dpi)),
                            title_size=int(1000 / int(dpi)),
                            title=self._tEnd.strftime("%Y/%m/%d %H:%M:%S"),
                            size=(sizex, sizey),
                            color=('#AF0000', '#00AF00', '#0000AF'),
                            vertical_scaling_range=yRange,
                            outfile=filename,
                            #handle=True,
                            time_offset=-3,
                            data_unit='mm/s',
                            events=self._events
                            )
#            im.savefig(filename)
#            plt.close(im)

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
                self.plotDrum(appTrace, self._basePathRT + 'RT/' + fileNameRT)

        with open(self._basePathRT + 'RT/geophone_network_status.json', 'w') as fp:
            json.dump(self._status, fp)
            fp.close()

        print('end ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
        self._rtRunning = False

    def hystDrumPlot(self,tEnd=0):

        appTrace = Stream()
        self._hyRunning = True
        if tEnd==0:
            tEnd=self._tEnd
        else:
            self._tEnd=tEnd
        print('Hyststart ' + tEnd.strftime("%Y%m%d %H%M%S"))
        for tr in self._traces:
            id = tr.get_id()
            # print('hyst '+id)
            spl = id.split('.')
            network = spl[0]
            station = spl[1]
            channel = spl[3]

            for h in hystType:

                if tEnd.hour % int(h / 60) == 0:
                    for b in band:
                        tStart = tEnd - h * 60
                        p = network + '/' + station + '/' + channel + '/' + str(tStart.year) + '/' + str(
                            tStart.month) + '/' + str(
                            tStart.day) + '/' + str(h) + '/' + str(b)

                        fileName = p + '/' + tStart.strftime("%Y%m%d%H")+ '00.png'# + '_' + (self._tEnd-60).strftime(
                            #"%Y%m%d%H") + '.png'

                        appTrace = tr.copy()
                        bb = band[b]
                        appTrace.trim(tStart, tEnd, pad=True, fill_value=0)
                        appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        self.plotDrum(appTrace, self._basePath + fileName)


        self._hyRunning = False

    def hystElab(self):
        tStart = self._tEnd - 1440 * 60
        for e in self._elabHyst:
            p = e.split('_')
            network = p[0]
            station = p[1]
            p = self._basePath + network + '/' + station + '/' + 'ELAB' + '/' + str(tStart.year) + '/' + str(
                tStart.month) + '/' + str(
                tStart.day) + '/'+tStart.strftime("%Y%m%d%H")+ '00.json'#ELAB_' + e + '.json'
            if not os.path.exists(os.path.dirname(p)):
                os.makedirs(os.path.dirname(p))
            # el = self._elabHyst[e]
            with open(p, 'w') as fp:
                json.dump(list(self._elabHyst[e].values()), fp)
                fp.close()
            self._elabHyst[e]={}

    def elab(self):
        self._elRunning = True

        self._2minRTraces = self._traces.copy()
        self._2minRTraces.trim(self._tEnd-120, self._tEnd)
        self._2minRTraces.remove_response(self._inv)

        tStart = self._tEnd - 60
        s = np.asarray(self.get_all_nslc())

        intTrace=self._2minRTraces.copy()
        intTrace.trim(tStart, self._tEnd)

        for network in np.unique(s[:, 0]):
            for station in np.unique(s[:, 1]):
                print('elab ' + station)
                stTrace = intTrace.select(network, station)
                elab = {
                    'ts': np.long(self._tEnd.strftime("%Y%m%d%H%M%S"))

                }
                # TREMOR
                nTr = network + '_' + station
                # f = self.elabWhere(nTr, (self._tEnd - 3600).strftime("%Y%m%d%H%M%S"),
                #                    self._tEnd.strftime("%Y%m%d%H%M%S"))
                for appTrace in stTrace:
                    rms = {}
                    id = appTrace.get_id()
                    spl = id.split('.')
                    channel = spl[3]
                    elab[channel] = {}
                    # tStart = self._tEnd - 60
                    # appTrace = tr.copy()
                    # appTrace.trim(tStart, self._tEnd)
                    # appTrace.remove_response(self._inv)

                    for b in band:
                        bb = band[b]
                        trF = appTrace.copy()
                        trF.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
                        rms[b] = np.sqrt(np.mean(trF.data ** 2))
                        elab[channel]['rms_' + b] = str("%0.2e" % rms[b])
                        # HC_rms = np.sum([float(s[channel]['rms_' + b]) for s in f])
                        # elab[channel]['HC_rms_' + b] = str("%0.2e" % HC_rms)

                try:
                    self._elab[nTr][elab['ts']] = elab
                    self._elabHyst[nTr][elab['ts']] = elab
                except:
                    self._elab[nTr] = {}
                    self._elab[nTr][elab['ts']] = elab
                    self._elabHyst[nTr] = {}
                    self._elabHyst[nTr][elab['ts']] = elab

                # pulisco e slavo
                m = np.long((self._tEnd - 1440 * 60).strftime("%Y%m%d%H%M%S"))
                mm = np.min(list(self._elab[nTr].keys()))
                if mm < m:
                    self._elab[nTr].pop(mm)
                for e in self._elab:
                    filename = self._basePathRT + 'RT/ELAB_' + e + '.json'

                    with open(filename, 'w') as fp:
                        json.dump(list(self._elab[e].values()), fp)
                        fp.close()


                # except:
                #     print('failed elab in '+station)
                #     pass

        np.savez(self._basePath+'elSave',h=self._elabHyst,e=self._elab)
        self._elRunning = False

    def elabWhere(self,id,ts,te):
        r=[]
        ts=np.long(ts)
        te=np.long(te)
        try:
            for x in (y for y in self._elab[id].keys() if (y > ts) & (y < te)):
                r.append(self._elab[id][x])
        except:
            pass
        return r



    def polAn(self):
        a=alert()
        appTrace=self._2minRTraces.copy()
        ts=self._tEnd-120
        te=self._tEnd-10

        appTrace.filter('bandpass', freqmin=self._polAn['fLow'], freqmax=self._polAn['fHigh'], corners=2, zerophase=True)
        s = np.asarray(self.get_all_nslc())
        for network in np.unique(s[:, 0]):
            for station in np.unique(s[:, 1]):
                nTr = network + '_' + station
                try:
                    print('polarizzation analisys '+station)
                    stTrace = appTrace.select(network, station)
                    u=obspy.signal.polarization.polarization_analysis(
                        stTrace,self._polAn['polWinLen'],
                        self._polAn['polWinFr'],
                        self._polAn['fLow'],
                        self._polAn['fHigh'],
                        ts,te,False,'flinn')

                    x=np.where(u['planarity']>self._polAn['plTh'])
                    ur={k: u[k][x] for k in u.keys()}
                    for u in ur:
                        a._a['utc_time']=UTCDateTime(u['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                        a._a['utc_time_str'] = UTCDateTime(u['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                        a._a['event_type']="PL"
                        a._a['station']=nTr
                        a._a['linearity']=u['planarity']
                        a._a['az']=a['azimuth']
                        a._a['tkoff']=a['incidence']

                    a._a = {
                        'id_alert': '',
                        'utc_time': '',
                        'utc_time_str': '',
                        'event_type': '',
                        'station': '',
                        'channel': '',
                        'amplitude': '',
                        'linearity': '',
                        'az': '',
                        'tkoff': '',
                        'freq': '',
                        'lat': '',
                        'lon': '',
                        'note': ''
                    }
                except:
                    print('polarizzation analisys '+station+ ' failed')


    def run(self, network, station, channel,tStart=UTCDateTime.now(),rt=True):
        logging.basicConfig(filename='log.log', level='WARNING',format='%(asctime)s %(message)s')

        r=False

        try:

            data=np.load(self._basePath+'elSave.npz')
            self._elab=data['e'].tolist()
            self._elabHyst=data['h'].tolist()
        except:

            pass

        self._stationData={
            'BRK0': self._inv.get_coordinates('LK.BRK0..EHZ'),
            'BRK1': self._inv.get_coordinates('LK.BRK1..EHZ'),
            'BRK2': self._inv.get_coordinates('LK.BRK2..EHZ'),
            'BRK3': self._inv.get_coordinates('LK.BRK3..EHZ'),
            'BRK4': self._inv.get_coordinates('LK.BRK4..EHZ'),
        }

        with open(self._basePathRT+'elab_status.json', 'w') as fp:
            json.dump(self._stationData, fp)
            fp.close()

        self._tNow=tStart
        while 1 < 2:

            if self._tNow>UTCDateTime.now()-5:
                time.sleep(5)
                self._tNow = UTCDateTime.now()
                print(self._tNow)
            else:
                self._tNow += 10
                if (not rt) & (not self._rtRunning)&(not self._hyRunning)&( not self._saving)& (not self._elRunning):

                    print('sk')
                    print(self._tNow)


            if self._tNow.second < self._lastData.second:
                self._tEnd = self._tNow

                print('getting traces')
                try:
                    self._traces = self.get_waveforms(network, station, '', channel, self._tEnd - 720 * 60,
                                                      self._tEnd)
                    self._traces.merge(fill_value=0)
                except:
                    print('failed to get traces')


                if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0) & rt:
                    print('getting events')
                    try:
                        self.getCasp()
                    except:
                        print('events failed')
                        pass

                    try:
                        self.pushEv()
                    except:
                        print('push events failed')
                        pass

                    if (not self._rtRunning) & rt:
                        pRt = multiprocessing.Process(target=self.realTimeDrumPlot)
                        pRt.start()

                if (not self._elRunning):
                    self.elab()
                    self.polAn()

                if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
                    if not self._hyRunning:
                        pHy = multiprocessing.Process(target=self.hystDrumPlot)
                        pHy.start()



                if self._tNow.hour<self._lastData.hour:
                    self.hystElab()







            self._lastData = self._tNow

    def getCasp(self):
        connection = psycopg2.connect(host='172.16.8.10', port='5432', database='casp_events', user='sismoweb',
                                      password='lun1t3k@@')
        sql = 'SELECT event_id, t0, lat, lon, dpt, magWA FROM auto_eventi'
        cursor = connection.cursor()
        cursor.execute(sql)
        p=cursor.fetchall()
        self._events=[]
        for pp in p:
            e={
                'id':pp[0],
                'time':UTCDateTime(pp[1]),
                'text':'CASP ev. mag'+str(pp[5]),
                'lat':np.float(pp[2]),
                'lon':np.float(pp[3]),
                'dpt':np.float(pp[4]),
                'mag':np.float(pp[5])
            }
            self._events.append(e)

    def pushEv(self):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        for e in self._events:

            sql = 'INSERT INTO seismic.events_casp (geom,lat,lon,utc_time,utc_time_str,magnitudo,depth,id_casp) ' \
                  "VALUES (ST_GeomFromText('POINT(" + str(e['lon']) + ' ' + str(e['lat']) + ")', 4326),"\
                  + str(e['lat']) + ','+ str(e['lon'])+ ",'"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+ "','"+  str(UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S"))+"',"+str(e['mag'])+','+ str(e['dpt'])  +','+e['id']+") ON CONFLICT DO NOTHING;"
            connection.cursor().execute(sql)
            connection.commit()

    def pushIntEv(self,e,table='seismic.events_swarm',id='id_swarm'):
        connection = psycopg2.connect(host='80.211.98.179', port='5432', user='maceio',
                                      password='Bebedouro77627')
        #for e in events:

        sql = 'INSERT INTO '+table+ ' (geom,note,lat,lon,utc_time,utc_time_str,magnitudo,depth,'+id+') ' \
              "VALUES (ST_GeomFromText('POINT(" + str(e['lon']) + ' ' + str(e['lat']) + ")', 4326)" \
              + ",'" + e['note'] + "'," + str(e['lat']) + ',' + str(e['lon']) + ",'" + str(
            UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S")) + "','" + str(
            UTCDateTime(e['time']).strftime("%Y-%m-%d %H:%M:%S")) + "'," + str(e['mag']) + ',' + str(e['dpt']) + ",'" + \
              e['id'] + "') ON CONFLICT DO NOTHING;"
        connection.cursor().execute(sql)
        connection.commit()
