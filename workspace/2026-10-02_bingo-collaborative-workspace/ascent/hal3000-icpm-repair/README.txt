BCW ICPM REPAIR (V0.16 at work, 24 Nov 2026)

Use when no BCW account has the ICPM role, so the Admin tab is gone for everyone.

1. On HAL3000, sign in to Windows as the user that runs BCW. BCW can stay running.
2. Double-click REPAIR-ICPM-BMT01.bat in this folder.
3. It lists every account and shows the change it would make. Nothing changes yet.
4. Press Y to repair, N to cancel. It backs up BCWs database first
   (Documents\BCW\data\backups\icpm-repair-<time>), then gives BMT01 the ICPM role
   on the account and on its active deployment, keeping its other roles.
5. In the browser, signed in as BMT01, press F5. Tools > Admin is back.

Until the fix for the cause arrives, do not move roles or deployments.
Afterwards give ICPM to a second account you can sign in to.
