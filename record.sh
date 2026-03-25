#!/bin/bash
# Bimanual teleoperation data recording script
# Left follower:  /dev/lerobot/left_follower, camera /dev/video4
# Right follower: /dev/lerobot/right_follower, camera /dev/video6
# Left leader:    /dev/lerobot/left_leader
# Right leader:   /dev/lerobot/right_leader

_hf_whoami="$(hf auth whoami 2>/dev/null | head -1)"
HF_USER="${HF_USER:-$( [[ "$_hf_whoami" == "Not logged in" || -z "$_hf_whoami" ]] && echo "local" || echo "$_hf_whoami" )}"
DATASET_NAME="${1:-bimanual_so101_demo}"
TASK="${2:-Pick and place task}"
NUM_EPISODES="${3:-20}"
EPISODE_TIME_S="${4:-60}"
RESET_TIME_S="${5:-30}"

echo "Recording dataset: ${HF_USER}/${DATASET_NAME}"
echo "Task: ${TASK}"
echo "Episodes: ${NUM_EPISODES}, Episode time: ${EPISODE_TIME_S}s, Reset time: ${RESET_TIME_S}s"

lerobot-record \
  --robot.type=bi_so_follower \
  --robot.left_arm_config.port=/dev/lerobot/left_follower \
  --robot.left_arm_config.cameras='{wrist: {type: opencv, index_or_path: /dev/lerobot/cam_left_wrist, width: 640, height: 480, fps: 30}}' \
  --robot.right_arm_config.port=/dev/lerobot/right_follower \
  --robot.right_arm_config.cameras='{wrist: {type: opencv, index_or_path: /dev/lerobot/cam_right_wrist, width: 640, height: 480, fps: 30}}' \
  --robot.id=first_bimanual_follower \
  --teleop.type=bi_so_leader \
  --teleop.left_arm_config.port=/dev/lerobot/left_leader \
  --teleop.right_arm_config.port=/dev/lerobot/right_leader \
  --teleop.id=first_bimanual_leader \
  --dataset.repo_id="${HF_USER}/${DATASET_NAME}" \
  --dataset.single_task="${TASK}" \
  --dataset.num_episodes="${NUM_EPISODES}" \
  --dataset.episode_time_s="${EPISODE_TIME_S}" \
  --dataset.reset_time_s="${RESET_TIME_S}" \
  --dataset.push_to_hub=false \
  --display_data=true
