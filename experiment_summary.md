
How well Gemma and Phi models turn smart home network events into plain-language narration for the exhibit.

Hardware: Acer Nitro V 15 RTX 5060. Each event is run 5 times per model.

**How the experiment was conducted**
1. Wrote 7 sample network events as JSON, each describing one thing a smart device did (e.g. a plug turning on, a bulb checking for an update etc.).
2. Wrote a prompt asking the model to describe each event in short, plain sentences for museum visitors.
3. Ran each model locally through Ollama. The script loads each model with an untimed warm-up, then sends every event 5 times with the same temperature (0.7) and seed for every model, and saves each answer, its timing and automatic checks to a CSV file.
4. Viewed the results, and counted how often each model included key facts, used technical words, or added details that weren't in the event.

## Results

The prompt asks for exactly two sentences, includes two examples, and says to call missing facts "unknown". There is one event where the server's company and country are unknown.

| Model       | Time   | Key facts (country, company, cause, encryption)   | Exactly 2 sentences | Numbers or technical words | Event 7 (unknown info) | Notes                                                                          |
| ----------- | ------ | ------------------------------------------------- | ------------------- | -------------------------- | ---------------------- | ------------------------------------------------------------------------------ |
| Gemma 4 E2B | 0.76 s | All included (left out who started it twice)      | 35/35               | 0/35                       | 5/5 said unknown       | Awkward phrasing ("data went to an unknown country run by an unknown company") |
| Gemma 4 E4B | 0.97 s | All included                                      | 35/35               | 0/35                       | 5/5 said unknown       | Cleanest; repetitive (18 different answers out of 35)                          |
| Phi-4 Mini  | 0.97 s | Skipped "on its own" or the company several times | 32/35               | 6/35                       | 0/5 said unknown       | Gave the IP address 3 times instead of saying the server was unknown           |
| Phi-4       | 9.50 s | All included                                      | 34/35               | 2/35                       | 4/5 said unknown       | Gave the IP address twice; very slow                                           |

Speeds depend on the laptop's power and heat state, so compare them within this table only.

## Hardware and software requirements

| Model | Download size | Memory needed (approx.) | Runs on Raspberry Pi 5 (8 GB) | Runs on test laptop GPU (8 GB) |
|---|---|---|---|---|
| Gemma 4 E2B | 4.6 GB | ~5 GB | Likely | Yes, fully on GPU |
| Gemma 4 E4B | 6.6 GB | ~7 GB | Tight; a 16 GB Pi is safer | Yes, fully on GPU |
| Phi-4 Mini | 2.5 GB | ~3–4 GB | Yes | Yes, fully on GPU |
| Phi-4 | 9.1 GB | ~10 GB | No | Partly; overflows into system RAM, which caused failed runs |

**Software:** Ollama (free; Windows, macOS, Linux and 64-bit Raspberry Pi OS), Python 3 for running the tests (standard library only). Models are downloaded once with `ollama pull` and run offline.

## Cost

All four models run locally, so there is **no API cost**: no per-request fees, no account and no internet needed on demo day. The only costs are hardware you already own (Raspberry Pi or laptop) and electricity. An accelerator for the Pi to increase processing speed (Raspberry Pi AI HAT+ 2, about $200 USD) is not needed based on these results.

## Expected response latency

| Model | Test laptop (measured) | Raspberry Pi 5 (estimated) |
|---|---|---|
| Gemma 4 E2B | 0.3–0.8 s | ~8–12 s |
| Gemma 4 E4B | 0.4–1.0 s | ~15–25 s |
| Phi-4 Mini | 0.7–1.0 s | ~10–15 s |
| Phi-4 | 6–10 s | Not possible |

Pi estimates are based on published Pi 5 benchmarks (about 7–8 tokens, or word pieces, per second for Gemma 4 E2B) and a two-sentence answer of about 50 tokens, plus time to read the prompt. **These have not been measured yet** and should be confirmed on the Pi. At these speeds, live narration on the Pi would have a noticeable delay; pre-generating narration for common events (Version B) would avoid it.

## Recommendation

Gemma 4 E2B (run locally through Ollama):

- Met every requirement in testing: all key facts included, exactly two sentences, no numbers or technical terms, and "unknown" stated instead of guessed.
- Is the fastest model tested and the only accurate one small enough to run well on the Raspberry Pi.
- Runs offline at no cost.

**If the exhibit uses a laptop to run the model,** Gemma 4 E4B is a good alternative: equally accurate with smoother wording, but slower and more repetitive.

**Not recommended:** Phi-4 Mini (adds numbers and addresses, invents details, never said missing information was unknown) and Phi-4 (too slow and too large for the available hardware).

**Next steps:** measure Gemma 4 E2B and E4B speed on the Pi (if using), test on real PingPong events, and finalize the prompt once you've decided which facts the exhibit shows and how long narration can be.