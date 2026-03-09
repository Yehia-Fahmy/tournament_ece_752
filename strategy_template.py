import argparse
import time
import math
import json
import requests
import time

SERVER_URL = "http://localhost"

# ═══════════════════════════════════════════════════════════════════════
#  EDIT YOUR STRATEGY HERE
# ═══════════════════════════════════════════════════════════════════════

def strategy(player_index: int, history: list, delta: float) -> float:
    """
    Parameters
    ----------
    player_index : int
        Your position in the group: 0, 1, or 2.

    history : list of lists
        history[t] = [e0, e1, e2] for period t. Empty on first period.

    delta : float
        Continuation probability. The game ends after each round with
        probability 1 - delta.

    Returns
    -------
    float in [0.0, 1.0]
    """
    time.sleep(5)
    return 0.5

# ═══════════════════════════════════════════════════════════════════════
#  DO NOT EDIT BELOW THIS LINE
# ═══════════════════════════════════════════════════════════════════════

def _compute_stage_payoff(efforts: list, player_index: int) -> float:
    E = sum(efforts)
    S = math.sqrt(E) if E > 0 else 0.0
    min_e = min(efforts)
    bonus_recipients = [i for i in range(len(efforts)) if efforts[i] <= min_e + 1e-9]
    bonus = (0.25 * S) / len(bonus_recipients) if player_index in bonus_recipients else 0.0
    return 0.25 * S - (2/3) * efforts[player_index] ** 2 + bonus


def play_session(base: str, session_id: str, student_id: str,
                 player_index: int, player_token: str) -> float:
    print(f"\n  Session : {session_id}  |  Player : {player_index}")
    print("  Waiting for game to start...", end="", flush=True)

    delta = None
    while True:
        state = requests.get(
            f"{base}/api/session/{session_id}/state", timeout=10
        ).json()
        if state["status"] == "active":
            delta = float(state["delta"])
            print(" ready!\n")
            break
        if state["status"] == "finished":
            print(" already finished.")
            return 0.0
        print(".", end="", flush=True)
        time.sleep(1.5)

    history            = []
    period_payoffs     = []  # stage payoff per period (your player)
    auto_moved_periods = []  # periods where you were auto-moved

    while True:
        period = len(history)
        effort = float(strategy(player_index, history, delta))
        effort = max(0.0, min(1.0, effort))

        resp = requests.post(
            f"{base}/api/session/{session_id}/move",
            json={
                "player_index": player_index,
                "player_token": player_token,
                "effort":       effort,
                "period":       period,
            },
            timeout=15,
        )
        if resp.status_code not in (200, 409):
            resp.raise_for_status()

        result = _listen_for_period(base, session_id, period)

        if result.get("status") == "timeout":
            raise RuntimeError(
                f"Server timed out waiting for period {period} to resolve."
            )

        if player_index in result.get("auto_moved", []):
            auto_moved_periods.append(period)

        period_payoffs.append(_compute_stage_payoff(result["efforts"], player_index))
        history = result["history"]

        if result["status"] == "game_over":
            break

    # ── Post-game summary ──────────────────────────────────────────────
    final   = requests.get(f"{base}/api/session/{session_id}/result", timeout=10).json()
    payoffs = final["payoffs"]

    col = 3 * 9 + 4  # width of the efforts column
    print(f"  {'Period':>6}  {'Efforts (P0 / P1 / P2)':<{col}}  {'Your Payoff':>11}")
    print(f"  {'──────':>6}  {'──────────────────────────────':<{col}}  {'───────────':>11}")
    for t, (efforts, sp) in enumerate(zip(history, period_payoffs)):
        efforts_str = " / ".join(f"{e:.4f}" for e in efforts)
        auto_flag   = "  [auto]" if t in auto_moved_periods else ""
        print(f"  {t+1:6d}  {efforts_str:<{col}}  {sp:11.4f}{auto_flag}")

    print(f"\n  Total periods : {final['periods']}")
    print(f"\n  Final payoffs:")
    for k in sorted(payoffs.keys(), key=int):
        marker = "  ← you" if int(k) == player_index else ""
        print(f"    Player {k} : {float(payoffs[k]):.4f}{marker}")

    return float(payoffs.get(str(player_index), 0.0))


