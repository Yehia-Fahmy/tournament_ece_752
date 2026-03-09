## ECE 752/493 Tournament Client

This repository contains a Python client and strategy template for the ECE 752/493 repeated–effort game tournament. You will implement a single function, `strategy`, that repeatedly chooses an effort level for your agent to maximize its total utility when matched against two other agents.

### Game Overview

- **Players**: 3 agents per game.
- **Rounds**: Random length. After each round, the game continues with probability \( \delta \in (0, 1) \) and ends with probability \( 1 - \delta \). The value of \( \delta \) is known to all players before the game starts.
- **Action each round**: Agent \( i \) chooses an effort level \( a_{i,r} \in [0, 1] \).
- **Cost of effort**: \( C_i(a_{i,r}) = \frac{2}{3} a_{i,r}^2 \).
- **Total group effort**: \( A_r = a_{1,r} + a_{2,r} + a_{3,r} \).
- **Project surplus**: \( S(A_r) = p A_r \). In the template, \( p = 1 \), so \( S(A_r) = \sqrt{A_r} \) via `_compute_stage_payoff`.
- **Immediate payoff for agent i in round r**:
  - Base share: \( \frac{1}{4} S(A_r) \).
  - Bonus: The remaining \( \frac{1}{4} S(A_r) \) goes to the agent(s) with **lowest effort** that round (split equally if tied).
  - Cost: Effort cost \( \frac{2}{3} a_{i,r}^2 \).

Your goal is to design a strategy for choosing \( a_{i,r} \) each round to maximize your **discounted total payoff** over the whole game.

### Repository Contents

- **`strategy_template.py`**: Tournament client and strategy template.
  - You should **only edit** the `strategy` function at the top of this file.
  - The rest of the file handles communication with the tournament server and must remain unchanged.
- **`tournament.pdf`**: The full written specification of the game and tournament.

### Implementing Your Strategy

In `strategy_template.py`, edit:

- **Function**: `strategy(player_index: int, history: list, delta: float) -> float`
- **Arguments**:
  - `player_index`: Your index in the group (`0`, `1`, or `2`).
  - `history`: A list of past efforts, where `history[t] = [e0, e1, e2]` for period `t`. This list is **empty on the first period**.
  - `delta`: The continuation probability \( \delta \), shared by all players for the current game.
- **Return value**:
  - A single `float` in \([0.0, 1.0]\) representing your chosen effort for the current period.

**Important constraints**:

- **Time limit**: `strategy` must run in **under 4 seconds** every time it is called, or the server may auto-move on your behalf.
- **Side effects**: Avoid heavy I/O or long network calls inside `strategy`; it may be called many times per game.
- **Purity**: You are free to maintain your own state via `history` (and any internal structures you build from it), but do not modify global constants or networking code.

The template currently implements:

```python
def strategy(player_index: int, history: list, delta: float) -> float:
    time.sleep(5)
    return 0.5
```

You should **replace** this body with your own logic.

### Installation & Requirements

- **Python**: 3.10+ recommended.
- **Dependencies**:
  - `requests`

Install dependencies with:

```bash
pip install requests
```

### Running in Test Mode

Use test mode to debug and tune your strategy against a test session you create on the tournament website.

1. **Create a test session** on the tournament web page (`Create Test Session`).
2. Note the **Session ID** that the page shows you.
3. Run the client locally, pointing it at the tournament server and specifying test mode:

```bash
python strategy_template.py \
  --server http://maslab-hps1.uwaterloo.ca/tournament \
  --mode test \
  --student-id YOUR_STUDENT_ID \
  --session SESSION_ID_FROM_WEBSITE
```

Optional arguments for test mode:

- `--player-index`: Force a specific player index (`0`, `1`, or `2`) instead of letting the server assign one.
- `--player-token`: Use a pre-assigned player token if you already joined the session.

If `--player-index` or `--player-token` are omitted, the client will join the session automatically and print your assigned slot.

### Running in Tournament Mode

When the official tournament runs, you will be given a **Tournament ID**.

Run:

```bash
python strategy_template.py \
  --server http://maslab-hps1.uwaterloo.ca/tournament \
  --mode tournament \
  --student-id YOUR_STUDENT_ID \
  --tournament TOURNAMENT_ID_FROM_INSTRUCTOR
```

The client will:

- Register you for the tournament (or detect that you are already registered).
- Wait for the current round to start.
- Fetch your group assignment and automatically join the appropriate session.
- Play the full game using your `strategy` function.
- Display your period-by-period efforts and payoffs and show the tournament leaderboard.

### Tips for Designing a Strategy

- **Use history wisely**: Study how others’ efforts evolve and respond strategically (e.g., punish deviations from cooperative behavior, reward consistent cooperation, etc.).
- **Balance effort and cost**: High effort boosts surplus but is costly; low effort may earn the bonus but can reduce the group total.
- **Account for \( \delta \)**: When \( \delta \) is high, future payoffs matter more and long-run cooperative strategies may be more attractive; when \( \delta \) is low, the game is effectively shorter.
- **Test extensively**: Use the test sessions to compare variations of your strategy and verify that it runs within the time limit.

### Troubleshooting

- **Timeouts / auto-moves**:
  - If you see periods marked as `[auto]` in the summary, your client likely didn’t respond in time. Profile and simplify `strategy`.
- **Connection errors**:
  - Check VPN / network access to the tournament server.
  - Ensure the `--server` URL is correct and reachable.
- **Logic bugs**:
  - Add temporary `print` statements or logging in `strategy` during testing (but remove or minimize noisy output for the final tournament).

### License / Academic Honesty

This code is provided as a **template** for the ECE 752/493 course tournament. Follow your course policies on collaboration and academic integrity when implementing and sharing your strategy.

