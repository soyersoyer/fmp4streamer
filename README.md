# Pi H264 To Browser
*Pi H264 To Browser* is a simple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1, V2, or HQ camera module, directly to a browser. 

# Capabillities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi

# Features
1. A screen that displays an unaltered video stream that allows you to switch to full screen mode.

# Viewing
When server.py is running the feed can be vied from any broswer via the following urls. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_serverPort_** is the port you set in the configuration section.  
1. The viewing screen 
    ```
    http://<rpi_address>:<serverPort>/
    ```
# Installation
1. [Ensure the camera module is properly connected to the Raspberry Pi](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/2)
1. [Ensure the operating system is up to date, and the camera interface is enabled](https://www.raspberrypi.org/documentation/configuration/camera.md)
1. Install the [Picamera](https://picamera.readthedocs.io/en/release-1.13/) and Tornado Python module
    ```
    sudo apt-get install python3-picamera tornado
    ```
1. Donwload *Pi H264 To Browser*, and copy the src directoy to your Raspberry Pi    

# configuration
open server.py and edit the following section of code as needed. 
- The webserver will run on the port you set **_serverPort_** to.  
- Refer to the Picamera documentation for details on how to configure it. A lage number of options exist (far more than listed below), that allow for 100% customization of camera. 
    1. [sensor modes, resolutions and framerates](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)
    1. [general camera settings](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.ISO)
        * video_denoise
        * iso
        * shutter_speed
        * exposure_mode
        * awb_mode
        * awb_gains
        * exposure_compensation
        * brightness
        * sharpness
        * contrast
        * saturation
        * hflip
        * vflip
        * meter_mode
    1. [recordingOptions](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.start_recording)
        *  **_inline_headers and sps_timing should always be set to true._**
```python
# start configuration
serverPort = 8000

camera = PiCamera(sensor_mode=2, resolution='1920x1080', framerate=30)
camera.video_denoise = False

recordingOptions = {
    'format' : 'h264', 
    'quality' : 20, 
    'profile' : 'high', 
    'level' : '4.2', 
    'intra_period' : 15, 
    'intra_refresh' : 'both', 
    'inline_headers' : True, 
    'sps_timing' : True
}
# end configuration
```

# Running 
- from the terminal
    ```
    python3 server.py
    ```
- [at startup](https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/)
  * An rc.local example!
    ```
    sudo python3 /home/pi/code/streaming/server.py > /home/pi/code/streaming/log.txt 2>&1 &
    ```
# How It Works
- [Picamera](https://picamera.readthedocs.io/en/release-1.13/) handles all the video related tasks.
- [Tornado](https://www.tornadoweb.org/en/stable/) handles serving out the html and js assets via http, and the h264 stream via websockets.
- [jMuxer](https://github.com/samirkumardas/jmuxer) handles muxing the h264 stream (in browser) and playing it via Media Source extensions. 

# Licencing
- [Picamera](https://github.com/waveform80/picamera/blob/master/LICENSE.txt)
- [Tornado](https://github.com/tornadoweb/tornado/blob/master/LICENSE)
- [jMuxer](https://github.com/samirkumardas/jmuxer/blob/master/LICENSE)
