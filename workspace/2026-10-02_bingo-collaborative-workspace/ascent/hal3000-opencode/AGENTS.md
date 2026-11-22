# OpenCode on HAL3000

HAL3000 runs the live BCW for the site. You are a careful assistant on a
production machine with no internet. The model is Inkling 2 Mini on the Ascent GX10.

## The live BCW is read-only to you

- BCW's installation and data (under `Documents\BCW`), its Docker containers and
  volumes are production. Read files and logs and run `docker ps`, `docker logs`
  or `docker inspect` to diagnose. Never stop, restart, remove or recreate
  containers, edit BCW's installed files or data, or touch `.env` files.
- Report a problem with the exact message, what you checked and the fix you
  propose. The owner applies fixes to the live BCW through Maintenance.

## Developing BCW

- Code lives in `C:\OpenCode\bcw` (Gitea on the Ascent, branch `release/0.17`).
  Read its `AGENTS.md` and `docs/WORK-SYNC.md` first.
- Make small, reviewed changes: one fix per commit, the reason in the message.
  Commit and push only when the owner asks. Never force-push, rewrite history
  or delete branches. Gitea refuses those anyway.
- Bigger changes, kit builds and installs are done at home, not here.

## Everything else

- Work in `C:\OpenCode` unless the owner names another folder.
- Ask before deleting anything. Prefer moving to a dated backup folder.
- The Ascent's addresses: chat `http://192.168.2.45:8080/v1`, retrieval `:8081`,
  Docling `:8793`, ComfyUI `:8188`, Gitea `:3000`. Do not change the Ascent's
  settings from here.
- Blender: the Blender MCP works only while Blender is open with the
  "MCP for Blender" add-on connected.
- Say plainly what you did, what you could not check, and what is left.
