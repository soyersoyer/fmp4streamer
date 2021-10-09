# RaspiWebCam
RaspiWebCam is a simple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1, V2, or HQ camera module, directly to a browser. 

# Capabillities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi
- Able to handle high framerate (60-90 fps) streams

# Features
A screen that displays an unaltered video stream that allows you to switch to full screen mode.

# How It Works
This python script runs a [raspivid](https://www.raspberrypi.org/documentation/accessories/camera.html#raspivid-2) in the background, reads the h264 stream from it, adds some mp4 header and serves it via HTTP. It's pretty lightweight.

# Installation
1. [Ensure the camera module is properly connected to the Raspberry Pi](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera/2)
1. [Ensure the operating system is up to date, and the camera interface is enabled](https://www.raspberrypi.org/documentation/configuration/camera.md)
1. Download
   ```
   wget https://github.com/soyersoyer/raspiwebcam/archive/refs/heads/main.zip
   unzip main.zip
   mv raspiwebcam-main raspiwebcam
   ```

# Running 
- from the terminal
    ```
    cd raspiwebcam
    python3 raspiwebcam.py
    ```
- at startup
    ```
    cd raspiwebcam
    mkdir -p ~/.config/systemd/user
    cp raspiwebcam.service ~/.config/systemd/user/
    systemctl --user enable raspiwebcam
    systemctl --user start raspiwebcam
    loginctl enable-linger pi
    ```

    watch the logs
    ```
    systemctl --user status raspiwebcam
    journalctl --user-unit raspiwebcam
    ```

# Viewing
When raspiwebcam.py is running the feed can be vied from any browser via the following urls. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_serverPort_** (default: 8000) is the port you set in the configuration section.
The viewing screen
    ```
    http://<rpi_address>:<serverPort>/
    ```

# Configuration
Open raspiwebcam.py and edit the following section of code as needed. 
- The webserver will run on the port you set **_serverPort_** to.  
- Refer to the [raspivid documentation](https://www.raspberrypi.org/documentation/accessories/camera.html#raspivid-2) for details on how to configure it. A lage number of options exist (far more than listed below), that allow for 100% customization of camera. 
    ```sh
    $ raspivid | less
    ```

```python
# start configuration
serverPort = 8000

raspivid = Popen([
    'raspivid',
    '--width', '800',
    '--height', '600',
    '--framerate', '30',
    '--intra', '15',
    '--qp', '20',
    '--irefresh', 'both',
    '--level', '4.2',
    '--profile', 'high',
    '--nopreview',
    '--timeout', '0',
    '--output', '-'],
    stdout=PIPE, bufsize=65536)
# end configuration
```
