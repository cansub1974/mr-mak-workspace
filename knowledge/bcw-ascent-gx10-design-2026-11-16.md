# BCW Ascent GX10 design — 16 November 2026

Jason has the ASUS Ascent GX10 (NVIDIA GB10, 128 GB unified memory, DGX OS,
arm64). The deployment design for the isolated work LAN was settled question by
question and confirmed. Nothing is built yet. Work runs BCW V0.16
(`release/0.16`); the changes become V0.17. The full plan, build stages and
acceptance observations are in the BCW card tab `ascent-gx10.html`.

## Decisions

- **Roles.** The Ascent is a stateless compute server plus Gitea: llama-server
  (router mode) serving Qwen3.8-Flash-Next at 256k (default) and gpt-oss-120b at 128k
  (one loaded at a time) for chat, Qwen3-Embedding-4B and
  Qwen3-Reranker-0.6B for retrieval, a Docling parsing service, ComfyUI with
  Qwen-Image-Edit at FP8, Codex CLI, Gitea, SSH with tmux. HAL3000 keeps the
  BCW stack and every record: library rows, passages, vectors, approvals.
  Six users reach everything through BCW in a browser.
- **Inference server is llama-server, not Ollama.** BCW's adapter forwards chat
  to `<model URL>/v1/responses`, which llama-server serves, but BCW probes
  `/api/tags` (Ollama-only) in `v2/bcw_desktop/model_settings.py` (two places),
  `v2/bcw_release.py` and `v2/scripts/verify_model.py`. V0.17 switches the
  probe to `/v1/models`, which Ollama serves too, so home and the laptop
  fallback keep running Ollama.
- **Chat model chosen by a home bake-off** (decided 17 Nov 2026) of
  gpt-oss-120b MXFP4 (63.4 GB, provisional default), Qwen3.8-27B Q8_0 (29 GB,
  dense, slow for six users) and Qwen3.8-Flash-Next UD-IQ4_XS (93.7 GB,
  125B/6B active, does not fit beside ComfyUI). All three are downloaded and
  travel to work; the runner-up is the fallback. Tests: tool call through the
  Codex adapter, tokens/s at 1 and 6 users, a Codex task, cited Assistant
  answers, image edit during chat. Qwen3.5-122B was dropped for Qwen3.8.
  **Result (18 Nov 2026): gpt-oss-120b chosen.** Measured on the Ascent with
  llama.cpp b12462 (1ef8c5d68), CUDA 13.0, driver 580.178.04: gpt-oss-120b
  pp2048 1888 / tg128 60.8 tok/s; Flash-Next 1102 / 33.0 (87.2 GiB weights,
  94 GiB used and 26 GiB available with one 32k server, so no room for
  ComfyUI); Qwen3.8-27B 936 / 8.4. gpt-oss and Flash-Next both returned
  correct tool calls on `/v1/chat/completions` and `/v1/responses` (BCW's
  adapter path).
  **Revised 18 Nov 2026: 256k context is required** and gpt-oss-120b stops at
  131,072 tokens (its config). Decision: both models, one loaded at a time;
  gpt-oss at 128k default, Flash-Next at 256k on demand. Flash-Next at 256k
  measured 71.1 GB GPU (63.4 GB at 32k), 19 GiB system memory left, so no
  ComfyUI beside it. Two llama-server instances: a chat router (models-max
  1, presets with pinned `c`) and an always-loaded retrieval server, so
  swaps never evict the embedder. BCW V0.17 adds a Standard / Long context
  choice and frees ComfyUI (its `/free` endpoint) before loading Flash-Next
  and unloads Flash-Next (router `/models/unload`) before an image job.
  Router facts (README read 18 Nov 2026): INI presets keyed by CLI argument
  names, `load-on-startup`, `--models-max`, `--models-memory-margin`; a model
  serving requests is never unloaded, and if nothing can be unloaded the new
  model loads anyway, so the busy-swap case must be tested. `--lazy-mode`
  auto reads tensors over 4 GiB (Flash-Next's n-gram table) from disk.
  Qwen3.8-27B stays a spare.
  **Default changed 20 Nov 2026 to Flash-Next:** gpt-oss-120b failed a
  number of the owner's tasks that Flash-Next did well. `load-on-startup`
  moved to `[flash-next]` in `~/llm/chat.ini`; OpenCode default
  `ascent/flash-next`; Codex `model = "flash-next"`, context 262144.
  gpt-oss is now the image-work model: switch to it before ComfyUI jobs.
  Image model at FP8 not BF16; image jobs slow chat for up to 90 seconds.
- **Coding harness is Codex CLI** on HAL3000 (BCW and MCM development, in
  clones beside bare repos, never the production folder) and on the Ascent.
  HAL3000 reaches the Ascent over SSH and tmux. No code-server, ttyd or Mr Mak
  change: only the two administered machines need a full harness.
- **Library scope**: curated references, standards, specifications and vendor
  documents plus the archive of received and issued reports.
- **Parsing**: Docling on the Ascent (Traditional Chinese and English OCR).
- **Index store**: PostgreSQL with pgvector and full-text search in BCW's
  existing `db` container (pgvector image, same major). Chroma and the
  in-memory BM25 pass are replaced. Vectors at 1024 or 1536 dimensions via
  Qwen3-Embedding truncation. Rerank on the Ascent after fusion.
- **Ingestion**: watched Mother folders gated by category. References enter
  as uncertain and need an approver (bulk-approve for the first load); reports
  become current on arrival. Changed files create a new revision and supersede
  the old; removed files are flagged, never deleted.
- **User access**: Assistant library tool with citations that open the original
  at the page, a Library search page, and a Preliminary Review workflow saving
  a cited findings record for item-by-item accept or dismiss. All users read
  the whole library; approvers alone change status.
- **Build and test everything at home online; the unit travels complete,
  once.** It never comes home and never connects beyond the isolated LAN
  again. Every later update is an in-place kit prepared at home (application
  level; the OS is frozen), carried on the work drive and checksum-recorded.
  The Ascent keeps a full offline toolchain, apt and pip caches, source
  tarballs and spare model files (the two chat candidates not chosen, Qwen3-Embedding-8B,
  Qwen3-Reranker-4B, a GGUF Qwen-Image-Edit) on its own SSD. The Transcend
  stays the BCW kit and Git bundle drive. The departure checklist in the card
  tab (image, recovery USB, offline toolchain, network profile, services off,
  time source, accounts, runbook, spares, cold power cycle) gates the move.
- **Network: open on the LAN** by Jason's decision (no API key, no host
  firewall). Fixed address agreed with the site network owner first.
