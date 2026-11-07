"""
Runs each model on each event in events.json through a local Ollama server
and saves the outputs, timings and automatic checks to a new CSV file.

Setup:
  1. Install Ollama from https://ollama.com and make sure it is running
  2. Download the models first, e.g.:  ollama pull gemma4:e2b
  3. Set HARDWARE and PROMPT_VERSION below
  4. Run: python run_tests.py

Each run creates its own file, e.g. results_v4_2026-11-06_1714.csv,
so results from different rounds never mix.

"""

import csv
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

OLLAMA = "http://localhost:11434"

# ---------------------------------------------------------------------------
# Settings: edit these
# ---------------------------------------------------------------------------

# Models to test. Check exact tags with:  ollama list
MODELS = [
    "gemma4:e2b",
    "phi4-mini",
    "gemma4:e4b",
    "phi4",
]

# Change this label whenever you change any prompt part below or events.json,
# so each results file says which version produced it.
PROMPT_VERSION = "v2"

# ---------------------------------------------------------------------------
# Prompt, in two parts. Sent as the system prompt, separate from the event.
# Keep this the same for testing.
# ---------------------------------------------------------------------------

# PART 1: GENERAL RULES -- should hold no matter what the exhibit decides.
GENERAL_RULES = """\
You narrate a museum exhibit that shows visitors what their smart home devices \
do on the internet. Visitors have no technical background.

Rules:
- Use plain, everyday words. Leave out web addresses, numbers and technical \
terms, except "encrypted".
- Use only the facts in the event. Add no other details, reasons or explanations.
- If a fact you are asked to include is missing or marked "unknown", say that \
it is unknown. Never guess.
- Reply with only the narration, with no greeting or introduction."""

# PART 2: EXHIBIT-SPECIFIC -- Can update later:
#   - which fields the capture code produces (and their names)
#   - which facts the exhibit should tell visitors about
#   - how long narration can be on the display
LENGTH = "Write exactly two sentences."

FACTS_TO_INCLUDE = """\
- Sentence 1: what the device did, who started it (the user or the device on \
its own), and where the data went (the country and the company that runs the \
server).
- Sentence 2: whether the messages were encrypted, and what that means. \
Encrypted: no one else on the network could read what they said. Not \
encrypted: anyone on the network could."""

# Example events should use the same field names as the real event data.
EXAMPLES = """\
Example 1
Event: {"device": "Smart thermostat", "action": "sent a temperature reading", \
"triggered_by": "the device on its own", "server_run_by": "Microsoft Azure", \
"destination_country": "Ireland", "encrypted": true}
Narration: On its own, the smart thermostat sent a temperature reading to a \
server in Ireland run by Microsoft Azure. The message was encrypted, so no one \
else on the network could read what it said.

Example 2
Event: {"device": "Smart TV", "action": "opened a streaming app", \
"triggered_by": "the user", "server_run_by": "unknown", \
"destination_country": "Germany", "encrypted": false}
Narration: When the user opened a streaming app, the smart TV contacted a \
server in Germany, but the company that runs it is unknown. The message was \
not encrypted, so anyone on the network could read what it said."""

# The full prompt sent to the model (no need to edit this line).
SYSTEM_PROMPT = (
    f"{GENERAL_RULES}\n\n"
    f"For each event: {LENGTH}\n{FACTS_TO_INCLUDE}\n\n"
    f"{EXAMPLES}"
)

HARDWARE = "Acer Nitro V 15 (RTX 5060 laptop)"  # each tester: change this
EVENTS_FILE = "events.json"
RUNS_PER_EVENT = 5   # 5 runs per event for comparisons that go in the report
THINKING = False     # keep off: thinking adds hundreds of extra tokens per reply

# Same settings for every model so the comparison is fair.
# Each run uses SEED + run number: runs differ from each other, but a rerun
# of the whole script with the same settings reproduces the same answers.
TEMPERATURE = 0.7
SEED = 42

# ---------------------------------------------------------------------------
# Talking to Ollama
# ---------------------------------------------------------------------------


