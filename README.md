# RaspiWebCam
|
[What is RaspiWebCam](#what-is-raspiwebcam) |
[How does it work](#how-does-it-work) |
[Capabilities](#capabilities) |
[Installation](#installation) |
[Running](#running) |
[Viewing](#viewing) |
[Configuration](#configuration) |
[Motivation](#motivation) |

# What is RaspiWebCam
RaspiWebCam is a simple Python application designed to stream hardware encoded h.264 from a Raspberry Pi equiped with a V1, V2, or HQ camera module, directly to a browser.

# How does it work
This python script runs a [raspivid](https://www.raspberrypi.org/documentation/accessories/camera.html#raspivid-2) in the background, reads the h264 stream from it, adds some fMP4 (fragmented MP4) header and serves it via HTTP. It works with only one html5 video tag, no js needed. It's pretty lightweight.

# Capabilities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the camera module can capture and the gpu can encode 
- Able to do both of the preceding from any Raspberry Pi
- Able to handle high framerate (60-90 fps) streams
- Able to stream to iPhone and Safari via HLS.

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
When raspiwebcam.py is running the feed can be viewed from any browser via the following urls. **_rpi_address_** is the ip address or hostname of your Raspberry Pi, and **_server_port_** (default: 8000) is the port you set in the configuration section.
The viewing screen
    ```
    http://<rpi_address>:<server_port>/
    ```

# Configuration
Open raspiwebcam.py and edit the following section of code as needed. 
- The webserver will run on the port you set **_server_port_** to.  
- Refer to the [raspivid documentation](https://www.raspberrypi.org/documentation/accessories/camera.html#raspivid-2) for details on how to configure it. A lage number of options exist (far more than listed below), that allow for 100% customization of camera. 
    ```sh
    $ raspivid | less
    ```

```python
# start configuration
server_port = 8000

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
    stdout=PIPE, bufsize=0)
# end configuration
```
# Motivation

I wanted to stream my raspberry camera to the browser. I found some solution, but I think they are not optimal or too heavy.

## MJPEG streamers
We have h264, why do we want to stream mjpeg?

## VLC, Gstreamer, FFmpeg
```
apt install vlc
...
0 upgraded, 294 newly installed, 0 to remove and 0 not upgraded.
Need to get 107 MB of archives.
After this operation, 900 MB of additional disk space will be used.
```

```
apt install libgstreamer-plugins-base1.0 gstreamer1.0-tools
...
0 upgraded, 119 newly installed, 0 to remove and 0 not upgraded.
Need to get 51.5 MB of archives.
After this operation, 633 MB of additional disk space will be used.
```

```
apt install ffmpeg
...
0 upgraded, 149 newly installed, 0 to remove and 0 not upgraded.
Need to get 69.3 MB of archives.
After this operation, 714 MB of additional disk space will be used.
```


These are huge. It's bad because lot of binary contains a lot of security bugs and you have to update these packages too in your project lifetime, not just install them in one time.

## [U4VL](https://www.linux-projects.org/uv4l/)
You have to add a custom apt repository to your pi to install, you have to trust these guys. It has closed source components too. So no way.

## [131/h264-live-player](https://github.com/131/h264-live-player)
It uses a baseline javascript h264 decoder. We have better h264 decoders in our hardwares, so why do we want to use a javascript decoder?

## [dans98/pi-h264-to-browser](https://github.com/dans98/pi-h264-to-browser)
I like it, it's good, but I don't like its dependencies
```
apt install python3-picamera
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following additional packages will be installed:
  libblas3 libgfortran5 liblapack3 python3-numpy
Suggested packages:
  gfortran python-numpy-doc python3-dev python3-pytest python3-numpy-dbg python-picamera-docs
The following NEW packages will be installed:
  libblas3 libgfortran5 liblapack3 python3-numpy python3-picamera
0 upgraded, 5 newly installed, 0 to remove and 0 not upgraded.
Need to get 3,830 kB of archives.
After this operation, 18.1 MB of additional disk space will be used.
```
Do we really need fortran to use a camera in python? Do we look like dinosaurs? NO! And 18.1 MB for some init and some read?

![Fortran dinousaurs](https://i.pinimg.com/564x/7c/3a/c8/7c3ac86430655a9f22b2b2496bb4d1ee.jpg)

```
apt install python3-tornado
...
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 354 kB of archives.
After this operation, 1,800 kB of additional disk space will be used.
```
It's for the websocket server, not too big but do we really need websockets? No, simple http is enough for streaming to browsers.

[jmuxer](https://github.com/samirkumardas/jmuxer)

Why do we want to add mp4 headers to h264 with js in the browser? If we want to do it properly we have to send timing information next to h264 too, but what should be the format, custom encoding or protobuf? Or wait, there is already a format for that, I remember it, the mp4! So it should be done on the server side.

[Media Source Extensions](https://caniuse.com/mediasource)

It could be good, but safari on iOS doesn't support it... and why do we need javascript code to play a video?

## [thinkski/berrymse](https://github.com/thinkski/berrymse)

It inspired me, I like it very much, it's simple and minimal, but it uses websockets and the Media Source Extensions...

## raspiwebcam

So here we are.

It doesn't have any dependencies other than python and raspivid, but they are installed by default.

It adds fMP4 (fragmented MP4) headers to the h264 stream. It uses the python http server to serve it to the browser.

The browsers play it with only one html5 video tag (the most of). No javascript needed.

Safari on iOS plays it only with HLS playlists, but it works too. And the playlists added to the index.html of course.
