import cv2
import time
import random
import mediapipe as mp
import math
import numpy as np

# MediaPipe Initialization
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

total_hits = 0
total_misses = 0


# Correct Hands initialization with named parameters
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,  # 0=light, 1=full, 2=heavy
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

curr_Frame = 0
prev_Frame = 0
delta_time = 0

next_Time_to_Spawn = 0
Speed = [0, 5]
Fruit_Size = 30
Spawn_Rate = 1
Score = 0
Lives = 15
Difficulty_level = 1
game_Over = False

# Use a flat array for (x, y) pairs
slash = np.zeros((0,), np.int32)
slash_Color = (255, 255, 255)
slash_length = 19

w = h = 0

Fruits = []

def Spawn_Fruits():
    fruit = {}
    random_x = random.randint(15, 600)
    random_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    fruit["Color"] = random_color
    fruit["Curr_position"] = [random_x, 440]
    fruit["Next_position"] = [0, 0]
    Fruits.append(fruit)

def Fruit_Movement(Fruits, speed):
    global Lives,total_misses
    for fruit in list(Fruits):
        if fruit["Curr_position"][1] < 20 or fruit["Curr_position"][0] > 650:
            Lives -= 1
            Fruits.remove(fruit)
            total_misses += 1
        else:
            cv2.circle(img, tuple(fruit["Curr_position"]), Fruit_Size, fruit["Color"], -1)
            fruit["Next_position"][0] = fruit["Curr_position"][0] + speed[0]
            fruit["Next_position"][1] = fruit["Curr_position"][1] - speed[1]
            fruit["Curr_position"] = fruit["Next_position"]

def distance(a, b):
    return int(math.sqrt(pow(a[0] - b[0], 2) + pow(a[1] - b[1], 2)))

cap = cv2.VideoCapture(0)
while cap.isOpened():
    success, img = cap.read()
    if not success:
        print("skipping frame")
        continue
    h, w, c = img.shape
    img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
    img.flags.writeable = False
    results = hands.process(img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                img,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            for id, lm in enumerate(hand_landmarks.landmark):
                if id == 8:
                    index_pos = (int(lm.x * w), int(lm.y * h))
                    cv2.circle(img, index_pos, 18, slash_Color, -1)
                    slash = np.append(slash, index_pos)

                    # Ensure even number of elements
                    if len(slash) % 2 != 0:
                        slash = slash[:-1]
                    # Limit to last N points (slash_length)
                    if len(slash) > slash_length * 2:
                        slash = slash[-slash_length * 2:]

                    slash_reshaped = slash.reshape((-1, 1, 2))
                    cv2.polylines(img, [slash_reshaped], False, slash_Color, 15, 0)

                    for fruit in list(Fruits):
                        d = distance(index_pos, fruit["Curr_position"])
                        cv2.putText(img, str(d), fruit["Curr_position"], cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2, 3)
                        if d < Fruit_Size:
                            Score += 100
                            slash_Color = fruit["Color"]
                            Fruits.remove(fruit)
                            total_hits += 1

    if Score % 1000 == 0 and Score != 0:
        Difficulty_level = int(Score / 1000) + 1
        Spawn_Rate = Difficulty_level * 4 / 5
        Speed[0] *= Difficulty_level
        Speed[1] = int(5 * Difficulty_level / 2)

    if Lives <= 0:
        game_Over = True

    curr_Frame = time.time()
    delta_Time = curr_Frame - prev_Frame
    prev_Frame = curr_Frame
    FPS = int(1 / delta_Time) if delta_Time > 0 else 0

    cv2.putText(img, "FPS : " + str(FPS), (int(w * 0.82), 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 250, 0), 2)
    cv2.putText(img, "Score: " + str(Score), (int(w * 0.35), 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 5)
    cv2.putText(img, "Level: " + str(Difficulty_level), (int(w * 0.01), 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 150), 5)
    cv2.putText(img, "Lives remaining : " + str(Lives), (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Calculate accuracy safely
    if (total_hits + total_misses) > 0:
        Accuracy = (total_hits / (total_hits + total_misses)) * 100
    else:
        Accuracy = 100

    cv2.putText(img, f"Accuracy: {Accuracy:.2f}%", (int(w * 0.01), 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    if not game_Over:
        if time.time() > next_Time_to_Spawn:
            Spawn_Fruits()
            next_Time_to_Spawn = time.time() + (1 / Spawn_Rate)
        Fruit_Movement(Fruits, Speed)
    else:
        cv2.putText(img, "GAME OVER", (int(w * 0.1), int(h * 0.6)), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 3)
        Fruits.clear()

    cv2.imshow("img", img)

    if cv2.waitKey(5) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
