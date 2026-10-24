# VYAS - Vedic Yield Astrology System
## कमर्शियल सॉफ़्टवेयर डिप्लॉयमेंट गाइड (.EXE एवं .APK निर्माण)

**निर्माता:** पं. निखिल व्यास, MA (ज्योतिष)  
**मोबाइल:** +91 9414121172  
**ईमेल:** inikhilvyas@gmail.com  
**लाइसेंस:** Commercial Enterprise License

---

### 1. विंडोज़ के लिए .EXE (Windows Executable) कैसे बनाएं:
यह पैकेज पूरी तरह तैयार है। विंडोज़ कंप्यूटर पर मात्र 1 क्लिक में `.exe` बनाने के 2 आसान तरीके हैं:

#### तरीका A: एक-क्लिक स्वचालित बैट फ़ाइल (Recommended)
1. इस पूरे ज़िप फ़ोल्डर को अपने विंडोज़ कंप्यूटर में एक्सट्रैक्ट (Unzip) करें।
2. फ़ोल्डर में मौजूद `build_exe.bat` फ़ाइल पर डबल-क्लिक करें।
3. यह स्क्रिप्ट स्वचालित रूप से `PyInstaller` की मदद से `dist/VYAS_Astrology/VYAS_Astrology.exe` जनरेट कर देगी।

#### तरीका B: मैन्युअल कमांड (Command Prompt):
```bash
pip install pyinstaller pywebview
pyinstaller --noconfirm --onedir --windowed --add-data "vyas_astrology_system.html;." --name "VYAS_Astrology" app_desktop.py
```
इसके बाद `dist/VYAS_Astrology/` में आपकी `.exe` फ़ाइल बन जाएगी, जिसे आप पेनड्राइव या इंस्टॉलर के रूप में किसी भी क्लाइंट को दे सकते हैं।

---

### 2. एंड्रॉइड के लिए .APK (Android APK) कैसे बनाएं:

#### तरीका A: PWABuilder (बिना कोडिंग के 2 मिनट में डायरेक्ट APK डाउनलोड)
1. Microsoft द्वारा विकसित आधिकारिक **[PWABuilder.com](https://www.pwabuilder.com)** पर जाएं।
2. इस ऐप को किसी भी फ्री होस्टिंग (GitHub Pages, Netlify, या Vercel) पर होस्ट करें (या ज़िप फ़ाइल अपलोड करें)।
3. "Package for Android" पर क्लिक करें।
4. आपको सीधे हस्ताक्षरित (Signed) `.apk` और Google Play Store के लिए `.aab` फ़ाइल डाउनलोड मिल जाएगी।

#### तरीका B: कैपेसिटर / कॉर्डोवा CLI (Capacitor Build)
```bash
npm install -g @capacitor/cli @capacitor/core @capacitor/android
npx cap init "VYAS Astrology" com.nikhilvyas.vyas
npx cap add android
npx cap copy
npx cap open android
```
Android Studio में "Build APK" पर क्लिक करते ही 1 मिनट में आपकी व्यावसायिक `.apk` तैयार हो जाएगी!

#### तरीका C: डायरेक्ट 1-क्लिक PWA (बिना किसी ऐप स्टोर के फोन में इंस्टॉल करें)
* अपने मोबाइल के Chrome या Brave ब्राउज़र में `vyas_astrology_system.html` खोलें।
* ब्राउज़र मेनू (3 डॉट्स) पर क्लिक करके **"Add to Home Screen" (होम स्क्रीन पर जोड़ें)** या **"Install App"** दबाएं।
* यह सीधे आपके फोन में एक नेटिव एंड्रॉइड ऐप की तरह फुल-स्क्रीन में इंस्टॉल हो जाएगी और बिना इंटरनेट के भी 100% ऑफलाइन चलेगी!
