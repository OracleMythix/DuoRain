import requests,json,random,time,sys
from tqdm import tqdm
from datetime import datetime,timezone,timedelta
from colorama import Fore,init
import os,base64,calendar,pytz
from dateutil.relativedelta import relativedelta


init(autoreset=True)

#---SPEED---
SLEEP_TIME=0


# Self-updater
def normalize_code(lines):
return [l for l in lines if not l.strip().startswith("SLEEP_TIME=")]


def self_update():
url="https://raw.githubusercontent.com/OracleMythix/DuoRain/main/DuoRain.py"
try:
r=requests.get(url,timeout=15)
if r.status_code==200:
remote=r.text.strip().splitlines()
with open(__file__,"r",encoding="utf-8") as f: local=f.read().strip().splitlines()
if normalize_code(remote)!=normalize_code(local):
print(Fore.YELLOW+"Update found. Updating script...")
with open(__file__,"w",encoding="utf-8") as f: f.write("\n".join(remote))
print(Fore.GREEN+"Update applied. Please re-run the script.")
exit(0)
else:
print(Fore.GREEN+"Already up to date.")
else:
print(Fore.RED+f"Update check failed: {r.status_code}")
except Exception as e:
print(Fore.RED+f"Update error: {e}")


if "-m" in sys.argv:
try:
with open(__file__,"r",encoding="utf-8") as f: code=f.readlines()
new_code=[];skip=False
for line in code:
if "# Self-updater" in line: skip=True;continue
if skip and "self_update()" not in line and not line.strip().startswith("# Remove auto-update"):
continue
if "self_update()" in line: skip=False;continue
new_code.append(line)
with open(__file__,"w",encoding="utf-8") as f: f.writelines(new_code)
print(Fore.GREEN+"Auto-update code removed from this file.")
exit(0)
except Exception as e:
print(Fore.RED+f"Failed to remove auto-update: {e}");exit(1)


self_update()

if os.path.exists("config.json"):
    try:
        with open("config.json") as f: cfg=json.load(f)
    except json.JSONDecodeError as e:
        print(Fore.RED+f"Error parsing config.json: {e}");exit(1)
else:
    jwt=input("Enter your JWT: ").strip()
    try:
        payload=jwt.split('.')[1]
        padded=payload+'='*(-len(payload)%4)
        sub=json.loads(base64.urlsafe_b64decode(padded))["sub"]
    except Exception as e:
        print(Fore.RED+f"Failed to decode JWT: {e}");exit(1)
    HEADERS={
      "authorization":f"Bearer {jwt}","cookie":f"jwt_token={jwt}",
      "connection":"Keep-Alive","content-type":"application/json",
      "user-agent":"Duolingo-Storm/1.0","device-platform":"web",
      "x-duolingo-device-platform":"web","x-duolingo-app-version":"1.0.0",
      "x-duolingo-application":"chrome","x-duolingo-client-version":"web",
      "accept":"application/json"
    }
    r=requests.get(f"https://www.duolingo.com/2017-06-30/users/{sub}",headers=HEADERS)
    if r.status_code!=200:
        print(Fore.RED+f"Failed to fetch profile: {r.status_code}")
        print(r.text);exit(1)
    d=r.json()
    cfg={"JWT":jwt,"UID":sub,"FROM":d.get("fromLanguage","en"),"TO":d.get("learningLanguage","fr")}
    with open("config.json","w") as f: json.dump(cfg,f)

JWT=cfg.get("JWT")
UID=cfg.get("UID")
FROM_LANG=cfg.get("FROM","en")
TO_LANG=cfg.get("TO","fr")

if not JWT or not UID:
    print(Fore.RED+"Please ensure JWT and UID are set in config.json.");exit(1)

HEADERS={
"authorization":f"Bearer {JWT}","cookie":f"jwt_token={JWT}",
"connection":"Keep-Alive","content-type":"application/json",
"user-agent":"Duolingo-Storm/1.0","device-platform":"web",
"x-duolingo-device-platform":"web","x-duolingo-app-version":"1.0.0",
"x-duolingo-application":"chrome","x-duolingo-client-version":"web",
"accept":"application/json"
}

BASE_URL="https://www.duolingo.com/2017-06-30"
PROFILE_URL=f"{BASE_URL}/users/{UID}"
SESSIONS_URL=f"{BASE_URL}/sessions"
STORIES_URL="https://stories.duolingo.com/api2/stories"

gem_rewards=[
"SKILL_COMPLETION_BALANCED-…-2-GEMS","SKILL_COMPLETION_BALANCED-…-2-GEMS"
]

