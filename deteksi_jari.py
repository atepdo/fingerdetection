import math
import os
import platform
import queue
import threading
import time
import urllib.request
from collections import Counter, deque

import cv2
import mediapipe as mp

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


KAMERA_INDEX = 0
LEBAR, TINGGI = 1280, 720
MODEL_COMPLEXITY = 1
JENDELA_STABIL = 8
RASIO_STABIL = 0.7
JEDA_UCAP = 0.9
NAMA_JENDELA = "Deteksi Jari Tangan"

ANGKA = {
    0: "nol", 1: "satu", 2: "dua", 3: "tiga", 4: "empat", 5: "lima",
    6: "enam", 7: "tujuh", 8: "delapan", 9: "sembilan", 10: "sepuluh",
}


HIJAU = (120, 230, 80)
BIRU = (255, 170, 60)
PUTIH = (245, 245, 245)
ABU = (150, 150, 150)
MERAH = (80, 80, 240)
KUNING = (60, 220, 255)


class Suara:
    def __init__(self):
        self.aktif = pyttsx3 is not None
        self._q = queue.Queue()
        self._voice_id = None
        self._t = threading.Thread(target=self._worker, daemon=True)
        self._t.start()

    def _worker(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        while True:
            teks = self._q.get()
            if teks is None:
                break
            if pyttsx3 is None:
                continue
            try:


                engine = pyttsx3.init()
                engine.setProperty("rate", 165)
                if self._voice_id is None:
                    self._voice_id = ""
                    for v in engine.getProperty("voices"):
                        if "id" in v.id.lower() or "indonesia" in v.name.lower():
                            self._voice_id = v.id
                            break
                if self._voice_id:
                    engine.setProperty("voice", self._voice_id)
                engine.say(teks)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                print("[TTS] error:", e)

    def ucapkan(self, teks):
        if not self.aktif:
            return

        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._q.put(teks)

    def tutup(self):
        self._q.put(None)


class Kamera:
    def __init__(self, index, lebar, tinggi):
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(index, backend)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, lebar)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, tinggi)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._lock = threading.Lock()
        self._frame = None
        self._id = 0
        self._jalan = True
        self.gagal = False
        self._t = threading.Thread(target=self._loop, daemon=True)
        if self.cap.isOpened():
            self._t.start()

    def terbuka(self):
        return self.cap.isOpened()

    def _loop(self):
        gagal_beruntun = 0
        while self._jalan:
            ok, f = self.cap.read()
            if not ok:
                gagal_beruntun += 1
                if gagal_beruntun > 100:
                    self.gagal = True
                    break
                time.sleep(0.01)
                continue
            gagal_beruntun = 0
            with self._lock:
                self._frame = f
                self._id += 1

    def baca(self):
        with self._lock:
            return self._id, self._frame

    def tutup(self):
        self._jalan = False
        if self._t.is_alive():
            self._t.join(timeout=1)
        self.cap.release()


MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
             "hand_landmarker/float16/latest/hand_landmarker.task")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")


class DeteksiTangan:

    def __init__(self, max_tangan=2, kompleksitas=1, keyakinan=0.6):
        self._lama = hasattr(mp, "solutions")
        if self._lama:
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=max_tangan,
                model_complexity=kompleksitas,
                min_detection_confidence=keyakinan,
                min_tracking_confidence=keyakinan,
            )
        else:
            from mediapipe.tasks.python import BaseOptions, vision
            self._siapkan_model()
            opsi = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=MODEL_PATH),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=max_tangan,
                min_hand_detection_confidence=keyakinan,
                min_hand_presence_confidence=keyakinan,
                min_tracking_confidence=keyakinan,
            )
            self._hands = vision.HandLandmarker.create_from_options(opsi)
            self._ts = 0

    @staticmethod
    def _siapkan_model():
        if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1_000_000:
            return
        print("Mengunduh model tangan MediaPipe (sekali saja, ~8 MB)...")
        sementara = MODEL_PATH + ".part"
        urllib.request.urlretrieve(MODEL_URL, sementara)
        os.replace(sementara, MODEL_PATH)
        print("Model tersimpan di", MODEL_PATH)

    def deteksi(self, rgb):
        if self._lama:
            rgb.flags.writeable = False
            h = self._hands.process(rgb)
            if not h.multi_hand_landmarks:
                return []
            dunia = h.multi_hand_world_landmarks or h.multi_hand_landmarks
            return [
                (layar.landmark, d.landmark, info.classification[0].label)
                for layar, d, info in zip(h.multi_hand_landmarks, dunia, h.multi_handedness)
            ]


        ts = int(time.perf_counter() * 1000)
        self._ts = ts if ts > self._ts else self._ts + 1
        gambar = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        h = self._hands.detect_for_video(gambar, self._ts)
        dunia = h.hand_world_landmarks or h.hand_landmarks
        return [
            (layar, d, info[0].category_name)
            for layar, d, info in zip(h.hand_landmarks, dunia, h.handedness)
        ]

    def tutup(self):
        self._hands.close()


