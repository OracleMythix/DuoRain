import requests
import json
import random
import time
import sys
import os
import base64
import calendar
import traceback
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, SpinnerColumn, MofNCompleteColumn
from rich.layout import Layout
from rich.align import Align
from rich.live import Live
from rich.style import Style
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.rule import Rule
from rich.columns import Columns
from rich.status import Status

import pytz
from dateutil.relativedelta import relativedelta
from tzlocal import get_localzone

console = Console()

VERSION = "v2.0"
TIMEZONE = str(get_localzone())
CFG_FILE = "config.json"
DEBUG = False

BASE_URL = "https://www.duolingo.com/2017-06-30"
SESSIONS_URL = f"{BASE_URL}/sessions"
STORIES_URL = "https://stories.duolingo.com/api2/stories"
GOALS_API_URL = "https://goals-api.duolingo.com"
LEADERBOARDS_URL = "https://duolingo-leaderboards-prod.duolingo.com/leaderboards/7d9f5dd1-8423-491a-91f2-2532052038ce"

gem_rewards = [
    "SKILL_COMPLETION_BALANCED-…-2-GEMS", "SKILL_COMPLETION_BALANCED-…-2-GEMS"
]

CHALLENGE_TYPES = [
    "assist", "characterIntro", "characterMatch", "characterPuzzle", "characterSelect",
    "characterTrace", "characterWrite", "completeReverseTranslation", "definition", "dialogue",
    "extendedMatch", "extendedListenMatch", "form", "freeResponse", "gapFill", "judge", "listen",
    "listenComplete", "listenMatch", "match", "name", "listenComprehension", "listenIsolation",
    "listenSpeak", "listenTap", "orderTapComplete", "partialListen", "partialReverseTranslate",
    "patternTapComplete", "radioBinary", "radioImageSelect", "radioListenMatch",
    "radioListenRecognize", "radioSelect", "readComprehension", "reverseAssist", "sameDifferent",
    "select", "selectPronunciation", "selectTranscription", "svgPuzzle", "syllableTap",
    "syllableListenTap", "speak", "tapCloze", "tapClozeTable", "tapComplete", "tapCompleteTable",
    "tapDescribe", "translate", "transliterate", "transliterationAssist", "typeCloze",
    "typeClozeTable", "typeComplete", "typeCompleteTable", "writeComprehension"
]

def getch():
    try:
        import msvcrt
        return msvcrt.getch().decode('utf-8')
    except ImportError:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def check_stop_key():
    try:
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            return key == 'z'
    except ImportError:
        import sys
        import select
        import termios
        import tty
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(sys.stdin.fileno())
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                key = sys.stdin.read(1).lower()
                return key == 'z'
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return False

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def title_string():
    duo_part = "[bold white]Duo[/]"
    rain_part = "[bright_blue]Rain[/]"
    space_part = " "
    version_part = f"[white]{VERSION}[/]"
    
    full_markup_text = duo_part + rain_part + space_part + version_part
    
    plain_text_length = len(f"DuoRain {VERSION}")
    
    box_inner_width = 62
    
    padding = (box_inner_width - 2 - plain_text_length) // 2
    
    padded_title_markup = " " * padding + full_markup_text
    
    logo = f"""
  [bold white]╔══════════════════════════════════════════════════════════════╗[/]
  [bold white]║                                                              ║[/]
  [bold white]║{padded_title_markup}                          ║[/]
  [bold white]║                                                              ║[/]
  [bold white]╚══════════════════════════════════════════════════════════════╝[/]
  """
    
    if DEBUG:
        logo += "\n  [bold magenta][Debug Mode Enabled][/]"
    
    return logo

def dashboard(acc, delay_sec):
    duo_info = get_duo_info(acc)
    
    stats_table = Table(title="User Statistics", show_header=True, header_style="bold magenta")
    stats_table.add_column("Stat", style="cyan", width=20)
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Username", acc['username'])
    stats_table.add_row("Learning Language", duo_info.get('learningLanguage', 'Unknown'))
    stats_table.add_row("From Language", duo_info.get('fromLanguage', 'Unknown'))
    stats_table.add_row("Current Streak", str(duo_info.get('streak', 0)))
    stats_table.add_row("Total XP", str(duo_info.get('totalXp', 0)))
    stats_table.add_row("Gems", str(duo_info.get('gems', 0)))
    
    clear()
    console.print(title_string())
    console.print("\n")
    console.print(Panel(stats_table, title="[bold green]Account Dashboard[/]", border_style="green"))
    console.print("\n[yellow]Press Z to return to main menu[/]")
    
    while True:
        option = getch().upper()
        if option == 'Z':
            return

def get_headers(acc):
    jwt = acc['token']
    return {
        "authorization": f"Bearer {jwt}",
        "cookie": f"jwt_token={jwt}",
        "connection": "Keep-Alive",
        "content-type": "application/json",
        "user-agent": "Duolingo-Storm/1.0",
        "device-platform": "web",
        "x-duolingo-device-platform": "web",
        "x-duolingo-app-version": "1.0.0",
        "x-duolingo-application": "chrome",
        "x-duolingo-client-version": "web",
        "accept": "application/json"
    }

def get_duo_info(acc):
    headers = get_headers(acc)
    url = f"{BASE_URL}/users/{acc['id']}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

def fetch_username_and_id(token):
    try:
        payload = token.split('.')[1]
        padded = payload + '=' * (-len(payload) % 4)
        sub = json.loads(base64.urlsafe_b64decode(padded))["sub"]
        
        headers = {
            "authorization": f"Bearer {token}",
            "cookie": f"jwt_token={token}",
            "connection": "Keep-Alive",
            "content-type": "application/json",
            "user-agent": "Duolingo-Storm/1.0",
            "device-platform": "web",
            "x-duolingo-device-platform": "web",
            "x-duolingo-app-version": "1.0.0",
            "x-duolingo-application": "chrome",
            "x-duolingo-client-version": "web",
            "accept": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/users/{sub}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "username": data.get("username", "Unknown"),
                "id": data.get("id", sub)
            }
        else:
            return f"[red]Failed to fetch user info: {response.status_code}[/]"
    except Exception as e:
        return f"[red]Error decoding token: {str(e)}[/]"

def farm_xp_thread(target_xp, headers, from_lang, to_lang, slug, delay_sec, results, thread_id):
    total_xp = 0
    start_time = time.time()
    
    max_xp_req = 499
    min_xp_req = 30
    if target_xp < min_xp_req:
        target_xp = min_xp_req
    
    max_req = target_xp // max_xp_req
    remain_xp = target_xp % max_xp_req
    
    if remain_xp > 0 and remain_xp < min_xp_req:
        if max_req > 0:
            max_req -= 1
            remain_xp += max_xp_req
    
    total_req = max_req + (1 if remain_xp >= min_xp_req else 0)
    
    results[thread_id] = {
        "task": "XP Farm",
        "total": total_req,
        "current": 0,
        "value": 0,
        "status": "Running",
        "start_time": start_time
    }
    
    try:
        for _ in range(max_req):
            if results[thread_id]["status"] == "Stopped":
                break
            
            now_ts = int(datetime.now(timezone.utc).timestamp())
            duration = random.randint(300, 420)
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
                "endTime": now_ts + duration
            }
            
            r = requests.post(f"{STORIES_URL}/{slug}/complete", headers=headers, json=payload)
            if r.status_code != 200:
                results[thread_id]["status"] = "Error"
                break
            
            award_xp = r.json().get("awardedXp", 0)
            total_xp += award_xp
            
            results[thread_id]["current"] += 1
            results[thread_id]["value"] = total_xp
            
            time.sleep(delay_sec)
        
        if remain_xp >= min_xp_req and results[thread_id]["status"] != "Stopped" and results[thread_id]["status"] != "Error":
            now_ts = int(datetime.now(timezone.utc).timestamp())
            duration = random.randint(300, 420)
            bonus_xp = max(0, remain_xp - min_xp_req)
            bonus_xp = min(bonus_xp, 469)
            
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
                "happyHourBonusXp": bonus_xp,
                "startTime": now_ts,
                "endTime": now_ts + duration
            }
            
            r = requests.post(f"{STORIES_URL}/{slug}/complete", headers=headers, json=payload)
            if r.status_code != 200:
                results[thread_id]["status"] = "Error"
            else:
                award_xp = r.json().get("awardedXp", 0)
                total_xp += award_xp
                
                results[thread_id]["current"] += 1
                results[thread_id]["value"] = total_xp
            
            time.sleep(delay_sec)
        
        if results[thread_id]["status"] != "Stopped" and results[thread_id]["status"] != "Error":
            results[thread_id]["status"] = "Complete"
                    
    except Exception:
        results[thread_id]["status"] = "Error"

