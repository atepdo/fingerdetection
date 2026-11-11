# Deteksi Jari Tangan + Voice Command

Pakai OpenCV buat baca kamera, MediaPipe buat deteksi tangannya, sama pyttsx3 buat suaranya.

## Yang dibutuhkan

- Python **3.11** (paling aman). Aku sempat kejebak pakai Python 3.14 dan mediapipe-nya error terus (`module 'mediapipe' has no attribute 'solutions'`), ternyata mediapipe versi lama yang stabil belum support Python sebaru itu.
- Webcam
- Mic (buat voice command)
- Koneksi internet pas mau pakai voice command, soalnya speech recognition-nya lewat Google

Library yang dipakai:
```
opencv-python
mediapipe==0.10.9
pyttsx3
SpeechRecognition
pyaudio
pywin32
```

Kenapa mediapipe-nya disaranin versi 0.10.9? Versi mediapipe terbaru udah ganti API, modul `solutions` dihapus. Script ini sebenarnya udah bisa jalan di dua-duanya (otomatis pindah ke API baru kalau `solutions` gak ada), tapi yang paling sering aku tes ya pakai 0.10.9.

## Cara install

1. Install Python 3.11 dari python.org (cari "Python 3.11.9"). Pas instalasi, jangan lupa centang "Add python.exe to PATH".

   Cek udah kepasang belum:
   ```
   py -3.11 --version
   ```

2. Clone repo ini terus masuk ke foldernya:
   ```
   git clone https://github.com/atepdo/fingerdetection.git
   cd fingerdetection
   ```

3. Install library-librarynya:
   ```
   py -3.11 -m pip install opencv-python pyttsx3 SpeechRecognition pyaudio pywin32
   py -3.11 -m pip install mediapipe==0.10.9 protobuf==3.20.3
   ```

   `pyaudio` sekarang udah bisa langsung di-install lewat pip di Windows (Python 3.8 sampai 3.13), gak perlu cara aneh-aneh lagi.

## Cara jalanin

```
py -3.11 deteksi_jari.py
```

Kamera bakal langsung nyala. Tinggal angkat tangan ke depan kamera, nanti keluar garis-garis di jari kamu dan angka jumlah jarinya bakal keluar di panel kiri atas sambil diucapin. Jari yang kebuka ditandain lingkaran hijau, dan tiap tangan ada labelnya (Kanan / Kiri). Kalau mau lebih dari 5, angkat dua tangan sekaligus (regangin jangan ketumpuk biar kedeteksi dua-duanya).

Tombol keyboard (klik jendela kameranya dulu):

| Tombol | Fungsi |
|---|---|
| `Q` / `ESC` | keluar |
| `M` | suara hidup / mati |
| `F` | layar penuh |

Bisa juga keluar dengan klik tombol X di jendelanya.

Voice command, tinggal ngomong ke mic:
- **"halo jarvis"** → dia jawab "halo sir"
- **"berapa jari"** → dia nyebutin jumlah jari yang lagi kelihatan

## Pengaturan

Ada di bagian paling atas `deteksi_jari.py`:

- `KAMERA_INDEX = 0` → ganti ke 1 atau 2 kalau kamera yang kebuka salah / gak kebuka
- `MODEL_COMPLEXITY = 1` → ganti ke 0 kalau laptop berat (lebih ringan, sedikit kurang akurat)
- `JEDA_UCAP = 0.9` → jeda minimal antar ucapan (detik)

## Kalau ada masalah

**Error `module 'mediapipe' has no attribute 'solutions'`**
Berarti kamu masih pakai script versi lama dengan mediapipe versi baru. Pakai script terbaru, atau uninstall mediapipe terus install lagi yang versi 0.10.9.

**Error `'MessageFactory' object has no attribute 'GetPrototype'` atau `FieldDescriptor ... has no attribute 'label'`**
Versi `protobuf`-nya kebaru buat mediapipe 0.10.9 (biasanya ke-upgrade sama library lain). Turunin versinya:
```
py -3.11 -m pip install protobuf==3.20.3
```

**Pertama kali jalan muncul tulisan "Mengunduh model tangan MediaPipe..."**
Normal, ini cuma kejadian kalau mediapipe-nya versi baru. Dia download file `hand_landmarker.task` (~8 MB) sekali aja, jadi pastiin ada internet.

**Ketik `python` di CMD tapi masih kepake python versi lama**
Pakai `py -3.11` aja di depan, jangan cuma `python`.

**Jarinya mentok kehitung 5 walau dua tangan diangkat**
Biasanya karena dua tangannya kedeketan/numpuk jadi kamera cuma nangkep satu. Coba direnggangin sama pastiin dua-duanya masuk frame kamera.

**Suaranya kedengeran sekali doang terus abis itu hilang**
Ini bug bawaan pyttsx3 di Windows, biasanya kalau engine-nya dipake berkali-kali suka macet gitu aja. Solusinya di script ini udah dibikin biar tiap mau ngomong dia bikin ulang enginenya, jadi harusnya udah gak kejadian lagi kalau pakai script terbaru.

**Voice command-nya error `RequestError`**
Cek koneksi internet, soalnya proses ngenalin suaranya butuh internet (pakai Google).

**Kamera gak kebuka**
Ganti `KAMERA_INDEX = 0` di bagian atas script jadi 1 atau 2.

**Install pyaudio gagal**
Pastiin pip-nya udah terbaru dulu (`py -3.11 -m pip install --upgrade pip`), terus coba install lagi. Kalau tetap gagal, program masih bisa jalan, cuma voice command-nya yang mati.

## Isi folder

- `deteksi_jari.py`: script utamanya
- `README.md`: ini yang lagi kamu baca
- `hand_landmarker.task`: file model, cuma muncul kalau pakai mediapipe versi baru (gak perlu di-upload ke GitHub)

---

Bebas dipakai atau diutak-atik, ini cuma project belajar aja.
