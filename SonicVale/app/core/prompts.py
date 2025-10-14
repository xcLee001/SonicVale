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
    你的任务是将给定小说内容划分为角色和内容，并输出为结构化JSON结果。
    台词识别规则：
    1. 必须完整保留原文内容，不得遗漏、删改或省略任何字句。
    2. 提取角色对话内容喝旁白。识别所有内容，包括带引号（“”）、破折号（——）、感叹号（！）、冒号（：）等常见台词标记的文本，其余均为旁白内容。
    3. 若角色在已知角色列表<possible_characters>中，则直接使用该角色名；若不在列表中，则根据上下文合理判断角色身份。
    4. 相邻台词如属同一角色，可合并为一条，但单条台词长度不得超过150字。
    5. 若单条台词超过150字，需按语义完整性拆分为多条，每条不超过150字，并确保原文内容不缺失。
    
    旁白识别规则：
    1. 所有非台词的叙述性内容（包括心理活动、环境描写、动作描写、场景过渡等）均标记为“旁白”。
    2. 必须保留原文的所有文字内容，不得遗漏、删改或省略任何字句。
    3. 相邻的旁白内容可合并为一条，但单条长度不得超过150字。
    4. 若单条旁白超过150字，需按语义完整性拆分为多条，每条不超过150字，确保原文内容完整呈现。
    
    情绪与情绪强度识别规则：
    1. 根据上下文语境、语气及场景变化，为每条台词识别情绪和情绪强度。
    2. 情绪与强度必须严格从提供的情绪列表（possible_emotions）与强度列表（possible_strengths）中选择。
    3. “旁白”内容的情绪与强度统一为：情绪“平静”，强度“中等”。
    4. 情绪识别不得影响或改写原文内容，仅用于标注。
    
    特殊情况处理：
    1. 多角色连续对话时，确保每条台词对应正确角色，避免角色错配。
    2. 当段落中混合出现旁白与台词时，应拆分为独立记录：旁白一条、台词一条。
    3. 输出结果不得出现遗漏、重复、合并错误或原文缺失的情况。
    4. 拆分、合并及情绪标注仅为结构化目的，须保证原文内容100%完整保留。
    
    输出格式:
    严格输出为 json数组。
    
    示例：
    小说原文：
    <novel_content>
    一名靠前的灰衣少年似乎与石台上的少年颇为熟悉，他听得大伙的窃窃私语，不由得得意一笑，压低声音道：“牧哥可是被选拔出来参加过“灵路”的人，我们整个北灵境中，可就牧哥一人有名额，你们应该也知道参加“灵路”的都是些什么变态吧？当年我们这北灵境可是因为此事沸腾了好一阵的，从那里出来的人，最后基本全部都是被“五大院”给预定了的。”
    </novel_content>
    输出：
    [
      {"role_name": "旁白", "text_content": "一名靠前的灰衣少年似乎与石台上的少年颇为熟悉，他听得大伙的窃窃私语，不由得得意一笑，压低声音道", "emotion_name": "平静", "strength_name": "中等"},
      {"role_name": "灰衣少年", "text_content": "牧哥可是被选拔出来参加过“灵路”的人，我们整个北灵境中，可就牧哥一人有名额，你们应该也知道参加“灵路”的都是些什么变态吧？当年我们这北灵境可是因为此事沸腾了好一阵的，从那里出来的人，最后基本全部都是被“五大院”给预定了的。", "emotion_name": "高兴", "strength_name": "中等"}
    ]
    
    
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