# 根据小说内容生成

import textwrap


def get_context2lines_prompt(possible_characters, novel_content,possible_emotions,possible_strengths) -> str:

    prompt = f"""
你的任务是将给定小说内容划分为角色台词和旁白，并输出包含<result>标签的结构化JSON结果。

划分规则：

台词识别:
识别所有角色说话的内容，包括带引号、破折号、叹号等常见台词标记的文本。
如果角色在给定角色列表中，使用该角色名；
如果角色未在列表中出现，根据上下文合理归纳角色名。
重要规则：相邻台词之间如果角色相同，可以适当合并，但是一段内容最多不超过150字。如果单段内容超过150字，请将内容拆分为多条。


旁白识别:
对叙述性、心理描写、环境描写、动作描写等非台词内容统一标记为“旁白：”。
重要规则：相邻台词之间如果都为旁白内容，可以适当合并，但是一段内容最多不超过150字。如果单段内容超过150字，请将内容拆分为多条。

情绪以及情绪强弱识别:
根据上下文场景，识别出每条台词所对应的情绪以及情绪强度。情绪和情绪强度的内容必须来自情绪列表possible_emotions和情绪强度列表possible_strengths。
旁白的情绪和情绪强度统一为一样的，统一为‘平静’情绪，强度为‘中等’。

特殊情况处理:
多角色对话连续出现时，每条台词对应正确角色。
混合旁白和台词的段落可拆分为旁白和台词两条记录。
避免重复、遗漏台词或旁白。

输出格式:
输出严格遵循包含<result>标签的JSON数组形式

示例：
<result>
[
{"role_name": "张三", "text_content": "你到底在干什么！", "emotion_name": "生气", "strength_name": "强烈"},
{"role_name": "旁白", "text_content": "此时，张三愤怒站着", "emotion_name": "平静", "strength_name": "中等"},
{"role_name": "李四", "text_content": "这可不管我的事儿", "emotion_name": "害怕", "strength_name": "微弱"}
]
</result>

注意事项:
保持文本顺序与逻辑一致。
不要改写原文台词或旁白内容。
所有划分结果必须完整输出在 <result> 标签内。

输入内容：
可能包含的角色列表：
<possible_characters>
{possible_characters}
</possible_characters>

可能包含的情绪列表：
<possible_emotions>
{possible_emotions}
</possible_emotions>

可能包含的情绪强弱列表：
<possible_strengths>
{possible_strengths}
</possible_strengths>

小说原文：
<novel_content>
{novel_content}
</novel_content>


"""
    return textwrap.dedent(prompt)

def get_prompt_str():
    prompt = """
    你的任务是将给定小说内容划分为角色台词和旁白，并输出包含<result>标签的结构化JSON结果。
    
    划分规则：
    
    台词识别:
    识别所有角色说话的内容，包括带引号、破折号、叹号等常见台词标记的文本。
    如果角色在给定角色列表中，使用该角色名；
    如果角色未在列表中出现，根据上下文合理归纳角色名。
    重要规则：相邻台词之间如果角色相同，可以适当合并，但是一段内容最多不超过150字。如果单段内容超过150字，请将内容拆分为多条。
    
    旁白识别:
    对叙述性、心理描写、环境描写、动作描写等非台词内容统一标记为“旁白：”。
    重要规则：相邻台词之间如果都为旁白内容，可以适当合并，但是一段内容最多不超过150字。如果单段内容超过150字，请将内容拆分为多条。
    
    情绪以及情绪强弱识别:
    根据上下文场景，识别出每条台词所对应的情绪以及情绪强度。情绪和情绪强度的内容必须来自情绪列表possible_emotions和情绪强度列表possible_strengths。
    旁白的情绪和情绪强度统一为一样的，统一为‘平静’情绪，强度为‘中等’。
    
    特殊情况处理:
    多角色对话连续出现时，每条台词对应正确角色。
    混合旁白和台词的段落可拆分为旁白和台词两条记录。
    避免重复、遗漏台词或旁白。

    输出格式:
    严格输出在 <result> 标签内的 JSON 数组。

    示例：
    <result>
    [
      {"role_name": "张三", "text_content": "你到底在干什么！", "emotion_name": "生气", "strength_name": "强烈"},
      {"role_name": "旁白", "text_content": "此时，张三愤怒站着", "emotion_name": "平静", "strength_name": "中等"},
      {"role_name": "李四", "text_content": "这可不管我的事儿", "emotion_name": "害怕", "strength_name": "微弱"}
    ]
    </result>

    输入内容：
    可能包含的角色列表：
    <possible_characters>
    {possible_characters}
    </possible_characters>

    可能包含的情绪列表：
    <possible_emotions>
    {possible_emotions}
    </possible_emotions>

    可能包含的情绪强弱列表：
    <possible_strengths>
    {possible_strengths}
    </possible_strengths>

    小说原文：
    <novel_content>
    {novel_content}
    </novel_content>
    """
    return textwrap.dedent(prompt)
















def get_auto_fix_json_prompt(json_str: str) -> str:
    prompt = f"""
    你将收到一段可能出错的 JSON 字符串（它可能是 LLM 生成的结果），其中可能存在以下问题：
        多余或缺失的逗号
        缺少引号或多余引号
        键值格式错误
        JSON 外含无关说明文字
        非法转义符
    你的任务是：
    仅输出一个严格合法、可被 json.loads 解析的 JSON。
    保持原有数据结构和内容不变（除非必须修正格式）。
    不要在 JSON 外输出任何解释、额外文字或注释。
    输出必须完整输出在 <result> </result>标签内。
    输入内容：
    <json_str>
    {json_str}
    </json_str>w
    """
    return textwrap.dedent(prompt)