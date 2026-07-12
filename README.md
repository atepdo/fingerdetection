# Deteksi Jari Tangan + Voice Command

Pakai OpenCV buat baca kamera, MediaPipe buat deteksi tangannya, sama pyttsx3 buat suaranya.

## Yang dibutuhkan

- Python **3.11** — ini penting, jangan pakai versi lain. Aku sempat kejebak pakai Python 3.14 dan mediapipe-nya error terus (`module 'mediapipe' has no attribute 'solutions'`), ternyata versi mediapipe yang stabil belum support Python sebaru itu.
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
pypiwin32
```

Kenapa mediapipe-nya harus versi 0.10.9? Karena versi terbaru udah ganti API, modul `solutions` yang dipakai di script ini dihapus di versi baru. Jadi kalau install mediapipe versi paling baru malah error.

## Cara install

1. Install Python 3.11 dari python.org (cari "Python 3.11.9"). Pas instalasi, jangan lupa centang "Add python.exe to PATH".

   Cek udah kepasang belum:
   ```
   py -3.11 --version
   ```

2. Clone repo ini terus masuk ke foldernya:
   ```
   git clone https://github.com/USERNAME/NAMA-REPO.git
   cd NAMA-REPO
   ```

3. Install library-librarynya:
   ```
   py -3.11 -m pip install opencv-python pyttsx3 SpeechRecognition pypiwin32
   py -3.11 -m pip install mediapipe==0.10.9
   ```

4. `pyaudio` biasanya agak rewel kalau di-install langsung. Kalau error, coba ini:
   ```
   py -3.11 -m pip install pipwin
   py -3.11 -m pipwin install pyaudio
   ```

## Cara jalanin

```
py -3.11 deteksi_jari.py
```

Kamera bakal langsung nyala. Tinggal angkat tangan ke depan kamera, nanti keluar garis-garis di jari kamu dan angka jumlah jarinya bakal keluar di layar sambil diucapin. Kalau mau lebih dari 5, angkat dua tangan sekaligus (regangin jangan ketumpuk biar kedeteksi dua-duanya).

Terus kalau mau coba fitur satunya, tinggal ngomong aja ke mic "halo jarvis", nanti dia jawab "halo sir".

Buat keluar dari programnya, klik jendela kameranya terus pencet `q`.

## Kalau ada masalah

**Error `module 'mediapipe' has no attribute 'solutions'`**
Berarti versi mediapipe-nya kebaru. Uninstall dulu, install lagi yang versi 0.10.9.

**Ketik `python` di CMD tapi masih kepake python versi lama**
Pakai `py -3.11` aja di depan, jangan cuma `python`.

**Jarinya mentok kehitung 5 walau dua tangan diangkat**
Biasanya karena dua tangannya kedeketan/numpuk jadi kamera cuma nangkep satu. Coba direnggangin sama pastiin dua-duanya masuk frame kamera.

**Suaranya kedengeran sekali doang terus abis itu hilang**
Ini bug bawaan pyttsx3 di Windows, biasanya kalau engine-nya dipake berkali-kali suka macet gitu aja. Solusinya di script ini udah dibikin biar tiap mau ngomong dia bikin ulang enginenya, jadi harusnya udah gak kejadian lagi kalau pakai script terbaru.

**Voice command-nya error `RequestError`**
Cek koneksi internet, soalnya proses ngenalin suaranya butuh internet (pakai Google).

**Kamera gak kebuka**
Di dalam script ada baris `cv2.VideoCapture(0)`, coba ganti angka 0-nya jadi 1 atau 2.

**Install pyaudio gagal**
Pakai cara pipwin yang di atas.

## Isi folder

- `deteksi_jari.py` — script utamanya
- `README.md` — ini yang lagi kamu baca

---

Bebas dipakai atau diutak-atik, ini cuma project belajar aja.
