from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
 
myGPIO=12
 
myCorrection=0.45
maxPW=(2.0+myCorrection)/1000
minPW=(1.0-myCorrection)/1000
 
servo = Servo(myGPIO,min_pulse_width=minPW,max_pulse_width=maxPW, pin_factory = PiGPIOFactory())
 
while True:
    servo.mid()
    print("mid")
    sleep(1.5)
    servo.min()
    print("min")
    sleep(1.5)
    
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

servo_x = Servo(13, pin_factory = PiGPIOFactory())

while True:
    servo_x.min()
    sleep(2)
    servo_x.mid()
    sleep(2)
    servo_x.max()
    sleep(2)