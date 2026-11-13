# Recorder qualification, 2026-11-12

Version: `3.20.2-cscoach.20261112.2`, Windows x64, Hyper-V `gravadora1`.
Runtime changes are based on upstream `3ba51c9d`; the local daemon binds only to
`127.0.0.1`. Upstream's MIT license and attribution remain intact.

Environment: CS2 build `26598758`, client `1.41.9.7` (November 11 files),
HLAE `2.193.0`, demo analyzer `1.14.1`. The previously installed game was build
`26445667`; Steam completed its pending update before playback qualification.

Checks: formatting, lint, TypeScript, 177 upstream tests and dead-code detection
passed. CS Coach compatibility/control tests passed (10 tests including the
existing queue circuit); the stalled-capture regression script also passed.

Both reference demos were parsed and independently verified in a separate local
PostgreSQL database before capture. Four recordings were fully decoded and frames
were reviewed for the expected POV, kill feed and vertical crop:

| Reference     | Recording       | Duration | Mean audio volume |
| ------------- | --------------- | -------- | ----------------- |
| Before update | Horizontal      | 8.02 s   | -24.7 dB          |
| Before update | Vertical source | 8.00 s   | -24.7 dB          |
| After update  | Horizontal      | 8.00 s   | -23.8 dB          |
| After update  | Vertical source | 8.05 s   | -23.9 dB          |

The vertical source uses the existing CS Coach 2560x1440 capture with a central
9:16 crop, rather than the game's distorted native portrait mode. Frames were
reviewed after that crop. Reference videos, private configuration and demo files
are not published in this repository.

The approved portable build is installed separately from the official CSDM on
the VM. CS Coach selects its compatibility launcher through `CSDM_EXE`; the old
installation and database are preserved for rollback. The host PC is not switched
to this build. Operational production-batch results are tracked in CS Coach's
backlog card 225.