def farm_gems_thread(count, headers, uid, from_lang, to_lang, delay_sec, results, thread_id):
    total_gems = 0
    start_time = time.time()
    
    results[thread_id] = {
        "task": "Gem Farm",
        "total": count,
        "current": 0,
        "value": 0,
        "status": "Running",
        "start_time": start_time
    }
    
    try:
        for _ in range(count):
            if results[thread_id]["status"] == "Stopped":
                break
            
            random.shuffle(gem_rewards)
            for reward in gem_rewards:
                url = f"{BASE_URL}/users/{uid}/rewards/{reward}"
                payload = {"consumed": True, "fromLanguage": from_lang, "learningLanguage": to_lang}
                r = requests.patch(url, headers=headers, json=payload)
                if r.status_code != 200:
                    results[thread_id]["status"] = "Error"
                    break
            
            total_gems += 60
            
            results[thread_id]["current"] += 1
            results[thread_id]["value"] = total_gems
            
            time.sleep(delay_sec)
            
        if results[thread_id]["status"] != "Stopped" and results[thread_id]["status"] != "Error":
            results[thread_id]["status"] = "Complete"
                    
    except Exception:
        results[thread_id]["status"] = "Error"

def streak_farm_thread(amount, acc, delay_sec, results, thread_id):
    duo_info = get_duo_info(acc)
    headers = get_headers(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    learn_lang = duo_info.get('learningLanguage', 'fr')

    streak_data = duo_info.get('streakData', {})
    current_streak = streak_data.get('currentStreak', {})

    user_tz = pytz.timezone(TIMEZONE)
    now = datetime.now(user_tz)
    day_cnt = 0
    start_time = time.time()
    success_cnt = 0
    error_cnt = 0

    if not current_streak:
        streak_start = now
    else:
        try:
            streak_start = datetime.strptime(current_streak.get('startDate'), "%Y-%m-%d")
        except:
            results[thread_id] = {
                "task": "Streak Farm",
                "total": amount,
                "current": 0,
                "value": 0,
                "status": "Error",
                "start_time": start_time,
                "error": "Maximum streak days reached"
            }
            return

    farm_start = streak_start - timedelta(days=1)
    
    results[thread_id] = {
        "task": "Streak Farm",
        "total": amount,
        "current": 0,
        "value": 0,
        "status": "Running",
        "start_time": start_time
    }

    try:
        while day_cnt < amount:
            if results[thread_id]["status"] == "Stopped":
                break
            
            sim_day = farm_start - timedelta(days=day_cnt)

            session_payload = {
                "challengeTypes": CHALLENGE_TYPES,
                "fromLanguage": from_lang,
                "isFinalLevel": False,
                "isV2": True,
                "juicy": True,
                "learningLanguage": learn_lang,
                "smartTipsVersion": 2,
                "type": "GLOBAL_PRACTICE"
            }
            
            response = requests.post(SESSIONS_URL, headers=headers, json=session_payload)

            if response.status_code == 200:
                session_data = response.json()
            else:
                results[thread_id]["status"] = "Error"
                break
            
            if 'id' not in session_data:
                results[thread_id]["status"] = "Error"
                break

            try:
                start_ts = int((sim_day - timedelta(seconds=1)).timestamp())
                end_ts = int(sim_day.timestamp())
            except ValueError:
                results[thread_id]["status"] = "Error"
                break

            update_payload = {
                **session_data,
                "heartsLeft": 5,
                "startTime": start_ts,
                "endTime": end_ts,
                "enableBonusPoints": False,
                "failed": False,
                "maxInLessonStreak": 9,
                "shouldLearnThings": True
            }
            
            response = requests.put(f"{SESSIONS_URL}/{session_data['id']}", headers=headers, json=update_payload)

            if response.status_code == 200:
                day_cnt += 1
                success_cnt += 1
                
                results[thread_id]["current"] = day_cnt
                results[thread_id]["value"] = day_cnt
            else:
                error_cnt += 1
                time.sleep(delay_sec)
        
        if results[thread_id]["status"] != "Stopped" and results[thread_id]["status"] != "Error":
            results[thread_id]["status"] = "Complete"
                    
    except Exception:
        results[thread_id]["status"] = "Error"

def multi_task_farm(acc, delay_sec):
    clear()
    console.print(title_string())
    console.print("\n  [bold bright_cyan]Multi-Task Farm[/]\n")
    console.print("  Select tasks to run simultaneously:\n")
    console.print("  [bright_yellow]1. XP Farm[/]")
    console.print("  [bright_cyan]2. Gem Farm[/]")
    console.print("  [bright_yellow]3. Streak Farm[/]")
    console.print("  [bright_green]4. Start All Tasks[/]")
    console.print("  [bright_red]0. Go Back[/]\n")
    
    selected_tasks = []
    
    while True:
        option = getch().upper()
        
        if option == '0':
            return
        elif option == '1':
            try:
                amount = int(input("Enter amount of XP [Enter to cancel]: "))
                if amount > 0:
                    selected_tasks.append(("xp", amount))
                    console.print(f"[bright_green]Added XP Farm ({amount} XP)[/]")
            except ValueError:
                pass
        elif option == '2':
            try:
                amount = int(input("Enter amount of Gem Loops [Enter to cancel]: "))
                if amount > 0:
                    selected_tasks.append(("gems", amount))
                    console.print(f"[bright_green]Added Gem Farm ({amount} loops)[/]")
            except ValueError:
                pass
        elif option == '3':
            try:
                amount = int(input("Enter amount of streak days [Enter to cancel]: "))
                if amount > 0:
                    selected_tasks.append(("streak", amount))
                    console.print(f"[bright_green]Added Streak Farm ({amount} days)[/]")
            except ValueError:
                pass
        elif option == '4':
            if not selected_tasks:
                console.print("[red]No tasks selected. Please select at least one task.[/]")
                continue
            break
    
    if not selected_tasks:
        return
    
    console.print("\n[yellow]Starting multi-task farming... Press 'Z' to stop all tasks.[/]")
    time.sleep(2)
    
    headers = get_headers(acc)
    duo_info = get_duo_info(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    to_lang = duo_info.get('learningLanguage', 'fr')
    story_slug = "fr-en-le-passeport"
    
    results = {}
    threads = []
    
    for i, (task_type, amount) in enumerate(selected_tasks):
        if task_type == "xp":
            thread = threading.Thread(
                target=farm_xp_thread,
                args=(amount, headers, from_lang, to_lang, story_slug, delay_sec, results, i)
            )
            threads.append(thread)
        elif task_type == "gems":
            thread = threading.Thread(
                target=farm_gems_thread,
                args=(amount, headers, acc['id'], from_lang, to_lang, delay_sec, results, i)
            )
            threads.append(thread)
        elif task_type == "streak":
            thread = threading.Thread(
                target=streak_farm_thread,
                args=(amount, acc, delay_sec, results, i)
            )
            threads.append(thread)
    
    for thread in threads:
        thread.start()
    
    try:
        with Live(console=console, refresh_per_second=4) as live:
            while any(thread.is_alive() for thread in threads):
                if check_stop_key():
                    for thread_id in results:
                        results[thread_id]["status"] = "Stopped"
                    console.print("\n[yellow]All tasks stopped by user (Z key pressed).[/]")
                    break
                
                table = Table(title="Multi-Task Farm Progress", show_header=True, header_style="bold magenta")
                table.add_column("Task", style="cyan", width=12)
                table.add_column("Progress", style="green")
                table.add_column("Value", style="yellow")
                table.add_column("Status", style="bold")
                table.add_column("Time", style="blue")
                
                for thread_id, result in results.items():
                    task = result["task"]
                    current = result["current"]
                    total = result["total"]
                    value = result["value"]
                    status = result["status"]
                    
                    if status == "Running":
                        status_style = "bright_yellow"
                    elif status == "Complete":
                        status_style = "bright_green"
                    elif status == "Stopped":
                        status_style = "bright_red"
                    else:
                        status_style = "red"
                    
                    progress = f"{current}/{total}"
                    
                    elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time() - result["start_time"]))
                    
                    table.add_row(
                        task,
                        progress,
                        str(value),
                        f"[{status_style}]{status}[/{status_style}]",
                        elapsed
                    )
                
                live.update(table)
                time.sleep(0.5)
        
        for thread in threads:
            thread.join()
        
        console.print("\n")
        console.print(Panel(
            "[bold green]✓ Multi-Task Farming Complete![/]\n\n"
            + "\n".join(
                f"[cyan]{result['task']}:[/] [bold white]{result['value']}[/] ([green]{result['current']}/{result['total']}[/])"
                for result in results.values()
            ),
            title="[bold green]Multi-Task Farm Results[/]",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        for thread_id in results:
            results[thread_id]["status"] = "Stopped"
        console.print("\n[yellow]Multi-task farming interrupted by user.[/]")
    
    console.print("[bright_yellow]Press any key to continue.[/]")
    getch()

def farm_xp(target_xp, headers, from_lang, to_lang, slug, delay_sec):
    total_xp = 0
    start_time = time.time()
    
    max_xp_req = 499
    min_xp_req = 30
    if target_xp < min_xp_req:
        target_xp = min_xp_req
        console.print(f"[yellow]Target XP adjusted to minimum limit: {min_xp_req}[/]")
    
    max_req = target_xp // max_xp_req
    remain_xp = target_xp % max_xp_req
    
    if remain_xp > 0 and remain_xp < min_xp_req:
        if max_req > 0:
            max_req -= 1
            remain_xp += max_xp_req
    
    total_req = max_req + (1 if remain_xp >= min_xp_req else 0)
    
    console.print(f"[bright_yellow]Starting XP farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]")
    console.print(f"[cyan]Target XP: {target_xp} | Calculated requests: {total_req}[/]")
    console.print(f"[yellow]Press 'Z' to stop farming[/]")
    
    try:
        with Live(console=console, refresh_per_second=10) as live:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40, style="bar.back", complete_style="bar.complete"),
                MofNCompleteColumn(),
                TextColumn("•"),
                TextColumn("[green]{task.fields[current]}[/] XP"),
                TextColumn("•"),
                TextColumn("[cyan]{task.fields[speed]}[/] XP/s"),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[bold green]Farming XP...[/]", 
                    total=total_req,
                    current=0,
                    speed="0.0"
                )
                
                for _ in range(max_req):
                    if check_stop_key():
                        console.print("\n[yellow]XP farming stopped by user (Z key pressed).[/]")
                        break
                    
                    now_ts = int(datetime.now(timezone.utc).timestamp())
                    duration = random.randint(300, 420)
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
                        "endTime": now_ts + duration
                    }
                    
                    r = requests.post(f"{STORIES_URL}/{slug}/complete", headers=headers, json=payload)
                    if r.status_code != 200:
                        console.print(f"[red]Error {r.status_code} while farming XP[/]")
                        break
                    
                    award_xp = r.json().get("awardedXp", 0)
                    total_xp += award_xp
                    
                    elapsed = time.time() - start_time
                    speed = total_xp / elapsed if elapsed > 0 else 0
                    
                    progress.update(
                        task, 
                        advance=1,
                        current=total_xp,
                        speed=f"{speed:.1f}"
                    )
                    
                    time.sleep(delay_sec)
                
                if remain_xp >= min_xp_req:
                    if check_stop_key():
                        console.print("\n[yellow]XP farming stopped by user (Z key pressed).[/]")
                    else:
                        now_ts = int(datetime.now(timezone.utc).timestamp())
                        duration = random.randint(300, 420)
                        bonus_xp = max(0, remain_xp - min_xp_req)
                        bonus_xp = min(bonus_xp, 469)
                        
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
                            "happyHourBonusXp": bonus_xp,
                            "startTime": now_ts,
                            "endTime": now_ts + duration
                        }
                        
                        r = requests.post(f"{STORIES_URL}/{slug}/complete", headers=headers, json=payload)
                        if r.status_code != 200:
                            console.print(f"[red]Error {r.status_code} while farming XP[/]")
                        else:
                            award_xp = r.json().get("awardedXp", 0)
                            total_xp += award_xp
                            
                            elapsed = time.time() - start_time
                            speed = total_xp / elapsed if elapsed > 0 else 0
                            
                            progress.update(
                                task, 
                                advance=1,
                                current=total_xp,
                                speed=f"{speed:.1f}"
                            )
                        
                        time.sleep(delay_sec)
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]XP farming interrupted by user.[/]")
    
    console.print(Panel(
        f"[bold green]✓ Farming Complete![/]\n\n"
        f"[cyan]Target XP:[/] [bold white]{target_xp}[/]\n"
        f"[cyan]Total XP Farmed:[/] [bold white]{total_xp}[/]\n"
        f"[cyan]Difference:[/] [bold white]{total_xp - target_xp:+d}[/]\n"
        f"[cyan]Time Elapsed:[/] [bold white]{time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}[/]",
        title="[bold green]XP Farm Results[/]",
        border_style="green"
    ))

