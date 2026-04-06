from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


LANDMARKS: Dict[str, Tuple[float, float]] = {
    "royal city": (20.9983, 105.8156),
    "thanh xuan": (21.0015, 105.8080),
    "cau giay": (21.0367, 105.7909),
    "my dinh": (21.0285, 105.7792),
    "ba dinh": (21.0358, 105.8142),
    "ha dong": (20.9714, 105.7765),
    "hoan kiem": (21.0287, 105.8523),
    "district 1": (10.7769, 106.7009),
    "thu duc": (10.8506, 106.7719),
    "quan 7": (10.7297, 106.7214),
    "da nang center": (16.0471, 108.2068),
}

CINEMAS: List[Dict[str, Any]] = [
    {
        "name": "CGV Vincom Royal City",
        "chain": "CGV",
        "city": "Hà Nội",
        "lat": 20.9983,
        "lon": 105.8156,
        "address": "B2, Vincom Mega Mall Royal City, 72A Nguyễn Trãi, Thanh Xuân, Hà Nội",
    },
    {
        "name": "CGV Mipec Tây Sơn",
        "chain": "CGV",
        "city": "Hà Nội",
        "lat": 21.0089,
        "lon": 105.8211,
        "address": "229 Tây Sơn, Đống Đa, Hà Nội",
    },
    {
        "name": "Lotte Cinema Hà Đông",
        "chain": "Lotte",
        "city": "Hà Nội",
        "lat": 20.9718,
        "lon": 105.7795,
        "address": "Tầng 4, Hồ Gươm Plaza, 102 Trần Phú, Hà Đông, Hà Nội",
    },
    {
        "name": "Cinestar Quốc Thanh",
        "chain": "Cinestar",
        "city": "TP.HCM",
        "lat": 10.7717,
        "lon": 106.6877,
        "address": "271 Nguyễn Trãi, Quận 1, TP.HCM",
    },
    {
        "name": "CGV Crescent Mall",
        "chain": "CGV",
        "city": "TP.HCM",
        "lat": 10.7299,
        "lon": 106.7215,
        "address": "101 Tôn Dật Tiên, Quận 7, TP.HCM",
    },
    {
        "name": "Lotte Cinema Diamond",
        "chain": "Lotte",
        "city": "TP.HCM",
        "lat": 10.7802,
        "lon": 106.7007,
        "address": "34 Lê Duẩn, Quận 1, TP.HCM",
    },
    {
        "name": "CGV Vincom Đà Nẵng",
        "chain": "CGV",
        "city": "Đà Nẵng",
        "lat": 16.0613,
        "lon": 108.2239,
        "address": "910A Ngô Quyền, Sơn Trà, Đà Nẵng",
    },
]

MOVIES: List[Dict[str, Any]] = [
    {"title": "Captain America: Brave New World", "genres": ["action", "adventure"], "hot": 8.8},
    {"title": "Mufasa: The Lion King", "genres": ["family", "animation", "adventure"], "hot": 8.5},
    {"title": "Dune: Part Two", "genres": ["science fiction", "action", "drama"], "hot": 9.2},
    {"title": "Exhuma", "genres": ["horror", "mystery"], "hot": 8.1},
    {"title": "Mai", "genres": ["drama", "romance"], "hot": 8.6},
    {"title": "Quỷ Cẩu", "genres": ["horror"], "hot": 7.6},
    {"title": "Nhà Bà Nữ", "genres": ["comedy", "drama"], "hot": 8.0},
]

CHAIN_BASE_PRICE_K = {
    "CGV": 95,
    "Lotte": 90,
    "Cinestar": 85,
}


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    text = re.sub(r"\s+", " ", text)
    return text


