"""数据解析工具"""
import struct
from typing import List, Union, Tuple


class DataParser:
    """数据解析器"""

    @staticmethod
    def word_to_bits(word: int) -> List[bool]:
        """将字转换为位列表"""
        return [(word >> i) & 1 for i in range(16)]

    @staticmethod
    def bits_to_word(bits: List[bool]) -> int:
        """将位列表转换为字"""
        word = 0
        for i, bit in enumerate(bits[:16]):
            if bit:
                word |= (1 << i)
        return word

    @staticmethod
    def bytes_to_words(data: bytes) -> List[int]:
        """将字节数据转换为字列表"""
        words = []
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                word = struct.unpack('<H', data[i:i + 2])[0]
                words.append(word)
        return words

    @staticmethod
    def words_to_bytes(words: List[int]) -> bytes:
        """将字列表转换为字节数据"""
        data = b''
        for word in words:
            data += struct.pack('<H', word & 0xFFFF)
        return data

    @staticmethod
    def parse_position(raw_value: int, scale: float = 0.01) -> float:
        """解析位置数据

        Args:
            raw_value: 原始值
            scale: 比例因子（默认0.01mm）

        Returns:
            实际位置值（mm）
        """
        return raw_value * scale

    @staticmethod
    def encode_position(position: float, scale: float = 0.01) -> int:
        """编码位置数据

        Args:
            position: 位置值（mm）
            scale: 比例因子

        Returns:
            编码后的原始值
        """
        return int(position / scale)