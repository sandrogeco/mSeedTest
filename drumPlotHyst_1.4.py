# start 10.30
#!pippo2010
# sudo ./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# openvpn --config clientBRASKEM__GEOAPP.con
#
# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/



from seisLib import drumPlot


#
# class drumPlot(Client):
#     _file = 'tr.mseed'  # 'traces.mseed'
#     _traces = Stream()
#     _inv = read_inventory("metadata/Braskem_metadata.xml")
#     _rtSft = rtSft
#     _lastData = UTCDateTime.now()
#     _traces = Stream()
#     _appTrace = Stream()
#     _drTrace = Stream()
#     _drHTrace = Stream()
#     _rTWindow = rTWindow
#     _tEnd = UTCDateTime.now()
#     _tNow = UTCDateTime.now()
#     _rtRunning = False
#     _hyRunning = False
#     _saving = False
#     _elRunning = False
#     _status = {}
#     _elab = {}
#     _elabHyst={}
#
#     def plotDrum(self, trace, filename='tmp.png'):
#         print(trace.get_id())
#         try:
#             trace.data = trace.data * 1000 / 3.650539e+08
#
#             im = trace.plot(type='dayplot',
#                             dpi=dpi,
#                             x_labels_size=int(8 * 100 / int(dpi)),
#                             y_labels_size=int(8 * 100 / int(dpi)),
#                             title_size=int(1000 / int(dpi)),
#                             title=self._tEnd.strftime("%Y/%m/%d %H:%M:%S"),
#                             size=(sizex, sizey),
#                             color=('#AF0000', '#00AF00', '#0000AF'),
#                             vertical_scaling_range=yRange,
#                             handle=True,
#                             time_offset=-3,
#                             data_unit='mm/s'
#                             )
#             if not os.path.exists(os.path.dirname(filename)):
#                 os.makedirs(os.path.dirname(filename))
#             im.savefig(filename)
#             plt.close(im)
#
#             return True
#         except:
#             print('ops,something wrong in plotting!!')
#             return False
#
#     def realTimeDrumPlot(self):
#         print('start ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
#         appTrace = Stream()
#         self._rtRunning = True
#         for tr in self._traces:
#             id = tr.get_id()
#             spl = id.split('.')
#             network = spl[0]
#             station = spl[1]
#             channel = spl[3]
#             l = int(self._tEnd - tr.stats['endtime'])
#             self._status[station] = {}
#             self._status[station]["Noise Level"] = "---"
#             self._status[station]["Latency"] = str(l) + 's'
#             self._status[station]["Voltage"] = "---"
#             self._status[station]["Color"] = "#FF0000"
#
#             for b in band:
#                 fileNameRT = 'RT_' + network + '_' + station + '_' + channel + '_' + str(b) + '.png'
#                 appTrace = tr.copy()
#                 bb = band[b]
#                 appTrace.trim(self._tEnd - self._rTWindow * 60, self._tEnd, pad=True, fill_value=0)
#                 appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
#                 self.plotDrum(appTrace, basePathRT + 'RT/' + fileNameRT)
#
#         with open(basePathRT + 'RT/geophone_network_status.json', 'w') as fp:
#             json.dump(self._status, fp)
#             fp.close()
#
#         print('end ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
#         self._rtRunning = False
#
#     def hystDrumPlot(self):
#         print('Hyststart ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
#         appTrace = Stream()
#         self._hyRunning = True
#
#         for tr in self._traces:
#             id = tr.get_id()
#             # print('hyst '+id)
#             spl = id.split('.')
#             network = spl[0]
#             station = spl[1]
#             channel = spl[3]
#
#             for h in hystType:
#
#                 if self._tEnd.hour % int(h / 60) == 0:
#                     for b in band:
#                         tStart = self._tEnd - h * 60
#                         p = network + '/' + station + '/' + channel + '/' + str(tStart.year) + '/' + str(
#                             tStart.month) + '/' + str(
#                             tStart.day) + '/' + str(h) + '/' + str(b)
#
#                         fileName = p + '/' + tStart.strftime("%Y%m%d%H")+ '00.png'# + '_' + (self._tEnd-60).strftime(
#                             #"%Y%m%d%H") + '.png'
#
#                         appTrace = tr.copy()
#                         bb = band[b]
#                         appTrace.trim(tStart, self._tEnd, pad=True, fill_value=0)
#                         appTrace.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
#                         self.plotDrum(appTrace, basePath + fileName)
#
#         print('Hystend ' + UTCDateTime.now().strftime("%Y%m%d %H%M%S"))
#         self._hyRunning = False
#
#     def hystElab(self):
#         tStart = self._tEnd - 1440 * 60
#         for e in self._elabHyst:
#             p = e.split('_')
#             network = p[0]
#             station = p[1]
#             p = basePath + network + '/' + station + '/' + 'ELAB' + '/' + str(tStart.year) + '/' + str(
#                 tStart.month) + '/' + str(
#                 tStart.day) + '/'+tStart.strftime("%Y%m%d%H")+ '00.json'#ELAB_' + e + '.json'
#             if not os.path.exists(os.path.dirname(p)):
#                 os.makedirs(os.path.dirname(p))
#             el = self._elabHyst[e]
#             with open(p, 'w') as fp:
#                 json.dump(el, fp)
#                 fp.close()
#             self._elabHyst[e]={}
#
#     def elab(self):
#
#         s = np.asarray(self.get_all_nslc())
#         appTrace = Stream()
#         stTrace = Stream()
#         self._elRunning = True
#         for network in np.unique(s[:, 0]):
#             for station in np.unique(s[:, 1]):
#                 try:
#                     print('elab ' + station)
#                     stTrace = self._traces.select(network, station)
#                     elab = {
#                         'ts': np.long(self._tEnd.strftime("%Y%m%d%H%M%S"))
#
#                     }
#                     # TREMOR
#                     nTr = network + '_' + station
#                     f = self.elabWhere(nTr, (self._tEnd - 3600).strftime("%Y%m%d%H%M%S"), self._tEnd.strftime("%Y%m%d%H%M%S"))
#                     for tr in stTrace:
#                         rms = {}
#                         id = tr.get_id()
#                         spl = id.split('.')
#                         channel = spl[3]
#                         elab[channel] = {}
#                         tStart = self._tEnd - 60
#                         appTrace = tr.copy()
#                         appTrace.trim(tStart, self._tEnd)
#                         appTrace.remove_response(self._inv)
#
#                         for b in band:
#                             bb = band[b]
#                             trF = appTrace.copy()
#                             trF.filter('bandpass', freqmin=bb[0], freqmax=bb[1], corners=2, zerophase=True)
#                             rms[b] = np.sqrt(np.mean(trF.data ** 2))
#                             elab[channel]['rms_' + b] = str("%0.2e"%rms[b])
#                             HC_rms=np.sum([float(s[channel]['rms_' + b]) for s in f])
#                             elab[channel]['HC_rms_' + b]=str("%0.2e"%HC_rms)
#
#                     try:
#                         self._elab[nTr][elab['ts']] = elab
#                         self._elabHyst[nTr][elab['ts']] = elab
#                     except:
#                         self._elab[nTr] = {}
#                         self._elab[nTr][elab['ts']] = elab
#                         self._elabHyst[nTr] = {}
#                         self._elabHyst[nTr][elab['ts']] = elab
#
#
#                     # pulisco e slavo
#                     m = np.long((self._tEnd - 1440 * 60).strftime("%Y%m%d%H%M%S"))
#                     mm = np.min(list(self._elab[nTr].keys()))
#                     if mm < m:
#                         self._elab[nTr].pop(mm)
#                     for e in self._elab:
#                         filename = basePathRT + 'RT/ELAB_' + e + '.json'
#
#                         with open(filename, 'w') as fp:
#                             json.dump(list(self._elab[e].values()), fp)
#                             fp.close()
#
#                 except:
#                     print('failed elab in '+station)
#                     pass
#
#         np.savez('elSave',h=self._elabHyst,e=self._elab)
#         self._elRunning = False
#
#     def elabWhere(self,id,ts,te):
#         r=[]
#         ts=np.long(ts)
#         te=np.long(te)
#         for x in (y for y in self._elab[id].keys() if (y > ts) & (y < te)):
#             r.append(self._elab[id][x])
#         return r
#
#     #np.sum([s['EHE']['rms_low'] for s in f])
#
#     def run(self, network, station, channel):
#         r=False
#         try:
#             data=np.load('elSave.npz')
#             self._elab=data['e'].tolist()
#             self._elabHyst=data['h'].tolist()
#         except:
#             pass
#
#         self._stationData={
#             'BRK0': self._inv.get_coordinates('LK.BRK0..EHZ'),
#             'BRK1': self._inv.get_coordinates('LK.BRK1..EHZ'),
#             'BRK2': self._inv.get_coordinates('LK.BRK2..EHZ'),
#             'BRK3': self._inv.get_coordinates('LK.BRK3..EHZ'),
#             'BRK4': self._inv.get_coordinates('LK.BRK4..EHZ'),
#         }
#
#         with open(basePathRT+'elab_status.json', 'w') as fp:
#             json.dump(self._stationData, fp)
#             fp.close()
#
#
#         while 1 < 2:
#             time.sleep(5)
#             self._tNow = UTCDateTime.now()
#             print(self._tNow)
#             if self._tNow.second < self._lastData.second:
#                 self._tEnd = self._tNow
#                 print('getting traces')
#                 try:
#                     self._traces = self.get_waveforms(network, station, '', channel, self._tEnd - 720 * 60,
#                                                       UTCDateTime.now())
#                     self._traces.merge(fill_value=0)
#                 except:
#                     print('failed to get traces')
#
#                 if not self._elRunning:
#                     elThread = Thread(target=self.elab)
#                     elThread.start()
#
#
#                 if self._tNow.hour<self._lastData.hour:
#                     elSave = Thread(target=self.hystElab())
#                     elSave.start()
#
#                 if (self._tNow.minute % self._rtSft == 0) & (self._lastData.minute % self._rtSft != 0):
#                     if not self._rtRunning:
#                         rtThread = Thread(target=self.realTimeDrumPlot)
#                         rtThread.start()
#
#                 if (self._tEnd.minute == 0) & (self._lastData.minute != 0):
#                     if not self._hyRunning:
#                         hyThread = Thread(target=self.hystDrumPlot)
#                         hyThread.start()
#
#             self._lastData = self._tNow
#

client = drumPlot('/mnt/ide/seed/')

client.run('LK', 'BRK?', 'E??')
