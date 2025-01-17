Locate:   /home/developer/scripts/new_script-healthy.py


#!/usr/bin/env python3
import subprocess
import json
import requests
import time

# Список подів, які не можна перезапускати
EXCLUDE_PODS = ["postgres", "redis", "web", "api"]

# Список URL для перевірки стану подів
CHECK_BOTH = [
    "https://radio.kyivstar.ua/stream/tophits/status/health",
    "https://radio.kyivstar.ua/stream/worldchart/status/health",
    "https://radio.kyivstar.ua/stream/gold/status/health",
    "https://radio.kyivstar.ua/stream/ukraine/status/health",
    "https://radio.kyivstar.ua/stream/rock/status/health",
    "https://radio.kyivstar.ua/stream/chill/status/health",
    "https://radio.kyivstar.ua/stream/rap/status/health",
    "https://radio.kyivstar.ua/stream/retromusic/status/health",
    "https://radio.kyivstar.ua/stream/elektro/status/health",
    "https://radio.kyivstar.ua/stream/sport/status/health"
]

CHECK_TRANSCODING_ONLY = [
    "https://radio.kyivstar.ua/stream/luks/status/health",
    "https://radio.kyivstar.ua/stream/maximumhd/status/health",
    "https://radio.kyivstar.ua/stream/nostalgi/status/health",
    "https://radio.kyivstar.ua/stream/radiorelax/status/health",
    "https://radio.kyivstar.ua/stream/radiorocks/status/health",
    "https://radio.kyivstar.ua/stream/bayraktar/status/health",
    "https://radio.kyivstar.ua/stream/hitfmhd/status/health",
    "https://radio.kyivstar.ua/stream/kissfm/status/health",
    "https://radio.kyivstar.ua/stream/nasheradyo/status/health",
    "https://radio.kyivstar.ua/stream/classic/status/health",
    "https://radio.kyivstar.ua/stream/radiojazz/status/health",
    "https://radio.kyivstar.ua/stream/edyninov/status/health",
    "https://radio.kyivstar.ua/stream/hromadske/status/health",
    "https://radio.kyivstar.ua/stream/radionv/status/health",
    "https://radio.kyivstar.ua/stream/business/status/health",
    "https://radio.kyivstar.ua/stream/djfm/status/health",
    "https://radio.kyivstar.ua/stream/kazka/status/health",
    "https://radio.kyivstar.ua/stream/melodiafm/status/health",
    "https://radio.kyivstar.ua/stream/powerfm/status/health",
    "https://radio.kyivstar.ua/stream/shlyager/status/health",
    "https://radio.kyivstar.ua/stream/tysafm/status/health",
    "https://radio.kyivstar.ua/stream/ur1/status/health",
    "https://radio.kyivstar.ua/stream/ur2/status/health",
    "https://radio.kyivstar.ua/stream/ur3/status/health"
]

# Множина для відстеження перевірених URL
checked_urls = set()

def get_pods():
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-o", "json"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running kubectl command: {e.stderr}")
        return None

def log_to_file(filename, message):
    """Append a message to a specified log file."""
    with open(filename, "a") as f:
        f.write(message + "\n")

def check_url(url, check_metadata=True):
    if url in checked_urls:
        print(f"URL already checked: {url}")
        return False

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Unhealthy: {url} returned status {response.status_code}")
            return False

        # Перевіряємо JSON-відповідь
        data = response.json()
        if data.get("transcoding") != "HEALTHY":
            message = f"Unhealthy transcoding for {url}: {data.get('transcoding')}"
            print(message)
            log_to_file("Unhealthy-Transcoding.txt", message)
            return True

        if check_metadata and data.get("metadata") != "HEALTHY":
            message = f"Unhealthy metadata for {url}: {data.get('metadata')}"
            print(message)
            log_to_file("Unhealthy-Metadata.txt", message)
            return True

        print(f"Healthy: {url}")
        checked_urls.add(url)
        return False
    except requests.RequestException as e:
        message = f"Request failed for {url}: {e}"
        print(message)
        log_to_file("Unhealthy-Transcoding.txt", message)
        return False

def delete_pod(pod_name):
    try:
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        print(f"Deleted pod: {pod_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting pod {pod_name}: {e.stderr}")

def check_and_restart_unhealthy_pods():
    pods = get_pods()
    if not pods:
        return

    for pod in pods["items"]:
        pod_name = pod["metadata"]["name"]

        # Пропускаємо поди з EXCLUDE_PODS
        if any(exclude in pod_name for exclude in EXCLUDE_PODS):
            print(f"Skip: {pod_name}")
            continue

        # Перевіряємо URL для кожного пода
        unhealthy = False
        for url in CHECK_BOTH:
            if check_url(url, check_metadata=True):
                unhealthy = True

        for url in CHECK_TRANSCODING_ONLY:
            if check_url(url, check_metadata=False):
                unhealthy = True

        if unhealthy:
            print(f"Pod {pod_name} is unhealthy. Deleting...")
            delete_pod(pod_name)

if __name__ == "__main__":
    while True:
        check_and_restart_unhealthy_pods()
        time.sleep(30)

