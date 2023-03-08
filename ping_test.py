from pythonping import ping

device_ip = '10.0.3.209'

resp = ping(device_ip)

if resp.success() == True:
    print("device is up")
else:
    print("device is down")