def _jarak(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def _sudut(a, b, c):
    v1 = (a.x - b.x, a.y - b.y, a.z - b.z)
    v2 = (c.x - b.x, c.y - b.y, c.z - b.z)
    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    n1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
    n2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos))


JARI = [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]


def jari_terbuka(lm):
    pergelangan = lm[0]
    telapak = _jarak(lm[0], lm[9]) or 1e-6


    jempol = (
        _sudut(lm[2], lm[3], lm[4]) > 140
        and _jarak(lm[4], lm[17]) > _jarak(lm[2], lm[17])
        and _jarak(lm[4], lm[5]) > 0.5 * telapak
    )

    hasil = [jempol]
    for mcp, pip, dip, tip in JARI:
        lurus = _sudut(lm[mcp], lm[pip], lm[dip]) > 150
        menjauh = _jarak(lm[tip], pergelangan) > _jarak(lm[pip], pergelangan) * 1.1
        hasil.append(lurus and menjauh)
    return hasil


class Penstabil:

    def __init__(self, panjang=JENDELA_STABIL, rasio=RASIO_STABIL):
        self.riwayat = deque(maxlen=panjang)
        self.rasio = rasio
        self.nilai = None

    def tambah(self, angka):
        self.riwayat.append(angka)
        if len(self.riwayat) < self.riwayat.maxlen // 2:
            return self.nilai
        kandidat, jumlah = Counter(self.riwayat).most_common(1)[0]
        if jumlah >= self.rasio * len(self.riwayat):
            self.nilai = kandidat
        return self.nilai

    def reset(self):
        self.riwayat.clear()
        self.nilai = None


FONT = cv2.FONT_HERSHEY_DUPLEX
FONT_TEBAL = cv2.FONT_HERSHEY_TRIPLEX


def teks(img, s, org, skala, warna, tebal=1, font=FONT):
    x, y = org
    cv2.putText(img, s, (x + 1, y + 2), font, skala, (0, 0, 0), tebal, cv2.LINE_AA)
    cv2.putText(img, s, (x, y), font, skala, warna, tebal, cv2.LINE_AA)


def kotak_transparan(img, x1, y1, x2, y2, warna=(15, 15, 15), alpha=0.55, radius=18):
    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return
    roi = img[y1:y2, x1:x2]
    lapis = roi.copy()
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    ww, hh = x2 - x1, y2 - y1
    cv2.rectangle(lapis, (r, 0), (ww - r, hh), warna, -1)
    cv2.rectangle(lapis, (0, r), (ww, hh - r), warna, -1)
    for cx, cy in ((r, r), (ww - r - 1, r), (r, hh - r - 1), (ww - r - 1, hh - r - 1)):
        cv2.circle(lapis, (cx, cy), r, warna, -1, cv2.LINE_AA)
    cv2.addWeighted(lapis, alpha, roi, 1 - alpha, 0, roi)


UJUNG = [4, 8, 12, 16, 20]
SAMBUNGAN = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]


