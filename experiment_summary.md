How well Gemma, Phi and Llama models turn smart home network events into plain-language narration for the exhibit.

Hardware: Acer Nitro V 15 RTX 5060. Each event is run 5 times per model.

**How the experiment was conducted**
1. Wrote 7 sample network events as JSON, each describing one thing a smart device did (e.g. a plug turning on, a bulb checking for an update etc.).
2. Wrote a prompt asking the model to describe each event in short, plain sentences for museum visitors.
3. Ran each model locally through Ollama. The script loads each model with an untimed warm-up, then sends every event 5 times with the same temperature (0.7) and seed for every model, and saves each answer, its timing and automatic checks to a CSV file.
4. Read every answer and rated it against the event's known facts: accurate (all facts correct), partly (a fact missing, numbers or addresses included, or unclear wording) or inaccurate (something false). The rating and a note for every answer are in `results_v1_2026-11-07_1516_rated.csv`.

## Results

The prompt asks for exactly two sentences, includes two examples, and says to call missing facts "unknown". There is one event where the server's company and country are unknown.

| Model | Time | Accurate answers | Key facts (country, company, cause, encryption) | Exactly 2 sentences | Numbers or technical words | Event 7 (unknown info) | Notes |
|---|---|---|---|---|---|---|---|
| Gemma 4 E2B | 0.66 s | 29/35 (83%) | All included (left out who started it twice) | 35/35 | 0/35 | 5/5 said unknown | Awkward phrasing ("data went to an unknown country run by an unknown company") |
| Gemma 4 E4B | 0.45 s | 34/35 (97%) | All included | 35/35 | 0/35 | 5/5 said unknown | Cleanest; repetitive (18 different answers out of 35) |
| Phi-4 Mini | 0.57 s | 21/35 (60%), 1 false | Skipped "on its own" or the company several times | 32/35 | 8/35 | 0/5 said unknown | Gave the IP address 3 times instead of saying the server was unknown; listed packet counts and bytes |
| Phi-4 | 4.84 s | 30/35 (86%) | All included | 34/35 | 2/35 | 4/5 said unknown | Very slow; gave the IP address twice |
| Llama 3.2 3B | 0.45 s | 11/35 (31%), 2 false | Left out who started it in 16 of 35 answers | 34/35 | 5/35 | 2/5 said unknown | Often skipped "on its own"; mentioned packets and a web address |
| Llama 3.1 8B | 0.87 s | 23/35 (66%) | Left out who started it in 6 of 35 answers | 35/35 | 4/35 | 1/5 said unknown | Usually skipped the unknown country or company; mentioned packets, bytes and a web address |

Speeds depend on the laptop's power and heat state, so compare them within this table only.

## Is live narration viable?

Criteria: at least 95% of answers accurate, no false answers, and a median response under 2 seconds.

**Yes, with Gemma 4 E4B** on a laptop with a GPU: 34 of 35 answers were accurate, none were false, and the median response was under half a second. It is the only model that meets all three criteria. This should be confirmed with real events and on the exhibit computer.

## Hardware and software requirements

| Model | Download size | Memory needed (approx.) | Fits on an 8 GB GPU |
|---|---|---|---|
| Gemma 4 E2B | 4.6 GB | ~5 GB | Yes |
| Gemma 4 E4B | 6.6 GB | ~7 GB | Yes |
| Phi-4 Mini | 2.5 GB | ~3–4 GB | Yes |
| Phi-4 | 9.1 GB | ~10 GB | No; overflows into system RAM, which caused failed runs |
| Llama 3.2 3B | 2.0 GB | ~3 GB | Yes |
| Llama 3.1 8B | 4.9 GB | ~6 GB | Yes |

**Hardware:** a laptop or desktop with a dedicated GPU with at least 8 GB of memory (tested on an RTX 5060) and 16 GB of system RAM. Without a dedicated GPU, models run on the processor and are much slower.

**Software:** Ollama (free; Windows, macOS and Linux), Python 3 for running the tests (standard library only). Models are downloaded once with `ollama pull` and run offline.

## Cost

All six models run locally, so there is **no API cost**: no per-request fees, no account and no internet connection needed. The only costs are hardware we already own and electricity.

## Expected response latency

| Model | Measured on test laptop (RTX 5060) |
|---|---|
| Gemma 4 E2B | 0.5–1.5 s (median 0.66 s) |
| Gemma 4 E4B | 0.4–1.4 s (median 0.45 s) |
| Phi-4 Mini | 0.4–0.8 s (median 0.57 s) |
| Phi-4 | 3.5–6.8 s (median 4.84 s) |
| Llama 3.2 3B | 0.4–0.7 s (median 0.45 s) |
| Llama 3.1 8B | 0.7–1.2 s (median 0.87 s) |

On a computer with a similar GPU, every model except Phi-4 is fast enough for live narration. On a computer without a dedicated GPU, expect several seconds per answer; this has not been measured.

## Recommendation

Gemma 4 E4B (run locally through Ollama):

- Met every requirement in testing: all key facts included, exactly two sentences, no numbers or technical terms, and "unknown" stated instead of guessed.
- Had the clearest wording of the models tested.
- Answers in under a second on a laptop GPU, fast enough for live narration.
- Runs offline at no cost.

**If the exhibit computer has no dedicated GPU,** Gemma 4 E2B is a good alternative: nearly as accurate with similar speed, but with more awkward wording.

**Not recommended:**
- Llama 3.1 8B and Llama 3.2 3B: often left out who started the event and rarely said missing information was unknown.
- Phi-4 Mini: adds numbers and addresses, invents details, never said missing information was unknown.
- Phi-4: too slow and too large for an 8 GB GPU.

**Next steps:** confirm which computer will run the exhibit, test on real PingPong events, and finalize the prompt once we've decided which facts the exhibit shows and how long narration can be.