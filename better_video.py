import argparse
import cv2
from datetime import datetime, timedelta
import numpy as np
import subprocess
import json
import os

# Lista dostępnych metod interpolacji metody resize
resize_interpolation_methods = ['INTER_NEAREST', 'INTER_LINEAR', 'INTER_AREA', 'INTER_CUBIC', 'INTER_LANCZOS4']


def parse_arguments():
    parser = argparse.ArgumentParser(description='Better Stack Images')

    parser.add_argument('--open-file', type=str,
                        help='Full path to the video file.')
    parser.add_argument('--annotate', action='store_true',
                        help='Print file metadata visually on the image.')
    parser.add_argument('--stream', action='store_true',
                        help='Repack and save the video stream from mp4 to mjpg for picky Registax')
    parser.add_argument('--frame-center', nargs='+', type=int,
                        help='Find the centroid of the image and center it.')
    parser.add_argument('--frame-crop', nargs='+', type=int,
                        help='Crop size in x y pixels, e.g. 1200 1200.')
    parser.add_argument('--skip-blur', nargs=1, type=float,
                        help='Skip the most blurred images using an arbitrary threshold.')
    parser.add_argument('--frame-resize', nargs='+', type=int,
                        help='Resize frame to x y pixels, e.g. 1200 1200')
    parser.add_argument('--resize-method', type=str, choices=resize_interpolation_methods, default='INTER_CUBIC',
                        help='Method of interpolation to be used for resizing: '
                             'INTER_NEAREST, INTER_LINEAR, INTER_AREA, INTER_CUBIC, INTER_LANCZOS4')
    parser.add_argument('--frame-save', action='store_true',
                        help='Save all frames as .png, also for picky Registax.')

    _args = parser.parse_args()
    if _args.open_file is None:
        parser.print_help()
        exit()
    return _args


try:
    args = parse_arguments()
except SystemExit:
    print("No arguments? Exiting...")
    exit()

source_file_name = os.path.basename(args.open_file)
# ...bez rozszerzenia
source_plain_name = os.path.splitext(source_file_name)[0]

video_path = args.open_file
output_video_path = f"{os.path.splitext(args.open_file)[0]}.avi"
output_frame_folder = f"{os.path.splitext(args.open_file)[0]}_frames"

# mapa argumentów do stałych cv2
resize_interpolation_constants = {
    'INTER_NEAREST': cv2.INTER_NEAREST,
    'INTER_LINEAR': cv2.INTER_LINEAR,
    'INTER_AREA': cv2.INTER_AREA,
    'INTER_CUBIC': cv2.INTER_CUBIC,
    'INTER_LANCZOS4': cv2.INTER_LANCZOS4
}

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


