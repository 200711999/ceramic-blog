import json
import requests
from django.conf import settings


def _chat_completion(system_prompt='', user_prompt='', messages=None, temperature=0.7, max_tokens=2048):
    """
    通用 AI 对话调用，带主备 fallback。
    返回 dict: {'text': str, 'error': str or None}
    """
    configs = [
        {
            'api_key': getattr(settings, 'AI_API_KEY', ''),
            'base_url': getattr(settings, 'AI_BASE_URL', 'https://api.siliconflow.cn/v1'),
            'model': getattr(settings, 'AI_MODEL', 'deepseek-ai/DeepSeek-V3'),
        },
        {
            'api_key': getattr(settings, 'AI_API_KEY_BACKUP', ''),
            'base_url': getattr(settings, 'AI_BASE_URL_BACKUP', 'https://api.deepseek.com'),
            'model': getattr(settings, 'AI_MODEL_BACKUP', 'deepseek-chat'),
        },
    ]
    timeout = getattr(settings, 'AI_TIMEOUT', 30)
    last_error = ''

    if messages is None:
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]

    for cfg in configs:
        if not cfg['api_key']:
            continue
        try:
            resp = requests.post(
                f"{cfg['base_url']}/chat/completions",
                headers={
                    'Authorization': f'Bearer {cfg["api_key"]}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': cfg['model'],
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return {'text': data['choices'][0]['message']['content'], 'error': None}
        except requests.exceptions.Timeout:
            last_error = 'AI 请求超时,请稍后重试'
        except requests.exceptions.ConnectionError:
            last_error = '网络连接失败,请检查网络或 API 配置'
            continue
        except requests.exceptions.HTTPError as e:
            try:
                err = e.response.json()
                msg = err.get('error', {}).get('message', str(e))
            except Exception:
                msg = str(e)
            last_error = f'API 错误: {msg}'
            continue
        except Exception as e:
            last_error = f'请求异常: {str(e)}'
            continue

    return {'text': '', 'error': last_error or 'AI 服务暂不可用'}


def call_ai_generate(keywords='', style='干货帖子', existing_content='', wc_min='', wc_max=''):
    """
    调用 AI 生成/润色文章。
    style: '干货帖子' | '心情文案' | '技术教程' | '润色改写'
    wc_min/wc_max: 最小/最大字数 (字符串,可为空)
    返回 dict: {'title': str, 'content': str, 'error': str or None}
    """
    if style == '润色改写':
        system_prompt = (
            "你是一位资深编辑,擅长润色、纠错和排版中文文章。"
            "用户会给你一段原文,请直接输出润色后的正文内容,不要添加额外解释。"
            "保持原文主题和长度,只做语言优化、错别字修正、段落排版。"
        )
        user_prompt = f"请润色以下文章:\n\n{existing_content}"
    else:
        # 构建字数要求 — 以中文字符数为准
        if wc_min and wc_max:
            wc_requirement = f"正文字数严格在 {wc_min} 到 {wc_max} 字之间,以中文字符计(不含标点空格)"
        elif wc_min:
            wc_requirement = f"正文至少 {wc_min} 字,以中文字符计(不含标点空格)"
        elif wc_max:
            wc_requirement = f"正文不超过 {wc_max} 字,以中文字符计(不含标点空格)"
        else:
            wc_requirement = "正文1200字左右,以中文字符计(不含标点空格)"

        system_prompt = (
            f"你是一位资深内容创作者,擅长写{style}。"
            "根据用户提供的关键词,生成一篇结构完整、内容充实的正文。"
            f"文章要求: {wc_requirement},层次分明,包含2-4个小标题。"
            "\n\n【最高优先级规则】"
            "\n1. 完整性: 文章必须有完整的开头、正文、结尾,绝不能写到一半截断。字数没达到宁可多写也要保证结尾完整。"
            "\n2. 字数: 必须满足字数区间要求。如果不够,请补充细节、举例、分析来充实内容。"
            "\n3. 质量: 内容具体有深度,不要空泛说教。用具体例子和数据支撑观点。"
            "\n\n输出格式(严格执行):"
            "\n第一行: |||TITLE|||"
            "\n第二行: 文章标题"
            "\n第三行: |||CONTENT|||"
            "\n之后: 正文(支持 Markdown 排版,小标题用 ## 标记)"
            "\n\n注意: 分隔符各占独立一行,前后不要加任何文字。"
        )
        user_prompt = (
            f"关键词/主题:{keywords}\n\n"
            f"请生成一篇关于'{keywords}'的文章,{wc_requirement}。"
            f"写完后请自查: 结尾是否完整? 没有截断? 那就可以输出了。"
        )

    result = _chat_completion(system_prompt, user_prompt, temperature=0.7, max_tokens=8192)
    if result['error']:
        return {'title': '', 'content': '', 'error': result['error']}

    text = result['text']

    if style == '润色改写':
        return {'title': '', 'content': text.strip(), 'error': None}

    # 用分隔符 |||TITLE||| 和 |||CONTENT||| 解析
    title = ''
    content = ''
    try:
        if '|||TITLE|||' in text and '|||CONTENT|||' in text:
            # 提取标题：|||TITLE||| 之后、|||CONTENT||| 之前的内容
            title_part = text.split('|||TITLE|||')[1].split('|||CONTENT|||')[0]
            content_part = text.split('|||CONTENT|||')[1]
            title = title_part.strip()
            content = content_part.strip()
    except Exception:
        pass

    # 如果分隔符解析失败,回退到旧逻辑
    if not content:
        # 尝试 JSON
        try:
            clean = text
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0]
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0]
            obj = json.loads(clean.strip())
            title = obj.get('title', '')
            content = obj.get('content', '')
        except Exception:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                try:
                    obj = json.loads(text[start:end + 1])
                    title = obj.get('title', '')
                    content = obj.get('content', '')
                except Exception:
                    pass

    # 最终兜底
    if not content:
        lines = text.strip().split('\n')
        title = lines[0].lstrip('#').strip() if lines else ''
        content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else text.strip()

    return {'title': title, 'content': content, 'error': None}


