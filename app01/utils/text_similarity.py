"""
文本相似度检测工具
使用 Jaccard 相似度和余弦相似度算法
不依赖外部库，纯 Python 实现
"""

import re
from collections import Counter
from math import sqrt
from html import unescape


def strip_html_tags(text):
    """去除 HTML 标签，获取纯文本"""
    if not text:
        return ''
    
    text = unescape(text)
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_words(text, n=2):
    """
    提取文本中的 n-gram 词组
    中文使用字符级 n-gram，英文使用单词级 n-gram
    """
    text = re.sub(r'\s+', ' ', text.strip())
    if not text:
        return []

    chinese_chars = re.findall(r'[\u4e00-\u9fa5]+', text)
    english_words = re.findall(r'[a-zA-Z]+', text)

    result = []

    for char_block in chinese_chars:
        for i in range(len(char_block) - n + 1):
            result.append(char_block[i:i+n])

    for word in english_words:
        word = word.lower()
        if len(word) >= n:
            for i in range(len(word) - n + 1):
                result.append(word[i:i+n])

    return result


def get_ngram_set(text, n=2):
    """获取文本的 n-gram 集合"""
    words = extract_words(text, n)
    return set(words)


def jaccard_similarity(text1, text2, n=2):
    """计算 Jaccard 相似度（基于 n-gram 集合）"""
    set1 = get_ngram_set(text1, n)
    set2 = get_ngram_set(text2, n)

    if not set1 or not set2:
        return 0.0

    intersection = set1 & set2
    union = set1 | set2

    return len(intersection) / len(union) if union else 0.0


def get_ngram_frequency(text, n=2):
    """获取文本 n-gram 词频"""
    words = extract_words(text, n)
    return Counter(words)


def cosine_similarity(text1, text2, n=2):
    """计算余弦相似度（基于 n-gram）"""
    freq1 = get_ngram_frequency(text1, n)
    freq2 = get_ngram_frequency(text2, n)

    if not freq1 or not freq2:
        return 0.0

    all_ngrams = set(freq1.keys()) | set(freq2.keys())

    vec1 = [freq1.get(w, 0) for w in all_ngrams]
    vec2 = [freq2.get(w, 0) for w in all_ngrams]

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sqrt(sum(a * a for a in vec1))
    magnitude2 = sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def combined_similarity(text1, text2, jaccard_weight=0.4, cosine_weight=0.6):
    """
    综合相似度计算
    结合 Jaccard 和余弦相似度，加权平均
    n=2 使用字符级二元组，对中文效果好
    """
    text1 = strip_html_tags(text1)
    text2 = strip_html_tags(text2)
    jaccard = jaccard_similarity(text1, text2, n=2)
    cosine = cosine_similarity(text1, text2, n=2)

    return jaccard * jaccard_weight + cosine * cosine_weight


def check_text_similarity(text1, text2, threshold=0.8):
    """
    检查两段文本的相似度是否超过阈值

    Args:
        text1: 文本1
        text2: 文本2
        threshold: 阈值，默认 0.8 (80%)

    Returns:
        tuple: (是否超过阈值, 相似度值)
    """
    similarity = combined_similarity(text1, text2)
    is_similar = similarity >= threshold
    return is_similar, similarity


def find_most_similar_article(new_content, articles_queryset, threshold=0.8):
    """
    在文章列表中查找与新文章最相似的文章

    Args:
        new_content: 新文章内容
        articles_queryset: 文章查询集
        threshold: 阈值

    Returns:
        tuple: (是否有相似文章, 最相似文章对象, 相似度值)
    """
    most_similar = None
    max_similarity = 0.0

    for article in articles_queryset:
        similarity = combined_similarity(new_content, article.content)
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar = article

    if most_similar and max_similarity >= threshold:
        return True, most_similar, max_similarity

    return False, None, max_similarity