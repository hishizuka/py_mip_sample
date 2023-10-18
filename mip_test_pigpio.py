import time
from PIL import Image
import numpy as np
import datetime

IS_RASPI = False
try:
    import pigpio
    IS_RASPI = True
except:
   pass

print("SPI LOAD:", IS_RASPI)
print("##### PYTHON NIL #####")

DISP = 27
SCS = 23 #22
VCOMSEL = 17
BACKLIGHT = 18

#0x90 4bit update mode
#0x80 3bit update mode (fast)
#0x88 1bit update mode (most fast, but 2-color)
UPDATE_MODE = 0x80

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 240


class MipDisplay():

    pi = None
    spi = None
    
    buff_width = int(SCREEN_WIDTH*3/8)+2 #for 3bit update mode
    #buff_width = int(SCREEN_WIDTH*4/8)+2 #for 4bit update mode

    def __init__(self):
      
        if not IS_RASPI:
            return
       
        self.pi = pigpio.pi()
        #self.spi = self.pi.spi_open(0, 2000000, 0)
        self.spi = self.pi.spi_open(0, 5500000, 0)
        time.sleep(0.1)     #Wait
         
        self.pi.set_mode(DISP, pigpio.OUTPUT)
        self.pi.set_mode(SCS, pigpio.OUTPUT)
        self.pi.set_mode(VCOMSEL, pigpio.OUTPUT)
         
        self.pi.write(SCS, 0)
        self.pi.write(DISP, 1)
        self.pi.write(VCOMSEL, 1)
        time.sleep(0.1)

        self.pi.set_mode(BACKLIGHT, pigpio.OUTPUT)
        self.pi.hardware_PWM(BACKLIGHT, 64, 0)

        self.pre_img = np.zeros((SCREEN_HEIGHT, self.buff_width), dtype='uint8')
        self.img_buff_rgb8 = np.empty((SCREEN_HEIGHT, self.buff_width), dtype='uint8')
        self.img_buff_rgb8[:,0] = UPDATE_MODE 
        self.img_buff_rgb8[:,1] = np.arange(SCREEN_HEIGHT)
        self.img_buff_rgb8[:,0] = self.img_buff_rgb8[:,0] + (np.arange(SCREEN_HEIGHT) >> 8)

        self.clear()
    
    def clear(self):
        if not IS_RASPI:
            return
        self.pi.write(SCS, 1)
        time.sleep(0.000006)
        self.pi.spi_write(self.spi, [0b00100000,0]) # ALL CLEAR MODE
        self.pi.write(SCS, 0)
        time.sleep(0.000006)

    def no_update(self):
        if not IS_RASPI:
            return
        self.pi.write(SCS, 1)
        time.sleep(0.000006)
        self.pi.spi_write(self.spi, [0b00000000,0]) # NO UPDATE MODE
        self.pi.write(SCS, 0)
        time.sleep(0.000006)

    def blink(self, sec):
        if not IS_RASPI:
            return
        s = sec
        state = True
        interval = 0.5
        while s > 0:
            self.pi.write(SCS, 1)
            time.sleep(0.000006)
            if state:
                self.pi.spi_write(self.spi, [0b00010000,0]) # BLINK(BLACK) MODE
            else:
                self.pi.spi_write(self.spi, [0b00011000,0]) # BLINK(WHITE) MODE
            self.pi.write(SCS, 0)
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
            self.pi.write(SCS, 1)
            time.sleep(0.000006)
            if state:
                self.pi.spi_write(self.spi, [0b00010100,0]) # INVERSION MODE
            else:
                self.no_update()
            self.pi.write(SCS, 0)
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
            self.pi.write(SCS, 1)
            time.sleep(0.000006)
            if len(img_bytes) > 0:
                self.pi.spi_write(self.spi, img_bytes)
            #dummy output for ghost line
            self.pi.spi_write(self.spi, [0x00000000,0])
            time.sleep(0.000006)
            self.pi.write(SCS, 0)
        print("Drawing images... :", (datetime.datetime.now()-t).total_seconds(),"sec")

    def set_brightness(self, brightness):
      
        b = brightness
        if brightness >= 100:
            b = 100
        elif brightness <= 0:
            b = 0
        
        if not IS_RASPI:
            return
        self.pi.hardware_PWM(BACKLIGHT, 64, b*10000)
        time.sleep(0.05)

    def backlight_blink(self):
        if not IS_RASPI:
            return
        for x in range(2):
            for pw in range(0,100,1):
                self.pi.hardware_PWM(BACKLIGHT, 64, pw*10000)
                time.sleep(0.05)
            for pw in range(100,0,-1):
                self.pi.hardware_PWM(BACKLIGHT, 64, pw*10000)
                time.sleep(0.05)

    def quit(self):
        if not IS_RASPI:
            return
        #self.clear()
        self.set_brightness(0)
        self.pi.write(DISP, 1)
        time.sleep(0.1)
        self.pi.spi_close(self.spi)
        self.pi.stop()

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

