import sys
import os

class DummyConsole:
    def write(self, *args, **kwargs): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyConsole()
if sys.stderr is None:
    sys.stderr = DummyConsole()

import customtkinter as ctk
from tkinter import filedialog, messagebox
import pygame
import threading
import subprocess
import imageio_ffmpeg
import shutil
import soundfile as sf

from df.enhance import enhance, init_df, load_audio, save_audio
from pedalboard import Pedalboard, Compressor, LowShelfFilter, HighShelfFilter, HighpassFilter, Gain, Limiter

ctk.set_appearance_mode("Dark")
pygame.mixer.init()

class AudioEnhancerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ResoRefine AI - Pro Desk")
        self.geometry("750x800")
        self.minsize(700, 750)
        self.configure(fg_color="#0b0f19")

        self.original_file_path = None
        self.current_working_file = None
        self.ai_model = None
        self.df_state = None

        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=15, pady=15)
        self.scroll_container.grid_columnconfigure(0, weight=1)

        # --- DYNAMIC SPLIT COLOR HEADER ---
        self.header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(15, 20))
        
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_container.pack()
        
        self.title_reso = ctk.CTkLabel(self.title_container, text="Reso", font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"), text_color="#ffffff")
        self.title_reso.pack(side="left")
        self.title_refine = ctk.CTkLabel(self.title_container, text="Refine", font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"), text_color="#a855f7")
        self.title_refine.pack(side="left")
        self.title_ai = ctk.CTkLabel(self.title_container, text=" AI", font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"), text_color="#ffffff")
        self.title_ai.pack(side="left")

        self.sub_label = ctk.CTkLabel(self.header_frame, text="Professional Audio Restoration Engine", font=ctk.CTkFont(family="Segoe UI", size=14), text_color="#64748b")
        self.sub_label.pack(pady=(4, 0))

        # --- CARD 1: INPUT & TRANSPORT ---
        self.card_input = ctk.CTkFrame(self.scroll_container, fg_color="#111827", border_color="#1e293b", border_width=1, corner_radius=16)
        self.card_input.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.card_input.grid_columnconfigure(0, weight=1)

        # 1A. The Upload Button (Shown by default)
        self.upload_btn = ctk.CTkButton(
            self.card_input, 
            text="📁\n\nLoad Audio File\nClick here to browse your computer", 
            command=self.select_file, 
            height=130, 
            fg_color="#1e293b", 
            hover_color="#334155",
            border_color="#2563eb",
            border_width=1.5,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        )
        self.upload_btn.grid(row=0, column=0, pady=(25, 25), padx=25, sticky="ew")

        # 1B. The Active File Display Card (Hidden by default)
        self.active_file_frame = ctk.CTkFrame(self.card_input, fg_color="#1e293b", border_color="#10b981", border_width=1.5, corner_radius=12)
        self.active_file_frame.grid_columnconfigure(1, weight=1) # Pushes the "Change File" button to the right
        
        self.file_icon = ctk.CTkLabel(self.active_file_frame, text="🎵", font=ctk.CTkFont(size=36))
        self.file_icon.grid(row=0, column=0, rowspan=2, padx=(20, 15), pady=15)

        self.file_name_label = ctk.CTkLabel(self.active_file_frame, text="filename.wav", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.file_name_label.grid(row=0, column=1, sticky="sw", pady=(15, 0))

        self.file_path_label = ctk.CTkLabel(self.active_file_frame, text="C:/path/to/file", text_color="#94a3b8", font=ctk.CTkFont(family="Segoe UI", size=12))
        self.file_path_label.grid(row=1, column=1, sticky="nw", pady=(0, 15))

        self.change_file_btn = ctk.CTkButton(self.active_file_frame, text="Change File", width=100, height=32, fg_color="#334155", hover_color="#475569", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), command=self.select_file)
        self.change_file_btn.grid(row=0, column=2, rowspan=2, padx=20, sticky="e")

        # Transport Controls
        self.transport_frame = ctk.CTkFrame(self.card_input, fg_color="transparent")
        self.transport_frame.grid(row=1, column=0, pady=(0, 25))
        
        self.play_btn = ctk.CTkButton(self.transport_frame, text="▶ Play", width=140, height=42, state="disabled", command=self.play_audio, fg_color="#2563eb", hover_color="#1d4ed8", text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"))
        self.play_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ctk.CTkButton(self.transport_frame, text="⏹ Stop", width=140, height=42, state="disabled", command=self.stop_audio, fg_color="#dc2626", hover_color="#b91c1c", text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"))
        self.stop_btn.grid(row=0, column=1, padx=10)

        # --- CARD 2: THE STUDIO DESK ---
        self.card_controls = ctk.CTkFrame(self.scroll_container, fg_color="#111827", border_color="#1e293b", border_width=1, corner_radius=16)
        self.card_controls.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        self.card_controls.grid_columnconfigure(0, weight=1)
        self.card_controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.card_controls, text="ENGINE CONTROLS", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#3b82f6").grid(row=0, column=0, columnspan=2, sticky="w", padx=25, pady=(20, 15))

        self.left_control_frame = ctk.CTkFrame(self.card_controls, fg_color="transparent")
        self.left_control_frame.grid(row=1, column=0, sticky="nsew", padx=(25, 15), pady=(0, 20))

        self.noise_toggle = ctk.CTkSwitch(self.left_control_frame, text="AI Noise Reduction (DeepFilterNet)", progress_color="#2563eb", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=13))
        self.noise_toggle.select()
        self.noise_toggle.pack(anchor="w", pady=15)

        self.comp_toggle = ctk.CTkSwitch(self.left_control_frame, text="Auto-Leveling (Studio Compression)", progress_color="#2563eb", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=13))
        self.comp_toggle.select()
        self.comp_toggle.pack(anchor="w", pady=15)

        self.right_control_frame = ctk.CTkFrame(self.card_controls, fg_color="transparent")
        self.right_control_frame.grid(row=1, column=1, sticky="nsew", padx=(15, 25), pady=(0, 20))

        self.warmth_label_frame = ctk.CTkFrame(self.right_control_frame, fg_color="transparent")
        self.warmth_label_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(self.warmth_label_frame, text="Broadcast Warmth (Bass)", font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#ffffff").pack(side="left")
        self.warmth_pct = ctk.CTkLabel(self.warmth_label_frame, text="45%", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#3b82f6")
        self.warmth_pct.pack(side="right")

        self.warmth_slider = ctk.CTkSlider(self.right_control_frame, from_=0, to=10, number_of_steps=20, button_color="#2563eb", button_hover_color="#1d4ed8", progress_color="#2563eb", command=self.update_warmth_label)
        self.warmth_slider.set(4.5)
        self.warmth_slider.pack(fill="x", pady=(5, 15))

        self.clarity_label_frame = ctk.CTkFrame(self.right_control_frame, fg_color="transparent")
        self.clarity_label_frame.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(self.clarity_label_frame, text="Vocal Clarity (Treble)", font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#ffffff").pack(side="left")
        self.clarity_pct = ctk.CTkLabel(self.clarity_label_frame, text="25%", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#3b82f6")
        self.clarity_pct.pack(side="right")

        self.clarity_slider = ctk.CTkSlider(self.right_control_frame, from_=0, to=10, number_of_steps=20, button_color="#2563eb", button_hover_color="#1d4ed8", progress_color="#2563eb", command=self.update_clarity_label)
        self.clarity_slider.set(2.5)
        self.clarity_slider.pack(fill="x", pady=(5, 15))

        # --- CARD 3: EXECUTION ---
        self.card_exec = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.card_exec.grid(row=3, column=0, sticky="ew", padx=10, pady=15)
        self.card_exec.grid_columnconfigure(0, weight=1)

        self.action_btn = ctk.CTkButton(self.card_exec, text="✨ Render Studio Audio", command=self.trigger_action, state="disabled", height=55, fg_color="#05b311", hover_color="#048c0d", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.action_btn.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        self.process_status = ctk.CTkLabel(self.card_exec, text="", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
        self.process_status.grid(row=1, column=0, pady=5)

        self.save_btn = ctk.CTkButton(self.card_exec, text="💾 Export Final File", command=self.download_file, state="disabled", height=55, fg_color="#6705b3", hover_color="#4f048a", text_color="#ffffff", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))
        self.save_btn.grid(row=2, column=0, sticky="ew", pady=(5, 10))

    def update_warmth_label(self, value):
        self.warmth_pct.configure(text=f"{int(float(value) * 10)}%")

    def update_clarity_label(self, value):
        self.clarity_pct.configure(text=f"{int(float(value) * 10)}%")

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select an Audio File", filetypes=[("Audio Files", "*.wav *.mp3 *.ogg *.m4a *.aac *.flac")])
        if file_path:
            self.free_audio_lock() 
            self.original_file_path = file_path
            self.current_working_file = file_path
            
            # 1. Hide the big generic button
            self.upload_btn.grid_forget()
            
            # 2. Update and show the beautiful file display card
            filename = os.path.basename(file_path)
            self.file_name_label.configure(text=filename)
            self.file_path_label.configure(text=file_path)
            self.active_file_frame.grid(row=0, column=0, pady=(25, 25), padx=25, sticky="ew")
            
            # 3. Enable bottom controls
            self.action_btn.configure(state="normal")
            self.process_status.configure(text="")
            self.save_btn.configure(state="disabled") 

            try:
                pygame.mixer.music.load(self.current_working_file)
                self.play_btn.configure(state="normal")
                self.stop_btn.configure(state="normal")
            except Exception:
                pass # Playback not supported for this specific codec, but processing will still work

    def play_audio(self):
        if self.current_working_file: pygame.mixer.music.play()

    def stop_audio(self):
        pygame.mixer.music.stop()

    def free_audio_lock(self):
        pygame.mixer.music.stop()
        try: pygame.mixer.music.unload()
        except AttributeError: pass

    def trigger_action(self):
        self.free_audio_lock()
        self.action_btn.configure(state="disabled")
        self.play_btn.configure(state="disabled")
        self.stop_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        threading.Thread(target=self.run_full_pipeline, daemon=True).start()

    def run_full_pipeline(self):
        try:
            filename = os.path.basename(self.original_file_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_audio")
            os.makedirs(output_dir, exist_ok=True)

            self.after(0, lambda: self.process_status.configure(text="⚙️ Step 1/3: Formatting Audio...", text_color="#eab308"))
            prep_file = os.path.join(output_dir, f"{name_without_ext}_prep.wav")
            
            hide_console = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            subprocess.run(
                [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", self.original_file_path, "-ac", "1", "-ar", "48000", "-af", "loudnorm", prep_file], 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                creationflags=hide_console
            )
            
            cleaned_file = os.path.join(output_dir, f"{name_without_ext}_Cleaned.wav")
            if self.noise_toggle.get() == 1:
                self.after(0, lambda: self.process_status.configure(text="🧠 Step 2/3: Running DeepFilterNet AI...", text_color="#06b6d4"))
                if self.ai_model is None:
                    self.ai_model, self.df_state, _ = init_df()
                audio, _ = load_audio(prep_file, sr=self.df_state.sr())
                enhanced_audio = enhance(self.ai_model, self.df_state, audio)
                save_audio(cleaned_file, enhanced_audio, self.df_state.sr())
            else:
                shutil.copy2(prep_file, cleaned_file)

            self.after(0, lambda: self.process_status.configure(text="🎛️ Step 3/3: Applying Custom Mastering...", text_color="#f97316"))
            final_file = os.path.join(output_dir, f"{name_without_ext}_Mastered.wav")
            
            audio_data, sample_rate = sf.read(cleaned_file)
            pedal_chain = [HighpassFilter(cutoff_frequency_hz=80)] 
            
            warmth_db = self.warmth_slider.get()
            clarity_db = self.clarity_slider.get()
            
            if warmth_db > 0: pedal_chain.append(LowShelfFilter(cutoff_frequency_hz=150, gain_db=warmth_db))
            if clarity_db > 0: pedal_chain.append(HighShelfFilter(cutoff_frequency_hz=4000, gain_db=clarity_db))
            
            if self.comp_toggle.get() == 1:
                pedal_chain.append(Compressor(threshold_db=-18, ratio=3.0))
                pedal_chain.append(Gain(gain_db=3.0))
                
            pedal_chain.append(Limiter(threshold_db=-0.5))

            board = Pedalboard(pedal_chain)
            mastered_audio = board(audio_data, sample_rate)
            sf.write(final_file, mastered_audio, sample_rate)

            self.current_working_file = final_file
            self.after(0, self.pipeline_complete)

        except Exception as e:
            self.after(0, self.show_error, f"Pipeline failed: {str(e)}")

    def pipeline_complete(self):
        self.process_status.configure(text="✅ Render Complete!", text_color="#05b311")
        
        # Visually update the file card to show the new processed file
        self.file_name_label.configure(text=f"{os.path.basename(self.current_working_file)}")
        self.file_path_label.configure(text="Playback Stack: Mastered Audio Loaded", text_color="#05b311")
        self.active_file_frame.configure(border_color="#05b311") # Highlight border green
        
        self.action_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        
        pygame.mixer.music.load(self.current_working_file)
        self.play_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")

    def download_file(self):
        if not self.current_working_file: return
        suggested_name = f"{os.path.splitext(os.path.basename(self.original_file_path))[0]}_ResoRefine_Pro.wav"
        save_path = filedialog.asksaveasfilename(defaultextension=".wav", initialfile=suggested_name, title="Export Pro Audio File", filetypes=[("Uncompressed Audio (WAV)", "*.wav")])
        if save_path:
            try:
                shutil.copy2(self.current_working_file, save_path)
                messagebox.showinfo("Success", f"Pro Master exported successfully to:\n{save_path}")
            except Exception as e:
                self.show_error(f"Failed to write file export payload: {str(e)}")

    def show_error(self, error_msg):
        self.process_status.configure(text="❌ Engine Interrupt", text_color="#ef4444")
        messagebox.showerror("Error", error_msg)
        self.action_btn.configure(state="normal")

if __name__ == "__main__":
    app = AudioEnhancerApp()
    app.mainloop()