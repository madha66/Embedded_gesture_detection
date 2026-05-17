Gesture Controlled Home Automation using MediaPipe and ESP32

This project is a real-time gesture-based home automation system that allows users to control appliances using hand gestures captured through a webcam. The system uses MediaPipe for hand landmark detection, OpenCV for video processing, and an ESP32 microcontroller to control devices over Wi-Fi.

The main objective of the project is to create a touchless and intuitive way of interacting with home appliances using computer vision and IoT.

Features
Real-time hand gesture recognition
Controls appliances wirelessly using ESP32
Stable gesture detection with hold-time validation
Live webcam processing using OpenCV
Hand landmark tracking using MediaPipe
Gesture logging and device state monitoring
Prevention of accidental triggers using cooldown logic
Technologies Used
Python
OpenCV
MediaPipe
ESP32
HTTP Requests
Flask (for video streaming/dashboard if applicable)
Supported Gestures
Gesture	Function
👍 Thumbs Up	Toggle Light
✌️ Peace Sign	Toggle Fan
🖐️ Open Palm	Toggle Pump
✊ Fist	Toggle Door Lock
☝️ Pointing	Reset All Devices
System Workflow
Webcam captures live video frames.
Frames are processed using OpenCV.
MediaPipe detects 21 hand landmarks.
Finger positions are analyzed to identify gestures.
The gesture is validated using stability and hold-time checks.
A corresponding command is sent to the ESP32 using an HTTP request.
ESP32 performs the required device action.
Hand Gesture Detection Logic

The project does not use a pre-trained gesture classification model. Instead, gestures are identified using custom logic based on landmark positions returned by MediaPipe.

For example:

A finger is considered “up” when the fingertip landmark is above its lower joints.
A fist is detected when all fingers are folded.
A thumbs-up gesture is detected by checking thumb orientation and separation from the palm.

This approach keeps the system lightweight and suitable for real-time execution.

Stability Mechanism

During testing, frequent false detections occurred because gestures changed rapidly between frames. To solve this, the following mechanisms were added:

Gesture history buffer
Majority-vote stabilization
Hold duration validation
Cooldown timer between commands

These additions significantly improved detection reliability.