def gambar_tangan(img, lm_layar, terbuka, warna_tangan):
    h, w = img.shape[:2]
    titik = [(int(p.x * w), int(p.y * h)) for p in lm_layar]

    for a, b in SAMBUNGAN:
        cv2.line(img, titik[a], titik[b], (40, 40, 40), 6, cv2.LINE_AA)
        cv2.line(img, titik[a], titik[b], warna_tangan, 2, cv2.LINE_AA)

    for i, p in enumerate(titik):
        if i in UJUNG:
            continue
        cv2.circle(img, p, 4, PUTIH, -1, cv2.LINE_AA)

    for idx, buka in zip(UJUNG, terbuka):
        p = titik[idx]
        if buka:
            cv2.circle(img, p, 14, HIJAU, 2, cv2.LINE_AA)
            cv2.circle(img, p, 8, HIJAU, -1, cv2.LINE_AA)
        else:
            cv2.circle(img, p, 6, ABU, -1, cv2.LINE_AA)
    return titik


def gambar_label_tangan(img, titik, nama, jumlah, warna):
    x = min(p[0] for p in titik)
    y = min(p[1] for p in titik) - 18
    s = f"{nama}: {jumlah}"
    (tw, th), _ = cv2.getTextSize(s, FONT, 0.7, 1)
    kotak_transparan(img, x - 10, y - th - 12, x + tw + 12, y + 10, alpha=0.6, radius=10)
    teks(img, s, (x, y), 0.7, warna, 1)


