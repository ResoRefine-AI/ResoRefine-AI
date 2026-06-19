# ResoRefine Pro
Free AI Audio Enhancer &amp; Noise Reduction tool for Windows.

ResoRefine Pro is a free AI noise removing and audio enhancing tool built for podcasters, YouTubers, and indie creators to get pristine audio without recurring fees. Just drop in a noisy, echoing recording, click "Render," and instantly get a broadcast-ready `.wav` file.

## Key Features
* **Free AI Enhancer:** Zero subscriptions. Get unlimited, uncompressed WAV file exports.
* **100% Private & Offline:** Your audio never goes to the cloud. It processes entirely locally via our AI engine.
* **Remove Noise & Echo:** Instantly clean up mic hiss, fan noise, and room echo using deep-learning suppression.
* **Studio Desk Control:** Dial in "Broadcast Warmth" (Bass) and "Vocal Clarity" (Treble) for a rich, professional podcast sound.
* **Auto-Leveling:** Built-in studio compression ensures perfectly balanced, clear audio for YouTube, Spotify, and TikTok.

---

## How to Use ResoRefine Pro

You can run ResoRefine Pro either as a portable, ready-to-use desktop application or directly from the Python source code.

### Option 1: The Standalone Executable (`.exe`) - *Recommended for Creators*
If you just want to clean up your audio without installing Python or dealing with code, use this method.

1. Go to the **Releases** section on the right side of this GitHub page.
2. Download the latest `ResoRefine.exe` file.
3. Double-click the `.exe` file to launch the application. *(No installation required!)*
4. Drag and drop your noisy audio file into the upload zone.
5. Adjust your *Warmth* and *Clarity* sliders, then click **Render Studio Audio**.
6. Once processing is complete, click **Export Final File** to save your new `.wav` track.

### Option 2: Running from Source (`app.py`) - *For Developers*
If you want to run the raw code or modify the application, follow these steps:

**Prerequisites:** 
Ensure you have [Python 3.10 or newer](https://www.python.org/downloads/) installed on your system.

1. **Clone the repository:**
```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/resorefine-pro.git](https://github.com/YOUR_GITHUB_USERNAME/resorefine-pro.git)
   cd resorefine-pro
