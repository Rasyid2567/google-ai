# Linux setup and verification

[Documentation home](README.md) · [Dashboard usage](USAGE.md) · [Safety](SAFETY.md)

The Linux launcher targets Ubuntu x86_64 and exposes Steps 0–5 through the shared Textual dashboard. Use a rooted Android test device you control. If you only need to check the USB connection, use **Diagnose Android connection** in the dashboard.

**Android 16 and later.** The Linux launcher blocks all stages before device setup when the Android SDK is 36 or higher, or if it cannot read the SDK version. The toolkit pins Frida 16.5.9. Frida first announced Android 16 support in 17.1.4. The USB connection diagnostic remains available. [Frida 17.1.4 release notes](https://frida.re/news/2025/06/10/frida-17-1-4-released/).

The engine used by Steps 0 and 1 can request an ADB daemon restart for root, deploy or restart the Android Frida server, copy a billing module, clear the Android global HTTP proxy, and force-stop supported VPN apps.

## Setup

1. Install Git, Python 3.10+ with `venv` and `pip`, and Android SDK Platform-Tools. Put `adb` on `PATH` or set `ADB_PATH` to the path of the executable.
2. Connect one rooted Android device by USB. Enable USB debugging, unlock the device and approve the authorization prompt. Google Play Store and Google One must be installed. Sign in to the intended Google Play account on the device.
3. Once Linux support has been merged, clone the stable `main` branch and start the Linux launcher. The ADB check respects `ADB_PATH`:

   ```sh
   git clone --branch main --single-branch https://github.com/hoangsvit/google-ai.git
   cd google-ai
   "${ADB_PATH:-adb}" devices
   sh run-linux.sh
   ```

The launcher installs pinned Textual and Frida 16.5.9 into a local `.venv`. It opens the dashboard without starting a stage.

| Command | Behavior |
| --- | --- |
| `sh run-linux.sh --check` | Runs Step 0 environment setup and diagnostics. |
| `sh run-linux.sh --list` | Runs Step 1 offer listing. Android preparation can still change settings. |
| `sh run-linux.sh --step 3` | Opens Advanced controls with Step 3 selected. Steps 0–5 can be preselected. |
| `sh run-linux.sh --sequence` | Opens guided controls starting at Step 2. Add it after `--step N` to choose a starting step. Guided checkout accepts Steps 2–5. |

**Steps 2–5 may attempt real charges.** Each checkout requires its own approval, a verified current Google Play account and a fresh exact offer with a zero-priced first phase. Verify the subscription and renewal date in Google Play before continuing a sequence. Offer metadata alone cannot establish eligibility or renewal terms.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| ADB missing | Install Platform-Tools, update `PATH` or set `ADB_PATH` to the executable. When only `ADB_PATH` is set, run that executable with `devices` to check the connection. |
| `unauthorized` | Unlock the phone and approve the USB debugging prompt. Check for status `device`. |
| No device or USB permissions error | Reconnect with a data cable, check USB debugging, and verify Ubuntu's Android USB device rules and access for your user. |
| Multiple devices | Disconnect extra devices and retry. |
| Virtual environment error | Install `python3-venv` or its version-specific equivalent and check that the checkout is writable. If an existing `.venv` belongs to another host or is unusable, move it aside and rerun the launcher. |
| Frida or Android stage failure | Check the dashboard's technical details and device state. Confirm compatibility of Frida 16.5.9 with the Android build before repeating a stage. |
| Offer or account check fails | Open Google One and Google Play on Android and check the selected profile. If the device became unstable, stop testing and review the Android/Frida setup before proceeding. |

## Terminal preview

[PR #84](https://github.com/hoangsvit/google-ai/pull/84) includes screenshots captured from the running Textual app on a Linux CI runner, with synthetic account and offer data. These images are UI previews, **not** proof of a connected Android device, live account eligibility, successful payment or renewal.

## Validation status

Offline tests cover the launcher and dashboard with Python 3.11 and 3.13, including mocked checkout paths. End-to-end Steps 0–1 on a rooted USB phone remain pending. A live checkout is a separate release gate.

## Waydroid + Root setup (Fork Guide — `Rasyid2567/google-ai`)

> [!NOTE]
> **Fork-specific addition (not from upstream `hoangsvit/google-ai`).** Steps 0–1 were verified on Arch Linux (`x86_64`, Wayland, kernel with `CONFIG_ANDROID_BINDER_IPC_RUST=y`) running Waydroid Android 13 (SDK 33, `x86_64`) with `waydroidsu` (`wsu` v2.0.0 / KitsuneMagisk). **Steps 2–5 can initiate real Google Play charges and remain unverified on Waydroid.**

### Step-by-step setup

1. **Initialize Waydroid with GAPPS**
   ```sh
   sudo waydroid init -s GAPPS -f
   sudo chmod 755 /var/lib/waydroid
   sudo chmod 644 /var/lib/waydroid/waydroid.cfg
   ```
2. **Install Root with `waydroidsu` (`wsu` v2.0.0)**
   ```sh
   mkdir -p /tmp/wsu && cd /tmp/wsu
   curl -fsSLO https://github.com/AmanCode22/waydroidsu/releases/download/v2.0.0/wsu-2.0.0-x86_64-linux.tar.gz
   tar -xzf wsu-2.0.0-x86_64-linux.tar.gz
   waydroid session stop
   sudo ./wsu install
   sudo systemctl restart waydroid-container
   waydroid show-full-ui &
   # Once Android boots to the home screen:
   sudo /tmp/wsu/wsu setup
   ```
   Open **KitsuneMagisk** inside Waydroid (tap **OK** if prompted to upgrade to the full manager), then set **Settings → Superuser → Automatic Response → Grant**.
3. **Connect ADB and verify root**
   ```sh
   IP=$(waydroid status | awk '/IP address:/ {print $3}')
   adb connect "${IP}:5555"
   adb devices
   adb shell "su -c id"
   ```
   Expect **one** `device` entry and `uid=0(root)`.
4. **Install Google One & run read-only checks**
   Sign in to **Google Play Store** and install **Google One** (native `x86_64`; `libhoudini` is not required). Then run:
   ```sh
   sh run-linux.sh --check
   sh run-linux.sh --list
   sh run-linux.sh
   ```

### Waydroid troubleshooting

| Symptom | Fix |
| --- | --- |
| `waydroid status` says not initialized after `sudo waydroid init` | Check `/var/lib/waydroid` permissions (`sudo chmod 755 /var/lib/waydroid && sudo chmod 644 /var/lib/waydroid/waydroid.cfg`). |
| No internet inside Waydroid (UFW / Docker active) | Allow `waydroid0` ports 53/67 and forwarding (`sudo ufw allow in on waydroid0 to any port 53`, port 67, `ufw route allow in/out on waydroid0`, and `iptables -I FORWARD -i/-o waydroid0 -j ACCEPT`). |
| `ping 8.8.8.8` works, `ping google.com` fails (host DNS issue) | Ensure your host `/etc/resolv.conf` points to a reachable DNS server (e.g. `8.8.8.8` or `1.1.1.1`) so Waydroid's `dnsmasq` can resolve domains. |
| Waydroid window does not reopen after closing (`FROZEN`) | Wake the display (`adb shell input keyevent KEYCODE_WAKEUP && waydroid show-full-ui &`) or restart the session (`waydroid session stop && waydroid show-full-ui &`). |
| Play Store *Add payment method* dims/freezes | Add the payment method from a desktop browser at `https://play.google.com/store/paymentmethods` on the same Google account. |
| After host reboot | Start Waydroid (`waydroid show-full-ui &`) and reconnect ADB (`adb connect "$(waydroid status | awk '/IP address:/ {print $3}'):5555"`). |
