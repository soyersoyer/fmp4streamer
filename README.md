# fmp4streamer
[What is fmp4streamer](#what-is-fmp4streamer) |
[How does it work](#how-does-it-work) |
[Capabilities](#capabilities) |
[Installation](#installation) |
[Running](#running) |
[Viewing](#viewing) |
[Configuration](#configuration) |
[Raspberry](#raspberry) |
[Latency](#latency) |
[Tested cameras](#tested-cameras) |
[Roadmap](#roadmap) |
[Motivation](#motivation) |
[Changelog](https://github.com/soyersoyer/fmp4streamer/blob/main/CHANGELOG.md)

# What is fmp4streamer
The fmp4streamer is a Python application designed to stream hardware encoded H.264 from a V4L2 Linux video device directly to a browser.

# How does it work
This python script setups the V4L2 device, reads the H264 or MJPGH264 stream from it (or the YUYV stream and converts to H264 with a M2M V4L2 device), adds some fMP4 (fragmented MP4) header and serves it via HTTP. It works with only one html5 video tag, no js needed. It's pretty lightweight.

# Capabilities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the video device can capture
- Works in any Raspberry Pi with a camera module (If you are using the Raspberry OS Bullseye version please read the [Raspberry](#raspberry) section)
- Able to handle high framerate (60-90 fps) streams
- Able to handle cameras which only provide H264 inside MJPG format (UVC 1.5 H264 cameras, like Logitech C930e)
- Able to stream to iPhone and Safari via HLS.
- Low cpu utilization

# Installation
   ```
   wget https://github.com/soyersoyer/fmp4streamer/archive/refs/tags/v3.2.0.zip
   unzip v3.2.0.zip
   mv fmp4streamer-3.2.0 fmp4streamer
   ```

# Running 
- from the terminal
    ```
    cd fmp4streamer
    python3 fmp4streamer.py
    ```
- at startup
    ```
    cd fmp4streamer
    mkdir -p ~/.config/systemd/user
    cp fmp4streamer.service ~/.config/systemd/user/
    systemctl --user enable fmp4streamer
    systemctl --user start fmp4streamer
    loginctl enable-linger pi
    ```

    watch the logs
    ```
    systemctl --user status fmp4streamer
    journalctl --user-unit fmp4streamer
    ```

# Viewing
When fmp4streamer.py is running the stream can be viewed from any browser via the following url. **_ip_address_** is the ip address or hostname of your computer, and **_port_** (default: 8000) is the port you set in the configuration section.
```
http://<ip_address>:<port>/
```
  
If you want to view the stream via your favourite media player, you can use the
```
http://<ip_address>:<port>/stream.mp4
```
url.

# Configuration

You can start with the fmp4streamer.conf.dist:

```
cp fmp4streamer.conf.dist fmp4streamer.conf
```

Which contains:
```ini
[server]
listen = 
port = 8000

[/dev/video0]
width = 800
height = 600
fps = 30
# capture_format = H264 # H264, MJPGH264, YUYV
# encoder = /dev/video11 # if you have to encode the stream to H264

# you can set any V4L2 control too, list them with the -l option
h264_profile = High
h264_level = 4.2
h264_i_frame_period = 15
```

You can set all the V4L2 or UVCX H264 controls via the configuration file. List them with
```
python3 fmp4streamer.py -l
```

# Raspberry

The Raspberry PI camera works with the default config on Raspberry OS Buster version.
If you are using Bullseye with the PI cameras, you should setup the [old camera stack](https://forums.raspberrypi.com/viewtopic.php?t=323390) 


> Edit /boot/config.txt, remove the line "camera_auto_detect=1", and add "start_x=1" and "gpu_mem=128".
> Rebooting at this stage will reload the old V4L2 driver.


If you have a raspberry with an USB camera which supports YUYV format, you can use this configuration:

```ini
[server]
listen = 
port = 8000

[/dev/video1]
width = 640
height = 480
fps = 30
capture_format = YUYV
encoder = /dev/video11

[/dev/video11]
# you can set any V4L2 control too, list them with the -l option
h264_profile = High
h264_level = 4.2
h264_i_frame_period = 15
```

# Latency

You can reduce the latency with lower I-Frame periods. You can set with the `h264_i_frame_period` or `uvcx_h264_i_frame_period` controls.

# Tested Cameras

- Raspberry PI Camera V1
- Raspberry PI Camera V2
- Logitech C270 (works with capture_format = YUYV and the Raspiberry pi's H264 encoder)
- Logitech C920 V1 (046d:082d) (works with capture_format = H264) (Thanks @balazspeczeli for the camera)
- Logitech C930e (046d:0843) (works with capture_format = MJPGH264)

# Roadmap
- [x] Use V4L2 instead of raspivid
- [x] Use V4L2 M2M H264 encoder if the camera doesn't have H264 capability
- [x] Using UVC H264 extension to support cameras embedding H264 into MJPG capture format
- [ ] Adding AAC audio to the stream from ALSA
- [ ] Support multiple cameras
- [ ] Rewrite to c or Rust


# Motivation
I wanted to stream my raspberry camera to the browser. I found some solution, but I think they are not optimal or too heavy, so I decided to write one which doesn't have too many dependencies.

The fmp4streamer doesn't have any dependencies other than python and V4L2, but they are installed by default.

It adds fMP4 (fragmented MP4) headers to the h264 stream. It uses the python http server to serve it to the browser.

The browsers play it with only one html5 video tag. No javascript needed.

Safari on iOS plays it only with HLS playlists, but it works too. And the playlists added to the index.html of course.

## Inspired from

[UV4L](https://www.linux-projects.org/uv4l/)

[131/h264-live-player](https://github.com/131/h264-live-player)

[dans98/pi-h264-to-browser](https://github.com/dans98/pi-h264-to-browser)

[samirkumardas/jmuxer](https://github.com/samirkumardas/jmuxer)

[Media Source Extensions](https://caniuse.com/mediasource)

[thinkski/berrymse](https://github.com/thinkski/berrymse)