def _request(path, payload=None, timeout=600):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        OLLAMA + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def check_ollama():
    """Stop with a clear message if Ollama isn't running or a model is missing."""
    try:
        tags = _request("/api/tags", timeout=10)
    except (urllib.error.URLError, ConnectionError, OSError):
        sys.exit("Ollama isn't running. Start the Ollama app, then run this again.")

    installed = set()
    for m in tags.get("models", []):
        name = m.get("name", "")
        installed.add(name)
        if name.endswith(":latest"):
            installed.add(name[: -len(":latest")])

    missing = [m for m in MODELS if m not in installed]
    if missing:
        sys.exit("These models aren't downloaded: " + ", ".join(missing) +
                 "\nRun 'ollama pull <name>' for each, or remove them from MODELS.")


def unload_model(model):
    """Free the model's GPU memory so the next model has room to load."""
    try:
        _request("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
    except Exception:
        pass


def unload_all():
    """Unload any models already in memory, e.g. from an earlier 'ollama run'."""
    try:
        loaded = _request("/api/ps", timeout=10).get("models", [])
    except Exception:
        return
    for m in loaded:
        unload_model(m.get("model") or m.get("name"))


def generate(model, prompt, seed, system=None):
    payload = {
        "model": model,
        "prompt": prompt,
        **({"system": system} if system else {}),
        "stream": False,
        "think": THINKING,
        "options": {"temperature": TEMPERATURE, "seed": seed},
    }
    try:
        return _request("/api/generate", payload)
    except urllib.error.HTTPError as e:
        # Some models don't accept the "think" setting; retry without it.
        if e.code == 400:
            payload.pop("think")
            return _request("/api/generate", payload)
        # 500 usually means the model failed to load (often out of memory).
        # Free memory, wait a few seconds and try once more.
        if e.code == 500:
            unload_all()
            time.sleep(5)
            return _request("/api/generate", payload)
        raise


def warm_up(model):
    """Load the model with one untimed request so loading time isn't recorded."""
    print(f"Loading {model} ...", flush=True)
    generate(model, "Reply with the word ready.", SEED)


# ---------------------------------------------------------------------------
# Automatic checks
# ---------------------------------------------------------------------------

## Simple regexes to check for technical words, web addresses, and cause/unencrypted

TECH_WORDS = re.compile(
    # "encrypted" is allowed on purpose, so it isn't in this list
    r"\b(packets?|bytes?|kb|mb|gb|megabytes?|tls|ip address|protocol)\b",
    re.IGNORECASE,
)
WEB_ADDRESS = re.compile(
    r"\b[\w-]+(\.[\w-]+)*\.(com|net|org|cn|io|co|ca)\b|\b\d{1,3}(\.\d{1,3}){3}\b",  # domains or IP addresses
    re.IGNORECASE,
)
ON_ITS_OWN = re.compile(r"\b(on its own|by itself|itself|automatic\w*|without (any|you|anyone))\b",
                        re.IGNORECASE)
NOT_ENCRYPTED = re.compile(
    r"(not (scrambled|encrypted|secure)|unencrypted|wasn.t (scrambled|encrypted)|"
    r"weren.t (scrambled|encrypted)|anyone on the network could read)",
    re.IGNORECASE,
)


def _country(event):
    if "destination_country" in event:
        return event["destination_country"]
    m = re.search(r"\(([^)]+)\)", str(event.get("contacted", "")))
    return m.group(1) if m else None


def _yes_no(value):
    return "" if value is None else ("yes" if value else "no")
    

def auto_checks(event, output):
    """Simple checks for required facts and rule-breaking. Blank = not applicable."""
    low = output.lower()

    country = _country(event)
    has_country = (country.lower() in low) if country else None

    company = event.get("server_run_by")
    has_company = (company.split()[0].lower() in low) if company else None

    cause = event.get("triggered_by", "").lower()
    if "user" in cause:
        has_cause = ("user" in low) or ("you " in low) or ("your command" in low)
    elif "own" in cause:
        has_cause = bool(ON_ITS_OWN.search(output))
    else:
        has_cause = None

    has_unencrypted = bool(NOT_ENCRYPTED.search(output)) if event.get("encrypted") is False else None

    leaked = bool(WEB_ADDRESS.search(output))
    if "bytes_sent" in event:
        b = event["bytes_sent"]
        leaked = leaked or str(b) in output.replace(",", "") or f"{b:,}" in output

    # Split only where punctuation is followed by a space or the end,
    # so "api.example.com" and "0.3" don't count as extra sentences.
    sentences = len([s for s in re.split(r"[.!?]+(?:\s+|$)", output) if s.strip()])

    return {
        "mentions_country": _yes_no(has_country),
        "mentions_company": _yes_no(has_company),
        "says_who_caused_it": _yes_no(has_cause),
        "says_unencrypted": _yes_no(has_unencrypted),
        "uses_technical_words": _yes_no(bool(TECH_WORDS.search(output))),
        "leaks_address_or_bytes": _yes_no(leaked),
        "sentences": sentences,
        "words": len(output.split()),
    }


CHECK_COLUMNS = list(auto_checks({}, "").keys())

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, EVENTS_FILE), encoding="utf-8") as f:
        events = json.load(f)

    check_ollama()
    unload_all()

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_path = os.path.join(here, f"results_{PROMPT_VERSION}_{stamp}.csv")
    summary = {}

    # utf-8-sig so Excel shows accented characters correctly
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "prompt_version", "events_file", "model", "hardware",
            "temperature", "seed", "event_number", "run", "input", "output",
            "time_to_first_word_s", "total_time_s", "tokens_out", "tokens_per_sec",
            *CHECK_COLUMNS,
            "accurate (yes/partly/no)", "notes",
        ])

        for model in MODELS:
            times, counts = [], {c: [0, 0] for c in CHECK_COLUMNS[:6]}
            errors = 0

            try:
                warm_up(model)
            except Exception as e:
                print(f"  warm-up failed: {e}")

            for i, event in enumerate(events, start=1):
                for run in range(1, RUNS_PER_EVENT + 1):
                    seed = SEED + run
                    base = [datetime.now().isoformat(timespec="seconds"),
                            PROMPT_VERSION, EVENTS_FILE, model, HARDWARE,
                            TEMPERATURE, seed, i, run, json.dumps(event, ensure_ascii=False)]
                    print(f"{model} | event {i} | run {run} ...", flush=True)
                    try:
                        event_text = json.dumps(event, ensure_ascii=False)
                        r = generate(model, "Event:\n" + event_text, seed,
                                     system=SYSTEM_PROMPT)
                    except Exception as e:
                        errors += 1
                        print(f"  failed: {e}")
                        writer.writerow(base + [""] * (5 + len(CHECK_COLUMNS) + 1)
                                        + [f"ERROR: {e}"])
                        continue

                    ns = 1e9
                    load = r.get("load_duration", 0) / ns
                    prompt_time = r.get("prompt_eval_duration", 0) / ns
                    gen_time = r.get("eval_duration", 0) / ns
                    total = r.get("total_duration", 0) / ns
                    tokens = r.get("eval_count", 0)
                    tps = tokens / gen_time if gen_time else 0
                    output = r.get("response", "").strip()
                    checks = auto_checks(event, output)

                    times.append(total)
                    for c in counts:
                        if checks[c]:
                            counts[c][1] += 1
                            counts[c][0] += checks[c] == "yes"

                    print(f"  {total:.2f}s  {tps:.1f} tok/s  -> {output[:80]}")
                    writer.writerow(base + [
                        output, round(load + prompt_time, 2), round(total, 2),
                        tokens, round(tps, 1),
                        *[checks[c] for c in CHECK_COLUMNS], "", "",
                    ])
                    f.flush()

            unload_model(model)
            summary[model] = (times, counts, errors)

    print(f"\nDone. Results saved to {out_path}\n")
    print("Summary (counts are yes / applicable answers):")
    for model, (times, counts, errors) in summary.items():
        med = f"{statistics.median(times):.2f}s" if times else "n/a"
        parts = [f"{c}={y}/{n}" for c, (y, n) in counts.items() if n]
        print(f"  {model}: median {med}, failed {errors}, " + ", ".join(parts))
    print("\nThe checks are simple word matches. Read the answers to judge "
          "invented details and cause errors, then fill in 'accurate' and 'notes'.")


if __name__ == "__main__":
    main()