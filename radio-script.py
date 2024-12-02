#!/usr/bin/env python3
import subprocess
import json
import requests
import time  # Додано для затримки

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
    "https://radio.kyivstar.ua/stream/sport/status/health",
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
]

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

def check_url(url, check_metadata=True):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Unhealthy: {url} returned status {response.status_code}")
            return False

        # Перевіряємо JSON-відповідь
        data = response.json()
        if data.get("transcoding") != "HEALTHY":
            print(f"Unhealthy transcoding for {url}: {data.get('transcoding')}")
            return True

        if check_metadata and data.get("metadata") != "HEALTHY":
            print(f"Unhealthy metadata for {url}: {data.get('metadata')}")
            return True

        print(f"Healthy: {url}")
        return False
    except requests.RequestException as e:
        print(f"Request failed for {url}: {e}")
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
            print(f"Skipping excluded pod: {pod_name}")
            continue

        # Перевіряємо URL для кожного пода
        for url in CHECK_BOTH:
            if not check_url(url, check_metadata=True):
                continue
            print(f"Pod {pod_name} is unhealthy based on {url}. Deleting...")
            delete_pod(pod_name)

        for url in CHECK_TRANSCODING_ONLY:
            if not check_url(url, check_metadata=False):
                continue
            print(f"Pod {pod_name} is unhealthy based on {url}. Deleting...")
            delete_pod(pod_name)

if __name__ == "__main__":
    check_and_restart_unhealthy_pods()
