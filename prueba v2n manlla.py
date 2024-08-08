from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from machine import sleep, SoftI2C, Pin, Timer, PWM
from utime import ticks_diff, ticks_us
import machine
import ssd1306
from umqtt.simple import MQTTClient
import network, time, urequests
from utime import sleep, sleep_ms, ticks_us
import ujson


i2c = machine.I2C(0,scl=machine.Pin(22), sda=machine.Pin(21))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

i2c = SoftI2C(sda=Pin(21),scl=Pin(22),freq=400000)
sensor = MAX30102(i2c=i2c)

MQTT_CLIENT_ID = "manilla00112234332144"
MQTT_BROKER    = "broker.hivemq.com"
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_TOPIC     = "manilla/sensor/"



led = Pin(2, Pin.OUT)

MAX_HISTORY = 32
history = []
beats_history = []
beat = False
beats = 0

def conectaWifi (red, password):
      global miRed
      miRed = network.WLAN(network.STA_IF)     
      if not miRed.isconnected():              #Si no está conectado…
          miRed.active(True)                   #activa la interface
          miRed.connect(red, password)         #Intenta conectar con la red
          print('Conectando a la red', red +"…")
          timeout = time.time ()
          while not miRed.isconnected():           #Mientras no se conecte..
              if (time.ticks_diff (time.time (), timeout) > 10):
                  return False
      return True


if conectaWifi ("SED-CISCO", "Cisco2023"):

    print ("Conexión exitosa!")
    print('Datos de la red (IP/netmask/gw/DNS):', miRed.ifconfig())
     
    print("Conectando a  MQTT server... ",MQTT_BROKER,"...", end="")
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, user=MQTT_USER, password=MQTT_PASSWORD)
    client.connect()
    
    print("Conectado al Broker!")
    
    if sensor.i2c_address not in i2c.scan():
        print("Sensor not found.")
    
    elif not (sensor.check_part_id()):
        # Check that the targeted sensor is compatible
        print("I2C device ID not corresponding to MAX30102 or MAX30105.")
        
    else:
        print("Sensor connected and recognized.")

    
    print("Setting up sensor with default configuration.", '\n')
    sensor.setup_sensor()
    sensor.set_sample_rate(400)
    sensor.set_fifo_average(8)
    sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
    sensor.set_led_mode(2)
    sleep(1)

      
    print("Reading temperature in C.", '\n')
    print(sensor.read_temperature())

    t_start = ticks_us()  # Starting time of the acquisition   

    def display_bpm(t):
        global beats
        
        
        if beats >70:
            buzzer.value(1)
            sleep(0.1)
            buzzer.value(0)
              
        elif beats <60:
            buzzer.value(1)
            sleep(0.1)
            buzzer.value(0)
        else:
            
            buzzer.value(0)
            sleep(0.1)
            
            
        print('Tus latidos: ', beats)
        '''oled.fill(0)
        oled.text("Tus latidos:", 0, 0)
        oled.text(str(beats), 0, 20)
        oled.show()'''
         
        

    timer = Timer(1)
    timer.init(period=2000, mode=Timer.PERIODIC, callback=display_bpm)
    
    while True:    
        sensor.check()

        # Check if the storage contains available samples
        if sensor.available():
            # Access the storage FIFO and gather the readings (integers)
            red_reading = sensor.pop_red_from_storage()
            ir_reading = sensor.pop_ir_from_storage()
            
            value = red_reading
            history.append(value)
            # Get the tail, up to MAX_HISTORY length
            history = history[-MAX_HISTORY:]
            minima = 0
            maxima = 0
            threshold_on = 0
            threshold_off = 0

            minima, maxima = min(history), max(history)

            threshold_on = (minima + maxima * 3) // 4   # 3/4
            threshold_off = (minima + maxima) // 2      # 1/2
            
            if value > 1000:
                if not beat and value > threshold_on:
                    beat = True                    
                    led.on()
                    t_us = ticks_diff(ticks_us(), t_start)
                    t_s = t_us/1000000
                    f = 1/t_s
                    bpm = f * 60
                    if bpm < 500:
                        t_start = ticks_us()
                        beats_history.append(bpm)                    
                        beats_history = beats_history[-MAX_HISTORY:] 
                        beats = round(sum(beats_history)/len(beats_history) ,2)                    
                if beat and value< threshold_off:
                    beat = False
                    led.off()
            
            
            
            print("Revisando Condiciones ...... ")
            message = ujson.dumps({
            "Pulsos": beats,
             })
            
            print("Reportando a  MQTT topic {}: {}".format(MQTT_TOPIC, message))
            client.publish(MQTT_TOPIC, message)
            
    
      
else:
       print ("Imposible conectar")
       miRed.active (False)   