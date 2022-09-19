import upnpclient
devices = upnpclient.discover()
d = devices[0]
d.WANIPConnection.AddPortMapping(
    NewRemoteHost='0.0.0.0',
    NewExternalPort=12345,
    NewProtocol='TCP',
    NewInternalPort=12345,
    NewInternalClient='192.168.1.10',
    NewEnabled='1',
    NewPortMappingDescription='Testing',
    NewLeaseDuration=10000)