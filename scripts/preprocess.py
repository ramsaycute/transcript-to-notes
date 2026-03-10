#!/usr/bin/env python3
"""
录音转录文本预处理脚本

自动检测输入文本是否需要预处理：
- 需要：单行文本、单行过长、标点前后有多余空格等 → 执行清洗
- 不需要：已有正常分段 → 直接复制

无论是否处理，都输出一个 _cleaned.md 文件作为下游统一输入。
"""

import argparse
import re
import shutil
import sys
from pathlib import Path


def needs_preprocess(text: str) -> bool:
    """判断文本是否需要预处理。

    满足任一条件即需要：
    1. 非空行数 ≤ 3 且存在单行超过 500 字符的行
    2. 中文标点前后存在空格（Apple 听写特征）
    """
    lines = [l for l in text.splitlines() if l.strip()]

    # 条件1：行数极少且单行很长
    if len(lines) <= 3 and any(len(l) > 500 for l in lines):
        return True

    # 条件2：中文标点前后有空格
    cn_puncts = "，。？！、；：""''（）《》【】"
    if re.search(rf"\s[{cn_puncts}]|[{cn_puncts}]\s", text):
        return True

    return False


def clean_punctuation_spaces(text: str) -> str:
    """清理中文标点前后的多余空格。"""
    cn_puncts = "，。？！、；：""''（）《》【】"
    text = re.sub(rf"\s+([{cn_puncts}])", r"\1", text)
    text = re.sub(rf"([{cn_puncts}])\s+", r"\1", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """按句末标点断句，保留标点在句子末尾。"""
    parts = re.split(r"(。|？|！)", text)

    sentences = []
    i = 0
    while i < len(parts):
        seg = parts[i]
        if i + 1 < len(parts) and parts[i + 1] in ("。", "？", "！"):
            seg = seg + parts[i + 1]
            i += 2
        else:
            i += 1
        seg = seg.strip()
        if seg:
            sentences.append(seg)
    return sentences


def group_paragraphs(sentences: list[str], group_size: int = 5) -> list[str]:
    """将句子按固定数量分组为段落。"""
    paragraphs = []
    for i in range(0, len(sentences), group_size):
        group = sentences[i : i + group_size]
        paragraphs.append("".join(group))
    return paragraphs


def process_file(
    input_path: str, output_path: str | None = None, group_size: int = 5
) -> str:
    """处理单个文件，返回输出文件路径。

    自动判断是否需要预处理：
    - 需要 → 清洗标点、断句、分段
    - 不需要 → 直接复制原文件
    """
    in_path = Path(input_path)
    if not in_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 确定输出路径
    if output_path:
        out_path = Path(output_path)
    else:
        out_dir = in_path.parent / "_cleaned"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{in_path.stem}_cleaned{in_path.suffix}"

    # 读取原文
    text = in_path.read_text(encoding="utf-8")

    if needs_preprocess(text):
        # 执行预处理
        text = clean_punctuation_spaces(text)
        sentences = split_sentences(text)
        paragraphs = group_paragraphs(sentences, group_size)
        result = "\n\n".join(paragraphs) + "\n"
        out_path.write_text(result, encoding="utf-8")
        print(f"Preprocessed: {out_path}")
    else:
        # 不需要处理，直接复制
        shutil.copy2(str(in_path), str(out_path))
        print(f"Copied (no preprocess needed): {out_path}")

    return str(out_path)


def main():
    parser = argparse.ArgumentParser(
        description="录音转录文本预处理（自动检测是否需要处理）"
    )
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（默认为 *_cleaned.md）")
    parser.add_argument(
        "-n",
        "--group-size",
        type=int,
        default=5,
        help="每段包含的句子数（默认 5）",
    )
    args = parser.parse_args()

    process_file(args.input, args.output, args.group_size)


if __name__ == "__main__":
    main()
