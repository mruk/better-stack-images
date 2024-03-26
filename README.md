# Better Stack Images
A Tool Set of command line preprocessors for achieving better Quality-of-Life experience with image stacking.  
This is never-ending-project.

## better_video.py
### Main (target) features:  
#### Annotate frames with metadata from video file
***--annotate***  print file metadata visual on image,  

#### Skip blurred images using arbitrary treshold
***--skip-blur***       skipping blurred images. Float argument is a threshold for image sharpness.

#### Center frames using brigthness threshold
***--frame-center***    find feature centroid in input frame and center it in output frame. Int argument is a brigthness threshold for feature detection.

#### Crop frames
***--frame-crop***      crop frame with one or two arguments.  
 - one argument - crop square,
 - two arguments - crop with width and height.

#### Resize frames (OpenCV)
***--frame-resize***    resize frame with two arguments
***--resize-method***   method for resizing frame:
 - INTER_NEAREST - a nearest-neighbor interpolation
 - INTER_LINEAR - a bilinear interpolation (used by default)
 - INTER_AREA - resampling using pixel area relation,
 - INTER_CUBIC - a bicubic interpolation over 4x4 pixel neighborhood, default selection,
 - INTER_LANCZOS4 - a Lanczos interpolation over 8x8 pixel neighborhood.


#### Save frames as .png
***--frame-save***      save all frames as .png, also for picky Registax,

#### Repack video stream to new file
***--stream***    repack video stream from mp4 to mjpg for picky Registax,

### Order of operations
| operation          | obligatory | arguments |    example     |
|--------------------|:----------:|:---------:|:--------------:|
| 1 - open file      |     +      |  String   | D:/foo/bar.mp4 |
| 2 - skip blur      |     -      |   float   |      5.57      |
| 3 - center frame   |     -      |    int    |       40       |
| 4 - resize frame   |     -      |  int int  |   2650 1440    |
| 5 - resize method  |     -      |  String   | INTER_LANCZOS4 |
| 6 - crop frame     |     -      |  int int  |    1280 720    |
| 7 - annotate frame |     -      |     -     |                |
| 8a - save to img   |     -      |     -     |                |
| 8b - repack stream |     -      |     -     |                |

### Examples from the wild
Open video, skip blurred images, center frames, resize frames, save frames as .png:
```bash
python .\better_video.py --open-file "D:\rac\ASTRO\2024\2024_03_19 Luna\MVI_9197.mp4"  
 --skip-blur 6.75 
 --frame-center 8 
 --frame-resize 1920 1080 
 --resize-method INTER_LANCZOS4 
 --frame-save
```
Open video, skip blurred images, center frames, save frames as .png, repack stream to new file:
```bash
 python .\better_video.py --open-file D:\foo\bar.mp4 
  --skip-blur 20 --frame-center 40 --frame-save --stream
```