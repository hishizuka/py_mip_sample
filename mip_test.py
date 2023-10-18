import time
from PIL import Image
import numpy as np
import datetime

IS_RASPI = False
try:
    import spidev
    import RPi.GPIO as GPIO
    IS_RASPI = True
except:
   pass

print("SPI LOAD:", IS_RASPI)
print("##### PYTHON NIL #####")

DISP = 27
SCS = 23 #22
VCOMSEL = 17
BACKLIGHT = 4 #if GPIO 4(pin7) is already used with other devics, set 18(pin12) etc

#0x90 4bit update mode
#0x80 3bit update mode (fast)
#0x88 1bit update mode (most fast, but 2-color)
UPDATE_MODE = 0x80

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 240


class MipDisplay():

    spi = None
    
    buff_width = int(SCREEN_WIDTH*3/8)+2 #for 3bit update mode
    #buff_width = int(SCREEN_WIDTH*4/8)+2 #for 4bit update mode

    def __init__(self):
      
        if not IS_RASPI:
            return
        
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)
        self.spi.mode = 0b00 #SPI MODE0
        #self.spi.max_speed_hz = 2000000 #MAX 2MHz
        self.spi.max_speed_hz =  9500000 #overclocking
        self.spi.no_cs 
        time.sleep(0.1)     #Wait
         
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DISP, GPIO.OUT)
        GPIO.setup(SCS, GPIO.OUT)
        GPIO.setup(VCOMSEL, GPIO.OUT)
         
        GPIO.output(SCS, 0)     #1st=L
        GPIO.output(DISP, 1)    #1st=Display On
        #GPIO.output(DISP, 0)   #1st=No Display
        #GPIO.output(VCOMSEL, 0) #L=VCOM(1Hz)
        GPIO.output(VCOMSEL, 1) #L=VCOM(1Hz)
        time.sleep(0.1)

        GPIO.setup(BACKLIGHT, GPIO.OUT)
        #self.backlight = GPIO.PWM(BACKLIGHT, 60)
        self.backlight = GPIO.PWM(BACKLIGHT, 64)
        self.backlight.start(0)

        self.pre_img = np.zeros((SCREEN_HEIGHT, self.buff_width), dtype='uint8')
        self.img_buff_rgb8 = np.empty((SCREEN_HEIGHT, self.buff_width), dtype='uint8')
        self.img_buff_rgb8[:,0] = UPDATE_MODE 
        self.img_buff_rgb8[:,1] = np.arange(SCREEN_HEIGHT)
        self.img_buff_rgb8[:,0] = self.img_buff_rgb8[:,0] + (np.arange(SCREEN_HEIGHT) >> 8)

        self.clear()
    
    def clear(self):
        if not IS_RASPI:
            return
        GPIO.output(SCS, 1)
        time.sleep(0.000006)
        self.spi.xfer2([0b00100000,0]) # ALL CLEAR MODE
        GPIO.output(SCS, 0)
        time.sleep(0.000006)

    def no_update(self):
        if not IS_RASPI:
            return
        GPIO.output(SCS, 1)
        time.sleep(0.000006)
        self.spi.xfer2([0b00000000,0]) # NO UPDATE MODE
        GPIO.output(SCS, 0)
        time.sleep(0.000006)

    def blink(self, sec):
        if not IS_RASPI:
            return
        s = sec
        state = True
        interval = 0.5
        while s > 0:
            GPIO.output(SCS, 1)
            time.sleep(0.000006)
            if state:
                self.spi.xfer2([0b00010000,0]) # BLINK(BLACK) MODE
            else:
                self.spi.xfer2([0b00011000,0]) # BLINK(WHITE) MODE
            GPIO.output(SCS, 0)
            time.sleep(interval)
            s -= interval
            state = not state
        self.no_update()

    def inversion(self, sec):
        if not IS_RASPI:
            return
        s = sec
        state = True
        interval = 0.5
        while s > 0:
            GPIO.output(SCS, 1)
            time.sleep(0.000006)
            if state:
                self.spi.xfer2([0b00010100,0]) # INVERSION MODE
            else:
                self.no_update()
            GPIO.output(SCS, 0)
            time.sleep(interval)
            s -= interval
            state = not state
        self.no_update()

    #def pil_to_screen(self, pil_img):
    def pil_to_screen(self, img_file):

        im_array = np.array(Image.open(img_file))
        #im_array = np.array(pil_img)

        t = datetime.datetime.now()

        #3bit mode update
        self.img_buff_rgb8[:,2:] = np.packbits(
            ((im_array > 128).astype('uint8')).reshape(SCREEN_HEIGHT,SCREEN_WIDTH*3),
            axis=1
            )
        img_bytes = bytearray()

        #differential update
        rewrite_flag = False
        diff_lines = np.where(np.sum((self.img_buff_rgb8 == self.pre_img), axis=1) != self.buff_width)[0] 
        print("diff ", int(len(diff_lines)/SCREEN_HEIGHT*100), "%")
        img_bytes = self.img_buff_rgb8[diff_lines].tobytes()
        if len(diff_lines) > 0:
            rewrite_flag = True
        self.pre_img[diff_lines] = self.img_buff_rgb8[diff_lines]

        print("Loading images... :", (datetime.datetime.now()-t).total_seconds(),"sec")

        t = datetime.datetime.now()
        if IS_RASPI:
            GPIO.output(SCS, 1)
            time.sleep(0.000006)
            if len(img_bytes) > 0:
                self.spi.xfer3(img_bytes)
            #dummy output for ghost line
            self.spi.xfer2([0x00000000,0])
            time.sleep(0.000006)
            GPIO.output(SCS, 0)
        print("Drawing images... :", (datetime.datetime.now()-t).total_seconds(),"sec")

    def set_brightness(self, brightness):
      
        b = brightness
        if brightness >= 100:
            b = 100
        elif brightness <= 0:
            b = 0
        
        if not IS_RASPI:
            return
        self.backlight.ChangeDutyCycle(b)
        time.sleep(0.05)

    def backlight_blink(self):
        if not IS_RASPI:
            return
        for x in range(2):
            for pw in range(0,100,1):
                self.backlight.ChangeDutyCycle(pw)
                time.sleep(0.05)
            for pw in range(100,0,-1):
                self.backlight.ChangeDutyCycle(pw)
                time.sleep(0.05)

    def quit(self):
        if not IS_RASPI:
            return
        #self.clear()
        GPIO.output(DISP, 1)
        time.sleep(0.1)
        self.set_brightness(0)
        self.spi.close()
        GPIO.cleanup()

if __name__ == '__main__':
    m = MipDisplay() 
    m.set_brightness(50)
    #Get image from https://os.mbed.com/teams/JapanDisplayInc/code/MIP8f_FRDM_sample/. Need "LPM027M128x (400x240)".
    m.pil_to_screen('img/004_blood3.bmp')
    time.sleep(1)
    m.pil_to_screen('img/004_blood3.bmp')
    time.sleep(1)
    m.pil_to_screen('img/005_blood4.bmp')
    time.sleep(1)
    m.pil_to_screen('img/n00011 400x240 navi.bmp')
    time.sleep(1)
    m.pil_to_screen('img/n00012 400x240 navi.bmp')
    time.sleep(1)
    m.pil_to_screen('img/003_b1.bmp')
    time.sleep(1)
    m.blink(3)
    m.inversion(3)
    m.quit()

