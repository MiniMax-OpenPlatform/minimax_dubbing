"""
时间戳对齐算法
基于PRD文档中定义的5步优化流程
"""
import requests
import logging
import tempfile
import os
from typing import Dict, Any, Optional
from pydub import AudioSegment
from services.clients.minimax_client import MiniMaxClient

logger = logging.getLogger(__name__)


class TimestampAlignmentError(Exception):
    """时间戳对齐异常"""
    pass


class TimestampAligner:
    """时间戳对齐器"""

    def __init__(self, minimax_client: MiniMaxClient):
        self.client = minimax_client

    def calculate_speed_steps(self, max_speed: float) -> dict:
        """
        根据max_speed动态计算优化步骤

        Args:
            max_speed: 允许的最大speed参数

        Returns:
            dict: 包含各步骤增量的配置
        """
        if max_speed >= 2.0:
            # 高速模式：保持原有逻辑
            return {
                'step3_increment': 0.2,
                'step4_increment': 0.5,
                'step5_speed': 2.0
            }
        elif max_speed >= 1.8:
            # 较高速模式
            return {
                'step3_increment': 0.2,
                'step4_increment': 0.4,
                'step5_speed': max_speed
            }
        elif max_speed >= 1.6:
            # 中高速模式
            return {
                'step3_increment': 0.2,
                'step4_increment': 0.3,
                'step5_speed': max_speed
            }
        elif max_speed >= 1.4:
            # 中等速度模式
            return {
                'step3_increment': 0.15,
                'step4_increment': 0.2,
                'step5_speed': max_speed
            }
        else:  # max_speed >= 1.2
            # 低速模式：最保守策略
            return {
                'step3_increment': 0.1,
                'step4_increment': 0.1,
                'step5_speed': max_speed
            }

    def get_audio_duration(self, audio_url: str) -> float:
        """
        获取音频文件的时长（去除前后静音）

        Args:
            audio_url: 音频文件URL

        Returns:
            float: 音频时长（秒）
        """
        try:
            # 下载音频文件
            response = requests.get(audio_url, timeout=30)
            response.raise_for_status()

            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            try:
                # 加载音频
                audio = AudioSegment.from_mp3(temp_file_path)

                # 去除前后静音（使用较低的静音阈值）
                # 静音阈值设为 -50dB
                trimmed_audio = audio.strip_silence(silence_thresh=-50)

                # 返回时长（毫秒转秒）
                duration = len(trimmed_audio) / 1000.0
                logger.info(f"音频时长（去除静音后）: {duration:.3f}s")
                return duration

            finally:
                # 删除临时文件
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"获取音频时长失败: {str(e)}")
            raise TimestampAlignmentError(f"获取音频时长失败: {str(e)}")

    def align_timestamp(self, text: str, target_duration: float, voice_id: str,
                       original_text: str = "", target_language: str = "中文",
                       custom_vocabulary: list = None, emotion: str = "auto",
                       language_boost: str = "Chinese", model: str = "speech-01-turbo",
                       max_speed: float = 2.0) -> Dict[str, Any]:
        """
        时间戳对齐算法主函数
        按照PRD文档中定义的5步优化流程

        Args:
            text: 需要对齐的文本
            target_duration: 目标时长（秒）
            voice_id: 音色ID
            original_text: 原文（用于优化）
            target_language: 目标语言
            custom_vocabulary: 专有词汇表
            emotion: 情绪参数
            language_boost: 语言增强
            model: TTS模型
            max_speed: 允许的最大speed参数，范围1.2-2.0

        Returns:
            Dict: 对齐结果
            {
                'success': bool,
                'audio_url': str,
                'final_duration': float,
                'ratio': float,
                'speed': float,
                'optimized_text': str,
                'optimization_steps': list,
                'trace_ids': list
            }
        """
        logger.info(f"开始时间戳对齐: '{text}' 目标时长={target_duration:.3f}s max_speed={max_speed}")

        # 计算基于max_speed的动态步进策略
        speed_config = self.calculate_speed_steps(max_speed)
        logger.info(f"Speed策略配置: {speed_config}")

        optimization_steps = []
        trace_ids = []
        current_text = text
        current_speed = 1.0

        try:
            # 第一步：生成初始TTS音频
            logger.info("第一步: 生成初始TTS音频")
            step1_result = self.client.text_to_speech(
                text=current_text,
                voice_id=voice_id,
                speed=current_speed,
                emotion=emotion,
                language_boost=language_boost,
                model=model
            )

            if not step1_result['success']:
                raise TimestampAlignmentError("初始TTS生成失败")

            audio_url = step1_result['audio_url']
            trace_ids.append(step1_result['trace_id'])

            # 去除静音并计算时长
            t_tts = self.get_audio_duration(audio_url)
            ratio = round(t_tts / target_duration, 2)

            optimization_steps.append({
                'step': 1,
                'action': '初始TTS生成',
                'text': current_text,
                'speed': current_speed,
                'duration': t_tts,
                'ratio': ratio,
                'success': t_tts <= target_duration
            })

            logger.info(f"第一步结果: T_tts={t_tts:.3f}s, 目标={target_duration:.3f}s, ratio={ratio:.3f}")

            # 如果T_tts <= 目标时长，对齐成功
            if t_tts <= target_duration:
                logger.info("第一步对齐成功")
                return {
                    'success': True,
                    'audio_url': audio_url,
                    'final_duration': t_tts,
                    'ratio': ratio,
                    'speed': current_speed,
                    'optimized_text': current_text,
                    'optimization_steps': optimization_steps,
                    'trace_ids': trace_ids
                }

            # 第二步：LLM翻译优化
            logger.info("第二步: LLM翻译优化")
            if original_text:  # 只有在提供原文的情况下才进行翻译优化
                target_char_count = int(len(current_text) * target_duration / t_tts)

                # 直接使用字典格式的专有词汇表
                processed_vocabulary = custom_vocabulary or []
                logger.info(f"[TimestampAligner] 专有词汇表: {processed_vocabulary}")

                step2_result = self.client.optimize_translation(
                    original_text=original_text,
                    current_translation=current_text,
                    target_language=target_language,
                    target_char_count=target_char_count,
                    custom_vocabulary=processed_vocabulary
                )

                if step2_result['success']:
                    current_text = step2_result['optimized_translation']
                    trace_ids.append(step2_result['trace_id'])

                    # 重新生成TTS
                    step2_tts_result = self.client.text_to_speech(
                        text=current_text,
                        voice_id=voice_id,
                        speed=current_speed,
                        emotion=emotion,
                        language_boost=language_boost,
                        model=model
                    )

                    if step2_tts_result['success']:
                        audio_url = step2_tts_result['audio_url']
                        trace_ids.append(step2_tts_result['trace_id'])
                        t_tts = self.get_audio_duration(audio_url)
                        ratio = round(t_tts / target_duration, 2)

                        optimization_steps.append({
                            'step': 2,
                            'action': 'LLM翻译优化',
                            'text': current_text,
                            'speed': current_speed,
                            'duration': t_tts,
                            'ratio': ratio,
                            'success': t_tts <= target_duration
                        })

                        logger.info(f"第二步结果: T_tts={t_tts:.3f}s, ratio={ratio:.3f}")

                        if t_tts <= target_duration:
                            logger.info("第二步对齐成功")
                            return {
                                'success': True,
                                'audio_url': audio_url,
                                'final_duration': t_tts,
                                'ratio': ratio,
                                'speed': current_speed,
                                'optimized_text': current_text,
                                'optimization_steps': optimization_steps,
                                'trace_ids': trace_ids
                            }

            # 第三步：调整speed参数
            logger.info("第三步: 调整speed参数")
            current_speed = round(min(t_tts / target_duration + speed_config['step3_increment'], max_speed), 2)
            step3_result = self.client.text_to_speech(
                text=current_text,
                voice_id=voice_id,
                speed=current_speed,
                emotion=emotion,
                language_boost=language_boost,
                model=model
            )

            if step3_result['success']:
                audio_url = step3_result['audio_url']
                trace_ids.append(step3_result['trace_id'])
                t_tts = self.get_audio_duration(audio_url)
                ratio = round(t_tts / target_duration, 2)

                optimization_steps.append({
                    'step': 3,
                    'action': f'调整speed={current_speed:.2f}',
                    'text': current_text,
                    'speed': current_speed,
                    'duration': t_tts,
                    'ratio': ratio,
                    'success': t_tts <= target_duration
                })

                logger.info(f"第三步结果: speed={current_speed:.2f}, T_tts={t_tts:.3f}s, ratio={ratio:.3f}")

                if t_tts <= target_duration:
                    logger.info("第三步对齐成功")
                    return {
                        'success': True,
                        'audio_url': audio_url,
                        'final_duration': t_tts,
                        'ratio': ratio,
                        'speed': current_speed,
                        'optimized_text': current_text,
                        'optimization_steps': optimization_steps,
                        'trace_ids': trace_ids
                    }

            # 第四步：speed增加重试
            logger.info("第四步: speed增加重试")
            current_speed = round(min(current_speed + speed_config['step4_increment'], max_speed), 2)
            step4_result = self.client.text_to_speech(
                text=current_text,
                voice_id=voice_id,
                speed=current_speed,
                emotion=emotion,
                language_boost=language_boost,
                model=model
            )

            if step4_result['success']:
                audio_url = step4_result['audio_url']
                trace_ids.append(step4_result['trace_id'])
                t_tts = self.get_audio_duration(audio_url)
                ratio = round(t_tts / target_duration, 2)

                optimization_steps.append({
                    'step': 4,
                    'action': f'speed增加到{current_speed:.2f}',
                    'text': current_text,
                    'speed': current_speed,
                    'duration': t_tts,
                    'ratio': ratio,
                    'success': t_tts <= target_duration
                })

                logger.info(f"第四步结果: speed={current_speed:.2f}, T_tts={t_tts:.3f}s, ratio={ratio:.3f}")

                if t_tts <= target_duration:
                    logger.info("第四步对齐成功")
                    return {
                        'success': True,
                        'audio_url': audio_url,
                        'final_duration': t_tts,
                        'ratio': ratio,
                        'speed': current_speed,
                        'optimized_text': current_text,
                        'optimization_steps': optimization_steps,
                        'trace_ids': trace_ids
                    }

            # 第五步：最大speed最后尝试
            logger.info(f"第五步: speed={speed_config['step5_speed']}最后尝试")
            current_speed = speed_config['step5_speed']
            step5_result = self.client.text_to_speech(
                text=current_text,
                voice_id=voice_id,
                speed=current_speed,
                emotion=emotion,
                language_boost=language_boost,
                model=model
            )

            if step5_result['success']:
                audio_url = step5_result['audio_url']
                trace_ids.append(step5_result['trace_id'])
                t_tts = self.get_audio_duration(audio_url)
                ratio = round(t_tts / target_duration, 2)

                optimization_steps.append({
                    'step': 5,
                    'action': f'最大speed={current_speed:.2f}',
                    'text': current_text,
                    'speed': current_speed,
                    'duration': t_tts,
                    'ratio': ratio,
                    'success': t_tts <= target_duration
                })

                logger.info(f"第五步结果: speed={current_speed:.2f}, T_tts={t_tts:.3f}s, ratio={ratio:.3f}")

                if t_tts <= target_duration:
                    logger.info("第五步对齐成功")
                    return {
                        'success': True,
                        'audio_url': audio_url,
                        'final_duration': t_tts,
                        'ratio': ratio,
                        'speed': current_speed,
                        'optimized_text': current_text,
                        'optimization_steps': optimization_steps,
                        'trace_ids': trace_ids
                    }

            # 所有步骤都失败，返回失败结果（设为静音）
            logger.warning("所有优化步骤都失败，该段落将设为静音")
            optimization_steps.append({
                'step': 6,
                'action': '优化失败，设为静音',
                'text': current_text,
                'speed': current_speed,
                'duration': t_tts,
                'ratio': ratio,
                'success': False
            })

            return {
                'success': False,
                'audio_url': None,
                'final_duration': 0.0,
                'ratio': ratio,
                'speed': current_speed,
                'optimized_text': current_text,
                'optimization_steps': optimization_steps,
                'trace_ids': trace_ids
            }

        except Exception as e:
            logger.error(f"时间戳对齐过程中出错: {str(e)}")
            raise TimestampAlignmentError(f"时间戳对齐失败: {str(e)}")

    def batch_align_segments(self, segments: list, project_config: dict) -> Dict[str, Any]:
        """
        批量处理段落的时间戳对齐

        Args:
            segments: 段落列表
            project_config: 项目配置

        Returns:
            批量处理结果
        """
        logger.info(f"开始批量时间戳对齐，共{len(segments)}个段落")

        results = {
            'total': len(segments),
            'success': 0,
            'failed': 0,
            'details': []
        }

        for i, segment in enumerate(segments):
            logger.info(f"处理段落 {i+1}/{len(segments)}")

            try:
                result = self.align_timestamp(
                    text=segment.get('translated_text', ''),
                    target_duration=segment.get('target_duration', 0),
                    voice_id=segment.get('voice_id', ''),
                    original_text=segment.get('original_text', ''),
                    target_language=project_config.get('target_language', '中文'),
                    custom_vocabulary=project_config.get('custom_vocabulary', []),
                    emotion=segment.get('emotion', 'auto'),
                    language_boost=project_config.get('language_boost', 'Chinese')
                )

                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['details'].append({
                    'segment_index': segment.get('index', i+1),
                    'result': result
                })

            except Exception as e:
                logger.error(f"处理段落{i+1}时出错: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'segment_index': segment.get('index', i+1),
                    'result': {
                        'success': False,
                        'error': str(e)
                    }
                })

        logger.info(f"批量对齐完成: 成功{results['success']}个, 失败{results['failed']}个")
        return results