# Better Stack Images
A Tool Set of command line preprocessors for achieving better Quality-of-Life experience with image stacking.  
This is never-ending-project.

## better_video.py
### Main (target) features:  
**--annotate**  print file metadata visual on image,  
**--stream**    repack video stream from mp4 to mjpg for picky Registax,  
**--frame-center**    find centroid of image and center it,  
**--frame-crop**      crop frame,  
**--skip-blur**       skip bottom of blurred images,  
**--frame-resize**    resize,  
**--frame-save**      save all frames as .png, also for picky Registax,  

### Order of operations
 open video --> skip blur --> center frame --> crop frame --> resize frame --> annotate frame --> save to img --> save to stream