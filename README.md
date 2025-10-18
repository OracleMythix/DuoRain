# 🌧️ DuoRain — Duolingo Automation Tool

> A terminal-based XP, Gem, Streak farming and Quests Completer tool for Duolingo.

## ⚡️ Features

* Supports XP, Gem and Streak farming
* **NEW:** Multi-Task Farming - Run XP, Gem, and Streak farms simultaneously
* Farms \~499 XP per loop
* Farms \~120 gems per loop
* Completes All quests including past monthly badges quest, friend quest and daily quest.
* Free Items & Free Super (3-Days)

---

## 📦 Installation

* Clone The Repository

```bash
git clone https://github.com/OracleMythix/DuoRain.git
cd DuoRain
```

* Install Requirements

```bash
pip install -r requirements.txt
```

---

## 🔐 Fetch Your JWT Token Before Usage

Before running the script for the first time, you need to get your JWT token from the Duolingo website:

1. Go to [https://www.duolingo.com](https://www.duolingo.com) and log in to your account.
2. Open your browser's Developer Console (Press `F12` or `Ctrl+Shift+I`, then go to the **Console** tab).
3. Paste and run the following line of code:

```js
document.cookie.match(new RegExp('(^| )jwt_token=([^;]+)'))[0].slice(11)
```

4. Copy the string it returns — that's your JWT token.
5. Run the script and paste the JWT when prompted.

---

## 🚀 Usage

```bash
python DuoRain.py
```

### Single Task Farming

Each XP loop gives you \~499 XP and each Gem loop gives you \~120 gems.

### Multi-Task Farming

The new Multi-Task Farming feature allows you to run multiple farming tasks simultaneously:

1. Select option 7 "Multi-Task Farm" from the main menu
2. Choose which tasks you want to run:
   - XP Farm (enter desired XP amount)
   - Gem Farm (enter desired number of loops)
   - Streak Farm (enter desired number of days)
3. Select option 4 "Start All Tasks" to begin farming
4. Press 'Z' at any time to stop all running tasks

The multi-task interface will show you the progress of each task in real-time, including:
- Current progress (completed/total)
- Value gained (XP, gems, or streak days)
- Status (Running, Complete, Stopped, or Error)
- Elapsed time

> **Note:** The XP farm runs Duolingo stories in **English → French** Course (I will add a feature that will get you XP in user desired course).
> To earn XP, make sure the **French course** is already added to your Duolingo profile.

---

## 💧 Credits

* XP farming, Gem farming, Streak farming and All Quests Completer logic adapted from [`DuoXPy`](https://github.com/DuoXPy/DuoXPy-Bot) by [@DuoXPy](https://github.com/DuoXPy)
* CLI design, UX flow, theming, and enhancements by [@OracleMythix](https://github.com/OracleMythix)

---

## ⚠️ Disclaimer

*This tool is intended for learning and educational purposes only*. *Use responsibly*. And **DO NOT SKID OR SELL IT AS YOUR PRODUCT.**

---

Stay stormy. ⛈️
