#!/usr/bin/env python3
import requests
import json
import random
import time
from tqdm import tqdm
from datetime import datetime, timezone, timedelta
from colorama import Fore, init

init(autoreset=True)

#----SPEED CONTROL-----
SLEEP_TIME = 0

try:
    with open("config.json") as f:
        cfg = json.load(f)
except FileNotFoundError:
    print(Fore.RED + "config.json not found. Make sure it's in the same folder.")
    exit(1)
except json.JSONDecodeError as e:
    print(Fore.RED + f"Error parsing config.json: {e}")
    exit(1)

JWT       = cfg.get("JWT")
UID       = cfg.get("UID")
FROM_LANG = cfg.get("FROM", "en")
TO_LANG   = cfg.get("TO", "fr")

if not JWT or not UID:
    print(Fore.RED + "Please ensure JWT and UID are set in config.json.")
    exit(1)

HEADERS = {
    "authorization":             f"Bearer {JWT}",
    "cookie":                    f"jwt_token={JWT}",
    "connection":                "Keep-Alive",
    "content-type":              "application/json",
    "user-agent":                "Duolingo-Storm/1.0",
    "device-platform":           "web",
    "x-duolingo-device-platform":"web",
    "x-duolingo-app-version":     "1.0.0",
    "x-duolingo-application":     "chrome",
    "x-duolingo-client-version":  "web",
    "accept":                    "application/json"
}

BASE_URL     = "https://www.duolingo.com/2017-06-30"
PROFILE_URL  = f"{BASE_URL}/users/{UID}"
SESSIONS_URL = f"{BASE_URL}/sessions"
STORIES_URL  = "https://stories.duolingo.com/api2/stories"

gem_rewards = [
    "SKILL_COMPLETION_BALANCED-…-2-GEMS",
    "SKILL_COMPLETION_BALANCED-…-2-GEMS"
]

CHALLENGE_TYPES = [
    "assist","characterIntro","characterMatch","characterPuzzle","characterSelect",
    "characterTrace","characterWrite","completeReverseTranslation","definition",
    "dialogue","extendedMatch","extendedListenMatch","form","freeResponse","gapFill",
    "judge","listen","listenComplete","listenMatch","match","name","listenComprehension",
    "listenIsolation","listenSpeak","listenTap","orderTapComplete","partialListen",
    "partialReverseTranslate","patternTapComplete","radioBinary","radioImageSelect",
    "radioListenMatch","radioListenRecognize","radioSelect","readComprehension",
    "reverseAssist","sameDifferent","select","selectPronunciation","selectTranscription",
    "svgPuzzle","syllableTap","syllableListenTap","speak","tapCloze","tapClozeTable",
    "tapComplete","tapCompleteTable","tapDescribe","translate","transliterate",
    "transliterationAssist","typeCloze","typeClozeTable","typeComplete","typeCompleteTable",
    "writeComprehension"
]

def farm_xp(count, headers, from_lang, to_lang, slug):
    total_xp = 0
    print(Fore.LIGHTYELLOW_EX + f"\nStarting XP farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for _ in tqdm(range(count), desc="XP Loops", unit="loop"):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "awardXp": True,
            "completedBonusChallenge": True,
            "fromLanguage": from_lang,
            "learningLanguage": to_lang,
            "hasXpBoost": False,
            "illustrationFormat": "svg",
            "isFeaturedStoryInPracticeHub": True,
            "isLegendaryMode": True,
            "isV2Redo": False,
            "isV2Story": False,
            "masterVersion": True,
            "maxScore": 0,
            "score": 0,
            "happyHourBonusXp": 469,
            "startTime": now_ts,
            "endTime": now_ts
        }
        r = requests.post(f"{STORIES_URL}/{slug}/complete", headers=headers, json=payload)
        if r.status_code != 200:
            print(Fore.RED + f"Error {r.status_code} while farming XP")
            break
        total_xp += r.json().get("awardedXp", 0)
        time.sleep(SLEEP_TIME)
    print(Fore.GREEN + f"\nXP Farming complete. Total XP: {total_xp}\n")

