import asyncio
import websockets
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from flask import Flask, Response, jsonify, request
from base64 import b64encode


# Flask app setup
app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({ "message": "Hello World!" }), 200

@app.route('/light', methods=['POST'])
def receive_light_data():
    # Lấy dữ liệu JSON từ ESP8266
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Lấy giá trị ánh sáng từ dữ liệu
    light_state = data.get("light_value")
    if light_state is None:
        return jsonify({"error": "Invalid data format"}), 400

    # Xử lý và in dữ liệu nhận được
    print(f"Light state received: {light_state}")

    # Phản hồi về cho ESP8266
    return jsonify({"message": "Data received successfully", "light_value": light_state}), 200

@app.route('/')
def index():
    return Response(get_image(), mimetype='multipart/x-mixed-replace; boundary=frame')

def get_image():
    while True:
        try:
            with open("image.jpg", "rb") as f:
                image_bytes = f.read()
            image = Image.open(BytesIO(image_bytes))
            img_io = BytesIO()
            image.save(img_io, 'JPEG')
            img_io.seek(0)
            img_bytes = img_io.read()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
        except Exception as e:
            print("Error reading image: ", e)

            # Placeholder image fallback
            with open("placeholder.jpg", "rb") as f:
                image_bytes = f.read()
            image = Image.open(BytesIO(image_bytes))
            img_io = BytesIO()
            image.save(img_io, 'JPEG')
            img_io.seek(0)
            img_bytes = img_io.read()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
            continue


# WebSocket server setup
async def handle_connection(websocket, *_):
    print(f"Client connected: {websocket.remote_address}")
    async for message in websocket:
        try:
            image = Image.open(BytesIO(message))
            image.save("image.jpg")
            print(f"Received and saved image, size: {len(message)} bytes")
        except UnidentifiedImageError as e:
            print(f"Failed to decode image: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


async def websocket_server():
    print("Starting WebSocket server on ws://0.0.0.0:3001")
    async with websockets.serve(handle_connection, '0.0.0.0', 3001):
        await asyncio.Future()  # Keeps the server running


# Run both Flask and WebSocket servers
async def main():
    # Start Flask server in a separate thread
    loop = asyncio.get_event_loop()
    flask_future = loop.run_in_executor(None, app.run, "0.0.0.0", 5000, False)
    websocket_future = websocket_server()
    await asyncio.gather(flask_future, websocket_future)

if __name__ == "__main__":
    asyncio.run(main())