def _listen_for_period(base: str, session_id: str, period: int) -> dict:
    url = f"{base}/api/session/{session_id}/listen/{period}"
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode()
            if line.startswith("data: "):
                return json.loads(line[6:])
    raise RuntimeError("SSE stream closed without sending period result")


# ── Test mode ──────────────────────────────────────────────────────────

def run_test(base: str, session_id: str, student_id: str,
             player_index: int | None, player_token: str | None):
    print(f"═══ TEST MODE ═══════════════════════════════════════")
    print(f"  Student : {student_id}")

    if player_index is None or player_token is None:
        print("  Joining session (self-play — no pre-assigned slot)...")
        resp = requests.post(f"{base}/api/session/{session_id}/join", timeout=10)
        resp.raise_for_status()
        info         = resp.json()
        player_index = info["player_index"]
        player_token = info["player_token"]
        print(f"  Assigned slot: Player {player_index}")

    play_session(base, session_id, student_id, player_index, player_token)


# ── Tournament mode ────────────────────────────────────────────────────

def run_tournament(base: str, tournament_id: str, student_id: str):
    print(f"═══ TOURNAMENT MODE ═════════════════════════════════")
    print(f"  Student     : {student_id}")
    print(f"  Tournament  : {tournament_id}")

    print("\n[1/3] Registering...")
    r = requests.post(
        f"{base}/api/tournament/{tournament_id}/register",
        json={"student_id": student_id},
        timeout=10,
    )
    if r.status_code == 200:
        print(f"  Registered ✓  ({r.json()['player_count']} players so far)")
    elif "Already registered" in r.text:
        print("  Already registered ✓")
    else:
        print(f"  Warning: {r.status_code} {r.text}")

    print("\n[2/3] Waiting for round to start...")
    while True:
        status = requests.get(
            f"{base}/api/tournament/{tournament_id}/status", timeout=10
        ).json()
        if status["status"] == "round_active":
            print(f"  Round {status['current_round'] + 1} is active! ✓")
            break
        print(f"  Status: {status['status']}... (checking every 5s)", end="\r", flush=True)
        time.sleep(5)

    print("\n[3/3] Getting group assignment...")
    group = requests.get(
        f"{base}/api/tournament/{tournament_id}/my_group/{student_id}",
        timeout=10,
    ).json()
    print(f"  Group members : {group['group_members']}")

    join         = requests.post(
        f"{base}/api/session/{group['session_id']}/join", timeout=10
    ).json()
    player_index = join["player_index"]
    player_token = join["player_token"]
    print(f"  Your slot     : Player {player_index}")

    print()
    my_payoff = play_session(
        base, group["session_id"], student_id, player_index, player_token
    )

    print("\n  ── Leaderboard ──────────────────────────────────")
    board = requests.get(
        f"{base}/api/tournament/{tournament_id}/leaderboard", timeout=10
    ).json()
    for entry in board["leaderboard"][:10]:
        marker = "  ← you" if entry["student_id"] == student_id else ""
        print(f"  #{entry['rank']:2d}  {entry['student_id']:<24} "
              f"{entry['total_payoff']:.4f}{marker}")


# ── Entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Effort Tournament Client")
    parser.add_argument("--server",       default=SERVER_URL)
    parser.add_argument("--mode",         choices=["test", "tournament"], required=True)
    parser.add_argument("--student-id",   required=True)
    parser.add_argument("--session",      help="Session ID (test mode)")
    parser.add_argument("--player-index", type=int)
    parser.add_argument("--player-token")
    parser.add_argument("--tournament",   help="Tournament ID (tournament mode)")

    args = parser.parse_args()
    base = args.server.rstrip("/")

    if args.mode == "test":
        if not args.session:
            parser.error("--session is required for test mode.")
        run_test(base, args.session, args.student_id,
                 args.player_index, args.player_token)

    elif args.mode == "tournament":
        if not args.tournament:
            parser.error("--tournament is required for tournament mode.")
        run_tournament(base, args.tournament, args.student_id)
