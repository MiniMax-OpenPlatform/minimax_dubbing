#!/usr/bin/env python3
"""
手动下载所需的AI模型

这个脚本会预先下载项目所需的所有AI模型到本地缓存，
避免在首次使用功能时等待下载。

使用方法:
    python download_models.py

或者下载特定模型:
    python download_models.py --demucs     # 只下载Demucs模型
    python download_models.py --facenet    # 只下载FaceNet模型
    python download_models.py --all        # 下载所有模型（默认）
"""

import argparse
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_demucs_model():
    """下载Demucs人声分离模型"""
    logger.info("=" * 60)
    logger.info("开始下载 Demucs 人声分离模型 (htdemucs)")
    logger.info("=" * 60)

    try:
        import torch
        from demucs.pretrained import get_model

        logger.info(f"模型缓存目录: {torch.hub.get_dir()}")

        # 下载htdemucs模型（这是默认使用的高质量模型）
        logger.info("正在下载 htdemucs 模型（约320MB）...")
        model = get_model('htdemucs')

        logger.info("✅ Demucs 模型下载成功！")
        logger.info(f"   缓存位置: {torch.hub.get_dir()}/checkpoints/")

        return True

    except ImportError as e:
        logger.error("❌ 缺少依赖包，请先安装: pip install demucs torch")
        return False
    except Exception as e:
        logger.error(f"❌ Demucs 模型下载失败: {str(e)}")
        return False


def download_facenet_model():
    """下载FaceNet人脸识别模型"""
    logger.info("=" * 60)
    logger.info("开始下载 FaceNet 人脸识别模型")
    logger.info("=" * 60)

    try:
        import torch
        from facenet_pytorch import MTCNN, InceptionResnetV1

        logger.info(f"模型缓存目录: {torch.hub.get_dir()}")

        # 下载MTCNN人脸检测模型
        logger.info("正在下载 MTCNN 人脸检测模型...")
        mtcnn = MTCNN(keep_all=True, device='cpu')
        logger.info("✅ MTCNN 模型下载成功！")

        # 下载InceptionResnetV1人脸特征提取模型
        logger.info("正在下载 InceptionResnetV1 特征提取模型（约100MB）...")
        resnet = InceptionResnetV1(pretrained='vggface2').eval()
        logger.info("✅ InceptionResnetV1 模型下载成功！")

        logger.info(f"   缓存位置: {torch.hub.get_dir()}/checkpoints/")

        return True

    except ImportError as e:
        logger.error("❌ 缺少依赖包，请先安装: pip install facenet-pytorch torch")
        return False
    except Exception as e:
        logger.error(f"❌ FaceNet 模型下载失败: {str(e)}")
        return False


def check_cache_status():
    """检查模型缓存状态"""
    logger.info("=" * 60)
    logger.info("检查模型缓存状态")
    logger.info("=" * 60)

    try:
        import torch
        cache_dir = torch.hub.get_dir()
        checkpoints_dir = os.path.join(cache_dir, 'checkpoints')

        logger.info(f"缓存目录: {cache_dir}")

        if os.path.exists(checkpoints_dir):
            files = os.listdir(checkpoints_dir)
            if files:
                logger.info(f"\n已缓存的模型文件 ({len(files)} 个):")
                total_size = 0
                for f in sorted(files):
                    file_path = os.path.join(checkpoints_dir, f)
                    size = os.path.getsize(file_path)
                    total_size += size
                    size_mb = size / (1024 * 1024)
                    logger.info(f"  - {f} ({size_mb:.1f} MB)")

                total_mb = total_size / (1024 * 1024)
                logger.info(f"\n总缓存大小: {total_mb:.1f} MB")
            else:
                logger.info("缓存目录为空，尚未下载任何模型")
        else:
            logger.info("缓存目录不存在，尚未下载任何模型")

    except ImportError:
        logger.error("❌ 请先安装 torch: pip install torch")
    except Exception as e:
        logger.error(f"❌ 检查缓存状态失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description='手动下载项目所需的AI模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python download_models.py              # 下载所有模型
  python download_models.py --demucs     # 只下载Demucs
  python download_models.py --facenet    # 只下载FaceNet
  python download_models.py --check      # 检查缓存状态
        """
    )

    parser.add_argument('--demucs', action='store_true',
                       help='只下载Demucs人声分离模型')
    parser.add_argument('--facenet', action='store_true',
                       help='只下载FaceNet人脸识别模型')
    parser.add_argument('--all', action='store_true',
                       help='下载所有模型（默认）')
    parser.add_argument('--check', action='store_true',
                       help='检查模型缓存状态')

    args = parser.parse_args()

    # 如果只是检查状态
    if args.check:
        check_cache_status()
        return

    # 确定要下载的模型
    download_all = args.all or (not args.demucs and not args.facenet)

    success_count = 0
    total_count = 0

    logger.info("🚀 开始下载模型...")
    logger.info("提示: 下载速度取决于网络状况，请耐心等待\n")

    # 下载Demucs
    if download_all or args.demucs:
        total_count += 1
        if download_demucs_model():
            success_count += 1
        print()  # 空行分隔

    # 下载FaceNet
    if download_all or args.facenet:
        total_count += 1
        if download_facenet_model():
            success_count += 1
        print()  # 空行分隔

    # 显示缓存状态
    check_cache_status()

    # 总结
    logger.info("\n" + "=" * 60)
    if success_count == total_count:
        logger.info(f"🎉 所有模型下载完成！({success_count}/{total_count})")
        logger.info("现在可以正常使用所有功能，无需等待模型下载")
    else:
        logger.warning(f"⚠️  部分模型下载失败 ({success_count}/{total_count})")
        logger.info("请检查网络连接和依赖包安装情况")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
