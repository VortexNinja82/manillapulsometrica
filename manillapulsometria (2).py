from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from machine import sleep, SoftI2C, Pin, Timer 
from utime import ticks_diff, ticks_us
from machine import Pin, PWM
from utime import sleep
import machine
import ssd1306
import time
# Configurar el I2C para la comunicación con la pantalla OLED
i2c = machine.I2C(scl=machine.Pin(22), sda=machine.Pin(21))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

# Limpiar la pantalla
oled.fill(0)
oled.show()

buzzer =Pin(14, Pin.OUT)
# Definir una función para mostrar texto en la pantalla OLED
def mostrar_texto(texto):
    oled.fill(0)
    oled.text(texto, 0, 0)
    oled.show()

# Mostrar texto en la pantalla
mostrar_texto("Hola!")

# Esperar unos segundos
time.sleep(2)

# Mostrar otro mensaje en la pantalla
mostrar_texto("Ejercitate <3!")

# Esperar unos segundos
time.sleep(2)

# Limpiar la pantalla antes de salir
oled.fill(0)
oled.show()


led = Pin(2, Pin.OUT)

MAX_HISTORY = 32
history = []
beats_history = []
beat = False
beats = 0
    
i2c = SoftI2C(sda=Pin(21),scl=Pin(22),freq=400000)
sensor = MAX30102(i2c=i2c)  # An I2C instance is required

# Scan I2C bus to ensure that the sensor is connected
if sensor.i2c_address not in i2c.scan():
    print("Sensor not found.")
    
elif not (sensor.check_part_id()):
    # Check that the targeted sensor is compatible
    print("I2C device ID not corresponding to MAX30102 or MAX30105.")
    
else:
    print("Sensor connected and recognized.")

# It's possible to set up the sensor at once with the setup_sensor() method.
# If no parameters are supplied, the default config is loaded:
# Led mode: 2 (RED + IR)
# ADC range: 16384
# Sample rate: 400 Hz
# Led power: maximum (50.0mA - Presence detection of ~12 inch)
# Averaged samples: 8
# pulse width: 411
print("Setting up sensor with default configuration.", '\n')
sensor.setup_sensor()

# It is also possible to tune the configuration parameters one by one.
# Set the sample rate to 400: 400 samples/s are collected by the sensor
sensor.set_sample_rate(400)
# Set the number of samples to be averaged per each reading
sensor.set_fifo_average(8)
# Set LED brightness to a medium value
sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)
sensor.set_led_mode(2)
sleep(1)

# The readTemperature() method allows to extract the die temperature in °C    
print("Reading temperature in C.", '\n')
print(sensor.read_temperature())

t_start = ticks_us()  # Starting time of the acquisition   

def display_bpm(t):
    global beats
    
    
    if beats >70:
        buzzer.value(1)
        sleep(0.1)
        buzzer.value(0)
          
    elif beats <50:
        buzzer.value(1)
        sleep(0.1)
        buzzer.value(0)
    else:
        
        buzzer.value(0)
        sleep(0.1)
        
        
    print('Tus latidos: ', beats)
    oled.fill(0)
    oled.text("Tus latidos:", 0, 0)
    oled.text(str(beats), 0, 20)
    oled.show()
     
    

timer = Timer(1)
timer.init(period=2000, mode=Timer.PERIODIC, callback=display_bpm)

while True:    
    # The check() method has to be continuously polled, to check if
    # there are new readings into the sensor's FIFO queue. When new
    # readings are available, this function will put them into the storage.
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
                
        else:
            led.off()
            print('No dedo')
            oled.fill(0)
            oled.text("No dedo", 0, 0)
            oled.show()
            
