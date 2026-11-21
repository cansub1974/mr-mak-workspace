#!/bin/bash
# Ascent offline toolkit: everything needed to repair or reinstall the
# software on the Ascent without internet. Builds ~/offline. Safe to re-run:
# finished pieces are skipped. Run inside tmux; asks for the sudo password once.
set -u
O="$HOME/offline"
mkdir -p "$O"/{debs,docker,npm,src,venvs,config}
exec > >(tee -a "$O/toolkit.log") 2>&1
echo "== $(date '+%F %T') toolkit start"
df -h "$HOME" | tail -1

step() { echo; echo "== $1"; }
have() { [ -s "$1" ] && echo "   already done: $(basename "$1")"; }

# 1. Steps that need sudo first, while the password is fresh.
step "1/7 apt keeps every package it downloads from now on"
echo 'APT::Keep-Downloaded-Packages "true";' | sudo tee /etc/apt/apt.conf.d/01keep-debs >/dev/null && echo "   set"

step "2/7 Docker images (Docling, Gitea)"
for img in bcw-docling:0.1.0 gitea/gitea:28.4.0; do
  f="$O/docker/$(echo "$img" | tr '/:' '__').tar.gz"
  have "$f" || { sudo docker save "$img" | gzip > "$f" && echo "   saved $img"; }
done

step "3/7 every installed system package (.deb), one at a time"
dpkg-query -W -f='${db:Status-Abbrev} ${binary:Package}=${Version}\n' | awk '$1=="ii"{print $2}' > "$O/installed-packages.txt"
total=$(wc -l < "$O/installed-packages.txt"); n=0; got=0; miss=0
: > "$O/debs-not-downloadable.txt"
cd "$O/debs" || exit 1
while read -r p; do
  n=$((n+1)); name="${p%%=*}"; name="${name%%:*}"
  if compgen -G "${name}_*.deb" >/dev/null; then got=$((got+1)); continue; fi
  if apt-get download "$p" >/dev/null 2>&1; then got=$((got+1)); else miss=$((miss+1)); echo "$p" >> "$O/debs-not-downloadable.txt"; fi
  [ $((n % 200)) -eq 0 ] && echo "   $n of $total"
done < "$O/installed-packages.txt"
echo "   $got packages saved, $miss not downloadable (listed in debs-not-downloadable.txt)"

step "4/7 Python environments (ComfyUI, converter, Hugging Face)"
for v in comfy convert hf; do
  f="$O/venvs/$v.tar.gz"
  [ -d "$HOME/venvs/$v" ] || { echo "   no ~/venvs/$v, skipped"; continue; }
  have "$f" || { "$HOME/venvs/$v/bin/pip" freeze > "$O/venvs/$v-requirements.txt"; tar czf "$f" -C "$HOME/venvs" "$v" && echo "   saved $v"; }
done

step "5/7 Codex and OpenCode (programs, settings, cached provider package)"
NR="$(npm root -g 2>/dev/null)"
f="$O/npm/codex-global.tar.gz"
if [ -d "$NR/@openai/codex" ]; then have "$f" || { tar czf "$f" -C "$NR" @openai && echo "   saved Codex ($(codex --version 2>/dev/null))"; }; else echo "   Codex not found under $NR"; fi
tar czf "$O/config/user-config.tar.gz" -C "$HOME" .codex .config/opencode llm bin 2>/dev/null && echo "   saved ~/.codex, ~/.config/opencode, ~/llm, ~/bin"
[ -d "$HOME/.cache/opencode" ] && tar czf "$O/npm/opencode-cache.tar.gz" -C "$HOME" .cache/opencode && echo "   saved OpenCode cache"
cp -f /etc/systemd/system/llama-chat.service /etc/systemd/system/llama-retrieval.service /etc/systemd/system/comfyui.service "$O/config/" 2>/dev/null && echo "   saved service files"

step "6/7 source code and builds (llama.cpp with its build, ComfyUI without models, Docling files)"
c=$(git -C "$HOME/src/llama.cpp" rev-parse --short HEAD 2>/dev/null)
f="$O/src/llama.cpp-$c.tar.gz"; have "$f" || { tar czf "$f" -C "$HOME/src" llama.cpp && echo "   saved llama.cpp $c"; }
c=$(git -C "$HOME/src/ComfyUI" rev-parse --short HEAD 2>/dev/null)
f="$O/src/ComfyUI-$c.tar.gz"; have "$f" || { tar czf "$f" --exclude='ComfyUI/models/*/*.safetensors' --exclude='ComfyUI/output/*' -C "$HOME/src" ComfyUI && echo "   saved ComfyUI $c (models left in place)"; }
f="$O/src/docling-build.tar.gz"; have "$f" || { tar czf "$f" -C "$HOME" docling && echo "   saved Docling build files"; }

step "7/7 checksums and summary"
cd "$O" && find . -type f ! -name SHA256SUMS ! -name toolkit.log ! -path './debs/*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
(cd debs && sha256sum ./*.deb) > debs/SHA256SUMS
echo "   $(wc -l < SHA256SUMS) files plus $(ls debs/*.deb | wc -l) .deb files checksummed"
du -sh "$O"/* | sort -h
df -h "$HOME" | tail -1
echo "== $(date '+%F %T') toolkit done"
