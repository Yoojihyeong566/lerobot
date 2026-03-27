#!/usr/bin/env python3
"""
Bimanual teleoperation data recording script (Python version).

Ports:
  Left follower:  /dev/ttyACM1, camera /dev/video4
  Right follower: /dev/ttyACM3, camera /dev/video6
  Left leader:    /dev/ttyACM0
  Right leader:   /dev/ttyACM2

Usage:
  python record.py
  python record.py --dataset my_dataset --task "Pick up cube" --episodes 20
"""

import argparse
import logging
import os
import time
from pathlib import Path

# Use calibration files bundled in this repo (overrides ~/.cache/huggingface/lerobot/calibration)
os.environ.setdefault("HF_LEROBOT_CALIBRATION", str(Path(__file__).parent / "calibration"))

# ── Robot configs ──────────────────────────────────────────────────────────────
from lerobot.robots.bi_so_follower.config_bi_so_follower import BiSOFollowerConfig
from lerobot.robots.so_follower.config_so_follower import SOFollowerConfig

# ── Teleop configs ─────────────────────────────────────────────────────────────
from lerobot.teleoperators.bi_so_leader.config_bi_so_leader import BiSOLeaderConfig
from lerobot.teleoperators.so_leader.config_so_leader import SOLeaderConfig

# ── Camera config ──────────────────────────────────────────────────────────────
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

# ── Robot / Teleop factories ───────────────────────────────────────────────────
from lerobot.robots.utils import make_robot_from_config
from lerobot.teleoperators.utils import make_teleoperator_from_config

# ── Dataset ────────────────────────────────────────────────────────────────────
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.pipeline_features import (
    aggregate_pipeline_dataset_features,
    create_initial_features,
)
from lerobot.datasets.utils import combine_feature_dicts
from lerobot.datasets.video_utils import VideoEncodingManager

# ── Processor / control utilities ─────────────────────────────────────────────
from lerobot.processor import make_default_processors
from lerobot.utils.control_utils import init_keyboard_listener, is_headless
from lerobot.utils.utils import init_logging, log_say
from lerobot.utils.visualization_utils import init_rerun

# ── record_loop (plain function, no CLI decorator) ────────────────────────────
from lerobot.scripts.lerobot_record import record_loop

# ── Suppress verbose import warnings ──────────────────────────────────────────
from lerobot.utils.import_utils import register_third_party_plugins


# ──────────────────────────────────────────────────────────────────────────────
# Settings  (edit here or pass CLI args)
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_DATASET   = "local/bimanual_so101_demo"
DEFAULT_TASK      = "Pick and place task"
DEFAULT_EPISODES  = 20
DEFAULT_EPISODE_S = 60
DEFAULT_RESET_S   = 30
DEFAULT_FPS       = 30
DEFAULT_ROOT      = None          # None → ~/.cache/huggingface/lerobot/
DISPLAY_DATA      = True


def build_robot_config() -> BiSOFollowerConfig:
    return BiSOFollowerConfig(
        id="first_bimanual_follower",
        left_arm_config=SOFollowerConfig(
            port="/dev/lerobot/left_follower",
            cameras={
                "wrist": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_left_wrist",
                    width=640,
                    height=480,
                    fps=30,
                    fourcc="MJPG",
                )
            },
        ),
        right_arm_config=SOFollowerConfig(
            port="/dev/lerobot/right_follower",
            cameras={
                "wrist": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_right_wrist",
                    width=640,
                    height=480,
                    fps=30,
                    fourcc="MJPG",
                ),
                "top": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_right_top",
                    width=640,
                    height=480,
                    fps=30,
                    fourcc="MJPG",
                ),
            },
        ),
    )


def build_teleop_config() -> BiSOLeaderConfig:
    return BiSOLeaderConfig(
        id="first_bimanual_leader",
        left_arm_config=SOLeaderConfig(port="/dev/lerobot/left_leader"),
        right_arm_config=SOLeaderConfig(port="/dev/lerobot/right_leader"),
    )


