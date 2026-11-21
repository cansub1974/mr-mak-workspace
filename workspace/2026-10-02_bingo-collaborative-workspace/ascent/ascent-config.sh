#!/bin/bash
# Ascent configuration repository: copies every setting that is not a model
# file into ~/ascent-config, commits it and pushes it to Gitea. Re-run after
# any change on the Ascent; it commits only what changed.
# Secrets are never copied: no Gitea app.ini, no Codex auth.json, no OpenCode auth.
set -u
R="$HOME/ascent-config"
mkdir -p "$R"/{llm,systemd,apt,codex,opencode,bin,docling,comfyui/workflows,docker,tools,state}
cd "$R" || exit 1
[ -d .git ] || { git init -q -b main; git config user.name "bmt01 on gx10"; git config user.email "bmt01@gx10.local"; }

cp -f ~/llm/*.ini llm/ 2>/dev/null
cp -f /etc/systemd/system/llama-chat.service /etc/systemd/system/llama-retrieval.service /etc/systemd/system/comfyui.service systemd/ 2>/dev/null
cp -f /etc/apt/apt.conf.d/01keep-debs /etc/apt/apt.conf.d/20auto-upgrades apt/ 2>/dev/null
cp -f ~/.codex/config.toml codex/ 2>/dev/null
cp -f ~/.config/opencode/opencode.json opencode/ 2>/dev/null
find ~/bin -maxdepth 1 -type f -size -100k -exec cp -f {} bin/ \; 2>/dev/null
(cd ~/docling 2>/dev/null && find . -type f -size -1M | while read -r f; do mkdir -p "$R/docling/$(dirname "$f")"; cp -f "$f" "$R/docling/$f"; done)
cp -f ~/src/ComfyUI/user/default/workflows/*.json comfyui/workflows/ 2>/dev/null
cp -f ~/offline-toolkit.sh ~/ascent-config.sh tools/ 2>/dev/null

for c in gitea docling; do
  sudo docker inspect --format 'image: {{.Config.Image}}
restart: {{.HostConfig.RestartPolicy.Name}}
ports: {{json .HostConfig.PortBindings}}
mounts: {{range .Mounts}}{{.Source}} -> {{.Destination}}; {{end}}
env: {{json .Config.Env}}' "$c" > "docker/$c.txt" 2>/dev/null || echo "no container $c" > "docker/$c.txt"
done

{
  echo "hostname: $(hostname)"
  echo "kernel: $(uname -r)"
  echo "driver: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null)"
  echo "cuda: $(nvcc --version 2>/dev/null | grep -o 'release [0-9.]*')"
  echo "llama.cpp: $(git -C ~/src/llama.cpp rev-parse --short HEAD 2>/dev/null)"
  echo "ComfyUI: $(git -C ~/src/ComfyUI rev-parse --short HEAD 2>/dev/null)"
  echo "codex: $(codex --version 2>/dev/null)"
  echo "opencode: $(opencode --version 2>/dev/null)"
  echo "docker: $(docker --version 2>/dev/null)"
} > state/versions.txt
systemctl list-unit-files apt-daily.timer apt-daily-upgrade.timer motd-news.timer fwupd-refresh.timer ua-timer.timer esm-cache.service llama-chat.service llama-retrieval.service comfyui.service --no-pager > state/unit-states.txt 2>/dev/null
dpkg-query -W -f='${binary:Package}=${Version}\n' > state/installed-packages.txt
ls -la ~/models/* > state/models.txt 2>/dev/null

[ -f README.md ] || cat > README.md <<'EOF'
# Ascent GX10 configuration

Everything on the Ascent that is not a model file, so the machine can be
rebuilt or checked. Refresh with `bash ~/ascent-config.sh` after any change.

| Folder | What | Goes to |
|---|---|---|
| llm/ | llama-server presets (chat router, retrieval) | ~/llm/ |
| systemd/ | service units for chat, retrieval, ComfyUI | /etc/systemd/system/ |
| apt/ | keep-downloaded-debs and auto-updates-off settings | /etc/apt/apt.conf.d/ |
| codex/, opencode/ | coding harness settings | ~/.codex/, ~/.config/opencode/ |
| bin/ | small helper scripts | ~/bin/ |
| docling/ | Docling image build files | ~/docling/ |
| comfyui/workflows/ | saved ComfyUI workflows | ~/src/ComfyUI/user/default/workflows/ |
| docker/ | how the gitea and docling containers run | reference for `docker run` |
| tools/ | offline-toolkit.sh and this script | ~/ |
| state/ | versions, unit states, package list, model files | reference only |

Secrets are deliberately not here: Gitea's app.ini, Codex auth.json and
OpenCode auth stay only on the machine and in the golden image.
The offline install kit (packages, images, builds) is in ~/offline.
EOF

git add -A
if git diff --cached --quiet; then echo "== no changes since last commit"; else git commit -q -m "Ascent config $(date '+%F %T')" && echo "== committed: $(git log -1 --format=%s)"; fi

if ! git remote get-url origin >/dev/null 2>&1; then
  read -r -p "Your Gitea user name: " GU
  git remote add origin "http://127.0.0.1:3000/$GU/ascent-config.git"
fi
git push -u origin main && echo "== pushed to Gitea"
