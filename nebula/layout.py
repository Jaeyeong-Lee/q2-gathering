"""Deterministic display-only port of Heritage's 300-tick warm-up."""

import math
import random


def place_people(people, edges, pjt_count):
    # ponytail: O(300*n²) repulsion is enough for the 320-person presentation.
    # Revisit with a spatial index if the roster grows into the thousands.
    width, height = 1400, 800
    rng = random.Random(0)
    anchors = [
        (
            width * (0.5 + 0.32 * math.cos(i * math.tau / pjt_count - math.pi / 2)),
            height * (0.5 + 0.30 * math.sin(i * math.tau / pjt_count - math.pi / 2)),
        )
        for i in range(pjt_count)
    ]
    positions = []
    for p in people:
        ax, ay = anchors[p["pjt"]]
        angle, radius = rng.random() * math.tau, math.sqrt(rng.random()) * 0.08
        positions.append(
            [
                ax + math.cos(angle) * radius * width,
                ay + math.sin(angle) * radius * height,
                0.0,
                0.0,
            ]
        )
    springs = []
    for e in sorted(edges, key=lambda e: (e["a"], e["b"])):
        a, b, weight = e["a"], e["b"], max(e["w"], 0)
        stiffness = (0.02 + weight * 0.03) * (
            1 if people[a]["pjt"] == people[b]["pjt"] else 0.05
        )
        springs.append((a, b, (1 - weight) * 200 + 95, stiffness))
    alpha = 1.0
    for _ in range(300):
        for i, a in enumerate(positions):
            for j in range(i + 1, len(positions)):
                b = positions[j]
                dx, dy = a[0] - b[0], a[1] - b[1]
                distance_sq = dx * dx + dy * dy + 0.01
                if distance_sq > 260000:
                    continue
                force = 900 / (distance_sq * math.sqrt(distance_sq))
                fx, fy = dx * force, dy * force
                a[2] += fx
                a[3] += fy
                b[2] -= fx
                b[3] -= fy
        for ai, bi, rest, stiffness in springs:
            a, b = positions[ai], positions[bi]
            dx, dy = b[0] - a[0], b[1] - a[1]
            distance = math.hypot(dx, dy) or 0.01
            force = (distance - rest) * stiffness / distance
            fx, fy = dx * force, dy * force
            a[2] += fx
            a[3] += fy
            b[2] -= fx
            b[3] -= fy
        for p, n in zip(people, positions):
            ax, ay = anchors[p["pjt"]]
            n[2] = (n[2] + (ax - n[0]) * 0.008 + (width / 2 - n[0]) * 0.0001) * 0.8
            n[3] = (n[3] + (ay - n[1]) * 0.008 + (height / 2 - n[1]) * 0.0001) * 0.8
            n[0] = max(24, min(width - 24, n[0] + n[2] * alpha))
            n[1] = max(24, min(height - 24, n[1] + n[3] * alpha))
        alpha = max(0.012, alpha * 0.994)
    for p, n in zip(people, positions):
        p["x"], p["y"] = n[0], n[1]
