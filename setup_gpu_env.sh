#!/usr/bin/env bash
# Ubuntu GPU 서버에 프로젝트용 Python 가상환경과 CUDA 지원 패키지를 설치하고 검증한다.
set -euo pipefail

# nvidia-smi의 CUDA Version을 보고 필요하면 이 값을 cu121/cu124/cu126 등으로 바꾸세요.
CUDA_TAG="cu128"

echo "[1/7] NVIDIA 드라이버 확인"
if ! nvidia-smi; then
    echo "오류: NVIDIA 드라이버를 확인할 수 없습니다. nvidia-smi가 정상 동작하는지 확인하세요." >&2
    exit 1
fi

echo "[2/7] Python 3.13 확인"
if python3.13 --version; then
    echo "Python 3.13이 이미 설치되어 있습니다."
else
    echo "Python 3.13을 설치합니다."
    sudo apt-get update
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt-get update
    sudo apt-get install -y python3.13 python3.13-venv
fi

echo "[3/7] 가상환경 확인"
if [[ -x "venv/bin/python3.13" ]]; then
    echo "기존 venv 가상환경을 사용합니다."
else
    if [[ -d "venv" ]]; then
        echo "기존 venv는 Linux Python 3.13 가상환경이 아니므로 삭제 후 다시 생성합니다."
        rm -rf venv
    fi
    python3.13 -m venv venv
fi

echo "[4/7] CUDA 지원 PyTorch 설치"
# 해당 CUDA 인덱스의 최신 호환 버전을 requirements.txt보다 먼저 설치한다.
venv/bin/python -m pip install torch torchvision --index-url "https://download.pytorch.org/whl/${CUDA_TAG}"

echo "[5/7] 나머지 의존성 설치"
venv/bin/python -m pip install -r requirements.txt

echo "[6/7] GPU 인식 검증"
if ! environment_output="$(venv/bin/python src/check_environment.py)"; then
    printf '%s\n' "${environment_output}"
    echo "오류: 환경 검증에 실패했습니다. CUDA_TAG를 확인하고 다시 실행하세요." >&2
    exit 1
fi
printf '%s\n' "${environment_output}"
if ! grep -Fq "CUDA Available : Yes" <<<"${environment_output}"; then
    echo "오류: GPU가 인식되지 않았습니다. CUDA_TAG를 확인하고 다시 실행하세요." >&2
    exit 1
fi

echo "[7/7] 환경 설정 완료"
echo "다음: python src/model/smoke_test.py 로 스모크 테스트 → python src/model/exp8/train_baseline.py 실행"