- **Backup**: configuration repo pushed to HAL3000; a full golden image
  (about 150 GB) on a 1 TB drive that lives at work, taken at the end of home
  acceptance (the home disks cannot hold it: D: had about 127 GB free on
  16 Nov 2026) and refreshed after major kits; an Ubuntu Desktop ARM64 live
  USB that boots the Ascent and takes and restores the image (NVIDIA's System
  Repair method, non-destructive); the ASUS factory recovery USB as last
  resort (it erases the SSD); an on-device snapshot before every
  update; optionally a spare SSD. Gitea repos push-mirror to HAL3000.
- **Rollout: one release, V0.17**, with the Ascent, in one HAL3000 maintenance
  window. The review workflow is therefore accepted at home against a seeded
  library.
- **Source at work**: bare Git repos on HAL3000 for BCW and MCM, synced by Git
  bundles on the update drive; Gitea on the Ascent for on-site software.

## Facts found (release/0.16, 16 November 2026)

- BCW already has a technical library in the Docker API (`bcw/api.py`,
  `bcw/documents.py`, `bcw/retrieval.py`, `bcw/docling_service.py`): Postgres
  `Document` rows with category policy/reference/report, status
  current/superseded/uncertain, approver decision gate, immutable originals,
  Library UI tab. Ingestion is one upload at a time; search is Python BM25
  reloading all passages per query plus optional Chroma; production compose
  leaves `CHROMA_URL` empty, so the deployed library is keyword-only; the
  Docling image is not in the shipped kit; the V0.16 Assistant tool set
  (`v2/bcw_desktop/harness_tools.py`) has no library tool.
- llama-server (documentation read 16 Nov 2026): serves `/v1/responses` by
  converting to chat completions; no `/api/tags`; router mode with
  `--models-dir`, `--models-preset`, `--models-max`, LRU unload;
  `/v1/embeddings` and `/v1/rerank` (`--embeddings`, `--reranking`); slots
  `--parallel`, unified KV, `--cache-reuse`; `--api-key`, `--host`.
- Pi harness: terminal only, no web UI, no permission system, direct llama.cpp
  router integration. Reserve harness if Codex misbehaves with the conversion.
- Mr Mak: Windows Tauri app, service bound to 127.0.0.1, fixed agent list via
  ConPTY; cannot run on the Ascent or target a remote host; its PowerShell tab
  can SSH to the Ascent today.

## Verified downloads and procedures (16 November 2026)

- Chat: `ggml-org/gpt-oss-120b-GGUF` file `gpt-oss-120b-MXFP4.gguf` (63.4 GB,
  single file; the repo default tag points at an eagle3 draft, so name the file).
- Embeddings: `Qwen/Qwen3-Embedding-4B-GGUF` `Qwen3-Embedding-4B-Q8_0.gguf`
  (4.28 GB); spare `Qwen/Qwen3-Embedding-8B-GGUF` Q8_0 (8.05 GB).
- Rerankers: `Qwen/Qwen3-Reranker-0.6B` (1.19 GB) and `-4B` (8 GB) exist only
  as safetensors; the official GGUF repo is not public. Convert with llama.cpp.
- Chat candidates (Qwen3.8, released August 2026; check Hugging Face for
  newer releases before fixing a model choice): `unsloth/Qwen3.8-27B-GGUF`
  `Qwen3.8-27B-Q8_0.gguf` (29.0 GB, Apache 2.0) and
  `unsloth/Qwen3.8-Flash-Next-GGUF` folder `UD-IQ4_XS/` (93.7 GB; Qwen
  Community licence permits internal use; architecture `qwen4_exp_text`, may
  need a very recent llama.cpp). Qwen model card: SWE-bench Pro 62.5
  Flash-Next, 61.7 27B. Total download about 238 GB, done 17 Nov 2026.
- Image edit: `Comfy-Org/Qwen-Image-Edit` (renamed from `_ComfyUI`)
  `split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors`
  (20.5 GB; no plain e4m3fn build for 2511). Text encoder and VAE are in
  `Comfy-Org/Qwen-Image` (renamed): `qwen_2.5_vl_7b_fp8_scaled.safetensors`
  (9.38 GB) and `qwen_image_vae.safetensors` (254 MB). ComfyUI's 2511 tutorial
  uses the bf16 model; this plan uses fp8mixed for the memory budget.
- DGX Spark docs (docs.nvidia.com/dgx/dgx-spark, updated 4 Nov 2026): first
  boot by display and keyboard or Wi-Fi hotspot (SSID on the Quick Start Guide
  sticker); updates `apt update`, `apt dist-upgrade` (not `upgrade`),
  `fwupdmgr refresh/upgrade`; never install `nvidia-dkms-*` (Secure Boot).
  The update and recovery pages are marked Founders Edition only; OEM
  recovery images come from the OEM. ASUS's GX10 support page renders its
  download list with JavaScript, so it was not readable by fetch; check it in
  a browser. Factory recovery erases the SSD and needs a 16 GB or larger USB.
  System Repair uses an Ubuntu Desktop ARM64 live USB and does not erase.
  Internal SSD: NVMe M.2, self-encrypting; replaceability not documented.

## Codex on the Ascent (working 18 Nov 2026)

- Codex CLI 0.170.0 via `sudo apt install nodejs npm` and `sudo npm install -g
  @openai/codex`. `~/.codex/config.toml`: `model_provider = "llamacpp"`,
  `[model_providers.llamacpp]` with `base_url = "http://127.0.0.1:8080/v1"` and
  `wire_api = "responses"` (the only supported value), `model_context_window`
  matching the preset `c`. Without that file Codex calls OpenAI and fails
  with "incorrect API key".
- Codex accepts a placeholder key (`echo sk-local | codex login
  --with-api-key`) so it never needs a ChatGPT sign-in, which is impossible
  offline at work.
- GUI: VS Code arm64 `.deb` (kept in `~/offline`) plus extension
  `openai.chatgpt` (has a linux-arm64 build). VS Code's Copilot chat also
  offers a "Codex" agent that wants to download an agent SDK: that is not the
  OpenAI extension; do not use it. Codex needs an open folder.
- Model switching: chat router with `~/llm/chat.ini` (`gpt-oss-120b` c 131072
  loaded at startup, `flash-next` c 262144), `--models-max 1`; `~/bin/codex-use
  fast|long` rewrites `model` and `model_context_window` in config.toml.

## OpenCode on the Ascent (18 Nov 2026)

- Chosen over DeepSeek Harness (`deepseek-ai/deepseek-harness`, MIT, still
  v0.2.2 release candidates, web UI via `npx @deepseek-ai/dsh web`, no
  documented local OpenAI-compatible provider; its community desktop has no
  Linux build). OpenCode (`anomalyco/opencode`, v1.19.6) ships
  `opencode-desktop-linux-arm64.deb` and `opencode-linux-arm64.tar.gz`, both
  kept in `~/offline`; CLI extracted to `~/bin`.