def canonical_genre(genre: Optional[str]) -> str:
    aliases = {
        "hanh dong": "action",
        "action": "action",
        "kinh di": "horror",
        "horror": "horror",
        "tinh cam": "romance",
        "romance": "romance",
        "hai": "comedy",
        "comedy": "comedy",
        "vien tuong": "science fiction",
        "science fiction": "science fiction",
        "phieu luu": "adventure",
        "adventure": "adventure",
        "gia dinh": "family",
        "family": "family",
        "hoat hinh": "animation",
        "animation": "animation",
        "chinh kich": "drama",
        "drama": "drama",
        "bi an": "mystery",
        "mystery": "mystery",
    }
    return aliases.get(normalize_text(genre), normalize_text(genre))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def resolve_reference_point(location: str) -> Dict[str, Any]:
    norm = normalize_text(location)
    for key, coords in LANDMARKS.items():
        if key in norm or norm in key:
            return {"name": key, "lat": coords[0], "lon": coords[1]}

    for cinema in CINEMAS:
        cinema_norm = normalize_text(cinema["name"])
        if cinema_norm in norm or norm in cinema_norm:
            return {"name": cinema["name"], "lat": cinema["lat"], "lon": cinema["lon"]}

    return {"name": "royal city", "lat": LANDMARKS["royal city"][0], "lon": LANDMARKS["royal city"][1]}


def fallback_times_for(title: str) -> List[str]:
    patterns = [
        ["16:30", "19:00", "21:20"],
        ["17:00", "19:30", "21:45"],
        ["16:45", "18:55", "21:10"],
        ["17:15", "19:20", "21:40"],
    ]
    idx = int(hashlib.md5(title.encode("utf-8")).hexdigest()[:2], 16) % len(patterns)
    return patterns[idx]


def genre_match(movie: Dict[str, Any], genre: Optional[str]) -> bool:
    wanted = canonical_genre(genre)
    if not wanted:
        return True
    movie_genres = [canonical_genre(item) for item in movie["genres"]]
    return wanted in movie_genres


def time_bonus(showtime: str, preferred_time: str) -> float:
    hour = int(showtime.split(":")[0])
    pref = normalize_text(preferred_time)
    if pref in {"toi", "evening"}:
        return 8.0 if 18 <= hour <= 21 else 0.0
    if pref in {"chieu", "afternoon"}:
        return 8.0 if 13 <= hour <= 17 else 0.0
    if pref in {"sang", "morning"}:
        return 8.0 if 8 <= hour <= 11 else 0.0
    return 0.0


def recommend_showtimes(
    location: str,
    genre: Optional[str] = None,
    movie_keyword: Optional[str] = None,
    seats: int = 2,
    budget_k: int = 250,
    preferred_time: str = "evening",
    max_results: int = 5,
) -> Dict[str, Any]:
    reference = resolve_reference_point(location)
    keyword_norm = normalize_text(movie_keyword)

    ranked = []
    for cinema in CINEMAS:
        distance = haversine_km(reference["lat"], reference["lon"], cinema["lat"], cinema["lon"])
        price_per_seat_k = CHAIN_BASE_PRICE_K.get(cinema["chain"], 90)

        for movie in MOVIES:
            if not genre_match(movie, genre):
                continue
            if keyword_norm and keyword_norm not in normalize_text(movie["title"]):
                continue

            for showtime in fallback_times_for(movie["title"]):
                total_vnd = seats * price_per_seat_k * 1000
                if budget_k and total_vnd > budget_k * 1000:
                    continue

                score = (
                    movie["hot"] * 10
                    - distance * 6
                    + time_bonus(showtime, preferred_time)
                )

                ranked.append(
                    {
                        "cinema_name": cinema["name"],
                        "cinema_chain": cinema["chain"],
                        "city": cinema["city"],
                        "address": cinema["address"],
                        "distance_km": round(distance, 2),
                        "movie_title": movie["title"],
                        "genres": movie["genres"],
                        "showtime": showtime,
                        "est_price_per_seat_k": price_per_seat_k,
                        "est_total_vnd": total_vnd,
                        "score": round(score, 2),
                    }
                )

    ranked.sort(key=lambda item: (-item["score"], item["distance_km"], item["est_total_vnd"]))

    return {
        "reference_location": location,
        "resolved_reference": reference["name"],
        "recommendations": ranked[:max_results],
        "note": "Dữ liệu rạp là địa điểm thật ở Việt Nam; lịch chiếu và giá được mô phỏng ổn định cho lab demo.",
    }


def seat_is_blocked(seed: str, seat_label: str) -> bool:
    value = int(hashlib.md5(f"{seed}-{seat_label}".encode("utf-8")).hexdigest()[:2], 16)
    return value < 48


