"""Script de trafico Python.

Genera requests aleatorios contra los endpoints de la API.

Uso:
    python generate-traffic.py
    python generate-traffic.py --base http://localhost:3000 --duration 300
"""
import argparse
import random
import time
import uuid
import sys

try:
    import requests
except ImportError:
    sys.exit("Falta dependencia. Instala con: pip install requests")


ENDPOINTS = [
    ("GET",  "/",                 5),
    ("GET",  "/api/datos",        8),
    ("GET",  "/api/lento",        1),
    ("GET",  "/api/usuarios",     6),
    ("GET",  "/api/usuarios/1",   4),
    ("GET",  "/api/usuarios/2",   3),
    ("GET",  "/api/usuarios/999", 2),
    ("POST", "/api/usuarios",     2),
    ("GET",  "/api/error",        3),
    ("GET",  "/health",           2),
]


def build_pool():
    pool = []
    for method, path, weight in ENDPOINTS:
        pool.extend([(method, path)] * weight)
    return pool


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:3000")
    parser.add_argument("--duration", type=int, default=0, help="0 = infinito")
    parser.add_argument("--delay-min", type=float, default=0.1)
    parser.add_argument("--delay-max", type=float, default=0.6)
    args = parser.parse_args()

    pool = build_pool()
    print(f"Generando trafico contra {args.base}")
    print(f"Duracion: {'infinita' if args.duration <= 0 else f'{args.duration}s'}")
    print("Detener con Ctrl+C\n")

    start = time.time()
    count = ok = fail = 0
    try:
        while True:
            if args.duration > 0 and (time.time() - start) >= args.duration:
                break

            method, path = random.choice(pool)
            url = f"{args.base}{path}"
            count += 1
            try:
                if method == "POST":
                    payload = {"name": f"user-{uuid.uuid4().hex[:6]}", "role": "user"}
                    r = requests.post(url, json=payload, timeout=10)
                else:
                    r = requests.request(method, url, timeout=10)
                status = r.status_code
                ok += 1
            except requests.RequestException as exc:
                status = f"ERR({exc.__class__.__name__})"
                fail += 1

            print(f"[{count:4d}] {method:<4} {path:<25} -> {status}")
            time.sleep(random.uniform(args.delay_min, args.delay_max))
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")

    print(f"\nTotal: {count}  OK: {ok}  Fallidos: {fail}")


if __name__ == "__main__":
    main()
