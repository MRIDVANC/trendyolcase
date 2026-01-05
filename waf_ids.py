#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trendyol Security Operations Center - Autonomous IDS/IPS Engine v15.0
====================================================================
Professional Edition: Real-time Performance Monitoring & Multi-Layer Defense
"""

import time
import subprocess
import os
import re
import json
import signal
import sys
import psutil
from datetime import datetime
from collections import defaultdict, deque

# ============================================
# CONFIGURATION PARAMETERS
# ============================================

LOG_FILE = "/var/log/nginx/error.log"
BLACKLIST_FILE = "/var/www/security/blacklist.txt"
INCIDENT_LOG = "/var/log/waf/incidents.json"
STATS_FILE = "/var/log/waf/daily_statistics.json"

L7_THRESHOLD = 5
L4_THRESHOLD = 20
ATTACK_WINDOW = 300
REFRESH_RATE = 0.5
MAX_DISPLAY_LOGS = 10

# Renk ve Stil Tanımları
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ============================================
# GLOBAL STATE MANAGEMENT
# ============================================

attacks = defaultdict(int)
attack_timestamps = defaultdict(list)
banned_l7_ips = set()
banned_l4_ips = set()
incident_logs = deque(maxlen=100)

statistics = {
    "total_attacks": 0,
    "l7_bans": 0,
    "l4_bans": 0,
    "start_time": datetime.now(),
    "cpu_percent": 0.0,
    "ram_percent": 0.0,
    "network_in_mbps": 0.0,
    "nginx_latency_ms": 0.0,
}

# Network monitoring baseline
net_io_baseline = None

# ============================================
# CORE FUNCTIONS
# ============================================

def signal_handler(sig, frame):
    print(f"\n\n{YELLOW}{BOLD}⚠ SHUTTING DOWN SYSTEM...{RESET}")
    save_statistics()
    sys.exit(0)

def check_firewall_availability():
    iptables_ok = subprocess.run(["which", "iptables"], capture_output=True).returncode == 0
    nftables_ok = subprocess.run(["which", "nft"], capture_output=True).returncode == 0
    return iptables_ok, nftables_ok

def save_statistics():
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        stats_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_attacks": statistics["total_attacks"],
            "l7_bans": statistics["l7_bans"],
            "l4_bans": statistics["l4_bans"],
            "uptime": str(datetime.now() - statistics["start_time"]),
            "avg_cpu": f"{statistics['cpu_percent']:.1f}%",
            "avg_ram": f"{statistics['ram_percent']:.1f}%",
        }
        with open(STATS_FILE, 'w') as f:
            json.dump(stats_data, f, indent=2)
    except:
        pass

def parse_modsec_details(line):
    rid = (re.search(r'id "(\d+)"', line) or re.search(r'', '')).group(1) if re.search(r'id "(\d+)"', line) else "N/A"
    msg = (re.search(r'msg "([^"]+)"', line) or re.search(r'', '')).group(1) if re.search(r'msg "([^"]+)"', line) else "Pattern Match"
    data = (re.search(r'data "([^"]+)"', line) or re.search(r'', '')).group(1) if re.search(r'data "([^"]+)"', line) else "Header"

    category = "PROBING"
    l_line = line.lower()
    if any(x in l_line for x in ["sql", "select", "union"]):
        category = "SQL INJECTION"
    elif "script" in l_line or "xss" in l_line:
        category = "XSS ATTACK"
    elif any(x in l_line for x in ["cat ", "passwd", "bin/sh"]):
        category = "RCE ATTEMPT"
    elif ".." in l_line or "traversal" in l_line:
        category = "PATH TRAVERSAL"
    elif "limiting requests" in l_line or "limiting connections" in l_line:
        category = "HTTP FLOOD"

    return rid, msg, data, category

# ============================================
# PERFORMANCE MONITORING
# ============================================

def collect_metrics():
    """Gerçek zamanlı sistem metriklerini toplar"""
    global net_io_baseline
    net_io_baseline = psutil.net_io_counters()

    while True:
        time.sleep(2)

        # CPU ve RAM
        statistics["cpu_percent"] = psutil.cpu_percent(interval=1)
        statistics["ram_percent"] = psutil.virtual_memory().percent

        # Network I/O (Mbps hesaplama)
        net_io_now = psutil.net_io_counters()
        bytes_recv_diff = net_io_now.bytes_recv - net_io_baseline.bytes_recv
        statistics["network_in_mbps"] = (bytes_recv_diff * 8) / (2 * 1024 * 1024)  # 2 saniyelik ölçüm
        net_io_baseline = net_io_now

        # Nginx Response Time (access.log'dan parse)
        try:
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/nginx/access.log"],
                capture_output=True,
                text=True,
                timeout=1
            )
            # Log format: ... "$request_time" (sondaki değer)
            latencies = []
            for line in result.stdout.split('\n'):
                match = re.search(r' (0\.\d+)$', line)
                if match:
                    latencies.append(float(match.group(1)))

            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                statistics["nginx_latency_ms"] = avg_latency * 1000
            else:
                statistics["nginx_latency_ms"] = 0.0
        except:
            pass

# ============================================
# DASHBOARD UI ENGINE
# ============================================

def print_dashboard():
    sys.stdout.write("\033[H\033[2J")  # Clear screen + move cursor to top
    uptime = str(datetime.now() - statistics["start_time"]).split('.')[0]
    width = 120

    # Header
    print(f"{CYAN}╔" + "═" * width + "╗")
    print(f"║{RESET}{BOLD} 🛡️  TRENDYOL SOC - AUTONOMOUS DEFENSE ENGINE v15.0 ".center(width + 8) + f"{CYAN}║")
    print(f"╠" + "═" * width + f"╣{RESET}")

    # Stats Row
    stats = f" UPTIME: {BOLD}{uptime}{RESET} │ ATTACKS: {BOLD}{statistics['total_attacks']}{RESET} │ L7 BANS: {YELLOW}{statistics['l7_bans']}{RESET} │ L4 BANS: {RED}{statistics['l4_bans']}{RESET} "
    print(f"{CYAN}║{RESET}" + stats.center(width + 32) + f"{CYAN}║{RESET}")
    print(f"{CYAN}╠" + "─" * width + f"╣{RESET}")

    # PERFORMANCE METRICS ROW
    cpu = statistics["cpu_percent"]
    ram = statistics["ram_percent"]
    net = statistics["network_in_mbps"]
    lat = statistics["nginx_latency_ms"]

    cpu_color = RED if cpu > 80 else YELLOW if cpu > 50 else GREEN
    ram_color = RED if ram > 80 else YELLOW if ram > 50 else GREEN
    lat_color = RED if lat > 200 else YELLOW if lat > 100 else GREEN

    metrics = (
        f" CPU: {cpu_color}{BOLD}{cpu:.1f}%{RESET} │ "
        f"RAM: {ram_color}{BOLD}{ram:.1f}%{RESET} │ "
        f"NETWORK: {CYAN}{BOLD}{net:.2f} Mbps{RESET} │ "
        f"LATENCY: {lat_color}{BOLD}{lat:.1f}ms{RESET} "
    )
    print(f"{CYAN}║{RESET}" + metrics.center(width + 56) + f"{CYAN}║{RESET}")
    print(f"{CYAN}╠" + "─" * width + f"╣{RESET}")

    # Threats Table Header
    table_header = f" {BOLD}{'SOURCE IP':18} │ {'HITS':5} │ {'CATEGORY':20} │ {'DEFENSE STATUS':38} │ {'IDS'}{RESET} "
    print(f"{CYAN}║{RESET}" + table_header.ljust(width + 32) + f"{CYAN}║{RESET}")
    print(f"{CYAN}╠" + "─" * width + f"╣{RESET}")

    # Threats Data
    sorted_ips = sorted(attacks.items(), key=lambda x: x[1], reverse=True)[:10]
    if not sorted_ips:
        print(f"{CYAN}║{RESET}" + f"{YELLOW}SCANNING TRAFFIC... NO THREATS DETECTED{RESET}".center(width + 8) + f"{CYAN}║{RESET}")
    else:
        for ip, count in sorted_ips:
            if ip in banned_l4_ips:
                status = f"{RED}{BOLD}🚫 KERNEL DROP (L4){RESET}"
            elif ip in banned_l7_ips:
                status = f"{YELLOW}{BOLD}🔒 NGINX BLOCK (L7){RESET}"
            else:
                status = f"{GREEN}👁️  MONITORING{RESET}"

            cat = "PROBING"
            for log in reversed(incident_logs):
                if ip in log and "TEKNİK:" in log:
                    cat = log.split("TEKNİK:")[1].split("|")[0].strip()[:18]
                    break

            row = f" {ip:18} │ {count:5} │ {cat:20} │ {status:47} │ {BOLD}{GREEN}ON{RESET} "
            print(f"{CYAN}║{RESET}" + row.ljust(width + 41) + f"{CYAN}║{RESET}")

    print(f"{CYAN}╠" + "═" * width + f"╣{RESET}")
    print(f"{CYAN}║{RESET} {BOLD}{MAGENTA}🔍 DEEP PACKET INSPECTION & FORENSIC LOGS:{RESET}".ljust(width + 10) + f"{CYAN}║{RESET}")
    print(f"{CYAN}╠" + "─" * width + f"╣{RESET}")

    # Log Stream
    logs = list(incident_logs)[-MAX_DISPLAY_LOGS:]
    for log in logs:
        clean_len = len(re.sub(r'\033\[[0-9;]*m', '', log))
        print(f"{CYAN}║{RESET} " + log + " " * (width - clean_len - 1) + f"{CYAN}║{RESET}")

    for _ in range(MAX_DISPLAY_LOGS - len(logs)):
        print(f"{CYAN}║{RESET}" + " " * width + f"{CYAN}║{RESET}")

    print(f"{CYAN}╚" + "═" * width + f"╝{RESET}")

# ============================================
# OPERATIONAL LOGIC
# ============================================

def apply_l7_ban(ip, timestamp):
    try:
        os.makedirs(os.path.dirname(BLACKLIST_FILE), exist_ok=True)
        with open(BLACKLIST_FILE, "a") as bl:
            bl.write(f"{ip} 1; # Banned at {timestamp}\n")

        if subprocess.run(["nginx", "-s", "reload"], capture_output=True).returncode == 0:
            banned_l7_ips.add(ip)
            statistics["l7_bans"] += 1
            incident_logs.append(
                f"{YELLOW}{BOLD}⚠ L7 BAN APPLIED:{RESET} {ip} - {BOLD}REASON: ATTACK THRESHOLD ({attacks[ip]} hits){RESET}"
            )
    except Exception as e:
        incident_logs.append(f"{RED}L7 ERROR: {str(e)}{RESET}")

def apply_l4_drop(ip, timestamp):
    success, method = False, ""
    try:
        if subprocess.run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"], capture_output=True).returncode == 0:
            success, method = True, "IPTABLES"
    except:
        pass

    if not success:
        try:
            subprocess.run(["nft", "add", "rule", "inet", "filter", "input", "ip", "saddr", ip, "drop"], capture_output=True)
            success, method = True, "NFTABLES"
        except:
            pass

    if success:
        banned_l4_ips.add(ip)
        statistics["l4_bans"] += 1
        incident_logs.append(
            f"{RED}{BOLD}🚫 L4 DROP APPLIED ({method}):{RESET} {ip} - {BOLD}PROTOCOL: TCP/ALL{RESET}"
        )

def monitor_logs():
    iptables_ok, nftables_ok = check_firewall_availability()
    os.system('clear')
    print(f"{GREEN}{BOLD}[✓] SOC DEFENSE ENGINE v15.0 INITIALIZED{RESET}")
    print(f"{BLUE}[+] L4 BACKEND: IPTABLES={iptables_ok} | NFTABLES={nftables_ok}{RESET}")
    print(f"{BLUE}[+] PERFORMANCE MONITORING: ENABLED{RESET}")
    print(f"{BLUE}[+] METRICS: CPU | RAM | NETWORK | LATENCY{RESET}")
    time.sleep(2)

    # Metrics thread başlat
    import threading
    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()

    f = open(LOG_FILE, "r")
    f.seek(0, 2)

    try:
        while True:
            line = f.readline()
            if not line:
                print_dashboard()
                time.sleep(REFRESH_RATE)
                continue

            if "ModSecurity" in line or "403" in line or "limiting requests" in line:
                ip_match = re.search(r"client: ([\d.]+)", line)
                if ip_match:
                    ip = ip_match.group(1)
                    if ip.startswith("127.0"):
                        continue

                    attacks[ip] += 1
                    statistics["total_attacks"] += 1
                    h_now = datetime.now().strftime('%H:%M:%S')

                    rid, msg, payload, cat = parse_modsec_details(line)

                    # Profesyonel log formatı
                    incident_logs.append(
                        f"{BOLD}{BLUE}[{h_now}]{RESET} | {RED}TEKNİK: {cat:15}{RESET} | {CYAN}RULE:{rid:6}{RESET} | {BOLD}IP:{ip}{RESET}"
                    )

                    if attacks[ip] >= L7_THRESHOLD and ip not in banned_l7_ips:
                        apply_l7_ban(ip, h_now)

                    if attacks[ip] >= L4_THRESHOLD and ip not in banned_l4_ips:
                        apply_l4_drop(ip, h_now)

                    print_dashboard()

    except Exception as e:
        print(f"{RED}FATAL ERROR: {e}{RESET}")
    finally:
        f.close()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{RED}ROOT PRIVILEGES REQUIRED!{RESET}")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    monitor_logs()