def call_ai_summarize(content=''):
    """
    调用 AI 对文章进行总结。
    返回 dict: {'summary': str, 'error': str or None}
    """
    if not content:
        return {'summary': '', 'error': '正文为空,无法总结'}

    system_prompt = (
        "你是一位资深内容摘要专家。请对用户提供的文章进行精炼总结,"
        "保留核心观点和关键信息,去除冗余描述。"
        "总结控制在 150 字以内,语言简洁流畅,直接输出总结文本,不要添加额外说明。"
    )
    user_prompt = f"请总结以下文章:\n\n{content}"

    result = _chat_completion(system_prompt, user_prompt, temperature=0.5, max_tokens=512)
    if result['error']:
        return {'summary': '', 'error': result['error']}
    return {'summary': result['text'].strip(), 'error': None}


def call_ai_continue(content=''):
    """
    调用 AI 对文章进行续写。
    返回 dict: {'continuation': str, 'error': str or None}
    """
    if not content:
        return {'continuation': '', 'error': '正文为空,无法续写'}

    system_prompt = (
        "你是一位资深内容创作者。请根据用户提供的文章上下文,"
        "以相同的风格和语气继续撰写后续内容。"
        "保持逻辑连贯、内容充实,直接输出续写段落,不要添加额外说明。"
        "输出长度控制在 300-800 字。"
    )
    user_prompt = f"请续写以下内容:\n\n{content}"

    result = _chat_completion(system_prompt, user_prompt, temperature=0.7, max_tokens=2048)
    if result['error']:
        return {'continuation': '', 'error': result['error']}
    return {'continuation': result['text'].strip(), 'error': None}


