py_mip_sample
===========

py_mip_sample is Python sample program of JDI MIP reflective color display.

[![youtube](http://img.youtube.com/vi/c4KMGHixH8Y/0.jpg)](http://www.youtube.com/watch?v=c4KMGHixH8Y)

MIP reflective color display(Japan Display Inc.) product information.  
https://os.mbed.com/teams/JapanDisplayInc/wiki/MIP-reflective-color-display

Description page (in Japanese):  
[MIPカラー反射型液晶モジュールをRaspberry Pi Zeroで使う](https://qiita.com/hishi/items/669ce474fcd76bdce1f1)

Requirements
------------

- Raspberry Pi Series
- Python3
- NumPy
- Pillow
- spidev

Also, you need to set SPI on by ``raspi-config``.

    $ sudo raspi-config


Application Example
------------

Raspberry Pi based cyclecomputer(in development)
![mip.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/100741/3d7ee1ee-4c27-2e55-cb0a-6a71e228fa4f.png)


Reference
------------

Images are obtained from the mbed sample program.
https://os.mbed.com/teams/JapanDisplayInc/code/MIP8f_FRDM_sample/

