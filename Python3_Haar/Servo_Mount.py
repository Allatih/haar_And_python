import cv2
import serial
import time 

arduino = serial.Serial("COM4", 9600)
time.sleep(2)

start_angle = 90
current_angle = start_angle
arduino.write(f"{start_angle}\n".encode())
print(f"Установлена стартовая позиция: {start_angle}")
time.sleep(0.5)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(1)

angle_threshold = 30      # Минимальное изменение угла для обновления цели
send_delay = 0.0      # Минимум 100 мс между отправками
last_send_time = 0
target_angle = start_angle
step = 2                  # Шаг изменения угла за итерацию

dead_zone_min = 60
dead_zone_max = 90

frame_skip = 1         # Обрабатывать каждый n-й кадр
frame_count = 0

sent_angles = []          # Список для хранения последних отправленных углов

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        cv2.imshow("Frame", frame)
        if cv2.waitKey(10) & 0xFF == 27:
            break
        continue

    frame = cv2.flip(frame, 1)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        cx = x + w // 2
        new_target = 150 - int((cx / frame.shape[1]) * 120)
        new_target = max(30, min(new_target, 150))

        if dead_zone_min <= target_angle <= dead_zone_max:
            if new_target < dead_zone_min or new_target > dead_zone_max:
                target_angle = new_target
        else:
            if abs(new_target - target_angle) >= angle_threshold:
                target_angle = new_target

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.circle(frame, (cx, y + h // 2), 5, (0, 255, 0), -1)
        cv2.putText(frame, f"cx: {cx}, target: {target_angle}, current: {current_angle}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    if current_angle < target_angle:
        current_angle = min(current_angle + step, target_angle)
    elif current_angle > target_angle:
        current_angle = max(current_angle - step, target_angle)

    current_time = time.time()
    if (current_time - last_send_time) > send_delay:
        angle_to_send = int(current_angle)
        arduino.write(f"{angle_to_send}\n".encode())
        print(f"Отправлен угол: {angle_to_send}")

        sent_angles.append(angle_to_send)
        if len(sent_angles) > 5:
            last_angle = sent_angles[-1]
            sent_angles.clear()
            sent_angles.append(last_angle)

        last_send_time = current_time

    cv2.imshow("Frame", frame)

    if cv2.waitKey(10) & 0xFF == 27:  
        break

cap.release()
cv2.destroyAllWindows()
