"""Offline qualification on gravadora1. No uploads, customer records or notifications."""
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\cscoach\clips")
import worker_highlights as worker

if worker.ENV.get("MAQUINA", "pc") != "gravadora1":
    raise SystemExit("Qualification is restricted to gravadora1")

ROOT = Path(r"C:\cscoach\csdm-qualification-20261112")
BUILD = Path(__file__).resolve().parents[1] / "dist" / "win-unpacked"
PROFILE = ROOT / "profile"
DATABASE = "csdm_cscoach_20261112"
RUN_ID = datetime.now().strftime("%Y%m%d%H%M%S")
ROOT.mkdir(exist_ok=True)


def run(args, label, env=None, timeout=300):
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", env=env, timeout=timeout)
    (ROOT / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}); inspect its local log")
    return result


def prepare():
    settings = json.loads((Path.home() / ".csdm" / "settings.json").read_text(encoding="utf-8-sig"))
    database = settings["database"]
    psqls = list(Path(r"C:\Program Files\PostgreSQL").glob("*/bin/psql.exe"))
    if not psqls:
        raise RuntimeError("psql is required")
    pg_env = dict(os.environ, PGPASSWORD=database["password"])
    pg = [str(psqls[-1]), "-X", "-v", "ON_ERROR_STOP=1", "-h", database["hostname"],
          "-p", str(database["port"]), "-U", database["username"], "-d", "postgres"]
    exists = run(pg + ["-tAc", f"SELECT 1 FROM pg_database WHERE datname='{DATABASE}'"], "database-check", pg_env)
    if exists.stdout.strip() != "1":
        run(pg + ["-c", f'CREATE DATABASE "{DATABASE}"'], "database-create", pg_env)
    settings["database"] = {**database, "mode": "external", "database": DATABASE}
    settings["autoDownloadUpdates"] = False
    settings["playback"]["cs2PluginVersion"] = "latest"
    settings["video"]["ffmpegSettings"]["videoContainer"] = "avi"
    folder = PROFILE / ".csdm"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    # The fork daemon must not attach to the official CSDM daemon.
    os.environ["CSDM_PROFILE"] = str(PROFILE)
    os.environ["CSDM_WS_PORT"] = "4584"
    worker.CSDM = str(BUILD / "csdm-cscoach.cmd")
    return pg, pg_env


def main():
    pg, pg_env = prepare()
    report = {"version": run([worker.CSDM, "--version"], "version").stdout.strip(),
              "database": DATABASE, "demos": []}
    for name in ("antiga_ok", "nova_cs2_1111"):
        print(f"QUALIFY {name}", flush=True)
        demo = Path(r"C:\cscoach-dados\vigia\demos") / f"{name}.dem"
        output = ROOT / name
        output.mkdir(exist_ok=True)
        run([str(BUILD / "resources/static/csda.exe"), "-demo-path", str(demo),
             "-format", "json", "-output", str(output)], f"{name}-parser")
        parsed = json.loads((output / f"{name}.json").read_text(encoding="utf-8-sig"))
        analyzed = run([worker.CSDM, "analyze", str(demo), "--force"], f"{name}-analyze")
        if "Inserting match into database [CS Coach: confirmed persisted]" not in analyzed.stdout:
            raise RuntimeError("Missing persistence confirmation")
        # Query the isolated database independently of the CLI success message.
        verify = pg[:]
        verify[verify.index("-d") + 1] = DATABASE
        checksum = str(parsed["checksum"])
        if not re.fullmatch(r"[A-Za-z0-9]+", checksum):
            raise RuntimeError("Unexpected checksum")
        found = run(verify + ["-tAc", f"SELECT count(*) FROM matches WHERE checksum='{checksum}'"],
                    f"{name}-persisted", pg_env)
        if found.stdout.strip() != "1":
            raise RuntimeError("The analyzed match was not persisted")
        kill = next(k for k in parsed["kills"] if k["killerSteamId"] and k["tick"] > 512)
        start, end = kill["tick"] - 192, kill["tick"] + 320
        item = {"steam_id": str(kill["killerSteamId"]), "h": {"start_tick": start, "end_tick": end}}
        sequences, _ = worker._monta_sequencias([item])
        entry = {"name": name, "checksum": checksum, "map": parsed["mapName"],
                 "killer": kill["killerName"], "killTick": kill["tick"], "start": start, "end": end,
                 "recordings": []}
        for orientation in ("horizontal", "vertical"):
            width, height, seqs = worker.resolucao_e_sequencias(orientation, sequences)
            folder = output / f"{orientation}-{RUN_ID}"
            folder.mkdir(exist_ok=True)
            config = {"demoPath": str(demo), "width": width, "height": height, "framerate": 60,
                      "recordingSystem": "HLAE", "recordingOutput": "video", "encoderSoftware": "FFmpeg",
                      "closeGameAfterRecording": True, "keepRawFilesOnGameError": True,
                      "outputFolderPath": str(folder), "sequences": seqs}
            config_path = output / f"{orientation}.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            print(f"RECORD {name} {orientation} POV={kill['killerName']}", flush=True)
            run([worker.CSDM, "video", "--config-file", str(config_path)], f"{name}-{orientation}-video", timeout=420)
            videos = list(folder.rglob("*.avi"))
            if len(videos) != 1:
                raise RuntimeError(f"Expected one AVI, found {len(videos)}")
            video = videos[0]
            run([worker.FFMPEG, "-v", "error", "-i", str(video), "-f", "null", "-"],
                f"{name}-{orientation}-decode")
            audio = run([worker.FFMPEG, "-hide_banner", "-i", str(video), "-af", "volumedetect",
                         "-vn", "-f", "null", "-"], f"{name}-{orientation}-audio")
            mean = re.search(r"mean_volume:\s*(-?[\d.]+) dB", audio.stderr)
            duration = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", audio.stderr)
            if not mean or float(mean[1]) < -60 or not duration:
                raise RuntimeError("Missing audio or duration")
            seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
            if not 6.5 <= seconds <= 10.5:
                raise RuntimeError(f"Unexpected duration: {seconds}")
            for timestamp in (1, 3, 6):
                target = output / f"{orientation}-{timestamp}s.jpg"
                crop = (["-vf", "crop=ih*9/16:ih,scale=810:1440"] if orientation == "vertical" else [])
                run([worker.FFMPEG, "-y", "-ss", str(timestamp), "-i", str(video), *crop,
                     "-frames:v", "1", str(target)], f"{name}-{orientation}-frame{timestamp}")
            entry["recordings"].append({"orientation": orientation, "video": str(video),
                                        "duration": seconds, "meanVolume": float(mean[1])})
        report["demos"].append(entry)
        (ROOT / "qualification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("QUALIFICATION_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