def annotate_frame(_frame):
    # TODO: zastąpić to wszystko globalną kolekcją metadanych
    # if args.skip_blur:
    #    cv2.putText(_frame, f"Laplacian: {laplacian}",
    #                (16, 96), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

    cv2.putText(_frame, f"{get_frame_creation_time(video_capture, sub_sec_create_date)}",
                (16, 32), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(_frame, f"{text_autoiso}, {text_cameratemp}",
                (16, 64), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)


def get_centered_image(image, treshold):
    # klatki pomocnicze
    new_frame = np.zeros_like(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, treshold, 255, cv2.THRESH_BINARY)
    # momenty obrazu
    moments = cv2.moments(thresholded)
    # środek masy obiektu
    if moments["m00"] != 0:
        _cx = int(moments["m10"] / moments["m00"])
        _cy = int(moments["m01"] / moments["m00"])
    else:
        _cx = image.shape[1] // 2
        _cy = image.shape[0] // 2

    # wektor przesunięcia
    _start_x = image.shape[1] // 2 - _cx
    _start_y = image.shape[0] // 2 - _cy
    # punkty startowe dla kopiowania obrazu
    src_start_x = max(0, -_start_x)
    src_start_y = max(0, -_start_y)
    # punkty startowe dla wklejenia obrazua
    dst_start_x = max(0, _start_x)
    dst_start_y = max(0, _start_y)
    # rozmiar fragmentu do skopiowania
    copy_width = min(image.shape[1] - src_start_x, new_frame.shape[1] - dst_start_x)
    copy_height = min(image.shape[0] - src_start_y, new_frame.shape[0] - dst_start_y)
    # skopiowanie fragmentu obrazu do nowej ramki z przesunięciem
    new_frame[dst_start_y:dst_start_y + copy_height, dst_start_x:dst_start_x + copy_width] = \
        image[src_start_y:src_start_y + copy_height, src_start_x:src_start_x + copy_width]
    return new_frame


def get_crop_image(image, _crop_size):
    # planetary crop size: 128x128
    crop_width, crop_height = 128, 128

    if len(_crop_size) == 1:
        crop_width = crop_height = _crop_size[0]
    elif len(_crop_size) == 2:
        crop_width, crop_height = _crop_size
    # współrzędne początkowe (x, y) dla wycięcia
    start_x = image.shape[1] // 2 - crop_width // 2
    start_y = image.shape[0] // 2 - crop_height // 2
    return image[start_y:start_y + crop_height, start_x:start_x + crop_width]


def get_resized_image(_image, _size):
    return cv2.resize(_image, (_size[0], _size[1]),
                      interpolation=resize_interpolation_constants[args.resize_method])


def is_frame_blurred(_frame, _treshold):
    # kryterium Laplasjana lub inne do wyboru w przyszłości
    # Laplasjan obrazu - druga pochodna obrazu
    laplacian = cv2.Laplacian(_frame, cv2.CV_64F).var()
    print(f"frame Laplacian: {laplacian}")
    return laplacian < _treshold


def get_frame_creation_time(capture, sub_sec_createdatetime):
    msec = capture.get(cv2.CAP_PROP_POS_MSEC)
    frame_time = sub_sec_createdatetime + timedelta(milliseconds=msec)
    return frame_time.strftime('%Y/%m/%d T %H:%M:%S.%f')[:-4]


def get_sub_sec_create_date(_text_createdate):
    _date_formats = ['%Y:%m:%d %H:%M:%S.%f%z',
                     '%Y:%m:%d %H:%M:%S.%f',
                     '%Y:%m:%d %H:%M:%S',
                     '%Y:%m:%d %H:%M']

    _sub_sec_create_date = None
    for _date_format in _date_formats:
        try:
            _sub_sec_create_date = datetime.strptime(_text_createdate, _date_format)
            break
        except ValueError:
            continue

    if _sub_sec_create_date is None:
        print(f"Could not parse date: {_text_createdate}")

    return _sub_sec_create_date


def progress_bar(_current_frame, _total_frames, fps):
    total_seconds = int(_total_frames // fps)
    current_second = int(_current_frame // fps)
    bar = ['-' for _ in range(int(fps))]
    bar[int(_current_frame % fps)] = '|'  # aktualna klatka
    return f"[ {str(current_second).zfill(3)} / {str(total_seconds).zfill(3)}s ] |" + ''.join(bar) + '|'


# uruchomienie exiftool
cmd = ['exiftool', '-j', video_path]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
metadata = json.loads(stdout)[0]  # przekierowanie to Python dict

text_createdate = f"{metadata.get('SubSecCreateDate', 'Brak danych')}"
sub_sec_create_date = get_sub_sec_create_date(text_createdate)
text_mediaduration = f"{metadata.get('MediaDuration', 'Brak danych')}"
text_autoiso = f"ISO{metadata.get('AutoISO', 'Brak danych')}"
text_cameratemp = f"chip temp:{metadata.get('CameraTemperature', 'Brak danych')}"


print(metadata)
print(f"SubSecCreateDate: {sub_sec_create_date}")
print(f"MediaDuration   : {text_mediaduration}")
print(f"{text_autoiso}, {text_cameratemp}")

# Odczytanie wideo
video_capture = cv2.VideoCapture(video_path)
width_src = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
height_scr = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps_src = video_capture.get(cv2.CAP_PROP_FPS)
total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
output_size = (width_src, height_scr)

# zmienne pomocnicze
min_crop_size = 128

print(f"video: width: {width_src} x {height_scr}, {fps_src}fps")
print(f"total frames: {total_frames}")

# zapis wideo jeśli wybrano
if args.stream:
    # rozmiar ramki oczekiwanej
    if args.frame_crop:
        output_size = (args.frame_crop[0], args.frame_crop[1] if len(args.frame_crop) > 1 else args.frame_crop[0])

    # MJPG do timelapsów
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    wideo_out = cv2.VideoWriter(output_video_path, fourcc, fps_src, output_size)

# tworzenie folderu na klatki jeśli wybrano
if args.frame_save:
    if not os.path.exists(output_frame_folder):
        os.makedirs(output_frame_folder, exist_ok=True)

print("Processing: ")
while video_capture.isOpened():
    ret, video_frame = video_capture.read()
    if not ret:
        break

    current_frame = int(video_capture.get(cv2.CAP_PROP_POS_FRAMES))
    print(progress_bar(current_frame, total_frames, fps_src), end='\r')

    # skip blurred frames
    if args.skip_blur:
        if is_frame_blurred(video_frame, args.skip_blur[0]):
            continue
    # center frame
    if args.frame_center:
        video_frame = get_centered_image(video_frame, args.frame_center[0])
    # resize frame
    if args.frame_resize:
        video_frame = get_resized_image(video_frame, args.frame_resize)
    # crop frame
    if args.frame_crop:
        video_frame = get_crop_image(video_frame, args.frame_crop)
    # metadata
    if args.annotate:
        annotate_frame(video_frame)
    # save to image
    if args.frame_save:
        output_filename = os.path.join(output_frame_folder, f'{source_plain_name}_{current_frame:05d}.png')
        cv2.imwrite(output_filename, video_frame)
    # save to video
    if args.stream:
        wideo_out.write(video_frame)

# uwolnienie zasobów
if args.stream:
    wideo_out.release()
video_capture.release()
cv2.destroyAllWindows()
