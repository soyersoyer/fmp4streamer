# Pi H264 To Browser
*Pi H264 To Browser* is a siple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1, V2, or HQ camera module, directly to a browser. 

# Capabillities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi

# Features
1. A screen that displays an unaltered video stream that allows you to switch to full screen mode.
2. A screen that provides a focus peaking overlay to help focus the camera.
    [![focus peaking demo ](https://raw.githubusercontent.com/dans98/pi-h264-to-browser/main/readmeAssets/focusPeakingDemo.jpg)](http://www.youtube.com/watch?v=BtihM-EcTzU "focus peaking demo ")   
3. A screen that provides a center reticle overlay to aide in centering a subject in the frame.
4. A screen that provides a standard 9 grid overlay to aide in more creative framing.

# Viewing
When server.py is running the feed can be vied from any broswer via the following urls. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_serverPort_** is the port you set in the configuration section.  
1. The primary viewing screen 
    ```
    http://<rpi_address>:<serverPort>/
    ```
2. The focus peaking screen 
    ```
    http://<rpi_address>:<serverPort>/focus/
    ```
3. The center reticle screen 
    ```
    http://<rpi_address>:<serverPort>/center/
    ```
4. The 9 grid screen 
    ```
    http://<rpi_address>:<serverPort>/grid/
    ```
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
- Refer to the Picamera documentation for details on how to configure it. A lage number of options exist (far more than listed below), that allow for 100% customization of camera. 
    1. [sensor modes, resolutions and framerates](https://picamera.readthedocs.io/en/release-1.13/fov.html#sensor-modes)
    2. [general camera settings](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.ISO)
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
    3. [recordingOptions](https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.start_recording)
        *  **_inline_headers and sps_timing should always be set to true._**
    4. Focus peaking screen
        * focusPeakingColor - What color a pixel that is in focus should be. This is a webgl color format string, and must be 4 comma seperated floating point numbers between 0.0 and 1.0! From left to right the numbers represent the red, green, blue, and alpha channels. 
        * focusPeakingthreshold - Determines at what point a pixel is considred to be in focus. A pixel with a value below the threshold is considered out of focus, or an aberration. A pixel above the threshold is considered in focus. This is a floating point number that has a theoretical maximum range of 0.0 to 1.0, however values between 0.02 and 0.11 generally yield the best results.   
    5. Center screen
        * centerColor - What color the centering reticle should be. This is a css color format string, and must be 4 comma seperated values. The first three are integers ranging from 0 to 255, and the forth is a float ranging from 0.0 to 1.0. From left to right the numbers represent the red, green, blue, and alpha channels.   
        * centerThickness - and integer value that sets the thickness(in pixels) of the lines that make up the reticle.
    5. 9 grid screen
        * gridColor - What color the grid should be. This is a css color format string, and must be 4 comma seperated values. The first three are integers ranging from 0 to 255, and the forth is a float ranging from 0.0 to 1.0. From left to right the numbers represent the red, green, blue, and alpha channels.   
        * gridThickness - and integer value that sets the thickness(in pixels) of the lines that make up the grid.
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

focusPeakingColor = '1.0, 0.0, 0.0, 1.0'
focusPeakingthreshold = 0.055

centerColor = '255, 0, 0, 1.0'
centerThickness = 2

gridColor = '255, 0, 0, 1.0'
gridThickness = 2
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
    sudo python3 /home/pi/code/streaming/server.py & > /home/pi/code/streaming/log.txt 2>&1
    ```
# How It Works
- [Picamera](https://picamera.readthedocs.io/en/release-1.13/) handles all the video related tasks.
- [Tornado](https://www.tornadoweb.org/en/stable/) handles serving out the html and js assets via http, and the h264 stream via websockets.
- [jMuxer](https://github.com/samirkumardas/jmuxer) handles muxing the h264 stream (in browser) and playing it via Media Source extensions. 

# Licencing
- [Picamera](https://github.com/waveform80/picamera/blob/master/LICENSE.txt)
- [Tornado](https://github.com/tornadoweb/tornado/blob/master/LICENSE)
- [jMuxer](https://github.com/samirkumardas/jmuxer/blob/master/LICENSE)
