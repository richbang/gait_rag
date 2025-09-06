#!/bin/bash

# Python 3.12 설치 스크립트 (GPT-OSS 요구사항)

echo "🐍 Python 3.12 설치 스크립트"
echo "=================================="

# 옵션 선택
echo ""
echo "Python 3.12 설치 방법을 선택하세요:"
echo "1) uv를 사용한 자동 설치 (권장)"
echo "2) 시스템 패키지 매니저 사용 (apt)"
echo "3) pyenv 사용"
echo "4) 취소"
echo ""
read -p "선택 (1-4): " choice

case $choice in
    1)
        echo "📦 uv를 사용한 Python 3.12 설치..."
        
        # uv 설치 확인
        if ! command -v uv &> /dev/null; then
            echo "uv 설치 중..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            source $HOME/.cargo/env
        fi
        
        # uv가 Python 3.12를 자동으로 다운로드하고 설치
        echo "Python 3.12 다운로드 및 설치 중..."
        uv python install 3.12
        
        echo "✅ 완료! 이제 setup_gptoss_env.sh를 다시 실행하세요."
        ;;
        
    2)
        echo "📦 apt를 사용한 Python 3.12 설치..."
        echo "관리자 권한이 필요합니다."
        
        # deadsnakes PPA 추가
        sudo add-apt-repository ppa:deadsnakes/ppa -y
        sudo apt update
        sudo apt install python3.12 python3.12-venv python3.12-dev -y
        
        echo "✅ 완료! 이제 setup_gptoss_env.sh를 다시 실행하세요."
        ;;
        
    3)
        echo "📦 pyenv를 사용한 Python 3.12 설치..."
        
        # pyenv 설치 확인
        if ! command -v pyenv &> /dev/null; then
            echo "pyenv가 설치되어 있지 않습니다."
            echo "설치: https://github.com/pyenv/pyenv#installation"
            exit 1
        fi
        
        # Python 3.12 설치
        pyenv install 3.12.8
        pyenv local 3.12.8
        
        echo "✅ 완료! 이제 setup_gptoss_env.sh를 다시 실행하세요."
        ;;
        
    4)
        echo "취소되었습니다."
        exit 0
        ;;
        
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac