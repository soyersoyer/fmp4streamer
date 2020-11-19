# Pi H264 To Browser
*Pi H264 To Browser* is a siple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1 or V2 cameras module, directly to a browser. 

# Capabillities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi

# Installation
1. [Ensure the camera module is properly connected to the Raspberry Pi](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/2)
2. [Ensure the operating system is up to date, and the camera interface is enabled](https://www.raspberrypi.org/documentation/configuration/camera.md)
3. Install the [Picamera](https://picamera.readthedocs.io/en/release-1.13/) Python module
    ```
    sudo apt-get install python3-picamera
    ```
4. Install pip to handle loading Pyhton pckages not avaiable in the Raspberry Pi OS archives
    ```
    sudo apt install python3-pip
    ```
5. Install the [Tornado framework](https://www.tornadoweb.org/en/stable/)
    ```
    sudo pip3 install tornado
    ```
6. Donwload *Pi H264 To Browser*, and copy the src directoy to your Raspberry Pi    

# configuration
open server.py and edit the following section of code as needed. 
- The webserver will run on the port you set **_serverPort_** to.  
- Refer to Picamera documentation for details on how to configure it.
    1. [sensor modes, resolutions and framerates](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)
    2. [general camera settings](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.ISO)
        * ISO
        * awb_mode
        * exposure_compensation
        * exposure_mode
        * hflip
        * vflip
        * meter_mode
        * video_denoise
    3. [recordingOptions](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.start_recording)
        *  **_inline_headers and sps_timing should always be set to true._**
```python
# start configuration
serverPort = 8000

camera = PiCamera(sensor_mode=1, resolution='1920x1080', framerate=30)
camera.vflip = True
camera.hflip = True
camera.video_denoise = True

recordingOptions = {
    'format' : 'h264', 
    #'bitrate' : 25000000, 
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

# Viewing
When you have server.py running the feed can be vied from any broswer via the following url. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_serverPort_** is the port you chose in the configuration section.  
```
http://<rpi_address>:<serverPort>/
```

# How It Works
- [Picamera](https://picamera.readthedocs.io/en/release-1.13/) handles all the video related tasks.
- [Tornado](https://www.tornadoweb.org/en/stable/) handles serving out the html and js assets via http, and the h264 stream via websockets.
- [jMuxer](https://github.com/samirkumardas/jmuxer) handles muxing the h264 stream (in browser) and playing it via Media Source extensions. 

# Licencing
- [Picamera](https://github.com/waveform80/picamera/blob/master/LICENSE.txt)
- [Tornado](https://github.com/tornadoweb/tornado/blob/master/LICENSE)
- [jMuxer](https://github.com/samirkumardas/jmuxer/blob/master/LICENSE)