- `~/.config/opencode/opencode.json`: provider `ascent` with npm
  `@ai-sdk/openai-compatible`, baseURL `http://127.0.0.1:8080/v1`, models
  `gpt-oss-120b` (context 131072) and `flash-next` (262144); `/models`
  switches, and the router swaps the loaded model. The provider package is
  fetched on first run, so run it once at home before departure.

## Chat server as a service (18 Nov 2026, survives reboot)

- `/etc/systemd/system/llama-chat.service`, enabled: user `bmt01`, runs
  `build/bin/llama-server --models-preset ~/llm/chat.ini --models-max 1 --host
  127.0.0.1 --port 8080`, `Restart=on-failure`. `chat.ini` holds
  `gpt-oss-120b` (c 131072, load-on-startup), `flash-next` (c 262144) and
  `qwen3.8-27b` (c 262144); OpenCode lists all three. Switching unloads the
  old model unless it is still answering. Restart the service after editing
  `chat.ini`. Host changes to the LAN address at work (Q14).
- Retrieval server (18 Nov 2026): `/etc/systemd/system/llama-retrieval.service`,
  enabled, `--models-preset ~/llm/retrieval.ini --models-max 2 --host 127.0.0.1
  --port 8081`; presets `embed` (Qwen3-Embedding-4B Q8_0, `embeddings = true`)
  and `rerank` (Qwen3-Reranker-0.6B converted to Q8_0 GGUF, 610 MB,
  `reranking = true`), both load-on-startup. Verified: embeddings 2560
  dimensions; rerank scored a direct answer 1.0 and unrelated text 0.0 (a
  loosely related pair scored only 0.016, so scores are sharp, not graded).
  Spares downloaded: Qwen3-Embedding-8B Q8_0 and Qwen3-Reranker-4B (converted
  to `~/models/qwen3-reranker-4b/`).
- Docling (18 Nov 2026): BCW's own `Dockerfile.docling` and
  `bcw/docling_service.py` from `release/0.16`, copied to `~/docling` by scp
  (large terminal pastes get mangled; copy files instead), built on the
  Ascent as `bcw-docling:0.1.0` (Docling 2.132.0, CPU torch 2.8.0, EasyOCR
  ch_tra+en, models baked in, offline). Container `docling`, `--restart
  unless-stopped`, `127.0.0.1:8793`, `POST /extract`; verified on a PDF.
  Runs on CPU to keep GPU memory for the chat models. Docker 29.6.2 is part
  of DGX OS.
- ComfyUI (18 Nov 2026): cloned to `~/src/ComfyUI`, venv `~/venvs/comfy`;
  pip resolved torch 2.15.0+cu132 (driver reports CUDA 13.0; GPU detected and
  an image edit ran; suspect this first if CUDA errors appear). Qwen-Image-
  Edit 2511 fp8mixed, text encoder and VAE moved into `models/` inside the
  ComfyUI folder (do not delete it when reinstalling). Service
  `comfyui.service`, enabled, `--listen 127.0.0.1 --port 8188`. Edit verified
  with the 2511 template. Do not run image jobs while Flash-Next is loaded.
- Vision (19 Nov 2026): gpt-oss-120b is text-only. `mmproj-F16.gguf` from
  each unsloth repo downloaded beside Flash-Next and Qwen3.8-27B and set as
  `mmproj =` in their `chat.ini` sections; OpenCode marks both with
  `attachment: true` and image input modalities.
- Gitea (19 Nov 2026): Docker `gitea/gitea:28.4.0` (arm64), container
  `gitea`, `--restart unless-stopped`, data in `~/gitea`, web
  `127.0.0.1:3000`, SSH `127.0.0.1:2222`, `GITEA__server__OFFLINE_MODE=true`,
  SQLite; admin account created. At work: change `ROOT_URL` and the port
  bindings to the LAN address and set push mirrors to HAL3000.
- Offline toolkit (19 Nov 2026): `ascent/offline-toolkit.sh` in the card
  folder, copied by scp and run in tmux; builds `~/offline/{debs,docker,npm,
  src,venvs,config}` with SHA256SUMS and `toolkit.log`. apt now keeps every
  downloaded .deb (`/etc/apt/apt.conf.d/01keep-debs`). Re-run it after any
  install so the kit stays complete. Packages it could not download are
  listed in `~/offline/debs-not-downloadable.txt`.
  First run: 2,716 .debs (6.4 GB), about 14 GB in all; 26 not downloadable:
  ASUS desktop/OOBE customisation (local), the OpenCode desktop .deb (copy
  kept in `~/offline`), Ubuntu Pro ESM builds (freerdp, node-lodash,
  python3-pip, python3-wheel) and superseded Mesa, GStreamer and HP printer
  versions. None are needed by the services; the golden image covers them.
- Automatic updates off (20 Nov 2026): `unattended-upgrades` was never
  installed; disabled `apt-daily.timer`, `apt-daily-upgrade.timer`,
  `motd-news.timer`, `fwupd-refresh.timer`, `ua-timer.timer`,
  `esm-cache.service`; `snap refresh --hold`; `20auto-upgrades` set to "0".
  Updates now happen only when run by hand. Note: `systemctl disable` with a
  missing unit aborts the whole command, so disable units one at a time.