def farm_gems(count, headers, uid, from_lang, to_lang):
    total_gems = 0
    print(Fore.LIGHTYELLOW_EX + f"\nStarting Gem farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for _ in tqdm(range(count), desc="Gem Loops", unit="loop"):
        random.shuffle(gem_rewards)
        for reward in gem_rewards:
            url = f"{BASE_URL}/users/{uid}/rewards/{reward}"
            payload = {
                "consumed": True,
                "fromLanguage": from_lang,
                "learningLanguage": to_lang
            }
            r = requests.patch(url, headers=headers, json=payload)
            if r.status_code != 200:
                print(Fore.RED + f"Failed to redeem {reward} — {r.status_code}")
        total_gems += 120
        time.sleep(SLEEP_TIME)
    print(Fore.GREEN + f"\nGem Farming complete. Total Gems: {total_gems}\n")

def fetch_streak_start():
    r = requests.get(PROFILE_URL, headers=HEADERS)
    r.raise_for_status()
    info = r.json()
    start = info.get("streakData", {}).get("currentStreak", {}).get("startDate")
    if start:
        return datetime.strptime(start, "%Y-%m-%d")
    else:
        return datetime.now()

def farm_streak(days):
    start_date = fetch_streak_start()
    print(Fore.LIGHTYELLOW_EX + f"\nStarting streak farm from {start_date.date()} (going backwards)\n")
    pbar = tqdm(range(days), desc="Streak Loops", unit="day")
    for i in pbar:
        sim_day = start_date - timedelta(days=i)
        post_payload = {
            "challengeTypes":   CHALLENGE_TYPES,
            "fromLanguage":     FROM_LANG,
            "learningLanguage": TO_LANG,
            "isFinalLevel":     False,
            "isV2":             True,
            "juicy":            True,
            "smartTipsVersion": 2,
            "type":             "GLOBAL_PRACTICE"
        }
        r1 = requests.post(SESSIONS_URL, headers=HEADERS, json=post_payload)
        if not r1.ok:
            pbar.set_postfix_str(f"POST failed {sim_day.date()}")
            time.sleep(SLEEP_TIME)
            continue
        data = r1.json()
        session_id = data.get("id")
        if not session_id:
            pbar.set_postfix_str(f"No ID {sim_day.date()}")
            time.sleep(SLEEP_TIME)
            continue
        start_ts = int((sim_day - timedelta(seconds=1)).timestamp())
        end_ts   = int(sim_day.timestamp())
        put_payload = {
            **data,
            "heartsLeft":        5,
            "startTime":         start_ts,
            "endTime":           end_ts,
            "enableBonusPoints": False,
            "failed":            False,
            "maxInLessonStreak": 9,
            "shouldLearnThings": True
        }
        r2 = requests.put(f"{SESSIONS_URL}/{session_id}", headers=HEADERS, json=put_payload)
        if r2.ok:
            pbar.set_postfix_str(f"{sim_day.date()} ✓")
        else:
            pbar.set_postfix_str(f"PUT fail {sim_day.date()}")
        time.sleep(SLEEP_TIME)
    pbar.close()
    print(Fore.GREEN + "\n🎉 Streak farming complete!\n")

if __name__ == "__main__":
    print(Fore.BLUE + r"""
 ____                    ____                             
/\  _`\                 /\  _`\             __            
\ \ \/\ \  __  __    ___\ \ \L\ \     __   /\_\    ___    
 \ \ \ \ \/\ \/\ \  / __`\ \ ,  /   /'__`\ \/\ \ /' _ `\  
  \ \ \_\ \ \ \_\ \/\ \L\ \ \ \\ \ /\ \L\.\_\ \ \/\ \/\ \ 
   \ \____/\ \____/\ \____/\ \_\ \_\ \__/.\_\\ \_\ \_\ \_\
    \/___/  \/___/  \/___/  \/_/\/_/\/__/\/_/ \/_/\/_/\/_/
""" + Fore.LIGHTBLACK_EX + "           ~ Storm 🌪️\n")

    raw = input("What do you want to farm? (xp/gems/streak): ")
    mode = raw.strip().lower()
    if mode.endswith('s'):
        mode = mode[:-1]

    if mode == "streak":
        prompt = "How many days you want to farm? "
    elif mode in ("xp", "gem"):
        prompt = "How many loops you want to farm? "
    else:
        print(Fore.RED + "Unknown option. Use 'xp', 'gems', or 'streak'.")
        exit(1)

    try:
        count = int(input(prompt).strip())
        if count < 1:
            raise ValueError
    except ValueError:
        print(Fore.RED + "Please enter a valid positive integer.")
        exit(1)

    if mode == "xp":
        STORY_SLUG = cfg.get("STORY_SLUG", "fr-en-le-passeport")
        farm_xp(count, HEADERS, FROM_LANG, TO_LANG, STORY_SLUG)
    elif mode == "gem":
        farm_gems(count, HEADERS, UID, FROM_LANG, TO_LANG)
    else:
        farm_streak(count)
