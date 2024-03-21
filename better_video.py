import argparse
import cv2
from datetime import datetime, timedelta
import subprocess
import json
import os

video_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9192.MP4'
output_video_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9192.avi'
output_frame_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9192png/'


def parse_arguments():
    parser = argparse.ArgumentParser(description='Better Stack Images')

    parser.add_argument('--annotate', action='store_true', help='print file metadata visual on image')
    parser.add_argument('--stream', action='store_true', help='repack and save video stream from mp4 to mjpg for '
                                                              'picky Registax')
    parser.add_argument('--frame-center', action='store_true', help='find centroid of image and center it')
    parser.add_argument('--frame-crop', nargs='+', type=int, help='Crop size in x y pixels, e.g. 1200 1200')
    parser.add_argument('--skip-blur', action='store_true', help='skip bottom of blurred images')
    parser.add_argument('--frame-resize', action='store_true', help='resize')
    parser.add_argument('--frame-save', action='store_true', help='save all frames as .png, also for picky Registax')

    return parser.parse_args()


args = parse_arguments()

if args.annotate:
    print("Annotation is enabled")
if args.stream:
    print("Stream repacking is enabled")
if args.frame_center:
    print("Centering is enabled")
if args.frame_crop:
    print("Cropping is enabled")
if args.skip_blur:
    print("Skipping of blurred images is enabled")
if args.frame_resize:
    print("Resizing is enabled")
if args.frame_save:
    print("Saving all frames as .png is enabled")


def get_frame_creation_time(capture, sub_sec_createdatetime):
    msec = capture.get(cv2.CAP_PROP_POS_MSEC)
    frame_time = sub_sec_createdatetime + timedelta(milliseconds=msec)
    return frame_time.strftime('%Y/%m/%d T %H:%M:%S.%f')[:-4]


# uruchomienie exiftool
cmd = ['exiftool', '-j', video_path]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
metadata = json.loads(stdout)[0]  # przekierowanie to Python dict

text_createdate = f"{metadata.get('SubSecCreateDate', 'Brak danych')}"
text_mediaduration = f"{metadata.get('MediaDuration', 'Brak danych')}"
text_autoiso = f"ISO{metadata.get('AutoISO', 'Brak danych')}"
text_cameratemp = f"chip temp:{metadata.get('CameraTemperature', 'Brak danych')}"

sub_sec_create_date = datetime.strptime(text_createdate[:-6], '%Y:%m:%d %H:%M:%S.%f')

print(metadata)
print(f"{sub_sec_create_date}")
print(f"{text_mediaduration}")
print(f"{text_autoiso}, {text_cameratemp}")

# Odczytanie wideo
video_capture = cv2.VideoCapture(video_path)
width_src = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
height_scr = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_src = video_capture.get(cv2.CAP_PROP_FPS)
total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"total frames: {total_frames}")

# zapis wideo
if args.stream:
    # MJPG do timelapsów
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    wideo_out = cv2.VideoWriter(output_video_path, fourcc, fps_src, (width_src, height_scr))

print("processing frame:")
while video_capture.isOpened():
    ret, video_frame = video_capture.read()
    if not ret:
        break

    current_frame = int(video_capture.get(cv2.CAP_PROP_POS_FRAMES))

    # crop size
    if args.frame_crop:
        crop_width, crop_height = 128, 128
        if len(args.frame_crop) == 1:
            crop_width = crop_height = args.frame_crop[0]
        elif len(args.frame_crop) == 2:
            crop_width, crop_height = args.frame_crop
        # współrzędne początkowe (x, y) dla wycięcia
        start_x = video_frame.shape[1] // 2 - crop_width // 2
        start_y = video_frame.shape[0] // 2 - crop_height // 2
        # crop kwadratu/prostokąta ze środka
        video_frame = video_frame[start_y:start_y + crop_height, start_x:start_x + crop_width]

    # metadata
    if args.annotate:
        cv2.putText(video_frame, f"{get_frame_creation_time(video_capture, sub_sec_create_date)}",
                    (16, 32), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(video_frame, f"{text_autoiso}, {text_cameratemp}",
                    (16, 64), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

    # save to image
    if args.frame_save:
        output_filename = os.path.join(output_frame_path, f'frame_{current_frame:04d}.png')
        cv2.imwrite(output_filename, video_frame)

    # save to video
    if args.stream:
        wideo_out.write(video_frame)

    if current_frame % fps_src == 0:
        print(".")
    else:
        print(".", end="", flush=True)

# uwolnienie zasobów
video_capture.release()
wideo_out.release()
cv2.destroyAllWindows()
