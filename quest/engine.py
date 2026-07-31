# ============================================================
# НЕ ПОДСМАТРИВАЙ В ЭТОТ ФАЙЛ! ИСПОРТИШЬ СЕБЕ СЮРПРИЗ!
# Просто запусти `python reveal.py` из корня репозитория.
# ============================================================

import math
import sys
import time
from pathlib import Path

import yaml
from geopy.geocoders import Nominatim
from PIL import Image
import matplotlib.pyplot as plt

SUBMISSIONS_DIR = Path(__file__).resolve().parent.parent / "submissions"
TOTAL_COUNTRIES = 8
REQUIRED_FIELDS = {"name", "country", "lat", "lon", "photo"}
EARTH_RADIUS_KM = 6371.0
TRUE_TARGET = (55.931547, 37.518848)


def load_entries():
    entries = []
    for folder in sorted(SUBMISSIONS_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith((".", "_")):
            continue
        entry_file = folder / "entry.yaml"
        if not entry_file.exists():
            continue
        with open(entry_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _validate_entry(folder, data)
        data["photo_path"] = folder / data["photo"]
        entries.append(data)
    return entries


def _validate_entry(folder, data):
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise ValueError(f"submissions/{folder.name}/entry.yaml: не хватает полей {sorted(missing)}")
    lat, lon = data["lat"], data["lon"]
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise ValueError(f"submissions/{folder.name}/entry.yaml: координаты вне допустимого диапазона")
    if not (folder / data["photo"]).exists():
        raise ValueError(f"submissions/{folder.name}/entry.yaml: файл фото «{data['photo']}» не найден")


def geographic_center(points):
    x = y = z = 0.0
    for lat, lon in points:
        lat_r, lon_r = math.radians(lat), math.radians(lon)
        x += math.cos(lat_r) * math.cos(lon_r)
        y += math.cos(lat_r) * math.sin(lon_r)
        z += math.sin(lat_r)
    n = len(points)
    x, y, z = x / n, y / n, z / n
    center_lon = math.atan2(y, x)
    center_lat = math.atan2(z, math.sqrt(x * x + y * y))
    return math.degrees(center_lat), math.degrees(center_lon)


def haversine_km(point_a, point_b):
    lat1, lon1 = map(math.radians, point_a)
    lat2, lon2 = map(math.radians, point_b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def reverse_geocode(lat, lon):
    geolocator = Nominatim(user_agent="family_challenge_2026")
    try:
        location = geolocator.reverse((lat, lon), language="ru", timeout=10)
        if location:
            return location.address
    except Exception:
        pass
    return f"{lat:.5f}, {lon:.5f}"


def show_photos(entries):
    n = len(entries)
    cols = min(4, n)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = [axes] if n == 1 else axes.flatten()
    for ax, entry in zip(axes, entries):
        ax.imshow(Image.open(entry["photo_path"]))
        ax.set_title(f"{entry['name']} ({entry['country']})")
        ax.axis("off")
    for ax in axes[n:]:
        ax.axis("off")
    plt.tight_layout()
    plt.show()


def run():
    entries = load_entries()
    n = len(entries)

    if n == 0:
        print("Пока никто не добавил свою фотку. Будь первым — загляни в README!")
        return

    me_name = input("Как тебя зовут? ").strip()
    me = next((e for e in entries if e["name"].lower() == me_name.lower()), None)
    if me is None:
        print(
            f"Не нашёл в списке участника с именем «{me_name}». "
            f"Сначала добавь свою фотку и координаты в submissions/ (см. README)."
        )
        return

    if n == 1:
        distance_km = round(haversine_km((me["lat"], me["lon"]), TRUE_TARGET))
        print(
            f"Поздравляю, {me['name']}, ты первый завершил свою часть задания! "
            f"Чтобы узнать секретик, придётся дождаться остальных :(\n"
            f"До истинной цели осталось {distance_km} километров!"
        )
        return

    lat, lon = geographic_center([(e["lat"], e["lon"]) for e in entries])
    address = reverse_geocode(lat, lon)
    distance_km = round(haversine_km((lat, lon), TRUE_TARGET))

    if n < TOTAL_COUNTRIES:
        print(f"Поздравляю с завершением задания, {me['name']}! Вот секретик: {address}.")
        sys.stdout.flush()
        time.sleep(5)
        finished = ", ".join(e["name"] for e in entries)
        print(f"Хмм... кажется это что-то не то :(\nДо истинной цели осталось {distance_km} километров!")
        print(f"Уже выполнили задания: {finished}")
        show_photos(entries)
    else:
        print(
            f"Поздравляю! Вы успешно завершили задание! Секретное место: {address}. Как неожиданно :)\n"
            f"Ошибка составила всего {distance_km} километров!"
        )
        show_photos(entries)