def farm_gems(count, headers, uid, from_lang, to_lang, delay_sec):
    total_gems = 0
    start_time = time.time()
    
    console.print(f"[bright_yellow]Starting Gem farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]")
    console.print(f"[yellow]Press 'Z' to stop farming[/]")
    
    try:
        with Live(console=console, refresh_per_second=10) as live:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40, style="bar.back", complete_style="bar.complete"),
                MofNCompleteColumn(),
                TextColumn("•"),
                TextColumn("[green]{task.fields[current]}[/] Gems"),
                TextColumn("•"),
                TextColumn("[cyan]{task.fields[speed]}[/] Gems/min"),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[bold cyan]Farming Gems...[/]", 
                    total=count,
                    current=0,
                    speed="0.0"
                )
                
                for _ in range(count):
                    if check_stop_key():
                        console.print("\n[yellow]Gem farming stopped by user (Z key pressed).[/]")
                        break
                    
                    random.shuffle(gem_rewards)
                    for reward in gem_rewards:
                        url = f"{BASE_URL}/users/{uid}/rewards/{reward}"
                        payload = {"consumed": True, "fromLanguage": from_lang, "learningLanguage": to_lang}
                        r = requests.patch(url, headers=headers, json=payload)
                        if r.status_code != 200:
                            console.print(f"[red]Failed to redeem {reward} — {r.status_code}[/]")
                    
                    total_gems += 60
                    
                    elapsed = time.time() - start_time
                    speed = (total_gems / elapsed) * 60 if elapsed > 0 else 0
                    
                    progress.update(
                        task, 
                        advance=1,
                        current=total_gems,
                        speed=f"{speed:.1f}"
                    )
                    
                    time.sleep(delay_sec)
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Gem farming interrupted by user.[/]")
    
    console.print(Panel(
        f"[bold green]✓ Farming Complete![/]\n\n"
        f"[cyan]Total Gems Farmed:[/] [bold white]{total_gems}[/]\n"
        f"[cyan]Time Elapsed:[/] [bold white]{time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}[/]",
        title="[bold cyan]Gem Farm Results[/]",
        border_style="cyan"
    ))