- Offline test (20 Nov 2026): network unplugged, Ascent restarted; services
  came up at boot and OpenCode answered on gpt-oss-120b.
  Codex `exec --skip-git-repo-check` answered on flash-next (Codex refuses
  outside a git repo without that flag). Warnings seen: bubblewrap sandbox
  needs user namespaces (Ubuntu 24.04 AppArmor restricts them; fix only if
  Codex fails to run commands, and it is a security change needing the
  owner's confirmation); "model metadata for flash-next not found" is
  harmless because `model_context_window` is set.
- Configuration repository (21 Nov 2026): `~/ascent-config` on the Ascent,
  built by an OpenCode agent on Flash-Next (no sudo), pushed to Gitea repo
  `bmt01/ascent-config` (private, pushed 21 Nov 2026). Holds llm presets, service units, apt
  settings, Codex/OpenCode config, `~/bin` scripts, Docling build files,
  ComfyUI workflows, `docker/inspect.json`, and `state/` (versions,
  packages, models, unit states). Secrets excluded (Gitea app.ini, Codex
  auth.json, OpenCode auth). bmt01 is not in the docker group, so docker
  commands need sudo. `ascent/ascent-config.sh` in the card folder is a
  scripted alternative for refreshing it.
- Memory in Flash-Next default mode (21 Nov 2026, everything running plus
  desktop, OpenCode desktop and Firefox): 3.9 GiB available, about 10 GiB of
  swap holding old pages. Chat llama-server 23.5 GB resident on the CPU side
  (RSS) plus its GPU allocation, which RSS does not show; everything else is
  under 0.5 GB each. The 19 GiB measured on 18 Nov was a standalone server
  without retrieval, Docling or Gitea. Accepted for now; risk is a large
  Docling OCR job during heavy chat. At work run headless (no desktop
  session) to gain a few GB. ComfyUI had been running outside its unit
  (started from an OpenCode session); it was put back under
  `comfyui.service` on 21 Nov.
- Admin skill: `ascent/skills/ascent-admin/SKILL.md` in the card folder,
  copied to `~/ascent-config/skills/`; OpenCode and Codex reach it through a
  pointer line in `~/.config/opencode/AGENTS.md` and `~/.codex/AGENTS.md`.
  First run found the stray ComfyUI and an emptied `docker/inspect.json`
  (restored from Git history).
- Cold power cycle (21 Nov 2026): passed; every service came back by
  itself. The Ascent stays off after power returns until the power button is
  pressed, and the monitor may stay black after a full power cut while the
  machine is up (SSH works). After boot with Flash-Next loaded: 1.5 GiB
  available, swap in use at idle. ComfyUI dies with CUDA out-of-memory if it
  starts after Flash-Next has loaded (seen 21 Nov when restarted by hand;
  `Restart=on-failure` recovered it). Fixed 21 Nov with a drop-in
  `/etc/systemd/system/llama-chat.service.d/after-comfyui.conf` with
  `After=comfyui.service` (also in `~/ascent-config/systemd/`), so ComfyUI
  takes its GPU context first. The Gitea remote URL carries the user name
  `bmt01`, so a push only asks for the password.
- Stage 1 services all running at home by 19 Nov 2026. Remaining before
  departure: the departure checklist in the card tab.

- V0.17 build started 21 Nov 2026 on local branch `release/0.17` (from
  `release/0.16`, worktree `bcw-release-0.16`). Code map findings: v2 has no
  document library (library, Docling and retrieval exist only in the 0.1
  prototype `bcw/`); BCW data is SQLite (`.runtime/context.sqlite`), the only
  Postgres is Nextcloud's; v2 has no ComfyUI or image feature. Decisions:
  library in a new, separate pgvector Postgres 16 container (owner, 21 Nov);
  Ollama stays a supported backup model server (owner); image editing is
  built into the BCW Assistant in V0.17 through ComfyUI on the Ascent, with
  BCW swapping the chat router to gpt-oss first and back after (owner, 21
  Nov). During an image window (about 3 min) chat pauses with a notice and
  resumes on Flash-Next; waiting edits run together (owner, 21 Nov).
  Change 1 done
  (commit 6d97a0e): discovery via `/v1/models`; Ollama detected by
  `/api/version` and keeps its capability, digest and template checks;
  `model_server` saved in config; `think` sent only to Ollama; 180 s turn
  timeout for llama.cpp (router swaps); UI renamed "Model server". Full
  pytest 841 passed. Still Ollama-only: kit scripts `verify_model.py`,
  `bcw_release.py` digest check, `tools/work_setup` (handle in the Kit change).
  Change 2 (library database) done (commit 6d97a0e on release/0.17, not pushed), 21 Nov: `library_db.py`
  (schema v1: sources, documents, revisions, passages; tsvector 'simple',
  pg_trgm for Chinese substring search via ILIKE, vector(1024) HNSW;
  versioned `library_schema`), psycopg[binary] 3.3.9 pinned, Compose
  service `library-db` (`bcw/library-db:0.1.0` from pgvector/pgvector:pg16,
  PostgreSQL 16.16, pgvector 0.8.7) on network `front`, port 127.0.0.1:8803
  (rehearsal 8903, via `Deployment.library_port`), volume `library-db`.
  Upgrade safety: `LEGACY_VOLUMES` plus `ADDED_VOLUMES`; maintenance accepts
  a pre-V0.17 volume set; V0.17 update adds `BCW_LIBRARY_DB_PASSWORD` to an
  existing .env (`ensure_environment_secrets`); restoring a pre-V0.17 backup
  archives the library volume to `data/retired-volumes/<time>` and removes
  it (the earlier release would refuse an extra volume); restoring a V0.17
  backup recreates a retired volume. Full suite 849 passed. Still to do:
  run `migrate()` at bridge startup, ship the image in the kit, docs.
  Change 3 (document reading) done (commit 6d97a0e on release/0.17, not pushed): `library_extract.py`
  posts to Docling `/extract` (50 MiB limit, merges element passages per
  first provenance page, chunks of 1800 chars); on outage, timeout, 422 or
  over-limit it falls back to `library_extract_worker.py` run in the
  pinned networkless `bcw/agent-worker` container (hardened docker run,
  result written to /workspace/library-extract.json because runner stdout
  is truncated at 64 KiB; 30 MiB input limit; PDF via pdftotext with
  unreadable (scanned) pages listed for later Docling OCR; DOCX, PPTX per
  slide, XLSX per sheet, text). Images need Docling. Library service URLs
  must be loopback or private LAN, no path. Docling on the Ascent is bound to
  127.0.0.1 today: the work network profile must bind it (and retrieval
  8081) to the LAN address for HAL3000.
  Change 4 (search) done (commit 6d97a0e on release/0.17, not pushed): `library_search.py`. Keyword =
  `websearch_to_tsquery('simple')` plus ILIKE on Chinese runs (trigram
  index), fused; vectors from llama.cpp `/v1/embeddings` model `embed`,
  query prefixed with an Instruct line, first 1024 dims re-normalized;
  RRF k=60 over 50 candidates; top 30 reranked by `/v1/rerank` model
  `rerank`. Modes reported: hybrid+rerank, hybrid, keyword (with a note when
  the Ascent is unreachable, e.g. on the Ollama backup). AI search shows
  governing categories only when approved and never rejected or
  missing/unavailable revisions; the Library page sees pending ones too.
  Change 5 (sources and watcher) done (commit 6d97a0e on release/0.17, not pushed): `library_standard.py`
  (name regex, case-insensitive, normalized upper; Office lock, hidden and
  Thumbs files ignored), `library_watch.py` (Mother source `mother:Library`
  follows the configured Mother; walk without links/junctions; hash reused
  when size+mtime unchanged; statuses recomputed per scan: highest rank
  current, else superseded; same number+rev different content = conflict;
  same path new content = "changed without a new revision"; unreachable =
  unavailable), `library_index.py` (reuses passages by sha256; vectors
  backfilled when retrieval returns), `library_admin.py` (new permission
  feature `library`: view for all, edit default ICPM + Senior Engineer;
  sources add/pause/remove (Mother only pausable), bulk approve/reject up to
  500, retry failed reads, lists uncertain/pending/superseded/missing/
  failed, audited in SQLite `events`; background thread every 15 min, keeps
  going every 5 s while reading is unfinished, 10 min per pass),
  `library_routes.py` (`/api/library/*`, settings for Docling and
  retrieval URLs by managers, originals served only from inside their
  source). Full suite 875 passed.
  Changes 7 and 8 done (commit 5800b1d, 22 Nov): MCP tool `search_library`
  (query, category, current_only, limit) via `/api/agent/library/search`
  (AI view: approved governing only; passages with doc_no, rev, page and
  an `open` link `/api/library/original/<rev>#page=N`); Assistant
  instructions to cite doc_no rev, page and treat passages as untrusted.
  Library page `src/library.jsx` under Project: Search, Waiting for
  approval (bulk approve/reject), Uncertain, Superseded, Missing or
  unavailable, Failed reads (read again), Sources (scan now, add network
  folder, pause/resume/remove), Services (ICPM: Docling and retrieval
  addresses, database health). Phone layout stacks table rows. Browser test
  `tests/library-ui.mjs` (static dist + intercepted API, 1440 and 390 px)
  passes; it needs @playwright/test, which the worktree lacks (linked
  temporarily from mr-mak-workspace/node_modules, then removed).
  Full suite 876 passed.
  Change 9 (Preliminary Review) done (commit bdcd235, 22 Nov):
  `library_review.py`. Gathers the report's passages (up to 240k chars),
  searches about 40 of them against approved governing references (3 each)
  and earlier reports in the same subject folder (2 each, other revisions
  included), keeps 60 references; one model call through the Responses
  adapter (`model.infer`, 30 min timeout, one review at a time) with JSON
  findings labelled R<n>/P<id>; findings whose citations do not resolve
  are dropped and counted. Kinds: inconsistency, missing (may have no R),
  contradiction (needs two R), attention. SQLite tables `review_runs`,
  `review_findings` (decision, note, decided_by/at). Routes under
  `/api/reviews` gated by Reporting edit (engineers) plus Library view, so
  engineers decide findings without being library approvers. Keyword search
  now ORs meaningful words (`to_tsquery`) instead of requiring all words,
  which fixed recall for questions and whole-passage queries. UI tab
  "Preliminary Review" on the Library page. Full suite 879 passed.
  Change 10 (image editing) done (commit 94b12f0, 22 Nov): `comfyui.py`
  (upload, /prompt, /history poll, /view, /free, /system_stats; fills the
  API-format workflow by node type: LoadImage, first non-empty
  TextEncodeQwenImageEdit(Plus) prompt, KSampler seed), `image_window.py`
  (async gate on `/api/local-model/v1/responses`, including streams; the
  window waits for in-flight answers, then new chat waits; llama.cpp router
  `/models`, `/models/unload`, `/models/load`), `image_edit.py` (SQLite
  `image_jobs`, max 5 queued per user, MCP tool `edit_image`, result saved
  into the conversation as `<name>-edited-<id8>.png`; window order: check
  ComfyUI ready, open, unload chat model, edits, ComfyUI free, load
  `cfg['model']`, close; never pauses chat if ComfyUI is unreachable; not
  available on the Ollama backup). Decision A refined: chat pauses, so
  gpt-oss is not loaded during the window (shorter, more memory). UI:
  Assistant notice and recent edits; ComfyUI address on Library "Ascent
  services". Full suite 885 passed.
  Change 10b (commit fbce25f): owner exported both ComfyUI workflows (API
  format) from the Ascent: `image_qwen_image_edit_2511_int8.json` and
  `image_krea2_turbo_t2i_int8.json`, shipped as
  `bcw_desktop/comfyui_workflows/image-edit.json` and `text-to-image.json`.
  Explicit slot map (edit: 41 LoadImage.image, 170:151 positive
  TextEncodeQwenImageEditPlus.prompt, 170:169 KSampler.seed; Krea2: 30:19
  user-prompt PrimitiveStringMultiline.value, 30:3 KSampler.seed, 49
  ResolutionSelector.aspect_ratio, matched by prefix 16:9/9:16/1:1 from
  /object_info). Krea2 prompt refinement and the darkbrush LoRA stay off.
  New MCP tool `create_image` (landscape/portrait/square), output
  `images/generated-<id8>.png`, same image window.
  Change 11 (commit fa84624): release-version V0.17 (17, upgrade_from
  1-16, schema 3); V17_REQUIRED in `bcw_release.py`; install `check_model`
  and `scripts/verify_model.py` accept llama.cpp (preset in /v1/models, no
  digest); docs `RELEASE-0.17.md`, `LIBRARY-0.17.md`, library volume notes
  in UPDATES-AND-BACKUPS and DEPLOYMENT. Full suite 888 passed.
  Kit built 21 Nov 2026 at `D:\Downloads\BCW-V0.17-Work-USB` from fa84624
  (clean): release_id 10a0cd5e…e547c, 3136 files, 3.96 GB, `verify` passed.
  Gotchas: `prepare` reuses an existing `.runtime/release-input/images.tar`
  and `.runtime/portable-windows`, so a release that adds an image or a
  Python package must move both aside first (kept as `images-v016.tar` and
  `portable-windows-v016`); otherwise build fails "Portable Python
  preparation differs". A failed build leaves `<dest>.staging-*` beside the
  destination (it ended up in the Recycle Bin).
  Home update rehearsal 21 Nov 2026 (passed): orphaned V0.14 rehearsal
  containers/volumes/networks removed with owner's OK; fresh V0.16 rehearsal
  from `Documents\Codex\BCW-V0.16\BCW-release` at `D:\BCW-Rehearsal-20261121`
  (blank model, private empty Mother); seeded one chat; `bcw_release.py
  update --root <dest>pplication --release <kit>` with the kit's bundled
  Python. Result: health V0.17/17; no table lost rows (62 tables/379 rows to
  63/382, new `image_jobs`); `bcw-rehearsal-library-db-1` up with the
  installation's owner label, pgvector 0.8.7 + pg_trgm, library_schema 1,
  tables sources/documents/revisions/passages; keyword search answers with
  the "no retrieval server" note; pre-update backup of six volumes + local
  state (1.5 GB) under dataackups. The fresh rehearsal `icpm` is not an
  assigned ICPM, so ICPM-only settings answer 403 until assigned (a fresh
  rehearsal trait, not an update defect; set `account_state.roles` to
  ["ICPM"] for the test icpm). Ascent-connected acceptance over SSH tunnels
  (PC 18080/18081/18793/18188 to Ascent loopback; key login is refused, the
  owner runs `ssh -N -L ...` with the password) passed: compatibility,
  library settings schema 1/1, Docling read + embed of 4 test .md docs,
  approvals, hybrid+rerank search, Assistant answer citing PRO-0007 R01 with
  open links, Preliminary Review found all 4 planted faults (60 s, 0
  dropped), Krea2 image in a window while another user's chat waited.
  Fixes from it, commit 251302d (891 passed): llama.cpp context read from
  `/props?model=` n_ctx (blank = full, larger refused); current revisions
  rank before superseded; ComfyUI newer `["COMBO", {"options": [...]}]`
  format for ResolutionSelector (square came out 16:9 before).
  Owner decision 21 Nov 2026: Flash-Next gets the full context always, so
  `np = 1` in `[flash-next]` of `~/llm/chat.ini` (was 4 slots sharing
  262144); answers queue one at a time. Applied, /props shows n_ctx 262144,
  total_slots 1; ascent-config a032095 (backup chat.ini.bak-20261121).
  Revised same day after the queueing trade-off was explained: `np = 2`,
  /props shows n_ctx 131072 per slot, total_slots 2 (an explicit np gives
  separate, guaranteed per-slot context; the earlier default 4 slots shared
  one 262144 pool). FINAL owner decision (same day): two slots SHARING the
  full pool, `np = 2` plus `kv-unified = true`; /props shows n_ctx 262144,
  total_slots 2. Risk accepted: two very long conversations together can
  outgrow the pool and one answer fails. BCW commit a028582.
  Owner found in the rehearsal UI: finished pictures had no link, and the
  Library location was not shown. Commit 4c1baef: image jobs publish the
  picture as a conversation download (View/Download links, column
  image_jobs.artifact); Library Sources shows each real folder plus how to
  add a document. Kit r5 (superseded).
  Word documents via the Assistant were blank (owner report, 21 Nov 2026).
  Cause: Codex rewrites a bare {"type":"object"} tool field to one with
  "properties": {}, and llama.cpp's tool grammar then allows only {}. Hit
  create_document.spec, propose_change.payload, mcp tool arguments and
  spreadsheet mappings/updates. Declaring several fields is no cure: Codex
  sorts properties alphabetically and llama.cpp enforces that order, so the
  model writing "title" first garbled later keys ("sections' "). Fix: nested
  inputs are open objects ({"type":"object","additionalProperties":true})
  described in words, or single-field; a test enforces it. Empty specs are
  refused (BCW and worker) and the received fields echoed; the worker MCP
  client enforces inner tools' required fields; worker image now
  bcw/agent-worker:0.3.0 (same packages). Commits 5ca8974, d84a5a8.
  Diagnosis method worth reusing: point the test copy's model server at a
  local recording relay that forwards to the Ascent, then replay Codex's
  captured /v1/responses body with altered tool schemas.
  Kit `D:\Downloads\BCW-V0.17-Work-USB-r7` is the one for work (r1-r6
  superseded); test copy redone with it: Word document made first time
  through create_document with all content. Rehearsal redone with r5 (old test copy removed
  with owner's OK; same-version updates are refused, so a fresh V0.16 is
  needed): data kept, context saved blank = 262144, library folder shown,
  current revisions ranked first, square Krea2 picture viewable and in
  Downloads.
  NOT YET DONE: the Ascent LAN bindings for 8080/8081/8793/8188.

- Library standard (accepted by owner 21 Nov 2026, built from scratch):
  `Mother\Library\` with `01 Standards`, `02 Specifications`, `03 Procedures`
  (these three need approval before AI search uses them), `04 Manuals`,
  `05 Drawings`, `06 Reports\<Subject>\` (subfolder = subject for "earlier
  reports on the same subject"). File names `DocNo_Rev_Title.ext`; Rev `R00`,
  `R01`... or `E<year>` for external standards; DocNo codes STD, SPC, PRO,
  MAN, DWG, RPT; underscore separates. Higher Rev makes the older one
  superseded (still searchable, labelled); bad name or outside the tree is
  uncertain; same DocNo+Rev with different content is an uncertain
  conflict; deleted file is missing (record kept). BCW reads only; never
  moves, renames or deletes. Owner also wants extra library folders from
  network locations: approver-managed "Library sources" (Mother Library
  first); per source category = standard tree or one fixed category, naming
  = standard or "any names" (each file its own document, no superseding),
  approval per category or forced on; read with the Windows account BCW
  runs under, no stored passwords; unreachable source = "source
  unavailable", not missing; sources can be paused or removed (records and
  citations kept). Accepted 21 Nov 2026.

**Why:** the Ascent was funded to give BCW a capable agentic model and a cited
reference library on-site; keeping all data of record on HAL3000 preserves the
one-backup, one-permission-model, one-updater discipline the BCW kits rely on.

**How to apply:** build V0.17 on `release/0.16`, not `main` (main is at
V0.13/V0.14). Test the Codex-adapter tool-call path against llama-server before
anything else depends on it. Do not add an API key field. Never put the Mother
originals, index or approvals on the Ascent. Follow the BCW kit discipline
(checksum record, transfer note, CheckOnly route) for every Ascent update kit.
The move is one-shot: the departure checklist in the card tab, including a
rehearsed restore from the golden image, must be complete before the unit
leaves home.
See [[bcw-core-fixes-2026-10-15]] and [[bcw-v015-usb-2026-10-26]] for the kit
pattern.

## Work network setup (2026-11-22)

- Work LAN is isolated, 192.168.2.x. The Ascent's fixed work address is 192.168.2.45.
- Step 1 done: NetworkManager profile `work-lan` (any wired port, manual 192.168.2.45/24, no gateway, autoconnect priority 100). Idle at home, where the Ascent uses Wi-Fi 192.168.0.x. Undo: `sudo nmcli connection delete work-lan`.
- Still to do: services listen on the network (needs a restart per service, ask the owner first), firewall allows 8080/8081/8793/8188 from 192.168.2.0/24 only, and BCW addresses (`http://192.168.2.45:8080/v1`; Library > Ascent services :8793, :8081, :8188), ideally pre-filled in the work kit.
- Step 3 done early (firewall before opening services): ufw active, default deny incoming, 22/tcp from anywhere, 8080,8081,8188,8793/tcp from 192.168.2.0/24 only. Undo: `sudo ufw disable`. Docker-published ports bypass ufw, so Docling (container, published 127.0.0.1:8793, image bcw-docling:0.1.0, setup in ~/docling) needs its own plan.
- Units: llama-chat (`--host 127.0.0.1 --port 8080`), llama-retrieval (`--host 127.0.0.1 --port 8081`), comfyui (`--listen 127.0.0.1 --port 8188`), all /etc/systemd/system. They must bind 0.0.0.0, because 192.168.2.45 does not exist at home and a bind to it would fail.
- Step 2 done for chat, retrieval and ComfyUI: drop-ins `work-lan.conf` in each `/etc/systemd/system/<unit>.service.d/` bind 0.0.0.0. Verified: tunnel still works, and direct access from home Wi-Fi is blocked by ufw. Docling is still 127.0.0.1 only.
- Docling recreated with `--network host --restart unless-stopped bcw-docling:0.1.0` (the container had no mounts, env or GPU of its own), so it binds 0.0.0.0:8793 under ufw. Old container kept stopped as `docling-old`. Undo: `sudo docker rm -f docling && sudo docker rename docling-old docling && sudo docker start docling`. Verified: the tunnel works and Wi-Fi is blocked.
- Kit for work is now `D:\Downloads\BCW-V0.17-Work-USB-r8` (commit 1a36486, release_id be9b6ecd…, verified). It is -r7 plus the release notes section on connecting the Ascent at work.
- ascent-config recorded and pushed: fe4fc86 (skill with the work network section) and b0807d7 (systemd/work-lan/*.conf). The ufw rules and the work-lan NetworkManager profile are documented in the skill, not copied as files.

## Development at work (2026-11-22)

- The Ascent stays at work, which has no internet. Gitea `bmt01/bcw` (private, 127.0.0.1:3000 only) holds the work copy. Codex on the Ascent makes small fixes in `~/src/bcw` (release/0.17). Bigger changes, kit builds and rehearsals happen at home.
- Sync uses one USB git bundle. Home: `tools/sync/Sync-Work.ps1 -ToWork E:\` / `-FromWork E:\` (fetches into `work/*`, merged on purpose). Ascent: `sh ~/src/bcw/tools/sync/bcw-sync.sh import|export`. Branches only fast-forward; a branch changed on both sides is reported, never force-pushed. Rules are in BCW `docs/WORK-SYNC.md`.
- Setup done 2026-11-22: all 5 branches loaded, working copy made. Bug found on the way: `git bundle verify` needs a repository (fixed in 4146e9b). release/0.17 pushed to GitHub on 2026-11-22. Codex commits only; `export` pushes its commits to Gitea.
- Test tools on the Ascent (2026-11-22): venv `~/src/bcw/v2/.venv` (Python 3.12.3, wheels in `~/offline/bcw-wheels`), 845 pass, 21 fail on Linux (baseline `~/bcw-test-linux-failures.txt`, nearly all Windows-only: junctions, PowerShell, UNC, installer). Private Node v22.12.0 in `~/opt/node`, because Ubuntu Node 18 is too old for Vite 8 and its npm skips the rolldown Linux binding. Web build OK. Rules are in BCW docs/WORK-SYNC.md.
- Gitea opened to the work network (2026-11-22): container recreated (gitea/gitea:28.4.0, data /home/bmt01/gitea), 0.0.0.0:3000 and 127.0.0.1:2222, ROOT_URL http://192.168.2.45:3000/, registration disabled, sign-in required to view. A DOCKER-USER rule in /etc/ufw/after.rules (backup after.rules.bak-20261122) allows 3000 from 192.168.2.0/24 and drops other new connections; verified blocked on home Wi-Fi. Old container kept as `gitea-old`.
- Gitea account `opencode` (for HAL3000's OpenCode) has write access to bmt01/bcw only. Its token is in the Ascent's ~/opencode-gitea-token.txt (0600), fetched by the HAL3000 installer over SSH. Branch protection `*` on bcw: no force-push, no deletion.

## OpenCode on HAL3000 (2026-11-22)

- Package on Transcend `E:\OpenCode-HAL3000` (built in D:\Downloads\HAL3000-OpenCode-stage; sources in `workspace/.../ascent/hal3000-opencode/`). INSTALL-OPENCODE.bat needs no admin: OpenCode 1.19.6 (windows-x64-baseline), PortableGit 2.56.1, Node 22.12.0, uv-managed CPython 3.12.12 with blender-mcp 2.0.0 (mcp-for-blender 2.3.1; run as `python -c "from blender_mcp.server import main; main()"`, DISABLE_TELEMETRY=true), @playwright/mcp 0.0.86 with Chromium (PLAYWRIGHT_BROWSERS_PATH), and 76 skills in ~/.config/opencode/skills.
- Offline needs: OpenCode's first run installs `@opencode-ai/plugin` into ~/.config/opencode/node_modules and fetches ~/.cache/opencode/models.json. Both are shipped in opencode-cache.zip. Launcher sets OPENCODE_DISABLE_MODELS_FETCH/AUTOUPDATE/LSP_DOWNLOAD and OPENCODE_GIT_BASH_PATH. `@ai-sdk/openai-compatible` is built into the binary.
- Gotchas: in tests Git Bash's tar shadows Windows tar (use %SystemRoot%\System32\tar.exe). PowerShell 5.1 Set-Content utf8 writes a BOM, so the config is written with UTF8Encoding($false). With ErrorActionPreference=Stop, OpenCode's stderr from `opencode run` throws.
- Verified in a sandbox profile with a dead proxy, via the tunnel: install, "OPENCODE READY", both MCPs connected, Playwright read the BCW page title, 77 skills listed, and `docker stop` refused by a deny rule. Not verified: the Gitea token fetch over SSH and the clone (needs the Ascent at work).
- Blender for HAL3000 (2026-11-22): `E:\Blender-HAL3000` installs Blender 5.2.4 LTS (official zip, sha256 bbd78f89…) into %LOCALAPPDATA%\Programs\Blender\5.2.4 and the add-on as `blender_mcp` (the module name used at home; auto-start on, port 9876). The add-on is enabled by a background Blender script; `bpy.utils.refresh_script_paths()` is needed when the add-ons folder is new. Verified in a sandbox (BLENDER_USER_RESOURCES): add-on enabled, server up, and OpenCode via Flash-Next listed the scene objects. Home add-ons (HardOps, Boxcutter, DECALmachine, MACHIN3tools, MESHmachine…) are not included. Sources in `ascent/hal3000-blender/`.

## Inkling 2 Mini trial and the Codex sandbox (2026-11-22)

- Inkling 2 Mini (Thinking Machines, released 2026-11-20, 26B total / ~5B active looped MoE, Apache 2.0). unsloth `Mainline_Support/Inkling-2-Mini-UD-Q8_K_XL` plus mmproj-F16, in `~/models/inkling-2-mini` (22 GB). It needs llama.cpp with #32694 and #32704 (merged 11-20 and 11-21); built in `~/src/llama.cpp-inkling` (build 12628, 8a97fa98a). The chat service still runs the old build 12462. Trial tooling: `~/inkling-trial.sh` (start/status/download/serve/speed/codex/restore; long jobs run as `systemd-run` units, because nohup jobs died when SSH closed) and `~/inkling-codex.sh`.
- Memory: Flash-Next loaded leaves about 4 GB free, so Inkling and Flash-Next cannot run together; the trial stopped llama-chat. Inkling served at 27.3 tokens/s.
- Codex test with hidden tests from 251302d (tasks: ComfyUI COMBO aspect_option; slot_context with 409 refusal). Inkling: task1 pass in 267 s, task2 28/29 in 542 s. Flash-Next: task1 pass in 206 s, task2 27/29 in 1110 s. The test both failed (test_save_records_server_kind) comes from a gap in the prompt (behaviour when /props is unreadable was not specified). Decision: no switch before the Ascent leaves; revisit with more tasks once llama.cpp support matures.
- Codex 0.170 dropped `--full-auto` (use `-s workspace-write`) and `codex sandbox linux` (now `codex sandbox -- cmd`).
- Codex sandbox on the Ascent was broken: Ubuntu 24.04 `kernel.apparmor_restrict_unprivileged_userns=1` made bwrap fail ("loopback: Failed RTM_NEWADDR"), so Codex could run no command. Fixed with AppArmor profile `/etc/apparmor.d/bwrap` (`profile bwrap /usr/bin/bwrap flags=(unconfined) { userns, }`), which allows only bwrap; the global restriction stays on. Verified: bare sandbox works, and `codex exec -s workspace-write` on Flash-Next ran a command. Undo: `sudo apparmor_parser -R /etc/apparmor.d/bwrap && sudo rm /etc/apparmor.d/bwrap`.
- Coding mode (2026-11-22): `~/bin/coding-mode on|off|status`. `/etc/systemd/system/llama-inkling.service` (not enabled; Conflicts=llama-chat) serves Inkling on 0.0.0.0:8090, with ufw 8090 from 192.168.2.0/24. OpenCode on the Ascent and the HAL3000 installer (`-InklingUrl`, default http://<Ascent>:8090/v1) have provider `inkling`. Verified: on/answer/off on the Ascent; HAL3000 sandbox lists inkling/inkling-2-mini. Memory check: Flash-Next ≈72 GB GPU plus ≈22 GB RSS (mapped model file; `--no-mmap` might free it, untested), retrieval ≈15 GB, ComfyUI 170 MB when idle.
- no-mmap test (2026-11-22): build 12462 has no `no-mmap` preset key (router fails: "option 'no-mmap' not recognized"); the equivalent is `load-mode = none`. It made no difference (used 120 GB, server RSS 27.5 GB, writing 27.3 against 28.7 tokens/s, prompt slower), so it was reverted (`~/nommap.sh`, backup chat.ini.bak-nommap). The ~26 GB RSS beside 71.6 GB GPU memory is not the mapped file; the router's child buffer sizes are not in the journal at default verbosity. Normal state: Flash-Next + retrieval leave about 1 GB available; it has run this way, image edits included.
- Inkling switch (2026-11-22, `~/inkling-switch.sh apply|revert`, backups *.bak-preinkling): llama-chat runs the new build (work-lan.conf drop-in), chat.ini gains [inkling-2-mini] (c 262144, np 2, kv-unified, load-on-startup) and flash-next load-on-startup false; all four models stay selectable (models-max 1 swaps). Codex and OpenCode on the Ascent default to inkling-2-mini; coding-mode is retired. Measured: 29.1 tokens/s, memory used 79 GB, available 42 GB. Flash-Next qwen27b gpt-oss reductions: 27B 7.5 tokens/s (8.1 each with two at once), 70 GB used. BCW rehearsal on Inkling pending.
- BCW rehearsal on Inkling (2026-11-22, test copy 8897 via tunnel, scratchpad rehearsal/inkling.py): model saved with context 262144, compatibility passed; library question correct with PRO-0007 Rev 01 cited (90%, five readings), and it flagged RPT-0042 unprompted (65 s); Word document first time with nothing missing (35 s); Krea2 image done in 45 s with a working View link; Preliminary Review found all 4 planted faults (three readings, missing calibration serial, S-13 below 90% marked acceptable, sharp drop with no renewal assessment) in 60 s; weekly report correct, cited, and listed what was not in the documents. Flash-Next works on the new build (28.8 tokens/s); swapped back to Inkling (28.1).
- Switch completed (2026-11-22): RELEASE-0.17 guide and model-settings hint name inkling-2-mini (BCW 68b85e0), kit r9 `D:\Downloads\BCW-V0.17-Work-USB-r9` (release_id 26a379fe…) is on the Transcend and verified; HAL3000 OpenCode installer defaults to ascent/inkling-2-mini with Flash-Next (context 131072) as a fallback, and the coding-mode provider is removed. Ascent tidy (`~/ascent-tidy.sh`): Flash-Next c 131072, llama-inkling.service, the ufw 8090 rule and coding-mode removed, recorded in ascent-config. BCW still has the image window that pauses chat about 3 min (built for Flash-Next); dropping it is a later change.
- Image pause removed (BCW 2da0145, kit r10 `D:\Downloads\BCW-V0.17-Work-USB-r10`, release_id 8bb15e92…, on the Transcend and verified): setting imaging.pause_chat (Library > Ascent services tick box) defaults off; without it, image jobs run straight in ComfyUI and then free its memory, with no unload or reload. Full suite 897 passed. Fresh rehearsal (V0.16 test copy at D:\BCW-Rehearsal-20261122, updated with r10, no rows lost; the update needed the test copy's app stopped because it held a temp file in the data root): Inkling saved at 262144, library schema 1/1, hybrid+rerank. An image made during a chat finished at 89 s while the chat answered at 109 s; the window never opened and Inkling stayed loaded. The old test copy folder D:\BCW-Rehearsal-20261121 is left for the owner to delete (the rm safety check).
- HAL3000 extras on the Transcend (2026-11-22): `E:\GIMP-HAL3000` (GIMP 3.2.8 official installer, sha256 1d788742…, signed; per-user silent /CURRENTUSER, not run at home) and `E:\Tools-HAL3000` (INSTALL-TOOLS.bat: Ascent status check, VS Code 1.147 + ms-python vsix set, GIMP help 3.2.0, KeePassXC 2.8.0 zip, 7-Zip 26.06 unpacked with Windows tar, Notepad++ 8.9.9.1 portable, draw.io 32.7.4 /S /currentuser). All matched their makers' published checksums. The status check was tested through the tunnel and against a blocked address; KeePassXC, 7-Zip and Notepad++ installs were tested in a sandbox; the VS Code, draw.io and GIMP help installers were not run at home. Sources in `ascent/hal3000-gimp` and `ascent/hal3000-tools`.
