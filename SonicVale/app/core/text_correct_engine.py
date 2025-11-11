import re
import json
import difflib
from typing import List, Dict, Tuple, Optional


class TextCorrectorFinal:
    def clean_text(self, text: str) -> str:
        """清理文本，移除所有换行符、全角空格和引号，并将多个连续空格替换为单个空格。"""
        text = re.sub(r'[\n\r\u3000]', '', text)
        text = re.sub(r'["“”「」『』]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _looks_like_abbreviation(self, sentence_with_dot: str) -> bool:
        """
        判断当前这一个 '.' 更像是缩写的一部分，而不是句子结束。
        sentence_with_dot: 当前已经累积的句子（包含这个点）
        """
        s = sentence_with_dot.rstrip()
        # 找到以 . 结尾的最后一个 token（字母/数字/点）
        m = re.search(r'([A-Za-z0-9\.]+)\.$', s)
        if not m:
            return False

        token = m.group(1)  # 不包含最后这个点，但可能包含内部的 .

        # 1) 小写长度很短的缩写，例如 Mr. Dr. etc.
        #    这里简单认为：1~4 个字母，首字母大写
        if re.fullmatch(r'[A-Za-z]{1,4}', token) and token[0].isupper():
            return True

        # 2) 多点缩写：U.S.A / F.B.I 这种（至少 3 个字母、2 个点）
        #    U.S.A -> token 为 'U.S.A'
        if re.fullmatch(r'[A-Za-z](?:\.[A-Za-z]){2,}', token):
            return True

        # 3) 你如果有特殊缩写，可以在这里硬编码
        # if token in {"etc", "e.g", "i.e"}:
        #     return True

        return False

    def split_sentences(self, text: str) -> List[str]:
        """按照标点符号进行细粒度分句，同时尽量保护英文缩写和数字。
        保留换行作为候选分句符。如果产生了“只有标点/引号”的句子，则直接丢弃。
        """
        # 规范化换行：把 \r\n 和 \r 统一为 \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # 替换全角空格为普通空格，保留换行
        text = text.replace('\u3000', ' ').strip()

        # 分割：中文标点、特殊点号、或换行
        sentences = re.split(r'([。！？!?：；]|(?<!\d)\.(?!\d)|\n+)', text)

        result = []
        current_sentence = ""

        for part in sentences:
            if not part:
                continue

            current_sentence += part

            # 遇到句子结束符号时：
            if re.fullmatch(r'[。！？!?：；]', part) or part == '.' or re.fullmatch(r'\n+', part):
                if part == '.':
                    # 缩写保护
                    if self._looks_like_abbreviation(current_sentence):
                        continue

                # 清理末尾换行
                sent = current_sentence.strip()
                if re.fullmatch(r'\n+', part):
                    sent = re.sub(r'\n+$', '', sent).strip()

                # **关键：如果只有标点或引号，则直接跳过**
                if sent and not re.fullmatch(r'^[\W_]+$', sent):
                    result.append(sent)

                current_sentence = ""

        # 末尾残余
        tail = current_sentence.strip()
        if tail and not re.fullmatch(r'^[\W_]+$', tail):
            result.append(tail)

        return result

    def find_best_sentence_match(self, ai_sentence: str, original_sentences: List[str],
                                 start_index: int = 0, threshold: float = 0.6) -> Tuple[Optional[int], float]:
        """在原文句子列表中找到与AI句子最匹配的单个句子。"""
        # 预处理
        processed_ai_sentence = self.clean_text(ai_sentence)
        if not processed_ai_sentence:
            return None, 0

        best_match_index = None
        best_similarity = 0
        search_window = 20  # 向前看20个句子

        for i in range(start_index, min(start_index + search_window, len(original_sentences))):
            original_sentence = original_sentences[i]
            processed_original_sentence = self.clean_text(original_sentence)

            if not processed_original_sentence:
                continue

            matcher = difflib.SequenceMatcher(None, processed_ai_sentence, processed_original_sentence)
            similarity = matcher.ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_index = i

        if best_similarity < threshold:
            return None, best_similarity

        return best_match_index, best_similarity

    def correct_ai_text(self, original_text: str, ai_data: List[Dict]) -> List[Dict]:
        """使用分句匹配 + difflib 的方式校正AI文本。"""
        original_sentences = self.split_sentences(original_text)

        corrected_data = []
        used_original_indices = set()
        current_original_index = 0

        for ai_item in ai_data:
            ai_text = ai_item.get('text_content', '')
            ai_sentences = self.split_sentences(ai_text)

            corrected_sentences_for_item = []

            print(f"\n处理角色: {ai_item['role_name']} (AI原文: '{ai_text[:50]}')")

            for ai_sentence in ai_sentences:
                match_index, similarity = self.find_best_sentence_match(
                    ai_sentence, original_sentences, current_original_index
                )

                if match_index is not None:
                    original_match = original_sentences[match_index]
                    corrected_sentences_for_item.append(original_match)
                    used_original_indices.add(match_index)
                    current_original_index = match_index + 1
                    print(f"匹配成功 (相似度: {similarity:.2f}): AI='{ai_sentence}' -> 原文='{original_match}'")
                else:
                    corrected_sentences_for_item.append(ai_sentence)
                    print(f"匹配失败 (最高相似度: {similarity:.2f})，保留AI原句: '{ai_sentence}'")

            # 最终清理
            corrected_text = self.clean_text(" ".join(corrected_sentences_for_item))

            if corrected_text:
                corrected_item = ai_item.copy()
                corrected_item['text_content'] = corrected_text
                corrected_data.append(corrected_item)

        # 处理遗漏的原文句子
        missing_indices = sorted(list(set(range(len(original_sentences))) - used_original_indices))
        if missing_indices:
            print(f"\n发现 {len(missing_indices)} 个遗漏句子，正在插入...")

            final_data = []
            original_cursor = 0
            corrected_cursor = 0

            while original_cursor < len(original_sentences):
                if original_cursor in missing_indices:
                    # 插入遗漏的句子
                    missing_sentence = self.clean_text(original_sentences[original_cursor])
                    if missing_sentence:
                        print(f"  -> 插入遗漏句子: '{missing_sentence}'")
                        final_data.append({
                            'role_name': '旁白',
                            'text_content': missing_sentence,
                            'emotion_name': '',
                            'strength_name': ''
                        })
                    original_cursor += 1
                else:
                    if corrected_cursor < len(corrected_data):
                        final_data.append(corrected_data[corrected_cursor])
                        num_sentences_in_item = len(
                            self.split_sentences(corrected_data[corrected_cursor]['text_content']))
                        original_cursor += num_sentences_in_item
                        corrected_cursor += 1
                    else:
                        original_cursor += 1

            return final_data

        return corrected_data


def read_files():
    """读取原文和AI输出文件"""
    try:
        with open('原文3.txt', 'r', encoding='utf-8') as f:
            original_text = f.read()
        with open('AI输出的包含错误的文本3.json', 'r', encoding='utf-8') as f:
            ai_data = json.load(f)
        return original_text, ai_data
    except FileNotFoundError as e:
        print(f"文件读取错误: {e}")
        return None, None
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return None, None


def save_corrected_data(corrected_data: List[Dict]):
    """保存校正后的数据"""
    try:
        with open('校正后的文本_final.json', 'w', encoding='utf-8') as f:
            json.dump(corrected_data, f, ensure_ascii=False, indent=4)
        print("\n校正结果已保存到: 校正后的文本_final.json")
    except Exception as e:
        print(f"保存文件时出错: {e}")


def main():
    original_text, ai_data = read_files()
    if original_text is None or ai_data is None:
        return

    print("文件读取成功！开始校正...")

    corrector = TextCorrectorFinal()
    corrected_data = corrector.correct_ai_text(original_text, ai_data)

    save_corrected_data(corrected_data)

    print("\n校正完成！")


if __name__ == "__main__":
    main()
