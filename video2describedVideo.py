import cv2
from datetime import datetime, timedelta
import subprocess
import json
import os

video_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9192.MP4'
output_video_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9156.avi'
output_frame_path = 'D:/rac/ASTRO/2024/2024_03_19 Luna/MVI_9156png/'


def get_frame_creation_time(capture, sub_sec_createdatetime):
    msec = capture.get(cv2.CAP_PROP_POS_MSEC)
    frame_time = sub_sec_createdatetime + timedelta(milliseconds=msec)
    return frame_time.strftime('%Y/%m/%d T %H:%M:%S.%f')[:-5]


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
cap = cv2.VideoCapture(video_path)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"total frames: {total_frames}")

# MJPG do timelapsów
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
wideo_out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

print("processing frame:")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # metadata
    # cv2.putText(frame, f"{get_frame_creation_time(cap, sub_sec_create_date)}",
    #            (16, 32), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1)
    # cv2.putText(frame, f"{text_autoiso}, {text_cameratemp}",
    #            (16, 64), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1)

    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    output_filename = os.path.join(output_frame_path, f'frame_{current_frame:04d}.png')

    # crop size
    crop_width, crop_height = 1600, 1600
    # współrzędne początkowe (x, y) dla wycięcia
    start_x = frame.shape[1]//2 - crop_width//2 + 256
    start_y = frame.shape[0]//2 - crop_height//2 - 256
    # crop kwadratu ze środka
    cropped_frame = frame[start_y:start_y+crop_height, start_x:start_x+crop_width]

    cv2.imwrite(output_filename, frame)
    wideo_out.write(frame)

    if current_frame % 25 == 0:
        print(".")
    else:
        print(".", end="", flush=True)

# uwolnienie zasobów
cap.release()
wideo_out.release()
cv2.destroyAllWindows()
