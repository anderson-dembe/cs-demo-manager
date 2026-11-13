# CS Coach Windows build

Internal fork based on upstream `3ba51c9d`. Includes the CS2 update support
(`63257efa`), upstream Windows plugin (`93087c40`) and demo analyzer 1.14.1.
The upstream MIT license and attribution are preserved.

Build only on `gravadora1` while the host PC is being used for gaming:

```powershell
./cscoach/build.ps1 -Vp C:/cscoach/.tools/vite-plus/bin/vp.exe
```

Requires Git and Vite+ 1.5.1. The pinned runtime and package manager are downloaded
by Vite+. The build performs checks, tests, dead-code detection and packaging.
Missing Crowdin/API credentials are expected: this build only provides local
analysis and video generation, in English. No CS Coach secrets belong in this repo.
The daemon listens on IPv4 loopback only: its CLI, GUI and CS2 plugin all run on
the same recorder. No Windows Firewall access to public/private networks is needed.

Use `dist/win-unpacked/csdm-cscoach.cmd` as `CSDM_EXE`. The wrapper confirms the
new upstream JSON analysis result before emitting the legacy persistence marker
used by CS Coach. Other commands, including video generation, pass through.
`CSDM_PROFILE` can point to a separate Windows home directory for qualification;
its `.csdm/settings.json` must use a separate database and disable automatic updates.

Do not replace the official installation. Before promotion, qualify old/new demos,
database persistence, the correct POV and ticks, horizontal/vertical recording,
audio, duration and a production batch. Back up settings and keep the previous
database untouched. Roll back `CSDM_EXE` and the settings backup together.
Only promote on `gravadora1`; never alter the host's Steam, CS2 or pause state.

The game files must also match the plugin: the `latest` plugin in this fork is
for the November 11 update. During qualification the VM was found on build
26445667, with Steam targeting 26598758. Launching through HLAE bypassed Steam's
pending update. Request the update through the VM's Steam client and verify the
installed build before testing; a parser success alone does not prove playback.
