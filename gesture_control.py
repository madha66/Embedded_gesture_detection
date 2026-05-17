import cv2
import mediapipe as mp
import time
import requests
from collections import deque, Counter
import math

# ============================
# ESP32 SERVER CONFIG
# ============================
ESP32_IP = "192.168.4.1"
BASE_URL = f"http://{ESP32_IP}/cmd?g="

GESTURE_MAP = {
    "THUMBS_UP": 0,
    "PEACE_SIGN": 1,
    "PALM_OPEN": 2,
    "FIST": 3,
    "POINTING": 4
}

# ============================
# STABILITY SETTINGS
# ============================
HISTORY_SIZE = 12
MIN_MATCHES = 8
COOLDOWN_SECONDS = 2.5
HOLD_TIME = 0.8

gesture_history = deque(maxlen=HISTORY_SIZE)
last_sent_time = 0
last_sent_gesture = None
gesture_start_time = 0
candidate_gesture = None

# ============================
# MEDIAPIPE SETUP
# ============================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75
)

# ============================
# HELPER FUNCTIONS
# ============================
def distance(p1, p2):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def is_finger_up(landmarks, tip, pip, mcp):
    return landmarks[tip].y < landmarks[pip].y < landmarks[mcp].y

def is_thumb_up(landmarks):
    """
    Stronger thumbs-up detection:
    - thumb tip above thumb joints
    - thumb tip clearly above wrist
    - thumb extended away from palm
    """
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    wrist = landmarks[0]
    index_mcp = landmarks[5]

    return (
        thumb_tip.y < thumb_ip.y < thumb_mcp.y and
        thumb_tip.y < wrist.y - 0.05 and
        abs(thumb_tip.x - index_mcp.x) > 0.08
    )

def is_thumb_folded(landmarks):
    """
    Better folded-thumb detection:
    - thumb tip not above thumb joints
    OR
    - thumb stays close to palm
    """
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]
    index_mcp = landmarks[5]

    close_to_palm = distance(thumb_tip, index_mcp) < 0.12

    return (
        thumb_tip.y > thumb_ip.y or
        close_to_palm
    )

def detect_gesture(landmarks):
    # Finger states
    index_up  = is_finger_up(landmarks, 8, 6, 5)
    middle_up = is_finger_up(landmarks, 12, 10, 9)
    ring_up   = is_finger_up(landmarks, 16, 14, 13)
    pinky_up  = is_finger_up(landmarks, 20, 18, 17)

    thumb_up = is_thumb_up(landmarks)
    thumb_folded = is_thumb_folded(landmarks)

    fingers_up = [index_up, middle_up, ring_up, pinky_up]
    count = sum(fingers_up)

    # Distance checks
    index_middle_gap = distance(landmarks[8], landmarks[12])

    # ----------------------------
    # Gesture Rules
    # ----------------------------

    # 👍 THUMBS UP
    if thumb_up and count == 0:
        return "THUMBS_UP"

    # ✌️ PEACE SIGN
    if (
        index_up and middle_up
        and not ring_up and not pinky_up
        and index_middle_gap > 0.035
    ):
        return "PEACE_SIGN"

    # ☝️ POINTING
    if (
        index_up
        and not middle_up and not ring_up and not pinky_up
        and thumb_folded
    ):
        return "POINTING"

    # 🖐️ PALM OPEN
    if thumb_up and index_up and middle_up and ring_up and pinky_up:
        return "PALM_OPEN"

    # ✊ FIST
    if (
        count == 0
        and thumb_folded
        and not thumb_up
    ):
        return "FIST"

    return "UNKNOWN"

def get_stable_gesture(current_gesture):
    gesture_history.append(current_gesture)

    if len(gesture_history) < HISTORY_SIZE:
        return None

    counts = Counter(gesture_history)
    most_common_gesture, freq = counts.most_common(1)[0]

    if most_common_gesture != "UNKNOWN" and freq >= MIN_MATCHES:
        return most_common_gesture

    return None

def send_gesture_command(gesture_name):
    gesture_number = GESTURE_MAP[gesture_name]
    url = BASE_URL + str(gesture_number)

    try:
        response = requests.get(url, timeout=2)
        print(f"📡 Sent {gesture_name} -> {gesture_number} | HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send command: {e}")

# ============================
# MAIN LOOP
# ============================
cap = cv2.VideoCapture(0)

print("📷 Stable Gesture Control Started")
print("Hold gesture clearly for ~1 second")
print("Press Q to quit")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_gesture = "UNKNOWN"
    stable_gesture = None
    confirmed_gesture = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            current_gesture = detect_gesture(hand_landmarks.landmark)
            stable_gesture = get_stable_gesture(current_gesture)
    else:
        gesture_history.append("UNKNOWN")

    # ----------------------------
    # HOLD-TO-CONFIRM LOGIC
    # ----------------------------
    now = time.time()

    if stable_gesture:
        if candidate_gesture != stable_gesture:
            candidate_gesture = stable_gesture
            gesture_start_time = now
        else:
            if now - gesture_start_time >= HOLD_TIME:
                confirmed_gesture = stable_gesture
    else:
        candidate_gesture = None
        gesture_start_time = 0

    # Send only after hold + cooldown
    if confirmed_gesture:
        if (now - last_sent_time > COOLDOWN_SECONDS) or (confirmed_gesture != last_sent_gesture):
            send_gesture_command(confirmed_gesture)
            last_sent_time = now
            last_sent_gesture = confirmed_gesture
            candidate_gesture = None
            gesture_start_time = 0
            gesture_history.clear()

    # ============================
    # DISPLAY
    # ============================
    cv2.putText(frame, f"Current: {current_gesture}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)

    if stable_gesture:
        cv2.putText(frame, f"Stable: {stable_gesture}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "Stable: WAITING...", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 165, 255), 2)

    if candidate_gesture:
        hold_progress = min((now - gesture_start_time) / HOLD_TIME, 1.0)
        cv2.putText(frame, f"Holding: {candidate_gesture} ({hold_progress*100:.0f}%)", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 0), 2)
    else:
        cv2.putText(frame, "Holding: ---", (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)

    cv2.imshow("Stable Gesture Control ESP32", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()