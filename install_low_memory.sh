#!/bin/bash
# 低内存环境安装脚本

set -e  # 遇到错误立即退出

echo "========================================="
echo "低内存环境依赖安装脚本"
echo "========================================="
echo ""

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  警告: 未检测到虚拟环境，正在激活..."
    source venv/bin/activate
fi

# 清理缓存
echo "【1/7】清理 pip 缓存..."
pip cache purge
rm -rf ~/.cache/pip
echo "✅ 缓存清理完成"
echo ""

# 安装 Django 核心
echo "【2/7】安装 Django 核心包..."
pip install --no-cache-dir Django==5.2.* djangorestframework==3.15.* \
    django-cors-headers==4.8.* drf-nested-routers==0.94.* \
    psycopg2-binary==2.9.* requests==2.32.* pydub==0.25.* \
    python-dotenv==1.0.* django-ranged-response==0.2.0
echo "✅ Django 核心包安装完成"
echo ""

# 安装 PyTorch (CPU版本，体积小)
echo "【3/7】安装 PyTorch CPU 版本..."
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
echo "✅ PyTorch 安装完成"
echo ""

# 等待一下，让系统释放内存
sleep 3

# 安装 FaceNet
echo "【4/7】安装 FaceNet..."
pip install --no-cache-dir facenet-pytorch>=2.5.0
echo "✅ FaceNet 安装完成"
echo ""

sleep 2

# 安装 OpenCV 和 scikit-learn
echo "【5/7】安装 OpenCV 和 scikit-learn..."
pip install --no-cache-dir opencv-python>=4.10.0 scikit-learn>=1.5.0
echo "✅ OpenCV 和 scikit-learn 安装完成"
echo ""

sleep 2

# 安装 Demucs
echo "【6/7】安装 Demucs..."
pip install --no-cache-dir demucs==4.0.*
echo "✅ Demucs 安装完成"
echo ""

sleep 2

# 安装阿里云 SDK
echo "【7/7】安装阿里云 SDK..."
pip install --no-cache-dir dashscope==1.24.* librosa==0.10.* aliyun-python-sdk-core==2.16.*
echo "✅ 阿里云 SDK 安装完成"
echo ""

echo "========================================="
echo "🎉 所有依赖安装完成！"
echo "========================================="
echo ""
echo "验证安装..."
python -c "import torch; import cv2; import sklearn; print('✅ 核心包导入成功')"
echo ""
echo "可以运行以下命令启动服务："
echo "  python manage.py runserver 0.0.0.0:5172"
