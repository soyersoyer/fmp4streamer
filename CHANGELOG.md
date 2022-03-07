# Changelog
## [Unreleased]
### Added
- MP4 rotation
### Fixed
- UVCX: Handle if the device is a symlink (like: /dev/v4l/by-id/...)

## [3.4.5] - 2022-03-02
### Added
- New UVC H264 XU controls: uvcx_h264_slice_mode, uvcx_h264_slice_units, uvcx_h264_entropy, uvcx_h264_usage, uvcx_h264_leaky_bucket_size
### Fixed
- Fixed the glitches if the H264 payload in the MJPG is bigger than 65k


## [3.4.4] - 2022-02-20
### Changed
- Use TCP_NODELAY to disable Nagle's algorithm for lower latency
- Set viewport for mobiles

## [3.4.3] - 2022-02-20
### Added
- Logo, Favicon, App icon (add to home screen)
### Fixed
- Remove stacktrace from logging

## [3.4.2] - 2022-02-19
### Fixed
- Fix logging to systemd journal (python -u -> unbuffered stdout)
- Fix systemd service if user is not pi
- Better systemd handling section in README

## [3.4.1] - 2022-02-18
### Fixed
- Basic checks for buffer configurations

## [3.4.0] - 2022-02-17
### Added
- Auto sleep mode (sleep the camera when no one is watching the stream) (enabled by default)

## [3.3.2] - 2022-02-17
### Fixed
- Fix the bug in resolution check caused invalid resolutions could be set
- Use 640x480 in the default config for better compatibility
- Use NV12 instead of YU12 by default for the decoder output, it has the same alignment on the encoder and decoder

## [3.3.1] - 2022-02-17
### Fixed
- Set the correct sizeimage in the m2m decoder for suitable DMABUFs for the camera

## [3.3.0] - 2022-02-16
### Added
- Able to convert MJPG camera stream to H264 via M2M decoder and encoder devices.
### Fixed
- Don't start the http server until the first H264 frame arrives

## [3.2.2] - 2022-02-13
### Added
- List controls: print device, driver names too

## [3.2.1] - 2022-02-13
### Fixed
- Use a better way to check if the H264 UVC extension exists. Read the ID from the usb descriptors.

## [3.2.0] - 2022-02-10
### Added
- Support UVC H264 extension
- Support H264 inside MJPG
### Fixed
- Handle H264 slices

## [3.1.0] - 2022-01-12
### Added
- V4L2 M2M H264 encoding for USB cameras

## [3.0.3] - 2021-10-25
### Fixed
- Eliminate the rounding errors in sampleduration calculation

## [3.0.2] - 2021-10-24
### Fixed
- Better sampleduration calculation
### Added
- Requesting keyframe at new connections for faster startup

## [3.0.1] - 2021-10-23
### Fixed
- Fixed sampleduration calculation
- Default config shouldn't set h264 profile and level

## [3.0.0] - 2021-10-22
### Added
- Use V4L2 instead of the raspivid, because reading from pipe is slow with big frames
- Config file with ability to set v4l2 parameters
### Changed
- RaspiWebcam has been renamed fmp4streamer, because with V4L2 it works on other linux machines too 

## [2.2.1] - 2021-10-13
### Changed
- Better duration and decode time calculation
- Code, speed and compatibility improvements

## [2.2.0] - 2021-10-10
### Added
- HLS streaming for iPhone
### Changed
- Speed and compatibility improvements

## [2.1.4] - 2021-10-09
### Fixed
- Fixed streaming in Chromium and Android

## [2.1.3] - 2021-10-09
### Changed
- Inline is not needed anymore in the raspivid's parameters
- Speed improvements

## [2.1.2] - 2021-10-09
### Changed
- Works with high fps settings too: use actual decode times for frames, not the fps calculated
### Fixed
- Fix race condition in MP4Writer

## [2.1.1] - 2021-10-09
### Changed
- Speed up frame writing by 4x

## [2.1.0] - 2021-10-08
### Added
- Use a tiny python muxer instead of the javascript based jmuxer.
- Use html5 video tag instead of Fetch api
### Changed
- Use correct timescale

## [2.0.0] - 2021-10-06

- Starting a new project based on [dans98/pi-h264-to-browser](https://github.com/dans98/pi-h264-to-browser).
- Raspiwebcam is the new project name.

### Added
- Use raspivid instead of python3-picamera
- Use Fetch api instead of websockets
### Changed
- Use jmuxer 2.0.2
### Removed
- Removed unnecessary screens
- Removed python3-picamera dependency
- Removed python3-tornado dependency