def streak_farm(amount, acc, delay_sec):
    duo_info = get_duo_info(acc)
    headers = get_headers(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    learn_lang = duo_info.get('learningLanguage', 'fr')

    streak_data = duo_info.get('streakData', {})
    current_streak = streak_data.get('currentStreak', {})

    user_tz = pytz.timezone(TIMEZONE)
    now = datetime.now(user_tz)
    day_cnt = 0
    start_time = time.time()
    success_cnt = 0
    error_cnt = 0

    if not current_streak:
        streak_start = now
    else:
        try:
            streak_start = datetime.strptime(current_streak.get('startDate'), "%Y-%m-%d")
        except:
            console.print("[yellow]You have already reached the maximum amount of streak days possible![/]")
            return

    farm_start = streak_start - timedelta(days=1)
    
    console.print(f"[bright_yellow]Starting Streak farm at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]")
    console.print(f"[cyan]Streak started on: {streak_start.strftime('%Y-%m-%d')}[/]")
    console.print(f"[cyan]Starting farm from: {farm_start.strftime('%Y-%m-%d')}[/]")
    console.print(f"[yellow]Press 'Z' to stop farming[/]")

    try:
        with Live(console=console, refresh_per_second=10) as live:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40, style="bar.back", complete_style="bar.complete"),
                MofNCompleteColumn(),
                TextColumn("•"),
                TextColumn("[green]{task.fields[current_date]}[/]"),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[bold yellow]Farming Streak...[/]", 
                    total=amount,
                    current_date=""
                )
                
                while day_cnt < amount:
                    if check_stop_key():
                        console.print("\n[yellow]Streak farming stopped by user (Z key pressed).[/]")
                        break
                    
                    sim_day = farm_start - timedelta(days=day_cnt)

                    session_payload = {
                        "challengeTypes": CHALLENGE_TYPES,
                        "fromLanguage": from_lang,
                        "isFinalLevel": False,
                        "isV2": True,
                        "juicy": True,
                        "learningLanguage": learn_lang,
                        "smartTipsVersion": 2,
                        "type": "GLOBAL_PRACTICE"
                    }
                    
                    response = requests.post(SESSIONS_URL, headers=headers, json=session_payload)

                    if response.status_code == 200:
                        session_data = response.json()
                    else:
                        console.print("[red]An error has occurred while trying to create a session.[/]")
                        if DEBUG:
                            console.print(f"[dim]{response.text}[/]")
                        return
                    
                    if 'id' not in session_data:
                        console.print("[red]Session ID not found in response data.[/]")
                        if DEBUG:
                            console.print(f"[dim]{response.text}[/]")
                        return

                    try:
                        start_ts = int((sim_day - timedelta(seconds=1)).timestamp())
                        end_ts = int(sim_day.timestamp())
                    except ValueError:
                        return

                    update_payload = {
                        **session_data,
                        "heartsLeft": 5,
                        "startTime": start_ts,
                        "endTime": end_ts,
                        "enableBonusPoints": False,
                        "failed": False,
                        "maxInLessonStreak": 9,
                        "shouldLearnThings": True
                    }
                    
                    response = requests.put(f"{SESSIONS_URL}/{session_data['id']}", headers=headers, json=update_payload)

                    if response.status_code == 200:
                        day_cnt += 1
                        success_cnt += 1
                        
                        progress.update(
                            task, 
                            completed=day_cnt,
                            current_date=sim_day.strftime("%Y-%m-%d")
                        )
                    else:
                        error_cnt += 1
                        if DEBUG:
                            console.print(f"[red]Failed to extend streak ({response.status_code})[/]")
                            console.print(f"[dim]{response.text}[/]")
                        time.sleep(delay_sec)
    except KeyboardInterrupt:
        console.print("\n[yellow]Streak farming interrupted by user.[/]")
    
    console.print(Panel(
        f"[bold green]✓ Farming Complete![/]\n\n"
        f"[cyan]Total Days Farmed:[/] [bold white]{day_cnt}[/]\n"
        f"[cyan]Successful Requests:[/] [bold green]{success_cnt}[/]\n"
        f"[cyan]Failed Requests:[/] [bold red]{error_cnt}[/]\n"
        f"[cyan]Time Elapsed:[/] [bold white]{time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}[/]",
        title="[bold yellow]Streak Farm Results[/]",
        border_style="yellow"
    ))

def activate_super(acc):
    url = f"{BASE_URL}/users/{acc['id']}/shop-items"
    headers = get_headers(acc)
    json_data = {"itemName":"immersive_subscription","productId":"com.duolingo.immersive_free_trial_subscription"}

    with console.status("[bold green]Activating Super Duolingo...", spinner="dots"):
        response = requests.post(url, headers=headers, json=json_data)
    
    try:
        res_json = response.json()
    except requests.exceptions.JSONDecodeError:
        console.print(Panel(
            "[red]Failed to extract JSON data in response.[/]\n"
            f"[yellow]Status code: {response.status_code}[/]",
            title="[bold red]Activation Failed[/]",
            border_style="red"
        ))
        if DEBUG:
            console.print(f"[dim]{response.text}[/]")
        return
    
    if response.status_code == 200 and "purchaseId" in res_json:
        console.print(Panel(
            "[bold green]✓ Successfully activated 3 days of Duolingo Super![/]\n\n"
            "[yellow]Note: You most likely didn't actually get Duolingo Super\n"
            "due to Duolingo's new detection system.[/]",
            title="[bold green]Activation Successful[/]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[red]Failed to activate 3 days of Duolingo Super.[/]",
            title="[bold red]Activation Failed[/]",
            border_style="red"
        ))
    
    if DEBUG:
        console.print(f"[dim]{response.text}[/]")

