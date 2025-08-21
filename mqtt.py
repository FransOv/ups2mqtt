import paho.mqtt.client as paho

# Command data received via MQTT
reconnect_required=False
test_required=False
test_minutes=1
poll_interval=30

mqtt_client=None

def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe("ups/cmnd")
    mqtt_client.publish("ups/LWT" , "online", qos=0,  retain=True)
    print("MQTT connected, listening on ups/cmnd")
    
def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        print('mqtt broker disconnected. reason_code = ' + str(reason_code))
    mqtt_client.publish("ups/LWT" , "offline", qos=0,  retain=True)

def on_message(client, userdata, msg):
    global reconnect_required, test_required, test_minutes, poll_interval
    try:
        cmnd=msg.payload.decode('utf-8').split(",")
        if cmnd[0]=="restart":
            reconnect_required=True
        elif cmnd[0]=="test":
            if len(cmnd)==2:
                minutes=int(cmnd[1])
            else:
                minutes = 1
            test_minutes=minutes
            test_required=True
        elif cmnd[0]=="polling":
            if len(cmnd)==2:
                poll_interval=int(cmnd[1])
    except Exception as e:
        print(f"MQTT invalid command: Topic = {str(msg.topic)}, Payload = {str(msg.payload)}",e)

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_log(client, userdata, level, buf):
    print("MQTT Log:", buf)

def publish(payload):
    mqtt_client.publish("ups/data",payload)

def connect_mqtt():
    global mqtt_client
    try:
        mqtt_client = paho.Client(paho.CallbackAPIVersion.VERSION2)
        mqtt_client.username_pw_set("hamqtt", password="hamqtt")
        mqtt_client.connect("192.168.2.33",1883)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_disconnect = on_disconnect
        mqtt_client.on_message = on_message
        mqtt_client.will_set("ups/LWT", "offline", qos=0,  retain=True)
        mqtt_client.on_subscribe = on_subscribe
        mqtt_client.connect("192.168.2.33",1883)
        mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)
        mqtt_client.loop_start()
    except Exception as e:
        raise Exception("Error connecting MQTT: " + str(e))


def exit_mqtt():
    if(mqtt_client != None):
        if(mqtt_client.is_connected):
            mqtt_client.publish("ups/LWT" , "offline", qos=0,  retain=True)
        mqtt_client.disconnect()
