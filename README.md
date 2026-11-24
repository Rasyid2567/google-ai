# ePlus AI Toolkit — Waydroid Linux Fork (`Rasyid2567/google-ai`)

Personal Linux fork of [hoangsvit/google-ai](https://github.com/hoangsvit/google-ai) focused specifically on running **ePlus AI Toolkit** with **Waydroid + Root** (Android 13, `x86_64`) via ADB, Frida 16.5.9, and Google Play.

![ePlus AI Toolkit — dashboard (Steps 0–5)](images/terminal-ui-overview.png)

> [!CAUTION]
> **Unofficial project. Potential billing charges.** Steps **2–5** can open a real Google Play checkout and may automatically tap **Subscribe**. A listed offer or zero-priced first phase does **not** guarantee eligibility, a free subscription, or activation. Always verify the account, today's charge, future pricing, and renewal date directly in Google Play. **Only Steps 0–1 have been verified on Waydroid; Steps 2–5 remain real-billing operations requiring your own approval.**

> [!NOTE]
> **Card authorization note (reported 24-month example):** Steps 2, 3, and 4 may each trigger a separate **~US$1** card-verification/payment event (**3 × US$1 = US$3**, not one US$3 charge), often as a temporary authorization hold that clears in **1–14 business days** depending on your bank. Verify actual status and renewal dates in [Google Play Subscriptions](https://play.google.com/store/account/subscriptions).

## Requirements

Linux (**Wayland** session) with Android `binder` kernel support (`grep binder /proc/filesystems`), **`waydroid`**, **`adb`** (Android SDK Platform-Tools), **`git`**, **`curl`**, and **`python3` 3.10+** (`venv` & `pip`).

## Setup Waydroid + Root (5 Steps)

### 1. Initialize Waydroid (GAPPS)

```sh
sudo waydroid init -s GAPPS -f
sudo chmod 755 /var/lib/waydroid
sudo chmod 644 /var/lib/waydroid/waydroid.cfg
```

### 2. Install Root (`waydroidsu` v2.0.0 / KitsuneMagisk)

```sh
mkdir -p /tmp/wsu && cd /tmp/wsu
curl -fsSLO https://github.com/AmanCode22/waydroidsu/releases/download/v2.0.0/wsu-2.0.0-x86_64-linux.tar.gz
tar -xzf wsu-2.0.0-x86_64-linux.tar.gz
waydroid session stop
sudo ./wsu install
sudo systemctl restart waydroid-container
waydroid show-full-ui &
```

Wait until Waydroid reaches the Android home screen, then finish setup:

```sh
sudo /tmp/wsu/wsu setup
```

Inside Waydroid, open **KitsuneMagisk** (tap **OK** if prompted to upgrade to the full manager) → **Settings → Superuser → Automatic Response → Grant**.

### 3. Prepare Google Play Store & Google One

1. If Play Store shows *"Device is not certified"*, register your Google Android ID at [google.com/android/uncertified](https://www.google.com/android/uncertified/), wait a few minutes, and restart Waydroid.
2. Sign in to **Google Play Store**, install **Google One** (native `x86_64` — `libhoudini` is not required), and open **Google One** to confirm it uses the same account.

### 4. Connect ADB & Verify Root

```sh
IP=$(waydroid status | awk '/IP address:/ {print $3}')
adb connect "${IP}:5555"
adb devices
adb shell "su -c id"
```

Confirm `adb devices` shows **exactly 1 device** (`device`) and `su -c id` prints `uid=0(root)`.

### 5. Clone & Run the Toolkit

```sh
git clone https://github.com/Rasyid2567/google-ai.git
cd google-ai
sh run-linux.sh --check   # Step 0: ADB, root & Frida 16.5.9
sh run-linux.sh --list    # Step 1: list offers (read-only, no checkout)
sh run-linux.sh           # Open the Textual dashboard
```

## Stages (Steps 0–5)

| Step | Purpose | Checkout risk |
| --- | --- | --- |
| **0 — Environment** | Diagnose/prepare Android, ADB and Frida 16.5.9 | No checkout (may alter Android/Frida settings) |
| **1 — Available offers** | List offers for the active Google Play account | No checkout |
| **2 — Pro 12 months** | Initial 12-month offer (`12months-eft`) | **May start real checkout** |
| **3 — Pro +6 months** | First +6 months update | **May start real checkout** |
| **4 — Pro +6 months (second)** | Second +6 months update | **May start real checkout** |
| **5 — Optional +6 months** | Optional update | **May start real checkout** |

Every checkout stage (Steps 2–5) requires a separate confirmation in the dashboard. After each stage, verify the subscription and renewal date directly in Google Play before pressing **Verified in Google Play → Next**.

## Waydroid Troubleshooting

| Problem | Fix |
| --- | --- |
| No internet inside Waydroid | Allow `waydroid0` (ports 53/67 and forwarding) in your Linux firewall (e.g. UFW/iptables) and ensure your host DNS is reachable. |
| Waydroid window won't reopen (`FROZEN`) | Run `adb shell input keyevent KEYCODE_WAKEUP && waydroid show-full-ui &` or restart the session (`waydroid session stop && waydroid show-full-ui &`). |
| Play Store *Add payment method* dims/freezes | Add your payment method from your desktop browser at [play.google.com/store/paymentmethods](https://play.google.com/store/paymentmethods) on the same Google account. |
| After host reboot | Start Waydroid (`waydroid show-full-ui &`) and reconnect ADB (`adb connect "$(waydroid status | awk '/IP address:/ {print $3}'):5555"`). |

## Fork-Specific Changes (`Rasyid2567/google-ai`)

Compared to upstream `hoangsvit/google-ai`, this fork adds two Waydroid compatibility patches in [ultra0.py](ultra0.py):

- `ensure_root()` checks `su -c id` before `adb root` so TCP ADB on Waydroid/Magisk does not briefly drop offline.
- `ensure_vending()` and `launch_app()` fall back to `cmd package resolve-activity` + `am start -n` when `monkey` fails on Waydroid (`SYS_KEYS has no physical keys`).

## Disclaimer & Credits

Provided **as is** without warranties. Read [DISCLAIMER.md](DISCLAIMER.md), [SECURITY.md](SECURITY.md), and [docs/LINUX.md](docs/LINUX.md) before use.

Upstream project by **[gylive/google-ultra](https://github.com/gylive/google-ultra)** and maintainer **[@hoangsvit](https://github.com/hoangsvit)**. See [CONTRIBUTORS.md](CONTRIBUTORS.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