def give_item(acc, item):
    item_id = item[0]
    item_name = item[1]
    headers = get_headers(acc)
    duo_info = get_duo_info(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    learn_lang = duo_info.get('learningLanguage', 'fr')

    with console.status(f"[bold green]Giving {item_name}...", spinner="dots"):
        #(iOS API)
        if item_id == "xp_boost_refill":
            inner_body = {
                "isFree": False,
                "learningLanguage": learn_lang,
                "subscriptionFeatureGroupId": 0,
                "xpBoostSource": "REFILL",
                "xpBoostMinutes": 15,
                "xpBoostMultiplier": 3,
                "id": item_id
            }
            payload = {
                "includeHeaders": True,
                "requests": [
                    {
                        "url": f"/2023-05-23/users/{acc['id']}/shop-items",
                        "extraHeaders": {},
                        "method": "POST",
                        "body": json.dumps(inner_body)
                    }
                ]
            }
            url = "https://ios-api-2.duolingo.com/2023-05-23/batch"
            headers["host"] = "ios-api-2.duolingo.com"
            headers["x-amzn-trace-id"] = f"User={acc['id']}"
            data = payload
        else:
            data = {
                "itemName": item_id,
                "isFree": True,
                "consumed": True,
                "fromLanguage": from_lang,
                "learningLanguage": learn_lang
            }
            url = f"{BASE_URL}/users/{acc['id']}/shop-items"

        response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        console.print(Panel(
            f"[bold green]✓ Successfully received \"{item_name}\"![/]",
            title="[bold green]Item Received[/]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[red]Failed to receive \"{item_name}\".[/]\n"
            f"[yellow]Status code: {response.status_code}[/]",
            title="[bold red]Failed[/]",
            border_style="red"
        ))
    
    if DEBUG:
        console.print(f"[dim]{response.text}[/]")

def complete_quests(acc):
    headers = get_headers(acc)
    duo_info = get_duo_info(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    learn_lang = duo_info.get('learningLanguage', 'fr')

    try:
        with console.status("[bold green]Fetching quest schema...", spinner="dots"):
            schema_url = f"{GOALS_API_URL}/schema?ui_language=en"
            response = requests.get(schema_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            console.print(f"[red]Failed to fetch schema: {response.status_code}[/]")
            return
            
        schema = response.json()
        
        seen = set()
        metrics = []
        
        for goal in schema.get("goals", []):
            metric = goal.get("metric")
            if metric and metric not in seen:
                seen.add(metric)
                metrics.append(metric)
                
        if not metrics:
            console.print("[yellow]No metrics found in schema.[/]")
            return
            
        with console.status("[bold green]Fetching user profile...", spinner="dots"):
            profile_resp = requests.get(f"{BASE_URL}/users/{acc['id']}", headers=headers, timeout=15)
        
        timezone_str = "UTC"
        
        if profile_resp.ok:
            profile = profile_resp.json()
            timezone_str = profile.get("timezone") or profile.get("tz") or "UTC"
            
        try:
            user_tz = pytz.timezone(timezone_str)
        except Exception:
            user_tz = pytz.timezone("UTC")
            timezone_str = "UTC"
            
        now = datetime.now(user_tz)
        current_day = now.day
        current_year = now.year
        current_month = now.month
        
        start_date = datetime(current_year, current_month, current_day, tzinfo=user_tz)
        end_date = datetime(2021, 1, current_day, tzinfo=user_tz)
        
        dates = []
        temp = start_date
        
        while temp >= end_date:
            _, last_day = calendar.monthrange(temp.year, temp.month)
            actual_day = min(current_day, last_day)
            temp = temp.replace(day=actual_day)
            dates.append(temp)
            temp = temp - relativedelta(months=1)
            
        metric_updates = [{"metric": m, "quantity": 2000} for m in metrics if m]
        
        if not any(mu["metric"] == "QUESTS" for mu in metric_updates):
            metric_updates.append({"metric": "QUESTS", "quantity": 1})
            
        url = f"{GOALS_API_URL}/users/{acc['id']}/progress/batch"
        sent = 0
        start_time = time.time()
        
        console.print(f"[bright_yellow]Starting Quest completion at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]")
        console.print(f"[yellow]Press 'Z' to stop farming[/]")
        
        with Live(console=console, refresh_per_second=10) as live:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40, style="bar.back", complete_style="bar.complete"),
                MofNCompleteColumn(),
                TextColumn("•"),
                TextColumn("[green]{task.fields[sent]}[/] Updates"),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task(
                    f"[bold pink1]Completing Quests...[/]", 
                    total=len(dates),
                    sent=0
                )
                
                for target in dates:
                    if check_stop_key():
                        console.print("\n[yellow]Quest completion stopped by user (Z key pressed).[/]")
                        break
                    
                    ts = target.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                    json_data = {
                        "metric_updates": metric_updates,
                        "timestamp": ts,
                        "timezone": timezone_str
                    }
                    
                    response = requests.post(url, headers=headers, json=json_data, timeout=15)
                    
                    if response.status_code == 200:
                        sent += 1
                        progress.update(task, advance=1, sent=sent)
                    else:
                        progress.update(task, advance=1)
                        if DEBUG:
                            console.print(f"[red]POST {ts} failed: {response.status_code}[/]")
                            console.print(f"[dim]{response.text}[/]")
                    
                    time.sleep(1)
                
        console.print(Panel(
            f"[bold green]✓ Quest Completion Complete![/]\n\n"
            f"[cyan]Updates Sent:[/] [bold green]{sent}[/]\n"
            f"[cyan]Total Dates:[/] [bold white]{len(dates)}[/]\n"
            f"[cyan]Time Elapsed:[/] [bold white]{time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}[/]",
            title="[bold pink1]Quest Results[/]",
            border_style="pink1"
        ))
            
    except Exception as e:
        console.print(Panel(
            f"[red]Error during quest completion: {e}[/]",
            title="[bold red]Error[/]",
            border_style="red"
        ))
        if DEBUG:
            traceback.print_exc()

def get_current_league_pos(acc):
    headers = get_headers(acc)
    duo_id = int(acc['id'])

    url = (f"{LEADERBOARDS_URL}/users/{duo_id}"
           f"?client_unlocked=true&get_reactions=true&_={int(time.time() * 1000)}")
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        if DEBUG:
            console.print(
                f"[bold magenta][DEBUG][/] Failed to fetch user data on leaderboard\n"
                f"[bold magenta][DEBUG][/] Status code: {response.status_code}\n"
                f"[bold magenta][DEBUG][/] Content: {response.text}"
            )
        return None
    
    leaderboard_data = response.json()
    if not leaderboard_data or 'active' not in leaderboard_data:
        return None
    
    active_data = leaderboard_data.get('active', None)
    if active_data is None or 'cohort' not in active_data:
        return None
    
    cohort_data = active_data.get('cohort', {})
    rankings = cohort_data.get('rankings', [])
    current_user = next((user_data for user_data in rankings if user_data['user_id'] == duo_id), None)
    
    if current_user is None:
        return None
    
    current_rank = next((index + 1 for index, user_data in enumerate(rankings) if user_data['user_id'] == duo_id), None)
    return current_rank

def league_registration(acc):
    if DEBUG:
        console.print(f"[bold magenta][DEBUG][/] Attempting to enter a leaderboard for {acc['username']}")
    duo_id = int(acc['id'])
    headers = get_headers(acc)

    url = f"{BASE_URL}/users/{duo_id}/privacy-settings"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        console.print(f"[red]Failed to get privacy settings.[/]")
        if DEBUG:
            console.print(
                f"[bold magenta][DEBUG][/] Status code: {response.status_code}\n"
                f"[bold magenta][DEBUG][/] Content: {response.text}"
            )
        return
    if DEBUG:
        console.print(f"[bold magenta][DEBUG][/] Fetched privacy settings")
    data = response.json()
    privacy_settings = data.get('privacySettings', [])
    social_setting = next((setting for setting in privacy_settings if setting['id'] == 'disable_social'), None)
    was_private = social_setting['enabled'] if social_setting else False
    if DEBUG:
        console.print(f"[bold magenta][DEBUG][/] {was_private = }")

    if was_private:
        url = f"{BASE_URL}/users/{duo_id}/privacy-settings?fields=privacySettings"
        payload = {"DISABLE_SOCIAL": False}
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code != 200:
            console.print(f"[red]Failed to set profile to public.[/]")
            if DEBUG:
                console.print(
                    f"[bold magenta][DEBUG][/] Status code: {response.status_code}\n"
                    f"[bold magenta][DEBUG][/] Content: {response.text}"
                )
            return
        if DEBUG:
            console.print(f"[bold magenta][DEBUG][/] Set profile to public")

        time.sleep(2)

    duo_info = get_duo_info(acc)
    from_lang = duo_info.get('fromLanguage', 'en')
    to_lang = duo_info.get('learningLanguage', 'fr')
    story_slug = "fr-en-le-passeport"
    farm_xp(30, headers, from_lang, to_lang, story_slug, 0.1)

    if was_private:
        url = f"{BASE_URL}/users/{duo_id}/privacy-settings?fields=privacySettings"
        payload = {"DISABLE_SOCIAL": True}
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code != 200:
            console.print(f"[red]Failed to restore privacy settings.[/]")
            if DEBUG:
                console.print(
                    f"[bold magenta][DEBUG][/] Status code: {response.status_code}\n"
                    f"[bold magenta][DEBUG][/] Content: {response.text}"
                )
            return

def save_league(acc, position, delay_sec):
    if DEBUG:
        console.print(f"[bold magenta][DEBUG][/] Checking league position for {acc['username']}")
    headers = get_headers(acc)
    duo_id = int(acc['id'])

    url = (f"{LEADERBOARDS_URL}/users/{duo_id}"
           f"?client_unlocked=true&get_reactions=true&_={int(time.time() * 1000)}")
    
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            if DEBUG:
                console.print(
                    f"[bold magenta][DEBUG][/] Failed to fetch user data on leaderboard\n"
                    f"[bold magenta][DEBUG][/] Status code: {response.status_code}\n"
                    f"[bold magenta][DEBUG][/] Content: {response.text}"
                )
            league_registration(acc)
            return
        leaderboard_data = response.json()
        if not leaderboard_data or 'active' not in leaderboard_data:
            league_registration(acc)
            return
        active_data = leaderboard_data.get('active', None)
        if active_data is None or 'cohort' not in active_data:
            league_registration(acc)
            return
        cohort_data = active_data.get('cohort', {})
        rankings = cohort_data.get('rankings', [])
        current_user = next((user_data for user_data in rankings if user_data['user_id'] == duo_id), None)
        if current_user is None:
            league_registration(acc)
            return

        current_score = current_user['score']
        current_rank = next((index + 1 for index, user_data in enumerate(rankings) if user_data['user_id'] == duo_id), None)
        if DEBUG:
            console.print(
                f"[bold magenta][DEBUG][/] {current_score = }\n"
                f"[bold magenta][DEBUG][/] {current_rank = }"
            )
        if current_rank is not None and current_rank <= position:
            break
        target_user = rankings[position - 1] if position and position - 1 < len(rankings) else None
        if DEBUG:
            console.print(f"[bold magenta][DEBUG][/] {target_user = }")
        if target_user is None:
            break
        target_score = target_user['score']
        xp_needed = (target_score - current_score) + 60
        if DEBUG:
            console.print(
                f"[bold magenta][DEBUG][/] {target_score = }\n"
                f"[bold magenta][DEBUG][/] {xp_needed = }"
            )
        if xp_needed > 0:
            if DEBUG:
                console.print(f"[bold magenta][DEBUG][/] Attempting to save league position")
            duo_info = get_duo_info(acc)
            from_lang = duo_info.get('fromLanguage', 'en')
            to_lang = duo_info.get('learningLanguage', 'fr')
            story_slug = "fr-en-le-passeport"
            farm_xp(xp_needed, headers, from_lang, to_lang, story_slug, delay_sec)
            console.print(f"[green]Saved league position![/]")

def auto_league_menu(acc, delay_sec):
    clear()
    console.print(title_string())
    console.print("\n  [bold bright_green]Auto League[/]\n")
    
    current_pos = get_current_league_pos(acc)
    
    if current_pos is None:
        console.print("[red]Failed to fetch current league position. Please try again later.[/]")
        console.print("\n[yellow]Press any key to continue.[/]")
        getch()
        return
    
    if current_pos == 1:
        console.print("[bright_green]✔ First position already achieved.[/]")
        console.print("\n[yellow]Press any key to continue.[/]")
        getch()
        return
    
    console.print("  What league position should be aimed for?\n")
    
    pos_options = {}
    for i in range(current_pos - 1, 0, -1):
        pos_options[str(i)] = i
        if i == 1:
            console.print(f"  [bright_green]{i}. First Position[/]")
        elif i == 2:
            console.print(f"  [bright_yellow]{i}. Second Position[/]")
        elif i == 3:
            console.print(f"  [orange1]{i}. Third Position[/]")
        else:
            console.print(f"  [bright_cyan]{i}. {i}th Position[/]")
    
    console.print("\n  [bright_red]0. Go Back[/]\n")
    
    while True:
        option = getch()
        
        if option == '0':
            return
        elif option in pos_options:
            target_pos = pos_options[option]
            save_league(acc, target_pos, delay_sec)
            console.print("\n[yellow]Press any key to continue.[/]")
            getch()
            return

def load_cfg():
    if os.path.exists(CFG_FILE):
        try:
            with open(CFG_FILE, "r") as f:
                cfg = json.load(f)
                if "loop_delay_ms" not in cfg:
                    cfg["loop_delay_ms"] = 100
                    save_cfg(cfg)
                return cfg
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing config file: {e}[/]")
            sys.exit(1)
    else:
        return create_cfg()

def create_cfg():
    console.print("[yellow]No configuration file found. Let's create one.[/]")
    jwt = input("Enter your JWT: ").strip()
    
    if not jwt:
        console.print("[red]JWT cannot be empty[/]")
        sys.exit(1)
        
    try:
        payload = jwt.split('.')[1]
        padded = payload + '=' * (-len(payload) % 4)
        sub = json.loads(base64.urlsafe_b64decode(padded))["sub"]
    except Exception as e:
        console.print(f"[red]Failed to decode JWT: {e}[/]")
        sys.exit(1)
        
    headers = {
        "authorization": f"Bearer {jwt}",
        "cookie": f"jwt_token={jwt}",
        "connection": "Keep-Alive",
        "content-type": "application/json",
        "user-agent": "Duolingo-Storm/1.0",
        "device-platform": "web",
        "x-duolingo-device-platform": "web",
        "x-duolingo-app-version": "1.0.0",
        "x-duolingo-application": "chrome",
        "x-duolingo-client-version": "web",
        "accept": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/users/{sub}", headers=headers)
    
    if response.status_code != 200:
        console.print(f"[red]Failed to fetch profile: {response.status_code}[/]")
        console.print(f"[dim]{response.text}[/]")
        sys.exit(1)
        
    profile = response.json()
    cfg = {
        "accounts": [
            {
                "username": profile.get("username", "Unknown"),
                "id": profile.get("id", sub),
                "token": jwt,
                "fromLanguage": profile.get("fromLanguage", "en"),
                "learningLanguage": profile.get("learningLanguage", "fr"),
                "autostreak": False
            }
        ],
        "debug": False,
        "loop_delay_ms": 100
    }
    
    save_cfg(cfg)
    return cfg

def save_cfg(cfg):
    with open(CFG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

def account_settings(acc, cfg):
    while True:
        clear()
        console.print(title_string())
        console.print(f"\n  [bold bright_green]Account Settings for {acc['username']}[/]")
        console.print("\n  [bright_cyan]1. Update Token[/]")
        console.print("  [bright_magenta]2. Switch Account[/]")
        console.print("  [bright_red]0. Go Back[/]\n")
        
        option = getch().upper()
        
        if option == '1':
            new_token = input("Enter your new token [Enter to cancel]: ").strip()
            if not new_token:
                continue
            
            console.print("[bright_yellow]Updating your account credentials, please wait...[/]", end='\r')
            new_acc = fetch_username_and_id(new_token)
            sys.stdout.write("\033[2K\r")
            sys.stdout.flush()
            
            if isinstance(new_acc, str):
                console.print(new_acc)
                console.print("[bright_yellow]Press any key to continue.[/]")
                getch()
                continue
            
            for i, a in enumerate(cfg['accounts']):
                if a['id'] == acc['id']:
                    cfg['accounts'][i]['username'] = new_acc['username']
                    cfg['accounts'][i]['id'] = new_acc['id']
                    cfg['accounts'][i]['token'] = new_token
                    acc = cfg['accounts'][i]
                    break
            
            console.print(f"[bright_green]Successfully updated account {new_acc['username']}![/]")
            console.print("[bright_yellow]Press any key to continue.[/]")
            getch()
        elif option == '2':
            return None
        elif option == '0':
            return acc

def switch_account(cfg):
    while True:
        clear()
        console.print(title_string())
        console.print("\n  [bright_magenta]Select Account:[/]")
        
        for i in range(len(cfg['accounts'])):
            current_marker = " [bright_green](Current)[/]" if cfg['accounts'][i]['id'] == cfg['current_account_id'] else ""
            console.print(f"  {i+1}: {cfg['accounts'][i]['username']}{current_marker}")
        
        console.print("\n  [bright_green]A. Add Account[/]")
        console.print("  [bright_red]0. Go Back[/]\n")
        
        try:
            option = getch().upper()
            
            if option == 'A':
                new_token = input("Enter your account's token [Enter to cancel]: ")
                if not new_token:
                    continue
                
                console.print("[bright_yellow]Adding your account, please wait...[/]", end='\r')
                new_acc = fetch_username_and_id(new_token)
                sys.stdout.write("\033[2K\r")
                sys.stdout.flush()
                
                if isinstance(new_acc, str):
                    console.print(new_acc)
                    console.print("[bright_yellow]Press any key to continue.[/]")
                    getch()
                    continue
                
                cfg['accounts'].append({
                    "username": new_acc['username'],
                    "id": new_acc['id'],
                    "token": new_token,
                    "fromLanguage": "en",
                    "learningLanguage": "fr",
                    "autostreak": False
                })
                
                console.print(f"[bright_green]Successfully added account {new_acc['username']}![/]")
                console.print("[bright_yellow]Press any key to continue.[/]")
                getch()
            elif option == '0':
                return None
            elif option.isdigit() and 1 <= int(option) <= len(cfg['accounts']):
                acc_index = int(option) - 1
                cfg['current_account_id'] = cfg['accounts'][acc_index]['id']
                return cfg['accounts'][acc_index]
        except (IndexError, ValueError):
            pass

def items_menu(acc):

    items = {
        # Streak Freeze Items
        "1": ("streak_freeze", "Streak Freeze"),
        "2": ("streak_freeze_gift", "Streak Freeze Gift"),
        "3": ("society_streak_freeze", "Society Streak Freeze"),
        "4": ("duo_streak_freeze", "Duo Streak Freeze"),
        "5": ("society_streak_freeze_refill", "Society Streak Freeze Refill"),
        
        # Health Items
        "6": ("health_shield", "Health Shield"),
        "7": ("heart_segment", "Heart Segment"),
        "8": ("heart_segment_reactive", "Heart Segment Reactive"),
        "9": ("health_refill", "Health Refill"),
        "A": ("health_refill_reactive", "Health Refill Reactive"),
        "B": ("health_refill_partial_1", "Health Refill Partial 1"),
        "C": ("health_refill_partial_2", "Health Refill Partial 2"),
        "D": ("health_refill_partial_3", "Health Refill Partial 3"),
        "E": ("health_refill_partial_4", "Health Refill Partial 4"),
        "F": ("health_refill_discounted", "Health Refill Discounted"),
        
        # XP Boosts
        "G": ("xp_boost_stackable", "XP Boost Stackable"),
        "H": ("general_xp_boost", "General XP Boost"),
        "I": ("xp_boost_15", "XP Boost 15 Min"),
        "J": ("xp_boost_60", "XP Boost 60 Min"),
        "K": ("unlimited_hearts_boost", "Unlimited Hearts Boost"),
        "L": ("early_bird_xp_boost", "Early Bird XP Boost"),
        "M": ("xp_boost_15_gift", "XP Boost 15 Min Gift"),
        "N": ("xp_boost_gift", "XP Boost Gift"),
        "O": ("xp_boost_refill", "XP Boost x3 15 Mins (iOS)"),
        
        # Tests/Challenges misc.
        "P": ("mastery_test", "Mastery Test"),
        "Q": ("skill_test", "Skill Test"),
        "R": ("skill_test_gems", "Skill Test Gems"),
        "S": ("skill_test_gems_200", "Skill Test Gems 200"),
        "T": ("levels_pacing_gems", "Levels Pacing Gems"),
        "U": ("hard_mode_gems_5", "Hard Mode Gems 5"),
        "V": ("hard_mode_gems_20", "Hard Mode Gems 20"),
        "W": ("hard_mode_gems_50", "Hard Mode Gems 50"),
        "X": ("mistakes_practice_gems_20", "Mistakes Practice Gems 20"),
        "Y": ("mistakes_practice_gems_200", "Mistakes Practice Gems 200"),
        "Z": ("mistakes_practice_gems_5", "Mistakes Practice Gems 5"),
        "a": ("mistakes_practice_gems_50", "Mistakes Practice Gems 50"),
        "b": ("pronunciation_review_10_pack", "Pronunciation Review 10 Pack"),
        "c": ("pronunciation_review_5_pack", "Pronunciation Review 5 Pack"),
        
        # Power-Ups misc.
        "d": ("row_blaster_150", "Row Blaster 150"),
        "e": ("row_blaster_250", "Row Blaster 250"),
        "f": ("legendary_keep_going", "Legendary Keep Going"),
        "g": ("side_quest_entry", "Side Quest Entry"),
        "h": ("daily_quest_reroll", "Daily Quest Reroll"),
        "i": ("bookshelf_chapter_unlock", "Bookshelf Chapter Unlock"),
        "j": ("final_level_attempt", "Final Level Attempt"),
        "k": ("ramp_up_entry", "Ramp Up Entry"),
        
        # Outfits misc.
        "l": ("formal_outfit", "Formal Attire"),
        "m": ("luxury_outfit", "Luxury Tracksuit"),
        
        # Gems Items
        "n": ("gem_timer_boosts_1_450", "Gem Timer Boosts 1"),
        "o": ("gem_timer_boosts_5_1800", "Gem Timer Boosts 5"),
        "p": ("gem_timer_boosts_15_4500", "Gem Timer Boosts 15"),
        "q": ("leaderboard_gem_wager_100", "Leaderboard Gem Wager 100"),
        "r": ("leaderboard_gem_wager_50", "Leaderboard Gem Wager 50"),
        "s": ("gem_wager", "Double or Nothing"),
        
        # Free Taste Items
        "t": ("roleplay_path_free_taste", "Roleplay Path Free Taste"),
        "u": ("video_call_path_free_taste", "Video Call Path Free Taste"),
        "v": ("guided_call_path_free_taste", "Guided Call Path Free Taste"),
    }
    
    categories = {
        "Streak Freeze Items": ["1", "2", "3", "4", "5"],
        "Health Items": ["6", "7", "8", "9", "A", "B", "C", "D", "E", "F"],
        "XP Boosts": ["G", "H", "I", "J", "K", "L", "M", "N", "O"],
        "Tests/Challenges misc.": ["P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "a", "b", "c"],
        "Power-Ups misc.": ["d", "e", "f", "g", "h", "i", "j", "k"],
        "Outfits misc.": ["l", "m"],
        "Gems Items": ["n", "o", "p", "q", "r", "s"],
        "Free Taste Items": ["t", "u", "v"]
    }
    
    category_colors = {
        "Streak Freeze Items": "[cyan]",
        "Health Items": "[red]",
        "XP Boosts": "[purple]",
        "Tests/Challenges misc.": "[green]",
        "Power-Ups misc.": "[green]",
        "Outfits misc.": "[green]",
        "Gems Items": "[cyan]",
        "Free Taste Items": "[green]"
    }
    
    while True:
        clear()
        console.print(title_string())
        console.print("\n  [bold bright_blue]Choose an item category:[/]")
        for i, (cat_name, item_keys) in enumerate(categories.items(), 1):
            color = category_colors[cat_name]
            console.print(f"  {color}{i}. {cat_name}[/]")
        
        console.print("  [bright_red]0. Go Back[/]\n")
        
        cat_option = getch().upper()
        
        if cat_option == '0':
            return
        
        try:
            cat_index = int(cat_option) - 1
            if 0 <= cat_index < len(categories):
                cat_name = list(categories.keys())[cat_index]
                item_keys = list(categories.values())[cat_index]
                color = category_colors[cat_name]
                
                while True:
                    clear()
                    console.print(title_string())
                    console.print(f"\n  {color}{cat_name}:[/]")
                    
                    for key in item_keys:
                        item_id, item_name = items[key]
                        console.print(f"  {color}{key}. {item_name}[/]")
                    
                    console.print("  [bright_red]0. Go Back[/]\n")
                    
                    item_option = getch().upper()
                    
                    if item_option == '0':
                        break
                    elif item_option in item_keys:
                        give_item(acc, items[item_option])
                        console.print("[bright_yellow]Press any key to continue.[/]")
                        getch()
            else:
                continue
        except ValueError:
            continue

def settings_menu(cfg):
    global DEBUG
    
    while True:
        clear()
        console.print(title_string())
        console.print("\n  [bold bright_blue]Settings:[/]")
        console.print("  1. Debug Mode: [bold bright_yellow]Toggle[/]")
        console.print(f"  2. Debug Status: {'[bright_green]Enabled[/]' if cfg['debug'] else '[bright_red]Disabled[/]'}")
        console.print(f"  3. Loop Delay (ms): [bold bright_yellow]{cfg['loop_delay_ms']}[/]")
        console.print("")
        console.print("  [bright_red]0. Go Back[/]\n")
        
        option = getch()
        
        if option == '1':
            DEBUG = cfg['debug'] = not cfg['debug']
            console.print(f"[bright_green]Debug mode {'enabled' if DEBUG else 'disabled'}[/]")
            console.print("[bright_yellow]Press any key to continue.[/]")
            getch()
        elif option == '3':
            try:
                new_delay = int(Prompt.ask("Enter new loop delay in milliseconds", default=str(cfg['loop_delay_ms'])))
                if new_delay < 0:
                    console.print("[red]Delay cannot be negative.[/]")
                else:
                    cfg['loop_delay_ms'] = new_delay
                    save_cfg(cfg)
                    console.print(f"[bright_green]Loop delay updated to {new_delay}ms.[/]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/]")
            console.print("[bright_yellow]Press any key to continue.[/]")
            getch()
        elif option == '0':
            return

def main_menu(acc, cfg):
    global DEBUG
    DEBUG = cfg.get('debug', False)
    loop_delay_ms = cfg.get('loop_delay_ms', 100)
    delay_sec = loop_delay_ms / 1000.0

    while True:
        clear()
        console.print(title_string())
        console.print(f"\n  [bold bright_green]Logged in as {acc['username']}[/]")
        console.print("\n  [bright_cyan]1. Dashboard[/]")
        console.print("  [bright_cyan]2. Account Settings[/]")
        console.print("  [bright_yellow]3. XP Farm[/]")
        console.print("  [bright_cyan]4. Gem Farm[/]")
        console.print("  [bright_yellow]5. Streak Farm[/]")
        console.print("  [bright_yellow]6. Auto League[/]")
        console.print("  [bright_magenta]7. Multi-Task Farm[/]")
        console.print("  [medium_purple1]8. More Options[/]")
        console.print("  [bright_blue]9. Settings[/]")
        console.print("  [bright_red]0. Quit[/]\n")
        
        option = getch().upper()
        
        if option == '1':
            dashboard(acc, delay_sec)
        elif option == '2':
            new_acc = account_settings(acc, cfg)
            if new_acc is None:
                new_acc = switch_account(cfg)
                if new_acc:
                    acc = new_acc
        elif option == '3':
            try:
                amount = int(input("Enter amount of XP [Enter to cancel]: "))
                if amount > 0:
                    headers = get_headers(acc)
                    duo_info = get_duo_info(acc)
                    from_lang = duo_info.get('fromLanguage', 'en')
                    to_lang = duo_info.get('learningLanguage', 'fr')
                    story_slug = "fr-en-le-passeport"
                    farm_xp(amount, headers, from_lang, to_lang, story_slug, delay_sec)
                    console.print("[bright_yellow]Press any key to continue.[/]")
                    getch()
            except ValueError:
                pass
        elif option == '4':
            try:
                amount = int(input("Enter amount of Gems Loops [Enter to cancel]: "))
                if amount > 0:
                    headers = get_headers(acc)
                    duo_info = get_duo_info(acc)
                    from_lang = duo_info.get('fromLanguage', 'en')
                    to_lang = duo_info.get('learningLanguage', 'fr')
                    farm_gems(amount, headers, acc['id'], from_lang, to_lang, delay_sec)
                    console.print("[bright_yellow]Press any key to continue.[/]")
                    getch()
            except ValueError:
                pass
        elif option == '5':
            try:
                amount = int(input("Enter amount of streak days [Enter to cancel]: "))
                if amount > 0:
                    streak_farm(amount, acc, delay_sec)
                    console.print("[bright_yellow]Press any key to continue.[/]")
                    getch()
            except ValueError:
                pass
        elif option == '6':
            auto_league_menu(acc, delay_sec)
        elif option == '7':
            multi_task_farm(acc, delay_sec)
        elif option == '8':
            more_options(acc)
        elif option == '9':
            settings_menu(cfg)
            loop_delay_ms = cfg.get('loop_delay_ms', 100)
            delay_sec = loop_delay_ms / 1000.0
        elif option == '0':
            save_cfg(cfg)
            clear()
            return True

def more_options(acc):
    while True:
        clear()
        console.print(title_string())
        console.print("\n  [bold bright_blue]More Options:[/]")
        console.print("  [medium_purple1]1. Free Items[/]")
        console.print("  [pink1]2. Complete Quests[/]")
        console.print("  [bright_green]3. Activate Super Duolingo[/]")
        console.print("  [bright_red]0. Go Back[/]\n")
        
        option = getch().upper()
        
        if option == '1':
            items_menu(acc)
        elif option == '2':
            if Confirm.ask("Complete every quest?"):
                complete_quests(acc)
            else:
                console.print("[yellow]Cancelled quest completion.[/]")
            console.print("[bright_yellow]Press any key to continue.[/]")
            getch()
        elif option == '3':
            activate_super(acc)
            console.print("[bright_yellow]Press any key to continue.[/]")
            getch()
        elif option == '0':
            return

def main():
    try:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        
        cfg = load_cfg()
        
        if 'current_account_id' not in cfg and cfg['accounts']:
            cfg['current_account_id'] = cfg['accounts'][0]['id']
            save_cfg(cfg)
        
        current_acc = None
        for a in cfg['accounts']:
            if a['id'] == cfg.get('current_account_id'):
                current_acc = a
                break
        
        if not current_acc and cfg['accounts']:
            current_acc = cfg['accounts'][0]
            cfg['current_account_id'] = current_acc['id']
            save_cfg(cfg)
        
        if not current_acc:
            console.print("[red]No accounts found. Please add an account first.[/]")
            console.print("[bright_yellow]Press any key to exit.[/]")
            getch()
            clear()
            sys.exit(1)
        
        while True:
            should_quit = main_menu(current_acc, cfg)
            
            if should_quit:
                clear()
                break
    
    except KeyboardInterrupt:
        clear()
    except Exception as e:
        console.print(f"[red][bold]An unexpected error occurred: {e}[/]\nDetailed error:[/]")
        if cfg.get('debug', False):
            console.print_exception()
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        save_cfg(cfg)
        sys.exit(0)

if __name__ == "__main__":
    main()
