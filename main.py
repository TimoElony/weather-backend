from fastapi import FastAPI, Response
import cv2
import asyncio

app = FastAPI()

# Webcam stream generator (MJPEG format)
async def generate_frames():
    cap = cv2.VideoCapture(0)  # Use 0 for default webcam
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# MJPEG Streaming Endpoint
@app.get("/video_feed")
async def video_feed():
    return Response(generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

# Basic API Test
@app.get("/")
async def root():
    return {"message": "Webcam Streaming API is running!"}