def call_ai_classify(title='', content='', categories=None, tags=None):
    """
    调用 AI 根据内容自动选择最合适的分类和标签。
    categories: [{'id': 1, 'name': '技术'}, ...]
    tags: [{'id': 1, 'name': 'Python'}, ...]
    返回 dict: {'category_id': int|None, 'tag_ids': list[int], 'error': str or None}
    """
    categories = categories or []
    tags = tags or []

    cat_list = '\n'.join([f"- ID:{c['id']} 名称:{c['name']}" for c in categories]) or '无'
    tag_list = '\n'.join([f"- ID:{t['id']} 名称:{t['name']}" for t in tags]) or '无'

    system_prompt = (
        "你是一个内容分类专家。根据用户提供的文章标题和正文,"
        "从给定的分类和标签列表中,选出最匹配的分类 ID 和标签 ID 列表。"
        "如果现有分类/标签都不合适,你可以建议新建一个,给出简洁的名称(不超过6个字)。"
        "只输出一行合法的 JSON 对象,不要用 markdown 代码块包裹,不要添加解释说明或任何其他文字。"
        "JSON 格式: {\"category_id\": 数字或null, \"new_category_name\": \"字符串或null\", \"tag_ids\": [数字1, 数字2], \"new_tag_names\": [\"字符串1\", \"字符串2\"]}"
    )

    user_prompt = (
        f"文章标题:{title}\n"
        f"文章正文:{content[:500]}\n\n"
        f"可选分类:\n{cat_list}\n\n"
        f"可选标签:\n{tag_list}\n\n"
        "请输出最匹配的 category_id 和 tag_ids。"
        "如果现有分类都不合适, category_id 填 null,并在 new_category_name 里给出一个新分类名称(如'技术求助');"
        "如果现有标签都不合适, tag_ids 填空数组 [],并在 new_tag_names 里给出1-3个新标签名称(如['电脑问题','蓝屏'])。"
        "new_category_name 和 new_tag_names 如果不需要则填 null 和空数组。"
    )

    result = _chat_completion(system_prompt, user_prompt, temperature=0.3, max_tokens=512)
    if result['error']:
        return {'category_id': None, 'tag_ids': [], 'error': result['error']}

    text = result['text']

    # 提取 JSON
    try:
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        obj = json.loads(text.strip())
    except Exception:
        # 尝试从文本中直接找 JSON
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and start < end:
            try:
                obj = json.loads(text[start:end + 1])
            except Exception:
                return {'category_id': None, 'tag_ids': [], 'error': '无法解析 JSON'}
        else:
            return {'category_id': None, 'tag_ids': [], 'error': '无法解析 JSON'}

    category_id = obj.get('category_id')
    new_category_name = obj.get('new_category_name')
    tag_ids = obj.get('tag_ids', [])
    new_tag_names = obj.get('new_tag_names', [])

    # 校验 category_id 是否在可选列表中
    valid_cat_ids = {c['id'] for c in categories}
    if category_id is not None and category_id not in valid_cat_ids:
        category_id = None

    # 校验 tag_ids
    valid_tag_ids = {t['id'] for t in tags}
    tag_ids = [tid for tid in tag_ids if tid in valid_tag_ids]

    # 清理新名称
    if not new_category_name or not isinstance(new_category_name, str):
        new_category_name = None
    if not new_tag_names or not isinstance(new_tag_names, list):
        new_tag_names = []
    new_tag_names = [n for n in new_tag_names if isinstance(n, str) and n.strip()]

    return {
        'category_id': category_id,
        'new_category_name': new_category_name,
        'tag_ids': tag_ids,
        'new_tag_names': new_tag_names,
        'error': None,
    }


def call_ai_chat(question='', history=None):
    """
    调用 AI 进行问答对话。
    history: [{'role': 'user'|'assistant', 'content': '...'}, ...]
    返回 dict: {'answer': str, 'error': str or None}
    """
    system_prompt = (
        "你是一个友好、专业的论坛智能助手,擅长回答技术和生活类问题。"
        "回答要简洁、有建设性,控制在 300 字以内。"
        "如果问题涉及代码,给出关键代码示例。"
        "如果问题不清楚,礼貌地请用户补充细节。"
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    if history:
        messages.extend(history[-10:])  # 只保留最近 10 轮
    messages.append({'role': 'user', 'content': question})

    result = _chat_completion(messages=messages, temperature=0.7, max_tokens=1024)
    if result['error']:
        return {'answer': '', 'error': result['error']}
    return {'answer': result['text'].strip(), 'error': None}
