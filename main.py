from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import cv2
import asyncio
import signal
import os
from dotenv import load_dotenv

# Global flag for graceful shutdown
should_exit = asyncio.Event()

load_dotenv()
app = FastAPI()

RTSP_URL = f"rtsp://admin:{os.getenv('REOLINK_PASSWORD')}@192.168.1.130:554/h264Preview_01_main"

async def generate_frames():
    while not should_exit.is_set():
        print("Connecting to RTSP stream...")
        cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        try:
            while not should_exit.is_set():
                ret, frame = cap.read()
                if not ret:
                    break
                _, buffer = cv2.imencode('.jpg', cv2.resize(frame, (640, 480)))
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                await asyncio.sleep(0.01)  # Prevent 100% CPU
        finally:
            cap.release()
            if not should_exit.is_set():
                await asyncio.sleep(3)  # Reconnect delay

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

def handle_shutdown():
    print("\nShutdown requested!")
    should_exit.set()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda *_: handle_shutdown())
    signal.signal(signal.SIGTERM, lambda *_: handle_shutdown())
    
    import uvicorn
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    
    try:
        server.run()
    except (KeyboardInterrupt, SystemExit):
        handle_shutdown()
    finally:
        print("Server stopped cleanly")