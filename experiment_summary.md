How well Gemma, Phi and Llama models turn smart home network events into plain-language narration for the exhibit.

Hardware: Acer Nitro V 15 RTX 5060. Each event is run 5 times per model.

**How the experiment was conducted**
1. Wrote 7 sample network events as JSON, each describing one thing a smart device did (e.g. a plug turning on, a bulb checking for an update etc.).
2. Wrote a prompt asking the model to describe each event in short, plain sentences for museum visitors.
3. Ran each model locally through Ollama. The script loads each model with an untimed warm-up, then sends every event 5 times with the same temperature (0.7) and seed for every model, and saves each answer, its timing and automatic checks to a CSV file.
4. Viewed the results, and counted how often each model included key facts, used technical words, or added details that weren't in the event.

## Results

The prompt asks for exactly two sentences, includes two examples, and says to call missing facts "unknown". There is one event where the server's company and country are unknown.

| Model | Time | Key facts (country, company, cause, encryption) | Exactly 2 sentences | Numbers or technical words | Event 7 (unknown info) | Notes |
|---|---|---|---|---|---|---|
| Gemma 4 E2B | 0.66 s | All included (left out who started it twice) | 35/35 | 0/35 | 5/5 said unknown | Awkward phrasing ("data went to an unknown country run by an unknown company") |
| Gemma 4 E4B | 0.45 s | All included | 35/35 | 0/35 | 5/5 said unknown | Cleanest; repetitive (18 different answers out of 35) |
| Phi-4 Mini | 0.57 s | Skipped "on its own" or the company several times | 32/35 | 6/35 | 0/5 said unknown | Gave the IP address 3 times instead of saying the server was unknown |
| Phi-4 | 4.84 s | All included | 34/35 | 2/35 | 4/5 said unknown | Very slow |
| Llama 3.2 3B | 0.45 s | Left out who started it in 16 of 35 answers | 34/35 | 4/35 | 2/5 said unknown | Often skipped "on its own"; mentioned packets and a web address |
| Llama 3.1 8B | 0.87 s | Left out who started it in 6 of 35 answers | 35/35 | 3/35 | 1/5 said unknown | Usually skipped the unknown country or company; mentioned bytes once |

Speeds depend on the laptop's power and heat state, so compare them within this table only.

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
| Gemma 4 E2B | 0.3–0.8 s |
| Gemma 4 E4B | 0.4–1.0 s |
| Phi-4 Mini | 0.6–1.0 s |
| Phi-4 | 5–10 s |
| Llama 3.2 3B | about 0.5 s |
| Llama 3.1 8B | about 0.9 s |

On a computer with a similar GPU, every model except Phi-4 is fast enough for live narration. On a computer without a dedicated GPU, expect several seconds per answer; this has not been measured.

## Recommendation

Gemma 4 E4B (run locally through Ollama):

- Met every requirement in testing: all key facts included, exactly two sentences, no numbers or technical terms, and "unknown" stated instead of guessed.
- Had the clearest wording of the models tested.
- Answers in under a second on a laptop GPU, fast enough for live narration.
- Runs offline at no cost.

**If the exhibit computer has no dedicated GPU,** Gemma 4 E2B is a good alternative: nearly as accurate and faster, but with more awkward wording.

**Not recommended:**
- Llama 3.1 8B and Llama 3.2 3B: often left out who started the event and rarely said missing information was unknown.
- Phi-4 Mini: adds numbers and addresses, invents details, never said missing information was unknown.
- Phi-4: too slow and too large for an 8 GB GPU.

**Next steps:** confirm which computer will run the exhibit, test on real PingPong events, and finalize the prompt once we've decided which facts the exhibit shows and how long narration can be.