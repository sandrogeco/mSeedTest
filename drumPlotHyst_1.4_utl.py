# start 10.30
#!pippo2010
# sudo ./slarchive -v -SDS /mnt/ide/seed/ -x statefile -S LK_BRK?:EH? 172.16.8.10:18000

# openvpn --config clientBRASKEM__GEOAPP.con
#
# #sudo sshfs -o allow_other braskem@80.211.98.179:/uploads /mnt/geoAppServer/



from seisLib import drumPlot




client = drumPlot('/mnt/ide/seed/')

client.hystDrumPlot()

client.run('LK', 'BRK?', 'E??')
