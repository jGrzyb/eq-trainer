# EQ Ear Trainer

An audio ear training app built with Python to help music producers, sound engineers, and musicians train their ears to identify boosted frequencies across the audible spectrum.

---

## 💡 How It Works

1. **Load Sound Source**: Load your own audio file (`.wav`, `.flac`, `.ogg`) or click **White Noise** to generate a static continuous noise loop.
2. **Listen to Baseline**: Click **Play Original** to hear the unedited sound.
3. **Apply Boost**: Click **🎲 Apply Random EQ Boost**. The app selects a random frequency from your active pool and boosts it according to your set parameters.
4. **Identify & Compare**: Switch between **Play Original** and **Play EQ'd** to A/B test the sound in your ears.
5. **Reveal**: Click **Reveal Frequency** to check if your guess was correct.
6. **Repeat**: Click **Apply Random EQ Boost** again to draw a new frequency and start the next round!

---

## ⚙️ Features & Parameters

- **Custom Frequency Pool**: Target standard ISO octave bands or input your own comma-separated frequencies (e.g. `125, 500, 2000, 8000`).
- **Boost Control**: Adjust boost intensity from `+1.0 dB` to `+24.0 dB`. Lower values increase training difficulty.
- **Q Factor Control**: Adjust the bandwidth of the EQ peak from `0.5` (wide) to `10.0` (narrow/surgical).
- **Built-in White Noise**: Instant static noise source for isolating frequency bands without musical bias.

---

## 🚀 Quick Start (Running from Source)

### Prerequisites
- Python 3.10+
- Conda or virtual environment (recommended)

### Setup & Launch

```bash
# Clone or extract the project
cd eq-ear-trainer

# Install dependencies
pip install numpy sounddevice soundfile scipy

# Launch the app
python eq_trainer.py
