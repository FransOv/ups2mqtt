import usb.core
import usb.util
import paho.mqtt.client as paho
import json
import sys
import datetime
from time import sleep
import mqtt
                
# Global data
# The usb device
dev=None
# USB requests
Q1=bytearray(b'Q1\r')
Q1=bytearray([0xa0|len(Q1)])+Q1
I=bytearray(b'I\r')
I=bytearray([0xa0|len(I)])+I
F=bytearray(b'F\r')
F=bytearray([0xa0|len(F)])+F
TST=bytearray(b'T01\r')
TST=bytearray([0xa0|len(TST)])+TST

def usb_connect (vendor, product): 
    # Find the device
    dev = usb.core.find(idVendor=vendor, idProduct=product)
    if dev is not None:
        print("Found UPS:",dev.manufacturer, dev.product)
        for cfg in dev:
            print('cfg:'+str(cfg.bConfigurationValue) + '\n')
            for intf in cfg:
                print('int:\t' + str(intf.bInterfaceNumber) + str(intf.bAlternateSetting) + '\n')
                for ep in intf:
                    print('ept:\t\t' + hex(ep.bEndpointAddress) + '\n')
        if dev.is_kernel_driver_active(0):
            try:
                dev.detach_kernel_driver(0)
                print ("kernel driver detached")
            except usb.core.USBError as e:
                sys.exit("Could not detach kernel driver: %s" % str(e))
        else:
            print ("no kernel driver attached")
    return dev

def publish_response(response):
    data={}
    data["device"]=dev.manufacturer+" - "+dev.product
    data["datetime"]=format(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S')
    data["volt_in"]=float(bytes(response[2:6]).decode('utf-8'))
    data["volt_out"]=float(bytes(response[14:19]).decode('utf-8'))
    data["load"]=float(bytes(response[7:13]).decode('utf-8'))
    data["frequency"]=float(bytes(response[24:28]).decode('utf-8'))
    data["volt_bat"]=float(bytes(response[29:33]).decode('utf-8'))
    volt_soc=[10.0,12.0,12.8,12.9,13.0,13.0,13.1,13.2,13.3,13.4,13.6]
    data["soc_bat"]=100
    for ix in range(11):
        if data["volt_bat"]<=volt_soc[ix]:
            data["soc_bat"]=(ix-1)*10
            break
    data["temp"]=float(bytes(response[34:38]).decode('utf-8'))
    data["ac_ok"]=response[39]==0x30
    data["test_mode"]=response[44]==0x31
    mqtt.publish(json.dumps(data))
    return True
    
 
def mainloop():
    global dev, TST
    init_print=True
    # Connect to MQTT
    mqtt.connect_mqtt()
    dev=usb_connect(0x925,0x1234)
    if dev is None:
        raise ValueError('Device not found')
    else:
        # Request info
        dev.write(0x02,I,1000)                # Request version
        response = dev.read(0x82, 64, 5000)
        print(format(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'),format(response[1],'#010b'),bytes(response[2:response[0]&0x3f]))
        dev.write(0x02,F,1000)                # Request specification
        response = dev.read(0x82, 64, 5000)
        print(format(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'),format(response[1],'#010b'),bytes(response[2:response[0]&0x3f]))

        # Start polling
        while True:
            try:
                dev.write(0x02,Q1,1000)       # Request data packet
                response = dev.read(0x82, 64, 5000)
                if init_print:
                    print(format(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'),format(response[1],'#010b'),bytes(response[2:response[0]&0x3f]))
                    #init_print=False
                publish_response(response)
                sleep(mqtt.poll_interval)
            except usb.core.USBError as e:
                print(format(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'), e)
                dev.reset()                   # By way of reset, only one configuration so default is ok
                sleep(mqtt.poll_interval*2)        # Give it some time
                dev=usb_connect(0x925,0x1234) # and try again
                if dev is None:               # No Go, so quit
                    sys.exit("Could not recover from error: %s" % str(e))

            if mqtt.reconnect_required:
                print("UPS2MQTT: Reconnecting.")
                mqtt.reconnect_required=False
                dev.reset()                   # Reset the device and the connection
                sleep(mqtt.poll_interval)     # Give it some time
                dev=usb_connect(0x925,0x1234) # and try to connect again
                if dev is None:               # No Go, so quit
                    sys.exit("UPS2MQTT: Could not Reconnect USB")
            if mqtt.test_required:
                print(f"UPS2MQTT: Testmode for {mqtt.test_minutes} minutes.")
                mqtt.test_required=False
                TST=bytearray(f"T{mqtt.test_minutes:02d}\r","utf-8")
                TST=bytearray([0xa0|len(TST)])+TST
                print(TST)
                dev.write(0x02,TST,1000)
                sleep(mqtt.poll_interval)    # give it some time to set up test mode otherwise test will not work

if __name__ == "__main__":
    mainloop()
