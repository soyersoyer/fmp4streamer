# Changelog

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