def main():
    parser = argparse.ArgumentParser(description="Bimanual SO101 data recorder")
    parser.add_argument("--dataset",  default=DEFAULT_DATASET,   help="repo_id (e.g. local/my_dataset)")
    parser.add_argument("--task",     default=DEFAULT_TASK,      help="Task description")
    parser.add_argument("--episodes", default=DEFAULT_EPISODES,  type=int)
    parser.add_argument("--episode_s",default=DEFAULT_EPISODE_S, type=int, help="Recording time per episode (s)")
    parser.add_argument("--reset_s",  default=DEFAULT_RESET_S,   type=int, help="Reset time between episodes (s)")
    parser.add_argument("--fps",      default=DEFAULT_FPS,       type=int)
    parser.add_argument("--root",     default=DEFAULT_ROOT,      help="Dataset root directory")
    parser.add_argument("--no_display", action="store_true",     help="Disable Rerun visualizer")
    args = parser.parse_args()

    display_data = DISPLAY_DATA and not args.no_display

    register_third_party_plugins()
    init_logging()

    print(f"Recording dataset : {args.dataset}")
    print(f"Task              : {args.task}")
    print(f"Episodes          : {args.episodes}, episode={args.episode_s}s, reset={args.reset_s}s")

    # ── Build robot & teleop ───────────────────────────────────────────────────
    robot_cfg = build_robot_config()
    teleop_cfg = build_teleop_config()

    robot = make_robot_from_config(robot_cfg)
    teleop = make_teleoperator_from_config(teleop_cfg)

    # ── Processors ────────────────────────────────────────────────────────────
    teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

    # ── Dataset features ──────────────────────────────────────────────────────
    dataset_features = combine_feature_dicts(
        aggregate_pipeline_dataset_features(
            pipeline=teleop_action_processor,
            initial_features=create_initial_features(action=robot.action_features),
            use_videos=True,
        ),
        aggregate_pipeline_dataset_features(
            pipeline=robot_observation_processor,
            initial_features=create_initial_features(observation=robot.observation_features),
            use_videos=True,
        ),
    )

    # ── Rerun visualizer ──────────────────────────────────────────────────────
    if display_data:
        init_rerun(session_name="recording")

    dataset = None
    listener = None

    try:
        # ── Create dataset ─────────────────────────────────────────────────────
        dataset = LeRobotDataset.create(
            args.dataset,
            args.fps,
            root=args.root,
            robot_type=robot.name,
            features=dataset_features,
            use_videos=True,
            image_writer_processes=0,
            image_writer_threads=4 * len(robot.cameras),
            batch_encoding_size=1,
            vcodec="h264",
        )

        # ── Connect ────────────────────────────────────────────────────────────
        robot.connect()
        teleop.connect()

        listener, events = init_keyboard_listener()

        # ── Record loop ────────────────────────────────────────────────────────
        with VideoEncodingManager(dataset):
            recorded_episodes = 0
            while recorded_episodes < args.episodes and not events["stop_recording"]:
                log_say(f"Recording episode {dataset.num_episodes}", play_sounds=True)

                record_loop(
                    robot=robot,
                    events=events,
                    fps=args.fps,
                    teleop_action_processor=teleop_action_processor,
                    robot_action_processor=robot_action_processor,
                    robot_observation_processor=robot_observation_processor,
                    teleop=teleop,
                    dataset=dataset,
                    control_time_s=args.episode_s,
                    single_task=args.task,
                    display_data=display_data,
                )

                # Reset phase (skip after last episode)
                if not events["stop_recording"] and (
                    recorded_episodes < args.episodes - 1 or events["rerecord_episode"]
                ):
                    log_say("Reset the environment", play_sounds=True)
                    record_loop(
                        robot=robot,
                        events=events,
                        fps=args.fps,
                        teleop_action_processor=teleop_action_processor,
                        robot_action_processor=robot_action_processor,
                        robot_observation_processor=robot_observation_processor,
                        teleop=teleop,
                        control_time_s=args.reset_s,
                        single_task=args.task,
                        display_data=display_data,
                    )

                if events["rerecord_episode"]:
                    log_say("Re-record episode", play_sounds=True)
                    events["rerecord_episode"] = False
                    events["exit_early"] = False
                    dataset.clear_episode_buffer()
                    continue

                dataset.save_episode()
                recorded_episodes += 1

    finally:
        log_say("Stop recording", play_sounds=True, blocking=True)

        # Note: dataset.finalize() is already called by VideoEncodingManager.__exit__

        if robot.is_connected:
            robot.disconnect()
        if teleop.is_connected:
            teleop.disconnect()

        if not is_headless() and listener is not None:
            listener.stop()

        log_say("Exiting", play_sounds=True)


if __name__ == "__main__":
    main()
