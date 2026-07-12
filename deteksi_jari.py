import cv2
import mediapipe as mp
import pyttsx3
import threading
import time
import queue
import speech_recognition as sr

angka_bahasa_indonesia = {
    0: "nol", 1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima",
    6: "enam", 7: "tujuh", 8: "delapan", 9: "sembilan", 10: "sepuluh"
}

_antrian_suara = queue.Queue()

def _worker_suara():
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    while True:
        teks = _antrian_suara.get()
        if teks is None:
            break
        try:
            print(f"[TTS] Mengucapkan: {teks}")
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            for voice in engine.getProperty('voices'):
                if 'id' in voice.id.lower() or 'indonesia' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.say(teks)
            engine.runAndWait()
            del engine
            print(f"[TTS] Selesai: {teks}")
        except Exception as e:
            print("TTS error:", e)
        _antrian_suara.task_done()

threading.Thread(target=_worker_suara, daemon=True).start()

def ucapkan(teks):
    while not _antrian_suara.empty():
        try:
            _antrian_suara.get_nowait()
            _antrian_suara.task_done()
        except queue.Empty:
            break
    _antrian_suara.put(teks)


def dengarkan_perintah_suara():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)

    print("Voice command aktif. Coba ucapkan: 'halo jarvis'")

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
            teks = recognizer.recognize_google(audio, language="id-ID").lower()
            print(f"[Suara terdengar]: {teks}")

            if "halo jarvis" in teks or "hallo jarvis" in teks or "halo jarpis" in teks:
                print("Perintah dikenali -> menjawab 'halo sir'")
                ucapkan("halo sir")

        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print("Tidak bisa akses layanan speech recognition (perlu internet):", e)
            time.sleep(3)
        except Exception as e:
            print("Voice command error:", e)
            time.sleep(1)


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

TIP_IDS = [4, 8, 12, 16, 20]


def hitung_jari(landmarks, label_tangan):
    jari_terbuka = []

    if label_tangan == "Right":
        if landmarks[TIP_IDS[0]].x < landmarks[TIP_IDS[0] - 1].x:
            jari_terbuka.append(1)
        else:
            jari_terbuka.append(0)
    else:
        if landmarks[TIP_IDS[0]].x > landmarks[TIP_IDS[0] - 1].x:
            jari_terbuka.append(1)
        else:
            jari_terbuka.append(0)

    for id in range(1, 5):
        if landmarks[TIP_IDS[id]].y < landmarks[TIP_IDS[id] - 2].y:
            jari_terbuka.append(1)
        else:
            jari_terbuka.append(0)

    return sum(jari_terbuka)


cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Kamera tidak bisa dibuka. Cek koneksi/izin kamera.")
    exit()

jumlah_sebelumnya = -1
waktu_terakhir_ucap = 0
JEDA_UCAP = 1.5

print("Kamera aktif. Tunjukkan tangan Anda. Tekan 'q' untuk keluar.")

threading.Thread(target=dengarkan_perintah_suara, daemon=True).start()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal membaca frame dari kamera.")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hasil = hands.process(rgb_frame)

    jumlah_jari = 0

    if hasil.multi_hand_landmarks and hasil.multi_handedness:
        for hand_landmarks, handedness in zip(hasil.multi_hand_landmarks, hasil.multi_handedness):
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            label = handedness.classification[0].label
            jumlah_jari += hitung_jari(hand_landmarks.landmark, label)

        jumlah_tangan = len(hasil.multi_hand_landmarks)
        cv2.putText(frame, f"Tangan terdeteksi: {jumlah_tangan}", (30, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Jari: {jumlah_jari}", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
        teks_angka = angka_bahasa_indonesia.get(jumlah_jari, str(jumlah_jari))
        cv2.putText(frame, teks_angka.upper(), (30, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)

        waktu_sekarang = time.time()
        if jumlah_jari != jumlah_sebelumnya and (waktu_sekarang - waktu_terakhir_ucap) > JEDA_UCAP:
            ucapkan(teks_angka)
            waktu_terakhir_ucap = waktu_sekarang
            jumlah_sebelumnya = jumlah_jari
    else:
        cv2.putText(frame, "Tangan tidak terdeteksi", (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        jumlah_sebelumnya = -1

    cv2.imshow("Deteksi Jari Tangan", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