CHALLENGE_TYPES=[
"assist","characterIntro","characterMatch","characterPuzzle","characterSelect",
"characterTrace","characterWrite","completeReverseTranslation","definition","dialogue",
"extendedMatch","extendedListenMatch","form","freeResponse","gapFill","judge","listen",
"listenComplete","listenMatch","match","name","listenComprehension","listenIsolation",
"listenSpeak","listenTap","orderTapComplete","partialListen","partialReverseTranslate",
"patternTapComplete","radioBinary","radioImageSelect","radioListenMatch",
"radioListenRecognize","radioSelect","readComprehension","reverseAssist","sameDifferent",
"select","selectPronunciation","selectTranscription","svgPuzzle","syllableTap",
"syllableListenTap","speak","tapCloze","tapClozeTable","tapComplete","tapCompleteTable",
"tapDescribe","translate","transliterate","transliterationAssist","typeCloze",
"typeClozeTable","typeComplete","typeCompleteTable","writeComprehension"
]

def farm_xp(count, headers, from_lang, to_lang, slug):
    total_xp=0
    print(Fore.LIGHTYELLOW_EX+f"\nStarting XP farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for _ in tqdm(range(count),desc="XP Loops",unit="loop"):
        now_ts=int(datetime.now(timezone.utc).timestamp())
        duration=random.randint(300,420)
        payload={
         "awardXp":True,"completedBonusChallenge":True,
         "fromLanguage":from_lang,"learningLanguage":to_lang,
         "hasXpBoost":False,"illustrationFormat":"svg",
         "isFeaturedStoryInPracticeHub":True,"isLegendaryMode":True,
         "isV2Redo":False,"isV2Story":False,"masterVersion":True,
         "maxScore":0,"score":0,"happyHourBonusXp":469,
         "startTime":now_ts,"endTime":now_ts+duration
        }
        r=requests.post(f"{STORIES_URL}/{slug}/complete",headers=headers,json=payload)
        if r.status_code!=200:
            print(Fore.RED+f"Error {r.status_code} while farming XP");break
        total_xp+=r.json().get("awardedXp",0)
        time.sleep(SLEEP_TIME)
    print(Fore.GREEN+f"\nXP Farming complete. Total XP: {total_xp}\n")

def farm_gems(count,headers,uid,from_lang,to_lang):
    total_gems=0
    print(Fore.LIGHTYELLOW_EX+f"\nStarting Gem farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    for _ in tqdm(range(count),desc="Gem Loops",unit="loop"):
        random.shuffle(gem_rewards)
        for reward in gem_rewards:
            url=f"{BASE_URL}/users/{uid}/rewards/{reward}"
            payload={"consumed":True,"fromLanguage":from_lang,"learningLanguage":to_lang}
            r=requests.patch(url,headers=headers,json=payload)
            if r.status_code!=200:print(Fore.RED+f"Failed to redeem {reward} — {r.status_code}")
        total_gems+=120
        time.sleep(SLEEP_TIME)
    print(Fore.GREEN+f"\nGem Farming complete. Total Gems: {total_gems}\n")

def farm_streak(days):
    start_date=datetime.now()
    print(Fore.LIGHTYELLOW_EX+f"\nStarting streak farm from {start_date.date()} (going backwards)\n")
    pbar=tqdm(range(days),desc="Streak Loops",unit="day")
    for i in pbar:
        sim_day=start_date - timedelta(days=i)
        post_payload={
         "challengeTypes":CHALLENGE_TYPES,"fromLanguage":FROM_LANG,
         "learningLanguage":TO_LANG,"isFinalLevel":False,"isV2":True,
         "juicy":True,"smartTipsVersion":2,"type":"GLOBAL_PRACTICE"
        }
        r1=requests.post(SESSIONS_URL,headers=HEADERS,json=post_payload)
        if not r1.ok:
            pbar.set_postfix_str(f"POST failed {sim_day.date()}");time.sleep(SLEEP_TIME);continue
        data=r1.json();session_id=data.get("id")
        if not session_id:
            pbar.set_postfix_str(f"No ID {sim_day.date()}");time.sleep(SLEEP_TIME);continue
        start_ts=int((sim_day - timedelta(seconds=1)).timestamp())
        end_ts=int(sim_day.timestamp())
        put_payload={**data,
         "heartsLeft":5,"startTime":start_ts,"endTime":end_ts,
         "enableBonusPoints":False,"failed":False,"maxInLessonStreak":9,
         "shouldLearnThings":True
        }
        r2=requests.put(f"{SESSIONS_URL}/{session_id}",headers=HEADERS,json=put_payload)
        if r2.ok:pbar.set_postfix_str(f"{sim_day.date()} ✓")
        else:pbar.set_postfix_str(f"PUT fail {sim_day.date()}")
        time.sleep(SLEEP_TIME)
    pbar.close();print(Fore.GREEN+"\n🎉 Streak farming complete!\n")

def complete_every_quest(headers, uid):
    try:
        schema_url="https://goals-api.duolingo.com/schema?ui_language=en"
        r=requests.get(schema_url,headers=headers,timeout=15)
        if r.status_code!=200:
            print(Fore.RED+f"Failed to fetch schema: {r.status_code}");return
        schema=r.json()
        seen=set();metrics=[]
        for goal in schema.get("goals",[]):
            metric=goal.get("metric")
            if metric and metric not in seen:
                seen.add(metric);metrics.append(metric)
        if not metrics:
            print(Fore.YELLOW+"No metrics found in schema.");return
        profile_r=requests.get(f"{BASE_URL}/users/{uid}",headers=headers,timeout=15)
        timezone_str="UTC"
        if profile_r.ok:
            profile=profile_r.json()
            timezone_str=profile.get("timezone") or profile.get("tz") or "UTC"
        try:user_tz=pytz.timezone(timezone_str)
        except Exception:user_tz=pytz.timezone("UTC");timezone_str="UTC"
        now=datetime.now(user_tz)
        current_day=now.day;current_year=now.year;current_month=now.month
        start_date=datetime(current_year,current_month,current_day,tzinfo=user_tz)
        end_date=datetime(2021,1,current_day,tzinfo=user_tz)
        dates=[];temp=start_date
        while temp>=end_date:
            _,last_day=calendar.monthrange(temp.year,temp.month)
            actual_day=min(current_day,last_day)
            temp=temp.replace(day=actual_day)
            dates.append(temp)
            temp=temp-relativedelta(months=1)
        metric_updates=[{"metric":m,"quantity":2000} for m in metrics if m]
        if not any(mu["metric"]=="QUESTS" for mu in metric_updates):
            metric_updates.append({"metric":"QUESTS","quantity":1})
        url=f"https://goals-api.duolingo.com/users/{uid}/progress/batch"
        sent=0
        for target in dates:
            ts=target.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
            json_data={"metric_updates":metric_updates,"timestamp":ts,"timezone":timezone_str}
            resp=requests.post(url,headers=headers,json=json_data,timeout=15)
            if resp.status_code==200:sent+=1
            else:print(Fore.RED+f"POST {ts} failed: {resp.status_code}")
            time.sleep(1)
        if sent==0:
            print(Fore.YELLOW+"No quest updates were accepted.")
        else:
            print(Fore.GREEN+f"All quests completed. {sent} updates sent.")
    except Exception as e:
        print(Fore.RED+f"Error during quest completion: {e}")

if __name__=="__main__":
    print(Fore.BLUE+r"""
 ____                    ____                             
/\  _`\                 /\  _`\             __            
\ \ \/\ \  __  __    ___\ \ \L\ \     __   /\_\    ___    
 \ \ \ \ \/\ \/\ \  / __`\\ \ ,  /   /'__`\ \/\ \ /' _ `\  
  \ \ \_\ \ \ \_\ \/\ \L\ \\ \ \\ \ /\ \L\.\_\ \ \/\ \/\ \ 
   \ \____/\ \____/\ \____/\ \_\ \_\\ \__/\.\\ \_\ \_\ \_\
    \/___/  \/___/  \/___/  \/_/\/_/ \/__/\/_/ \/_/\/_/\/_/
"""+Fore.LIGHTBLACK_EX+"           ~ Storm 🌪️\n")

    raw=input("What do you want? (xp/gems/streak/every quest): ").strip().lower()
    if raw.endswith('s'): raw=raw[:-1]
    if "quest" in raw or raw=="every":
        confirm=input("Do you want to complete every quest (Y/n)? ").strip().lower()
        if confirm in ("y","yes",""):
            complete_every_quest(HEADERS,UID)
        else:
            print(Fore.YELLOW+"Cancelled quest completion.")
        exit(0)

    if raw=="streak":
        prompt="How many days you want to farm? "
    elif raw in("xp","gem"):
        prompt="How many loops you want to farm? "
    else:
        print(Fore.RED+"Unknown option. Use 'xp', 'gems', 'streak', or 'every quest'.");exit(1)

    try:
        count=int(input(prompt).strip())
        if count<1:raise ValueError
    except ValueError:
        print(Fore.RED+"Please enter a valid positive integer.");exit(1)

    if raw=="xp":
        STORY_SLUG=cfg.get("STORY_SLUG","fr-en-le-passeport")
        farm_xp(count,HEADERS,FROM_LANG,TO_LANG,STORY_SLUG)
    elif raw=="gem":
        farm_gems(count,HEADERS,UID,FROM_LANG,TO_LANG)
    else:
        farm_streak(count)
