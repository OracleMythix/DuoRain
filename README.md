# 🌧️ DuoRain — Duolingo XP, Gem and Streak Farmer 

> A terminal-based XP, Gem and Streak farming tool for Duolingo.

## ⚡️ Features

* Supports XP, Gem and Streak farming
* Farms \~499 XP per loop
* Farms \~120 gems per loop

---

## 📦 Installation

* Clone The Repository

```bash
git clone https://github.com/OracleMythix/DuoRain.git
```

---

## 🚀 Usage

Before first use, retrieve your **JWT token** from your browser console while logged into Duolingo:

```js
document.cookie.match(new RegExp('(^| )jwt_token=([^;]+)'))[0].slice(11)
```

Copy the token and paste it into the terminal when prompted.

```bash
python DuoRain.py
```

Each XP loop gives you \~499 XP and each Gem loop gives \~120 gems.

> **Note:** The XP farm runs Duolingo stories in **English → French** Course.
> To earn XP, make sure the **French course** is already added to your Duolingo profile.

---

## 💧 Credits

* XP, Gem and Streak farming logic adapted from [`DuoXPy`](https://github.com/DuoXPy/DuoXPy-Bot) by [@DuoXPy](https://github.com/DuoXPy)
* CLI design, UX flow, theming, and enhancements by [@OracleMythix](https://github.com/OracleMythix)

---

## ⚠️ Disclaimer

*This tool is intended for learning and educational purposes only*. *Use responsibly*. And **DO NOT SKID OR SELL IT AS YOUR PRODUCT.**

---

Stay stormy. ⛈️