def hold_best_seats(
    cinema_name: str,
    movie_title: str,
    showtime: str,
    seats: int = 2,
    price_per_seat_k: Optional[int] = None,
    preference: str = "center",
) -> Dict[str, Any]:
    cinema = next(
        (item for item in CINEMAS if normalize_text(item["name"]) == normalize_text(cinema_name)),
        None,
    )
    if cinema is None:
        return {"status": "error", "message": f"Không tìm thấy rạp: {cinema_name}"}

    per_seat_k = price_per_seat_k or CHAIN_BASE_PRICE_K.get(cinema["chain"], 90)
    seed = f"{cinema_name}|{movie_title}|{showtime}"
    rows = "ABCDEFGH"
    best_block = None
    best_score = float("inf")

    for row_idx, row in enumerate(rows):
        for start in range(1, 13 - seats + 1):
            block = [f"{row}{seat_no}" for seat_no in range(start, start + seats)]
            if any(seat_is_blocked(seed, seat) for seat in block):
                continue

            avg_number = sum(int(seat[1:]) for seat in block) / len(block)
            row_penalty = abs(row_idx - 4)
            seat_penalty = abs(avg_number - 6.5)
            score = row_penalty * 2 + seat_penalty

            pref = normalize_text(preference)
            if pref in {"back", "cuoi"}:
                score -= row_idx * 0.3
            elif pref in {"front", "dau"}:
                score -= (7 - row_idx) * 0.3

            if score < best_score:
                best_score = score
                best_block = block

    if not best_block:
        return {"status": "failed", "message": "Không tìm được cụm ghế liền nhau phù hợp."}

    subtotal_vnd = seats * per_seat_k * 1000
    return {
        "status": "held",
        "cinema_name": cinema_name,
        "movie_title": movie_title,
        "showtime": showtime,
        "held_seats": best_block,
        "price_per_seat_k": per_seat_k,
        "subtotal_vnd": subtotal_vnd,
        "hold_expires_in_min": 5,
    }


def apply_best_promo(
    total_vnd: int,
    is_student: bool = False,
    is_member: bool = True,
    payment_method: str = "cash",
) -> Dict[str, Any]:
    options = []

    if is_member:
        options.append({
            "promo_code": "MEMBER10",
            "description": "Giảm 10% cho thành viên, tối đa 30k",
            "discount_vnd": min(int(total_vnd * 0.10), 30000),
        })

    if is_student:
        options.append({
            "promo_code": "STUDENT25K",
            "description": "Ưu đãi sinh viên 25k",
            "discount_vnd": 25000,
        })

    method = normalize_text(payment_method)
    if method in {"momo", "zalopay"}:
        options.append({
            "promo_code": method.upper() + "15K",
            "description": f"Ưu đãi thanh toán qua {payment_method}",
            "discount_vnd": 15000,
        })

    if not options:
        return {
            "applied_promo": None,
            "discount_vnd": 0,
            "total_before_vnd": total_vnd,
            "total_after_vnd": total_vnd,
        }

    best = max(options, key=lambda item: item["discount_vnd"])
    return {
        "applied_promo": best["promo_code"],
        "promo_description": best["description"],
        "discount_vnd": best["discount_vnd"],
        "total_before_vnd": total_vnd,
        "total_after_vnd": max(total_vnd - best["discount_vnd"], 0),
    }


def get_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "recommend_showtimes",
            "description": (
                "Tìm phim/rạp/suất chiếu phù hợp. "
                "Args JSON ví dụ: "
                "{\"location\":\"Royal City\",\"genre\":\"action\",\"movie_keyword\":\"\","
                "\"seats\":2,\"budget_k\":250,\"preferred_time\":\"evening\",\"max_results\":5}"
            ),
            "func": recommend_showtimes,
        },
        {
            "name": "hold_best_seats",
            "description": (
                "Giữ ghế đẹp cho một suất chiếu. "
                "Args JSON ví dụ: "
                "{\"cinema_name\":\"CGV Vincom Royal City\",\"movie_title\":\"Dune: Part Two\","
                "\"showtime\":\"19:30\",\"seats\":2,\"price_per_seat_k\":95,\"preference\":\"center\"}"
            ),
            "func": hold_best_seats,
        },
        {
            "name": "apply_best_promo",
            "description": (
                "Áp mã giảm giá tốt nhất. "
                "Args JSON ví dụ: "
                "{\"total_vnd\":190000,\"is_student\":false,\"is_member\":true,\"payment_method\":\"momo\"}"
            ),
            "func": apply_best_promo,
        },
    ]