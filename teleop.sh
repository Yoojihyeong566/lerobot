# 세트 A
lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/lerobot/right_follower --robot.id=right_follower --teleop.type=so101_leader --teleop.port=/dev/lerobot/right_leader --teleop.id=blue_leader &

# 세트 B
lerobot-teleoperate --robot.type=so101_follower --robot.port=/dev/lerobot/left_follower --robot.id=left_follower --teleop.type=so101_leader --teleop.port=/dev/lerobot/left_leader --teleop.id=black_leader &
