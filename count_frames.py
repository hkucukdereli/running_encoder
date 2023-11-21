import cv2

def count_frames(video_path):
    # Open the video file
    cap = cv2.VideoCapture(video_path)

    # Check if video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    # Get the total number of frames in the video
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Close the video file
    cap.release()

    return frame_count

# Replace with the path to your video file
video_path = '/path/to/your/video.avi'

# Count the frames
num_frames = count_frames(video_path)

print(f"The video has {num_frames}
