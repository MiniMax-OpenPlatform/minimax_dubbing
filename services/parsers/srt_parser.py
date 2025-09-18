"""
SRT字幕文件解析器
"""
import re
import logging
from typing import List, Dict, Tuple
from datetime import timedelta

logger = logging.getLogger(__name__)


class SRTParseError(Exception):
    """SRT解析异常"""
    pass


class SRTParser:
    """SRT字幕文件解析器"""

    @staticmethod
    def time_to_seconds(time_str: str) -> float:
        """
        将SRT时间格式转换为秒数
        格式: 00:00:06,879 -> 6.879秒
        """
        try:
            # 分离小时:分钟:秒,毫秒
            time_part, ms_part = time_str.split(',')
            hours, minutes, seconds = map(int, time_part.split(':'))
            milliseconds = int(ms_part)

            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            return total_seconds
        except (ValueError, IndexError) as e:
            raise SRTParseError(f"时间格式错误: {time_str} - {str(e)}")

    @staticmethod
    def seconds_to_time(seconds: float) -> str:
        """
        将秒数转换为SRT时间格式
        6.879秒 -> 00:00:06,879
        """
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            milliseconds = int((seconds % 1) * 1000)

            return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
        except (ValueError, OverflowError) as e:
            raise SRTParseError(f"秒数转换错误: {seconds} - {str(e)}")

    @classmethod
    def parse_srt_content(cls, content: str) -> List[Dict]:
        """
        解析SRT文件内容

        Args:
            content: SRT文件内容字符串

        Returns:
            List[Dict]: 解析后的字幕列表
            [
                {
                    'index': 1,
                    'start_time': 6.879,
                    'end_time': 11.039,
                    'text': '嗨，爸爸，我能借5万块钱吗？'
                },
                ...
            ]
        """
        if not content.strip():
            raise SRTParseError("SRT文件内容为空")

        logger.info("开始解析SRT内容")

        segments = []
        # 按双换行符分割段落
        blocks = re.split(r'\n\s*\n', content.strip())

        for block_idx, block in enumerate(blocks):
            if not block.strip():
                continue

            try:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    logger.warning(f"段落{block_idx + 1}格式不完整，跳过: {block}")
                    continue

                # 第一行：序号
                try:
                    index = int(lines[0].strip())
                except ValueError:
                    logger.warning(f"段落{block_idx + 1}序号格式错误: {lines[0]}")
                    index = block_idx + 1

                # 第二行：时间戳
                time_line = lines[1].strip()
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)

                if not time_match:
                    raise SRTParseError(f"段落{index}时间戳格式错误: {time_line}")

                start_time_str, end_time_str = time_match.groups()
                start_time = cls.time_to_seconds(start_time_str)
                end_time = cls.time_to_seconds(end_time_str)

                if start_time >= end_time:
                    raise SRTParseError(f"段落{index}时间戳逻辑错误: 开始时间({start_time})大于等于结束时间({end_time})")

                # 第三行及以后：文本内容
                text_lines = lines[2:]
                text = '\n'.join(text_lines).strip()

                if not text:
                    logger.warning(f"段落{index}文本内容为空")

                segment = {
                    'index': index,
                    'start_time': start_time,
                    'end_time': end_time,
                    'text': text,
                    'duration': end_time - start_time
                }

                segments.append(segment)
                logger.debug(f"解析段落{index}: {start_time:.3f}s-{end_time:.3f}s '{text[:30]}...'")

            except Exception as e:
                logger.error(f"解析段落{block_idx + 1}时出错: {str(e)}")
                raise SRTParseError(f"解析段落{block_idx + 1}失败: {str(e)}")

        if not segments:
            raise SRTParseError("未解析到任何有效段落")

        # 按索引排序
        segments.sort(key=lambda x: x['index'])

        logger.info(f"SRT解析完成，共{len(segments)}个段落")
        return segments

    @classmethod
    def parse_srt_file(cls, file_path: str) -> List[Dict]:
        """
        解析SRT文件

        Args:
            file_path: SRT文件路径

        Returns:
            List[Dict]: 解析后的字幕列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin1') as f:
                    content = f.read()
        except FileNotFoundError:
            raise SRTParseError(f"SRT文件不存在: {file_path}")
        except Exception as e:
            raise SRTParseError(f"读取SRT文件失败: {str(e)}")

        return cls.parse_srt_content(content)

    @classmethod
    def export_to_srt(cls, segments: List[Dict], output_path: str = None) -> str:
        """
        将段落列表导出为SRT格式

        Args:
            segments: 段落列表，每个段落包含index, start_time, end_time, text等字段
            output_path: 输出文件路径（可选）

        Returns:
            str: SRT格式的字符串内容
        """
        if not segments:
            raise SRTParseError("段落列表为空，无法导出")

        logger.info(f"开始导出{len(segments)}个段落到SRT格式")

        srt_content = []

        for segment in segments:
            try:
                index = segment.get('index', 0)
                start_time = segment.get('start_time', 0)
                end_time = segment.get('end_time', 0)
                text = segment.get('text', '')

                # 转换时间格式
                start_time_str = cls.seconds_to_time(start_time)
                end_time_str = cls.seconds_to_time(end_time)

                # 构建SRT段落
                srt_block = f"{index}\n{start_time_str} --> {end_time_str}\n{text}\n"
                srt_content.append(srt_block)

            except Exception as e:
                logger.error(f"导出段落{segment}时出错: {str(e)}")
                raise SRTParseError(f"导出段落失败: {str(e)}")

        result = '\n'.join(srt_content)

        # 如果指定了输出路径，写入文件
        if output_path:
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                logger.info(f"SRT文件已保存到: {output_path}")
            except Exception as e:
                raise SRTParseError(f"保存SRT文件失败: {str(e)}")

        return result

    @classmethod
    def validate_srt_format(cls, content: str) -> Tuple[bool, str]:
        """
        验证SRT格式是否正确

        Args:
            content: SRT内容

        Returns:
            Tuple[bool, str]: (是否有效, 错误消息)
        """
        try:
            segments = cls.parse_srt_content(content)
            return True, f"格式正确，共{len(segments)}个段落"
        except SRTParseError as e:
            return False, str(e)
        except Exception as e:
            return False, f"未知错误: {str(e)}"