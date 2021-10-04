# Raspicam
raspicam is a simple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1, V2, or HQ camera module, directly to a browser. 

# Capabillities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi

# Features
A screen that displays an unaltered video stream that allows you to switch to full screen mode.

# Installation
1. [Ensure the camera module is properly connected to the Raspberry Pi](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/2)
1. [Ensure the operating system is up to date, and the camera interface is enabled](https://www.raspberrypi.org/documentation/configuration/camera.md)
1. Install the [Picamera](https://picamera.readthedocs.io/en/release-1.13/) and Tornado Python module
    ```
    sudo apt-get install python3-picamera tornado
    ```
1. Download
   ```
   wget https://github.com/soyersoyer/raspicam/archive/refs/heads/main.zip
   unzip main.zip
   mv raspicam-main raspicam
   ```

# configuration
open raspicam.py and edit the following section of code as needed. 
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
    cd raspicam
    python3 raspicam.py
    ```
- at startup
    ```
    mkdir -p ~/.config/systemd/user
    cp raspicam.service ~/.config/systemd/user/
    systemd --user enable raspicam
    systemd --user start raspicam
    loginctl enable-linger pi
    ```

    watch the logs
    ```
    systemctl --user status raspicam
    journalctl --user-unit raspicam
    ```

# Viewing
When raspicam.py is running the feed can be vied from any broswer via the following urls. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_serverPort_** is the port you set in the configuration section.
The viewing screen
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
