# Fmp4streamer
[What is Fmp4streamer](#what-is-fmp4streamer) |
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

# What is Fmp4streamer
Fmp4streamer streams your V4L2 camera directly to any browser and media player as H264 inside fragmented mp4.

# How does it work
This python script setups the V4L2 device, reads the H264 or MJPGH264 stream from it (or the YUYV, MJPG stream and converts to H264 with a M2M V4L2 device), adds some fMP4 (fragmented MP4) header and serves it via HTTP. It works with only one html5 video tag, no js needed. It's pretty lightweight.

# Capabilities
- Stream to multiple clients simultaneously (usually only limited by your network connection) 
- Support any resolution and framerate the video device can capture
- Works in any Raspberry Pi with a camera module (If you are using the Raspberry OS Bullseye version please read the [Raspberry](#raspberry) section)
- Able to handle high framerate (60-90 fps) streams
- Able to handle cameras which only provide H264 inside MJPG format (UVC 1.5 H264 cameras, like Logitech C930e)
- Able to convert MJPG camera stream to H264 via M2M decoder and encoder devices.
- Able to put the camera into sleep mode when no one is watching the stream.
- Able to stream to iPhone and Safari via HLS.
- Low cpu utilization

# Installation
   ```
   wget https://github.com/soyersoyer/fmp4streamer/archive/refs/tags/v3.4.3.zip
   unzip v3.4.3.zip
   mv fmp4streamer-3.4.3 fmp4streamer
   ```

# Running 
- from the terminal
    ```
    cd fmp4streamer
    python3 fmp4streamer.py
    ```
- enable running at startup and start now:
    ```
    loginctl enable-linger
    systemctl --user enable --now ~/fmp4streamer/fmp4streamer.service
    ```
- disable running at startup and stop now:
    ```
    systemctl --user disable --now fmp4streamer
    ```
- to stop the service
    ```
    systemctl --user stop fmp4streamer
    ```
- to start the service
    ```
    systemctl --user start fmp4streamer
    ```
- check the status of the service
    ```
    systemctl --user status fmp4streamer
    ```
- watch the logs
    ```
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
width = 640
height = 480
fps = 30

# Device capture format (default: H264)
# H264, MJPGH264, YUYV, MJPG, JPEG
# capture_format = H264

# Decoder M2M device (default: disabled)
# To decode the stream to a compatible format with the encoder (eg MJPG -> NV12 -> H264)
# decoder = /dev/video10

# Encoder M2M device (default: disabled)
# To encode the stream to H264 (eg YUYV -> H264 or MJPG -> NV12 -> H264)
# encoder = /dev/video11

# Auto Sleep mode (default: yes)
# Sleep the camera when no one is watching the stream
# auto_sleep = yes

# Controls

# you can set any V4L2 control too, list them with the -l option
h264_profile = High
h264_level = 4.2
h264_i_frame_period = 15

uvcx_h264_i_frame_period = 1000
uvcx_h264_profile = High

# Advanced (change only if you know, what you are doing)

# Buffer memory configurations (MMAP or DMABUF)
# Sometimes contigous memory is not large enough for hardwares and tuning needed

# default: DMABUF if encoder or decoder else MMAP
# capture_memory = DMABUF

# decoder_memory = MMAP-DMABUF
# encoder_memory = MMAP-MMAP

# Input format for the decoder (default: MJPG if capture_format == JPEG else capture_format)
# If the capture_format isn't supported by the decoder directly,
# but it can decode it with another format eg (capture_format = JPEG, decoder_input_format = MJPG)
# decoder_input_format = MJPG

# Input format for the encoder (default: NV12 if decoder else capture_format)
# encoder_input_format = NV12
```

You can set all the V4L2 or UVCX H264 controls via the configuration file. List them with -l option:
```
$ python3 fmp4streamer.py -l
Device: /dev/video0
Name: Logitech Webcam C930e
Driver: uvcvideo

Controls
brightness = 128	( default: 128 min: 0 max: 255)
contrast = 128	( default: 128 min: 0 max: 255)
saturation = 128	( default: 128 min: 0 max: 255)
white_balance_temperature_auto = 1	( default: 1 min: 0 max: 1)
gain = 255	( default: 0 min: 0 max: 255)
power_line_frequency = 50 Hz	( default: 60 Hz values: 'Disabled' '50 Hz' '60 Hz' )
white_balance_temperature = 4000	( default: 4000 min: 2000 max: 7500)
sharpness = 128	( default: 128 min: 0 max: 255)
backlight_compensation = 0	( default: 0 min: 0 max: 1)
exposure_auto = Aperture Priority Mode	( default: Aperture Priority Mode values: 'Manual Mode' 'Aperture Priority Mode' )
exposure_absolute = 250	( default: 250 min: 3 max: 2047)
exposure_auto_priority = 1	( default: 0 min: 0 max: 1)
pan_absolute = 0	( default: 0 min: -36000 max: 36000 step: 3600)
tilt_absolute = 0	( default: 0 min: -36000 max: 36000 step: 3600)
focus_absolute = 0	( default: 0 min: 0 max: 255 step: 5)
focus_auto = 1	( default: 1 min: 0 max: 1)
zoom_absolute = 100	( default: 100 min: 100 max: 400)
led1_mode = Auto	( default: Off values: 'Off' 'On' 'Blink' 'Auto' )
led1_frequency = 0	( default: 0 min: 0 max: 255)
uvcx_h264_stream_mux = H264	( default: None values: 'None' 'H264' )
uvcx_h264_width = 1280	( default: 1920 min: 160 max: 1920)
uvcx_h264_height = 720	( default: 1080 min: 120 max: 1080)
uvcx_h264_frame_interval = 333333	( default: 333333 min: 333333 max: 2000000)
uvcx_h264_bitrate = 3000000	( default: 3000000 min: 64000 max: 12000000)
uvcx_h264_rate_control_mode = VBR	( default: CBR values: 'CBR' 'VBR' 'Const QP' )
uvcx_h264_profile = High	( default: Constrained values: 'Constrained' 'Baseline' 'Main' 'High' )
uvcx_h264_i_frame_period = 1000	( default: 10000 min: 0 max: 50000)

To set one, put ctrl_name = Value into fmp4streamer.conf under the device
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

[/dev/video0]
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

If you have a raspberry with an USB camera which supports MJPG format, you can use this configuration:

```ini
[server]
listen = 
port = 8000

[/dev/video0]
width = 640
height = 480
fps = 30
capture_format = MJPG
decoder = /dev/video10
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
- Logitech C270 (works with capture_format = YUYV or MJPG with the Raspiberry pi's H264 encoder)
- Logitech C920 V1 (046d:082d) (works with capture_format = H264 or YUYV or  MJPG) (Thanks @balazspeczeli for the camera)
- Logitech C930e (046d:0843) (works with capture_format = MJPGH264 or YUYV or MJPG)

# Roadmap
- [x] Use V4L2 instead of raspivid
- [x] Use V4L2 M2M H264 encoder if the camera doesn't have H264 capability
- [x] Using UVC H264 extension to support cameras embedding H264 into MJPG capture format
- [x] Use V4L2 M2M decoder device for MJPG streams
- [ ] Adding AAC audio to the stream from ALSA
- [ ] Support multiple cameras
- [ ] Rewrite to c or Rust


# Motivation
I wanted to stream my raspberry camera to the browser. I found some solution, but I think they are not optimal or too heavy (more than 100MB) or too hard to install, so I decided to write one which doesn't have too many dependencies.

Fmp4streamer doesn't have any dependencies other than Python and V4L2, but they are installed by default.

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
