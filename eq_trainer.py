import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import lfilter
import random

class EQTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EQ Ear Trainer")
        self.root.geometry("500x780")
        self.root.configure(bg="#f5f6f8")

        # --- High-DPI Crisp Text Fix ---
        self.enable_high_dpi()

        # Audio state
        self.audio_data = None
        self.sample_rate = 44100
        self.eq_audio_data = None
        self.current_freq = None
        
        # Default ISO 1/1 octave bands
        self.default_frequencies = "63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000"
        self.frequencies = [63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

        # Setup modern TTK styles
        self.setup_styles()
        self.setup_ui()

    def enable_high_dpi(self):
        """Fixes pixelated rendering on high-resolution screens."""
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        
        try:
            self.root.tk.call('tk', 'scaling', 1.33)
        except Exception:
            pass

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Base Color Palette
        BG_COLOR = "#f5f6f8"
        ACCENT_BLUE = "#2563eb"
        ACCENT_GREEN = "#16a34a"
        TEXT_MAIN = "#1e293b"

        self.style.configure(".", background=BG_COLOR, foreground=TEXT_MAIN, font=("Segoe UI", 9))
        
        # Frame Styling
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("Card.TFrame", background="#ffffff", relief="flat")
        
        # Label Styling
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_MAIN)
        self.style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"), foreground="#0f172a")
        self.style.configure("Sub.TLabel", font=("Segoe UI", 8), foreground="#64748b")
        
        # Slider Styling
        self.style.configure("TScale", background=BG_COLOR)

        # Custom Button Styling
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=6, borderwidth=0)
        self.style.configure("Action.TButton", background="#e2e8f0", foreground="#0f172a")
        self.style.map("Action.TButton", background=[("active", "#cbd5e1")])

        self.style.configure("Primary.TButton", background=ACCENT_BLUE, foreground="#ffffff")
        self.style.map("Primary.TButton", background=[("active", "#1d4ed8")])

        self.style.configure("Success.TButton", background=ACCENT_GREEN, foreground="#ffffff")
        self.style.map("Success.TButton", background=[("active", "#15803d")])

        self.style.configure("Stop.TButton", background="#ef4444", foreground="#ffffff")
        self.style.map("Stop.TButton", background=[("active", "#dc2626")])

    def setup_ui(self):
        main_container = ttk.Frame(self.root, padding="16 16 16 16")
        main_container.pack(fill="both", expand=True)

        # --- Section 1: Audio Source ---
        ttk.Label(main_container, text="1. Audio Source", style="Header.TLabel").pack(anchor="w", pady=(0, 4))
        
        frame_source_btns = ttk.Frame(main_container)
        frame_source_btns.pack(fill="x", pady=2)
        
        self.btn_load = ttk.Button(frame_source_btns, text="📁 Load File (.wav, .flac)", style="Action.TButton", command=self.load_file)
        self.btn_load.pack(side="left", expand=True, fill="x", padx=(0, 3))
        
        self.btn_noise = ttk.Button(frame_source_btns, text="🔊 White Noise", style="Action.TButton", command=self.generate_white_noise)
        self.btn_noise.pack(side="right", expand=True, fill="x", padx=(3, 0))
        
        self.lbl_status = ttk.Label(main_container, text="Status: No audio loaded", style="Sub.TLabel")
        self.lbl_status.pack(anchor="w", pady=(4, 10))

        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=8)

        # --- Section 2: EQ Parameters & Pool ---
        ttk.Label(main_container, text="2. EQ Parameters & Pool", style="Header.TLabel").pack(anchor="w", pady=(0, 4))

        ttk.Label(main_container, text="Target Frequencies (Hz, comma-separated):").pack(anchor="w")
        
        self.entry_freqs = ttk.Entry(main_container)
        self.entry_freqs.insert(0, self.default_frequencies)
        self.entry_freqs.pack(fill="x", pady=(2, 4))
        
        self.entry_freqs.bind("<KeyRelease>", lambda e: self.parse_frequencies())
        self.entry_freqs.bind("<Return>", lambda e: self.parse_frequencies())

        self.lbl_pool_preview = ttk.Label(
            main_container, 
            text=f"Active Pool ({len(self.frequencies)} bands): {self.frequencies}", 
            style="Sub.TLabel",
            wraplength=440, 
            justify="left"
        )
        self.lbl_pool_preview.pack(anchor="w", pady=(0, 10))

        # --- Sliders Frame for Boost & Q Factor ---
        frame_sliders = ttk.Frame(main_container)
        frame_sliders.pack(fill="x", pady=4)

        # 1. Boost Slider
        frame_boost_label = ttk.Frame(frame_sliders)
        frame_boost_label.pack(fill="x", pady=(2, 0))
        ttk.Label(frame_boost_label, text="Boost:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.lbl_boost_val = ttk.Label(frame_boost_label, text="+12.0 dB", font=("Segoe UI", 9, "bold"), foreground="#2563eb")
        self.lbl_boost_val.pack(side="right")

        self.slider_boost = ttk.Scale(
            frame_sliders, 
            from_=1.0, 
            to=24.0, 
            value=12.0, 
            command=self.update_boost_label
        )
        self.slider_boost.pack(fill="x", pady=(0, 8))

        # 2. Q Factor Slider
        frame_q_label = ttk.Frame(frame_sliders)
        frame_q_label.pack(fill="x", pady=(2, 0))
        ttk.Label(frame_q_label, text="Q Factor:", font=("Segoe UI", 9, "bold")).pack(side="left")
        self.lbl_q_val = ttk.Label(frame_q_label, text="2.0", font=("Segoe UI", 9, "bold"), foreground="#2563eb")
        self.lbl_q_val.pack(side="right")

        self.slider_q = ttk.Scale(
            frame_sliders, 
            from_=0.5, 
            to=10.0, 
            value=2.0, 
            command=self.update_q_label
        )
        self.slider_q.pack(fill="x", pady=(0, 4))

        # Clean Guide Card Frame
        card_guide = ttk.Frame(main_container, style="Card.TFrame", padding="10 10 10 10")
        card_guide.pack(fill="x", pady=(10, 10))

        guide_text = (
            "💡 Recommended Setup:\n"
            "• Boost: Start at +12 dB. Lower to +6 dB / +3 dB as you advance.\n"
            "• Q Factor: 1.0–2.0 (standard band). Higher Q (4.0+) narrows the boost."
        )
        lbl_guide = tk.Label(
            card_guide, 
            text=guide_text, 
            font=("Segoe UI", 8), 
            fg="#475569", 
            bg="#ffffff", 
            justify="left", 
            wraplength=420,
            anchor="w"
        )
        lbl_guide.pack(fill="x")

        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=8)

        # --- Section 3: Training & Playback Controls ---
        ttk.Label(main_container, text="3. Controls", style="Header.TLabel").pack(anchor="w", pady=(0, 6))

        frame_play_btns = ttk.Frame(main_container)
        frame_play_btns.pack(fill="x", pady=2)

        self.btn_play_orig = ttk.Button(frame_play_btns, text="Play Original", style="Action.TButton", command=self.play_original, state="disabled")
        self.btn_play_orig.pack(side="left", expand=True, fill="x", padx=(0, 3))

        self.btn_play_eq = ttk.Button(frame_play_btns, text="Play EQ'd", style="Action.TButton", command=self.play_eq, state="disabled")
        self.btn_play_eq.pack(side="right", expand=True, fill="x", padx=(3, 0))

        self.btn_apply_eq = ttk.Button(
            main_container, 
            text="🎲 Apply Random EQ Boost", 
            style="Primary.TButton",
            command=self.apply_random_eq, 
            state="disabled"
        )
        self.btn_apply_eq.pack(fill="x", pady=8)

        self.btn_stop = ttk.Button(main_container, text="Stop Playback", style="Stop.TButton", command=self.stop_playback, state="disabled")
        self.btn_stop.pack(fill="x", pady=2)

        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=10)

        # --- Section 4: Answer Section ---
        ttk.Label(main_container, text="4. Answer", style="Header.TLabel").pack(anchor="w", pady=(0, 4))

        self.btn_reveal = ttk.Button(main_container, text="Reveal Frequency", style="Success.TButton", command=self.reveal, state="disabled")
        self.btn_reveal.pack(fill="x", pady=2)

        self.lbl_answer = tk.Label(main_container, text="?", font=("Segoe UI", 22, "bold"), fg="#2563eb", bg="#f5f6f8")
        self.lbl_answer.pack(pady=6)

    def update_boost_label(self, val):
        """Updates Boost readout label when slider moves."""
        self.lbl_boost_val.config(text=f"+{float(val):.1f} dB")

    def update_q_label(self, val):
        """Updates Q Factor readout label when slider moves."""
        self.lbl_q_val.config(text=f"{float(val):.1f}")

    def parse_frequencies(self):
        """Parses frequency field dynamically on keystrokes."""
        raw_text = self.entry_freqs.get()
        try:
            parsed = [int(f.strip()) for f in raw_text.split(",") if f.strip().isdigit()]
            if not parsed:
                raise ValueError()
            parsed.sort()
            self.frequencies = parsed
            self.lbl_pool_preview.config(
                text=f"Active Pool ({len(self.frequencies)} bands): {self.frequencies}",
                foreground="#64748b"
            )
            return True
        except Exception:
            self.lbl_pool_preview.config(text="⚠️ Invalid frequencies! Use comma-separated numbers.", foreground="#ef4444")
            return False

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.flac *.ogg")])
        if not filepath:
            return
        
        try:
            self.audio_data, self.sample_rate = sf.read(filepath)
            self.audio_data = self.audio_data.astype(np.float32)
            
            self.lbl_status.config(text="Status: Audio File Loaded", foreground="#16a34a")
            self.reset_training_state()
            self.enable_controls()
        except Exception as e:
            messagebox.showerror("Error", f"Could not load audio: {e}")

    def generate_white_noise(self):
        duration = 10.0
        self.sample_rate = 44100
        self.audio_data = np.random.normal(0, 0.1, int(self.sample_rate * duration)).astype(np.float32)
        
        self.lbl_status.config(text="Status: White Noise Generated", foreground="#16a34a")
        self.reset_training_state()
        self.enable_controls()

    def enable_controls(self):
        self.btn_play_orig.config(state="normal")
        self.btn_apply_eq.config(state="normal")
        self.btn_stop.config(state="normal")

    def reset_training_state(self):
        self.eq_audio_data = None
        self.current_freq = None
        self.lbl_answer.config(text="?")
        self.btn_play_eq.config(state="disabled")
        self.btn_reveal.config(state="disabled")
        self.stop_playback()

    def apply_peaking_filter(self, data, freq, gain_db, q):
        nyquist = self.sample_rate / 2.0
        if freq >= nyquist:
            freq = nyquist - 100

        w0 = 2 * np.pi * freq / self.sample_rate
        alpha = np.sin(w0) / (2 * q)
        A = 10 ** (gain_db / 40.0)

        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A

        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        if len(data.shape) > 1:
            filtered = np.zeros_like(data)
            for ch in range(data.shape[1]):
                filtered[:, ch] = lfilter(b, a, data[:, ch])
            return filtered.astype(np.float32)
        else:
            return lfilter(b, a, data).astype(np.float32)

    def apply_random_eq(self):
        if self.audio_data is None:
            return
        
        if not self.parse_frequencies():
            messagebox.showerror("Invalid Input", "Please correct the target frequencies input before proceeding.")
            return

        boost_val = float(self.slider_boost.get())
        q_val = float(self.slider_q.get())

        self.stop_playback()
        self.lbl_answer.config(text="?")
        
        self.current_freq = random.choice(self.frequencies)
        
        self.eq_audio_data = self.apply_peaking_filter(
            self.audio_data, 
            freq=self.current_freq, 
            gain_db=boost_val, 
            q=q_val
        )

        self.btn_play_eq.config(state="normal")
        self.btn_reveal.config(state="normal")
        
        self.play_eq()

    def play_original(self):
        self.stop_playback()
        if self.audio_data is not None:
            sd.play(self.audio_data, self.sample_rate)

    def play_eq(self):
        self.stop_playback()
        if self.eq_audio_data is not None:
            sd.play(self.eq_audio_data, self.sample_rate)

    def stop_playback(self):
        sd.stop()

    def reveal(self):
        if self.current_freq:
            self.lbl_answer.config(text=f"{self.current_freq} Hz")

if __name__ == "__main__":
    root = tk.Tk()
    app = EQTrainerApp(root)
    root.mainloop()