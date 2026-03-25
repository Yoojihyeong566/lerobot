#!/usr/bin/env python3
"""
Bimanual MIRROR teleoperation test script.

Operator sits on the OPPOSITE side of the table (facing the robot).
  - Left leader  → Right follower  (cross-mapping)
  - Right leader → Left follower   (cross-mapping)
  - shoulder_pan & wrist_roll are negated (mirror symmetry)

Usage:
  python teleop_mirror.py
  python teleop_mirror.py --fps 30 --duration 120
"""

import argparse

from lerobot.robots.bi_so_follower.config_bi_so_follower import BiSOFollowerConfig
from lerobot.robots.so_follower.config_so_follower import SOFollowerConfig
from lerobot.teleoperators.bi_so_leader.config_bi_so_leader import BiSOLeaderConfig
from lerobot.teleoperators.so_leader.config_so_leader import SOLeaderConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.robots.utils import make_robot_from_config
from lerobot.teleoperators.utils import make_teleoperator_from_config
from lerobot.processor import make_default_processors
from lerobot.processor.pipeline import RobotActionProcessorStep
from lerobot.processor.core import RobotAction
from lerobot.scripts.lerobot_teleoperate import teleop_loop
from lerobot.utils.utils import init_logging


# ── Mirror configuration ─────────────────────────────────────────────────────
# Joints to negate when mirroring (pan/roll reverse direction across table)
NEGATE_JOINTS = {"shoulder_pan", "wrist_roll"}


class MirrorActionProcessor(RobotActionProcessorStep):
    """Swap left↔right arms and negate mirror-axis joints."""

    def action(self, action: RobotAction) -> RobotAction:
        mirrored: RobotAction = {}
        for key, value in action.items():
            # Swap prefixes: left → right, right → left
            if key.startswith("left_"):
                new_key = "right_" + key[len("left_"):]
            elif key.startswith("right_"):
                new_key = "left_" + key[len("right_"):]
            else:
                new_key = key

            # Negate mirror-axis joints (check joint name without prefix and .pos suffix)
            joint_name = new_key.split("_", 1)[-1].removesuffix(".pos")  # e.g. "shoulder_pan"
            # Also handle case where prefix was already stripped
            for neg_joint in NEGATE_JOINTS:
                if joint_name == neg_joint or new_key.removesuffix(".pos") == neg_joint:
                    value = -value
                    break

            mirrored[new_key] = value
        return mirrored

    def transform_features(self, features):
        return features  # No shape/dtype changes


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
    parser = argparse.ArgumentParser(description="Bimanual SO101 MIRROR teleoperation test")
    parser.add_argument("--fps", default=30, type=int)
    parser.add_argument("--duration", default=None, type=float, help="Duration in seconds (None=unlimited)")
    args = parser.parse_args()

    init_logging()

    robot = make_robot_from_config(build_robot_config())
    teleop = make_teleoperator_from_config(build_teleop_config())
    teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors()

    # Insert mirror processor as the first step in teleop_action_processor
    teleop_action_processor.steps.insert(0, MirrorActionProcessor())

    print("=== MIRROR MODE ===")
    print("Left leader  → Right follower")
    print("Right leader → Left follower")
    print(f"Negated joints: {NEGATE_JOINTS}")
    print("===================")

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
