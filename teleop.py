#!/usr/bin/env python3
"""
Bimanual teleoperation test script (no recording).

Usage:
  python teleop.py
  python teleop.py --fps 30 --duration 120
"""

import os
from pathlib import Path

# Use calibration files bundled in this repo (overrides ~/.cache/huggingface/lerobot/calibration)
os.environ.setdefault("HF_LEROBOT_CALIBRATION", str(Path(__file__).parent / "calibration"))

from lerobot.robots.bi_so_follower.config_bi_so_follower import BiSOFollowerConfig
from lerobot.robots.so_follower.config_so_follower import SOFollowerConfig
from lerobot.teleoperators.bi_so_leader.config_bi_so_leader import BiSOLeaderConfig
from lerobot.teleoperators.so_leader.config_so_leader import SOLeaderConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.teleoperators.utils import make_teleoperator_from_config
from lerobot.processor import make_default_processors
from lerobot.scripts.lerobot_teleoperate import teleop_loop
from lerobot.utils.utils import init_logging

import argparse


def build_robot_config() -> BiSOFollowerConfig:
    return BiSOFollowerConfig(
        id="first_bimanual_follower",
        left_arm_config=SOFollowerConfig(
            port="/dev/lerobot/left_follower",
            cameras={
                "wrist": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_left_wrist",
                    width=640, height=480, fps=30, fourcc="MJPG",
                )
            },
        ),
        right_arm_config=SOFollowerConfig(
            port="/dev/lerobot/right_follower",
            cameras={
                "wrist": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_right_wrist",
                    width=640, height=480, fps=30, fourcc="MJPG",
                ),
                "top": OpenCVCameraConfig(
                    index_or_path="/dev/lerobot/cam_right_top",
                    width=640, height=480, fps=30, fourcc="MJPG",
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
    parser = argparse.ArgumentParser(description="Bimanual SO101 teleoperation test")
    parser.add_argument("--fps", default=30, type=int)
    parser.add_argument("--duration", default=None, type=float, help="Duration in seconds (None=unlimited)")
    args = parser.parse_args()

    init_logging()

    robot = make_robot_from_config(build_robot_config())
    teleop = make_teleoperator_from_config(build_teleop_config())
    teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

    robot.connect()
    teleop.connect()

    try:
        teleop_loop(
            teleop=teleop,
            robot=robot,
            fps=args.fps,
            teleop_action_processor=teleop_action_processor,
            robot_action_processor=robot_action_processor,
            robot_observation_processor=robot_observation_processor,
            duration=args.duration,
        )
    except KeyboardInterrupt:
        pass
    finally:
        robot.disconnect()
        teleop.disconnect()


if __name__ == "__main__":
    main()