def gambar_panel(img, angka, n_tangan, fps, pop, suara_aktif):
    kotak_transparan(img, 20, 20, 300, 230)

    if angka is None:
        teks(img, "-", (45, 140), 3.2, ABU, 4, FONT_TEBAL)
        teks(img, "tunjukkan tangan", (45, 190), 0.75, ABU, 1)
    else:
        skala = 3.2 * (1 + 0.35 * pop)
        s = str(angka)
        (tw, th), _ = cv2.getTextSize(s, FONT_TEBAL, skala, 5)
        teks(img, s, (45, 70 + th // 2 + 40), skala, HIJAU, 5, FONT_TEBAL)
        teks(img, ANGKA.get(angka, s).upper(), (45 + tw + 20, 140), 1.0, PUTIH, 2)
        teks(img, "jari", (45 + tw + 20, 172), 0.7, ABU, 1)

    teks(img, f"Tangan: {n_tangan}", (45, 212), 0.6, KUNING, 1)
    teks(img, f"FPS {fps:4.0f}", (170, 212), 0.6, ABU, 1)
    teks(img, "Suara ON" if suara_aktif else "Suara OFF", (190, 52),
         0.5, HIJAU if suara_aktif else MERAH, 1)


def gambar_petunjuk(img):
    h, w = img.shape[:2]
    s = "Q/ESC keluar   M suara   F layar penuh"
    (tw, th), _ = cv2.getTextSize(s, FONT, 0.55, 1)
    x = (w - tw) // 2
    kotak_transparan(img, x - 16, h - th - 34, x + tw + 16, h - 12, alpha=0.5, radius=12)
    teks(img, s, (x, h - 22), 0.55, ABU, 1)


def dengarkan_perintah(suara, keadaan, berhenti):
    if sr is None:
        print("[Voice] speech_recognition belum terpasang, perintah suara dimatikan.")
        return
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
    except Exception as e:
        print("[Voice] Mikrofon tidak tersedia, perintah suara dimatikan:", e)
        return

    recognizer.dynamic_energy_threshold = True
    print("[Voice] Aktif. Coba ucapkan: 'halo jarvis' atau 'berapa jari'")

    while not berhenti.is_set():
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
            kata = recognizer.recognize_google(audio, language="id-ID").lower()
            print(f"[Voice] Terdengar: {kata}")

            if any(k in kata for k in ("halo jarvis", "hallo jarvis", "halo jarpis", "hello jarvis")):
                suara.ucapkan("halo sir")
            elif "berapa" in kata:
                n = keadaan.get("angka")
                if n is None:
                    suara.ucapkan("tidak ada tangan")
                else:
                    suara.ucapkan(f"{ANGKA.get(n, str(n))} jari")
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print("[Voice] Layanan speech recognition tidak bisa diakses (perlu internet):", e)
            time.sleep(3)
        except Exception as e:
            print("[Voice] error:", e)
            time.sleep(1)


def main():
    kamera = Kamera(KAMERA_INDEX, LEBAR, TINGGI)
    if not kamera.terbuka():
        print("Kamera tidak bisa dibuka. Cek koneksi/izin kamera.")
        return

    suara = Suara()
    keadaan = {"angka": None}
    berhenti = threading.Event()
    threading.Thread(target=dengarkan_perintah, args=(suara, keadaan, berhenti), daemon=True).start()

    try:
        detektor = DeteksiTangan(max_tangan=2, kompleksitas=MODEL_COMPLEXITY)
    except Exception as e:
        print("Gagal menyiapkan deteksi tangan MediaPipe:", e)
        kamera.tutup()
        return

    cv2.namedWindow(NAMA_JENDELA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(NAMA_JENDELA, 1100, 620)
    layar_penuh = False

    penstabil = Penstabil()
    angka_tampil = None
    angka_terucap = None
    waktu_ucap = 0.0
    waktu_pop = 0.0
    fps = 0.0
    t_sebelum = time.perf_counter()
    id_terakhir = -1

    print("Kamera aktif. Tunjukkan tangan Anda. Tekan Q atau ESC untuk keluar.")

    try:
        while True:
            fid, frame = kamera.baca()
            if kamera.gagal:
                print("Gagal membaca frame dari kamera.")
                break
            if frame is None or fid == id_terakhir:

                if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                    break
                continue
            id_terakhir = fid

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tangan = detektor.deteksi(rgb)

            n_tangan = len(tangan)
            total = 0
            if tangan:
                for lm_layar, lm_dunia, label in tangan:
                    terbuka = jari_terbuka(lm_dunia)
                    jumlah = sum(terbuka)
                    total += jumlah

                    kanan = label == "Right"
                    warna = BIRU if kanan else KUNING
                    titik = gambar_tangan(frame, lm_layar, terbuka, warna)
                    gambar_label_tangan(frame, titik, "Kanan" if kanan else "Kiri", jumlah, warna)
                angka_baru = penstabil.tambah(total)
            else:
                penstabil.reset()
                angka_baru = None

            if angka_baru != angka_tampil:
                angka_tampil = angka_baru
                waktu_pop = time.perf_counter()
            keadaan["angka"] = angka_tampil

            sekarang = time.perf_counter()
            if (angka_tampil is not None and angka_tampil != angka_terucap
                    and sekarang - waktu_ucap > JEDA_UCAP):
                suara.ucapkan(ANGKA.get(angka_tampil, str(angka_tampil)))
                angka_terucap = angka_tampil
                waktu_ucap = sekarang
            if angka_tampil is None:
                angka_terucap = None

            dt = sekarang - t_sebelum
            t_sebelum = sekarang
            if dt > 0:
                fps = fps * 0.9 + (1.0 / dt) * 0.1 if fps else 1.0 / dt

            pop = math.exp(-(sekarang - waktu_pop) * 8)
            gambar_panel(frame, angka_tampil, n_tangan, fps, pop, suara.aktif)
            gambar_petunjuk(frame)

            cv2.imshow(NAMA_JENDELA, frame)
            tombol = cv2.waitKey(1) & 0xFF
            if tombol in (ord("q"), 27):
                break
            if tombol == ord("m"):
                suara.aktif = not suara.aktif and pyttsx3 is not None
            if tombol == ord("f"):
                layar_penuh = not layar_penuh
                cv2.setWindowProperty(
                    NAMA_JENDELA, cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if layar_penuh else cv2.WINDOW_NORMAL,
                )
            if cv2.getWindowProperty(NAMA_JENDELA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        berhenti.set()
        suara.tutup()
        detektor.tutup()
        kamera.tutup()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
