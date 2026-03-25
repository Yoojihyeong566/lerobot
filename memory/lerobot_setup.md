# LeRobot SO-101 Bimanual Setup

## 하드웨어 구성

| 역할 | 포트 (고정) | 시리얼 번호 |
|---|---|---|
| Left follower | `/dev/lerobot/left_follower` → ttyACM1 | 5AE6082430 |
| Right follower | `/dev/lerobot/right_follower` → ttyACM3 | 5AE6081116 |
| Left leader | `/dev/lerobot/left_leader` → ttyACM0 | 5AE6053416 |
| Right leader | `/dev/lerobot/right_leader` → ttyACM2 | 5AE6081421 |

| 카메라 | 경로 (고정) | 장치 |
|---|---|---|
| Left wrist | `/dev/lerobot/cam_left_wrist` → video4 | USB HD Camera (1e45:8022, serial 200910120001) |
| Right wrist | `/dev/lerobot/cam_right_wrist` → video6 | icspring camera (32e6:9211) |
| Right top | `/dev/lerobot/cam_right_top` → video8 | Logitech C920 (046d:082d, serial 6FC73FAF) |

## 캘리브레이션

캘리브레이션 파일 위치: `~/.cache/huggingface/lerobot/calibration/`
- robots/so_follower/first_bimanual_follower_left.json
- robots/so_follower/first_bimanual_follower_right.json
- teleoperators/so_leader/first_bimanual_leader_left.json
- teleoperators/so_leader/first_bimanual_leader_right.json

캘리브레이션 명령어:
```bash
# Robot (follower) 캘리브레이션
lerobot-calibrate \
  --robot.type=bi_so_follower \
  --robot.left_arm_config.port=/dev/lerobot/left_follower \
  --robot.right_arm_config.port=/dev/lerobot/right_follower \
  --robot.id=first_bimanual_follower

# Teleop (leader) 캘리브레이션
lerobot-calibrate \
  --teleop.type=bi_so_leader \
  --teleop.left_arm_config.port=/dev/lerobot/left_leader \
  --teleop.right_arm_config.port=/dev/lerobot/right_leader \
  --teleop.id=first_bimanual_leader
```

## 주요 파일

| 파일 | 용도 |
|---|---|
| `teleop.sh` | teleoperation 테스트 (record 없이) |
| `record.py` | 데이터 녹화 (Python, 권장) |
| `record.sh` | 데이터 녹화 (bash, lerobot-record CLI) |
| `camera_stream.py` | 카메라 스트리밍 GUI |
| `99-lerobot.rules` | udev 장치 고정 규칙 |

## 실행 방법

```bash
# Teleoperation
bash teleop.sh

# 데이터 녹화
python record.py --dataset local/my_dataset --task "Pick up cube" --episodes 20 --episode_s 45

# 카메라 스트리밍 확인
python camera_stream.py /dev/lerobot/cam_left_wrist

# 사용 가능한 카메라 목록
python camera_stream.py
```

## record.py 주요 옵션

| 옵션 | 기본값 | 설명 |
|---|---|---|
| `--dataset` | `local/bimanual_so101_demo` | 저장 경로 |
| `--task` | `Pick and place task` | 태스크 설명 |
| `--episodes` | 20 | 에피소드 수 |
| `--episode_s` | 60 | 에피소드당 녹화 시간(초) |
| `--reset_s` | 30 | 에피소드 간 리셋 시간(초) |
| `--fps` | 30 | 프레임레이트 |
| `--root` | `~/.cache/huggingface/lerobot/` | 저장 루트 경로 |
| `--no_display` | False | Rerun 시각화 비활성화 |

데이터셋 저장 위치: `~/.cache/huggingface/lerobot/local/<dataset_name>/`

## udev 장치 고정 규칙

규칙 파일: `/etc/udev/rules.d/99-lerobot.rules`

재설치 방법:
```bash
sudo cp /home/yoo/lerobot/99-lerobot.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

원리: USB 장치마다 고유한 시리얼 번호를 갖고 있음. udev가 연결 시 시리얼 번호를 읽어 `/dev/lerobot/` 아래 고정 심볼릭 링크를 생성.

## 트러블슈팅

### FileExistsError: dataset directory already exists
이전 실패로 빈 디렉토리가 남은 경우:
```bash
rm -rf ~/.cache/huggingface/lerobot/local/<dataset_name>
```

### TimeoutError: camera latest frame is too old
카메라 설정에 `fourcc="MJPG"` 추가. YUYV(기본값)는 USB 대역폭을 많이 써서 느림.

### ConnectionError: Failed to write 'Lock' on id_=N
모터 N번이 응답 없음. 하드웨어 문제:
- 팔 전원 확인
- 모터 (N-1)번 ↔ N번 사이 케이블 연결 상태 확인 (daisy chain)

### 캘리브레이션 재요구
캘리브레이션 파일 이름이 robot.id와 불일치할 때 발생.
`bi_so_follower`는 내부적으로 `{robot.id}_left`, `{robot.id}_right` 이름으로 파일을 찾음.

기존 파일 재사용 시:
```bash
cd ~/.cache/huggingface/lerobot/calibration/robots/so_follower/
cp old_name.json first_bimanual_follower_left.json
cp old_name.json first_bimanual_follower_right.json
```

### video codec 재생 안됨
기본 코덱 `libsvtav1`(AV1)은 많은 플레이어가 미지원.
`record.py`에서 `vcodec="h264"`로 변경 (이미 적용됨).

### HF_USER "Not logged in" 문제
로그인:
```bash
hf auth login
```
또는 환경변수 설정:
```bash
export HF_USER=my_username
```
로그인 없이 로컬 저장만 할 경우 자동으로 `local/`로 저장됨.

## Rerun GUI 설명

- **observation**: 로봇 각 관절의 현재 각도 + 카메라 이미지
- **action**: 리더 암에서 읽어 팔로워에 보내는 목표 각도
- action과 observation이 거의 겹치면 팔로워가 잘 따라가는 것
