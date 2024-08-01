from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep
 
myGPIO=19
 
myCorrection=0.45
maxPW=(2.0+myCorrection)/1000
minPW=(1.0-myCorrection)/1000
 
servo = Servo(myGPIO,min_pulse_width=minPW,max_pulse_width=maxPW, pin_factory = PiGPIOFactory())
 
while True:
    servo.mid()
    print("mid")
    sleep(2)
    servo.min()
    print("min")
    sleep(2)
    print("max")
    servo.max()
    sleep(2)
    
    tl = haz
    tr = rec
    bl = bio
    br = nonbio