from flask import Flask, render_template, jsonify, Response
import gesture_detector
from gesture_detector import status_data, start_gesture_detection, send_gesture_command

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    return jsonify({
        "current_gesture": status_data["current_gesture"],
        "stable_gesture": status_data["stable_gesture"],
        "holding_gesture": status_data["holding_gesture"],
        "hold_progress": status_data["hold_progress"],
        "last_sent": status_data["last_sent"],
        "wifi_server": status_data["wifi_server"],
        "gesture_flash": status_data["gesture_flash"],
        "logs": status_data["logs"],
        "devices": status_data["devices"]
    })

@app.route("/manual/<gesture>")
def manual_gesture(gesture):
    gesture = gesture.upper()
    valid = ["THUMBS_UP", "PEACE_SIGN", "PALM_OPEN", "FIST", "POINTING"]
    if gesture in valid:
        send_gesture_command(gesture)
        return jsonify({"success": True, "gesture": gesture})
    return jsonify({"success": False, "error": "Invalid gesture"})

@app.route("/video_feed")
def video_feed():
    return Response(
        gesture_detector.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

if __name__ == "__main__":
    start_gesture_detection()
    app.run(debug=True, host="0.0.0.0", port=5000)