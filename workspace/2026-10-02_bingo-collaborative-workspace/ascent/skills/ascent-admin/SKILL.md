---
name: ascent-admin
description: Manage this ASUS Ascent GX10 AI host. Use to check, restart, reconfigure, switch chat models, install or update software, reinstall offline, or recover a service.
---

# Ascent administration

This machine is an ASUS Ascent GX10 (NVIDIA GB10, 128 GB unified memory,
DGX OS = Ubuntu 24.04 **arm64**) serving AI models to the BCW system. At work it
sits on an isolated network with **no internet**; before the move it is set up
at home, online. Plan every procedure for the offline case. User `bmt01`. Its settings of
record live in `~/ascent-config` (Git, pushed to the local Gitea); the offline
install kit lives in `~/offline`. Read the files there for exact values rather
than trusting this page when they differ.

## Services

| Service | Address | Started by | Check |
|---|---|---|---|
| Chat router (llama-server) | 0.0.0.0:8080 | `llama-chat.service`, presets `~/llm/chat.ini` | `curl -s 127.0.0.1:8080/models` |
| Retrieval (embed + rerank) | 0.0.0.0:8081 | `llama-retrieval.service`, presets `~/llm/retrieval.ini` | `curl -s 127.0.0.1:8081/models` |
| ComfyUI (image edit) | 0.0.0.0:8188 | `comfyui.service` | `curl -s 127.0.0.1:8188/system_stats` |
| Docling (document parsing) | 0.0.0.0:8793 | Docker container `docling`, `--network host` | `sudo docker ps` |
| Gitea | 127.0.0.1:3000, SSH 2222 | Docker container `gitea` | `curl -s 127.0.0.1:3000/api/healthz` |

Logs: `journalctl -u <service> -n 100 --no-pager`; containers `sudo docker logs --tail 100 <name>`.
Restart: `sudo systemctl restart <service>`; containers `sudo docker restart <name>`.
`bmt01` is not in the docker group: every docker command needs sudo.

Codex sandbox: Ubuntu blocks unprivileged user namespaces, so `/etc/apparmor.d/bwrap`
lets only `/usr/bin/bwrap` use them. Without it Codex can run no command
("bwrap: loopback: Failed RTM_NEWADDR"). Check: `codex sandbox -- echo ok`.

Work network: the four BCW services bind 0.0.0.0 through `work-lan.conf` drop-ins
in `/etc/systemd/system/<unit>.service.d/` (Docling through host networking).
ufw denies incoming traffic except SSH 22 and 8080, 8081, 8188 and 8793 from
192.168.2.0/24. NetworkManager profile `work-lan` gives any wired port
192.168.2.45/24 without a gateway; at home the Ascent uses Wi-Fi. Keep these
together: a service on 0.0.0.0 with ufw off is open to whatever network the
Ascent joins. A recreated Docling container needs `--network host`, because a
Docker-published port bypasses ufw.

## Chat models and the memory rule

The router holds **one chat model at a time**; a request naming the other
model swaps them (about a minute).

- `flash-next`: Qwen3.8-Flash-Next, 256k context, **default**, loaded at boot.
  Two slots sharing one pool (`np = 2`, `kv-unified = true`, owner's
  decision): two answers at once, any conversation may use the full 262144;
  a third request waits. Keep both lines.
- `gpt-oss-120b`: 128k context, faster, text only.
- `qwen3.8-27b`: spare, slow.

**Memory rule:** ComfyUI image jobs need about 35 GB, which only exists while
`gpt-oss-120b` is the loaded chat model. Before an image job, load gpt-oss
(`curl -s -X POST 127.0.0.1:8080/models/load -H 'Content-Type: application/json' -d '{"model":"gpt-oss-120b"}'`).
Before going back to Flash-Next, free ComfyUI
(`curl -s -X POST 127.0.0.1:8188/free -H 'Content-Type: application/json' -d '{"unload_models":true,"free_memory":true}'`).
The router loads a new model even when the old one is busy, so a swap during a
running request can exhaust memory: swap only when chat is idle.

Defaults live in three places, changed together: `load-on-startup` in
`~/llm/chat.ini`, `"model"` in `~/.config/opencode/opencode.json`, and
`model` / `model_context_window` in `~/.codex/config.toml`.

## Every change ends the same way

A change is done when all of these hold:

1. The affected service was restarted and its check above answers.
2. The changed file is copied into its folder in `~/ascent-config` (the
   README there maps each folder to its live location).
3. `cd ~/ascent-config && git add -A && git commit -m "<what changed>" && git push`
   has run. The push asks for the Gitea password; if you cannot type it, tell
   the owner to run `cd ~/ascent-config && git push`.

## Rules

- Ask the owner before anything with sudo that changes the system, deletes
  files, installs or upgrades packages, or touches security settings (AppArmor,
  firewall, users, SSH). Reading and restarting services need no approval.
- Keep secrets out of `~/ascent-config`: Gitea's `~/gitea/gitea/conf/app.ini`,
  `~/.codex/auth.json` and OpenCode's `~/.local/share/opencode` stay only on
  the machine.
- Write `ASCENT` in place of the machine's network address in any document.
- Model files in `~/models` are irreplaceable at work (no internet): move or
  delete them only on the owner's explicit instruction.
- Secure Boot is on with the open NVIDIA driver 580: install no `nvidia-dkms-*`
  package and no driver from outside the DGX OS repositories.

## Installing software

There is no internet at work, so new software arrives on a drive.

1. Confirm it is built for **arm64 / aarch64**. An `amd64`, `x86_64` or `x64`
   package cannot run here.
2. Install from the local file (`sudo apt install ./file.deb`), after the
   owner approves.
3. Re-run `bash ~/offline-toolkit.sh` so the kit holds it, then record the
   change in `~/ascent-config` as above.

## Updating deliberately

Automatic updates are off on purpose (apt timers disabled, snaps held,
`20auto-upgrades` set to 0). Keep them off. An update, approved by the owner:
take a golden image to the 1 TB work drive first; then update; re-run
`~/offline-toolkit.sh`; check every service; commit `~/ascent-config`.

## Reinstalling from `~/offline`

- Packages: `sudo apt install ~/offline/debs/<name>_*.deb` (checksums in `debs/SHA256SUMS`).
- Docker images: `gunzip -c ~/offline/docker/<image>.tar.gz | sudo docker load`; container settings are in `~/ascent-config/docker/inspect.json`.
- Python environments: `tar xzf ~/offline/venvs/<name>.tar.gz -C ~/venvs`.
- llama.cpp, ComfyUI, Docling build files: `tar xzf ~/offline/src/<file>.tar.gz -C ~/src` (Docling: `-C ~`).
- Codex: `tar xzf ~/offline/npm/codex-global.tar.gz -C "$(npm root -g)"`; OpenCode: `~/offline/opencode-linux-arm64.tar.gz` (CLI) and `~/offline/opencode-desktop-linux-arm64.deb`.
- Settings: copy back from `~/ascent-config`.

## Recovery ladder

Climb only as far as needed, and tell the owner before each step past the first:

1. Read the log, then restart the service.
2. Restore its settings from `~/ascent-config` and restart.
3. Reinstall the component from `~/offline`.
4. Restore the golden image from the 1 TB work drive, booting the Ubuntu
   ARM64 live USB.
5. ASUS factory recovery USB, then rebuild from `~/offline` and `~/ascent-config`.
