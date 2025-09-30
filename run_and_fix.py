import json, re, subprocess, requests, sys
from pathlib import Path

# ========== 用户只改这里 ==========
ENTRY_FILE = Path("C:/Users/leo/Desktop/za/work/2025/mini mini/ai/2.0/main.py")
# ENTRY_FILE   = Path("C:\Users\leo\Desktop\za\work\2025\mini mini\ai\2.0\main.py")   # 入口文件（相对或绝对）
# SOURCE_DIR   = Path("C:\Users\leo\Desktop\za\work\2025\mini mini\ai\2.0")           # 要扫描的源码目录
SOURCE_DIR = Path("C:/Users/leo/Desktop/za/work/2025/mini mini/ai/2.0")

PIP_FILE     = SOURCE_DIR / "requirements.txt"

REQ_FILE     = Path("requirements.md")
MODEL        = "qwen2.5-coder:7b"
OLLAMA_URL   = "http://localhost:11434/api/chat"
MAX_ROUND    = 5
# 检查用模型（可任意切换）
CHECK_MODEL = "deepseek-r1:latest"
CHECK_URL   = "http://localhost:11434/api/chat"   # 同一端口，不同模型
# ==================================

def read(f: Path) -> str: return f.read_text(encoding="utf8")
def write(f: Path, s: str): f.write_text(s, encoding="utf8")

req = read(REQ_FILE) if REQ_FILE.exists() else ""

# ① 加载整棵源码树（相对路径 → 内容）
# code_tree = {str(p.relative_to(SOURCE_DIR)): read(p)
#              for p in SOURCE_DIR.rglob("*.py")}


# ① 加载整棵源码树 + requirements.txt
code_tree = {str(p.relative_to(SOURCE_DIR)): read(p)
             for p in SOURCE_DIR.rglob("*.py")}
if PIP_FILE.exists():
    code_tree["requirements.txt"] = read(PIP_FILE)


# ② 运行入口文件
# def run():
#     r = subprocess.run([sys.executable, str(ENTRY_FILE)],
#                        capture_output=True, text=True, cwd=SOURCE_DIR.parent)
#     return r.returncode == 0, r.stdout + r.stderr



# def run():
#     """1. 安装依赖 2. 运行入口文件"""
#     if PIP_FILE.exists():
#         print("📦 安装依赖...", PIP_FILE)
#         subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(PIP_FILE)],
#                               cwd=SOURCE_DIR)
#     r = subprocess.run([sys.executable, str(ENTRY_FILE)],
#                        capture_output=True, text=True, cwd=SOURCE_DIR.parent)
#     return r.returncode == 0, r.stdout + r.stderr



def run():
    if PIP_FILE.exists():
        print("📦 安装依赖...", PIP_FILE)
        # 用“外部” pip，而不是 python -m pip
        subprocess.check_call(["pip", "install", "-r", str(PIP_FILE)],
                              cwd=SOURCE_DIR)
    r = subprocess.run([sys.executable, str(ENTRY_FILE)],
                       capture_output=True, text=True, cwd=SOURCE_DIR.parent)
    return r.returncode == 0, r.stdout + r.stderr









# ③ AI 需求校验
# def check_output(stdout: str):
#     sys_msg = ("你是需求检查官，只回答 True 或 False，再给出 1 句话原因。"
#                "用户需求如下：\n" + req)
#     payload = {"model": MODEL, "messages": [
#         {"role": "system", "content": sys_msg},
#         {"role": "user", "content": f"程序实际输出：\n{stdout}"}
#     ], "stream": False}
#     resp = requests.post(OLLAMA_URL, json=payload, timeout=60).json()["message"]["content"].strip()
#     if resp.startswith("True"):
#         return True, ""
#     return False, resp
# def check_output(stdout: str):
#     """
#     纯 AI 判断：需求 + 源码 + 输出 → True/False
#     """
#     sys_msg = (
#         "你是需求检查官。必须严格对照用户需求检查下列两项："
#         "1) 输出结果必须完全正确；2) 实现过程必须完全符合需求（如禁用+、使用位运算等）。"
#         "先简要分析，最后一行只写 True 或 False，不要写代码。"
#     )
#     user = (
#         f"用户需求：\n{req}\n\n"
#         f"当前源码：\n{json.dumps(code_tree, ensure_ascii=False)}\n\n"
#         f"实际输出：\n{stdout}"
#     )
#     payload = {"model": MODEL, "messages": [
#         {"role": "system", "content": sys_msg},
#         {"role": "user", "content": user}
#     ], "stream": False}
#     resp = requests.post(OLLAMA_URL, json=payload, timeout=60).json()["message"]["content"].strip()
#     # 取最后一行 True/False
#     last_line = resp.splitlines()[-1].strip()
#     if last_line == "True":
#         return True, ""
#     return False, resp

def check_output(stdout: str):
    """
    零硬规则：把需求原文 + 源码 + 输出
    交给 deepseek-r1:latest 判断 True/False
    """
    sys_msg = (
        "你是资深需求检查官，必须严格对照「用户需求」全文逐条检查："
        # "输出正确性、实现过程、禁用运算符、指定算法等。"
        "请严格按下面格式输出内容，千万不要多写无关内容："
        "先简要逐条回答，最后一行只写 True 或 False。若有任意一条不正确则判 False。全对才判 True。"
        "千万要记住最后一行只写 True 或 False。若有任意一条不正确则判 False。全对才判 True。"
    )
    user = (
        f"用户需求（全文）：\n{req}\n\n"
        f"当前源码：\n{json.dumps(code_tree, ensure_ascii=False)}\n\n"
        f"实际输出：\n{stdout}"
    )
    payload = {"model": CHECK_MODEL, "messages": [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user}
    ], "stream": False}
    resp = requests.post(CHECK_URL, json=payload, timeout=600).json()["message"]["content"].strip()

    last_line = resp.splitlines()[-1].strip()
    if last_line == "True":
        return True, ""
    return False, resp
    




# ④ 合并判断：异常 OR 需求不符 → 都算失败
def run_and_check():
    ok, log = run()
    if not ok:
        return False, log                       # 有异常
    fine, reason = check_output(log)          # log 即 stdout
    if not fine:
        return False, f"输出不符合需求：{reason}\n---- 实际输出 ----\n{log}"
    return True, log



# def fix(log: str):
#     """去 Markdown 块 + 自动缩进修正，整块写回入口文件"""
#     sys_msg = (
#         "你是资深 Python 开发，必须同时满足："
#         "1) 用户需求；2) 运行无异常且输出正确。"
#         "请返回 **纯代码文本**（不要 Markdown  fenced code，不要解释）。"
#         "如果需新增第三方库，请在返回的 write 指令里同时写出新的 requirements.txt 内容。"
#     )
#     user = (
#         f"需求：\n{req}\n\n"
#         f"当前报错/输出：\n{log}\n\n"
#         f"当前 main.py 源码：\n{code_tree.get('main.py', '')}"
#     )
#     payload = {"model": MODEL, "messages": [
#         {"role": "system", "content": sys_msg},
#         {"role": "user", "content": user}
#     ], "stream": False}
#     try:
#         out = requests.post(OLLAMA_URL, json=payload, timeout=300).json()["message"]["content"]
#     except Exception as e:
#         print("⚠️  调用 Ollama 失败:", e)
#         return

#     # 去掉 Markdown 围栏 + 自动剥离公共缩进
#     clean = re.sub(r"```python|```", "", out)  # 删除 ``` 语言标记
#     clean = re.sub(r"^\s+|\s+$", "", clean)    # 去首尾空行
#     # 如果有统一缩进，全部左移
#     lines = clean.splitlines(keepends=True)
#     if lines:
#         common_indent = min(len(re.match(r"\s*", ln).group(0)) for ln in lines if ln.strip())
#         clean = "".join(ln[common_indent:] for ln in lines)

#     write(ENTRY_FILE, clean)
#     print("📝 已 clean 覆盖 →", ENTRY_FILE)
#     code_tree["main.py"] = read(ENTRY_FILE)


#     # 如果 AI 改了 requirements.txt，同步落盘
#     if "requirements.txt" in code_tree:
#         write(PIP_FILE, code_tree["requirements.txt"])





def fix(log: str):
    """
    AI 可：1) 新建/覆盖任意文件；2) 删除文件/空目录；3) 改名。
    指令格式（大小写不敏感）：
        write <相对路径>
        <文件内容...>
        <空行或 EOF 结束>
        delete <相对路径>
    相对路径不得跳出 SOURCE_DIR。
    返回内容只接受 UTF-8 文本文件；二进制忽略。
    禁止删除 main.py（不区分大小写）。
    """
    import os, shutil

    sys_msg = (
        "你是全栈工程师，可新建、覆盖、删除项目内任意文件。但是非必要不新建，非必要不删除。"
        "必须同时满足：1) 用户需求；2) 运行无异常且输出正确。3) 指标达标。\n"
        "通用强制流程（不得跳过):\n" + open("universal_evr.txt", encoding="utf-8").read() +
        "非必要不新建文件，非必要不删除文件"
        "请严格按下面格式输出指令和内容，千万不要多写无关内容："
        "返回格式：每行一个指令，大小写不敏感："
        "write <相对路径>  # 下一行开始文件内容，空行或 EOF 结束"
        "delete <相对路径>  # 可删文件或空目录"
        "不要 Markdown，不要解释。"
    )
    # user = f"需求：\n{req}\n\n报错/输出：\n{log}\n\n当前树：\n{json.dumps(code_tree, ensure_ascii=False)}"
    user = (
    f"需求：\n{req}\n\n"
    f"判分 AI 的完整意见（含逐条分析与期望输出）：\n{log}\n\n"
    f"当前整个源码树：\n{json.dumps(code_tree, ensure_ascii=False)}"
)

    payload = {"model": MODEL, "messages": [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": user}
    ], "stream": False}
    out = requests.post(OLLAMA_URL, json=payload, timeout=300).json()["message"]["content"]

    lines = [ln.rstrip("\r") for ln in out.splitlines()]   # 统一去 \r
    i = 0
    while i < len(lines):
        line = lines[i].lower()
        # --------- write ---------
        if line.startswith("write "):
            raw_path = lines[i][6:].strip()
            target = (SOURCE_DIR / raw_path).resolve()
            # 防穿越
            if not str(target).startswith(str(SOURCE_DIR)):
                print("⚠️  路径穿越，已忽略：", raw_path)
                i += 1
                continue
            content_lines = []
            i += 1
            while i < len(lines) and lines[i] != "":   # 空行结束
                content_lines.append(lines[i])
                i += 1
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("\n".join(content_lines), encoding="utf-8")
            print("📝 写入 →", target.relative_to(SOURCE_DIR))

        # --------- delete ---------
        elif line.startswith("delete "):
            raw_path = lines[i][7:].strip()
            target = (SOURCE_DIR / raw_path).resolve()

            # 🔒 禁止删除 main.py
            if target.name.lower() == "main.py":
                print("🚫 禁止删除主程序 main.py，已忽略指令")
                i += 1
                continue

            if not str(target).startswith(str(SOURCE_DIR)):
                print("⚠️  路径穿越，已忽略：", raw_path)
                i += 1
                continue

            if target.is_file():
                target.unlink()
                print("🗑  删除文件 →", target.relative_to(SOURCE_DIR))
            elif target.is_dir() and not any(target.iterdir()):
                target.rmdir()
                print("🗑  删除空目录 →", target.relative_to(SOURCE_DIR))
            else:
                print("⚠️  目录非空，跳过 →", target.relative_to(SOURCE_DIR))
        else:
            i += 1

    # 刷新内存：只保留文本文件
    code_tree.clear()
    for p in SOURCE_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml"}:
            try:
                code_tree[str(p.relative_to(SOURCE_DIR))] = p.read_text(encoding="utf-8")
            except Exception as e:
                print("⚠️  读文本失败，跳过：", p, e)




# ⑥ 主循环
def main():
    for i in range(1, MAX_ROUND + 1):
        print(f"\n===== 第 {i} 次运行 =====")
        ok, log = run_and_check()
        print(log)
        if ok:
            print("✅ 运行成功且符合需求")
            break
        print("❌ 失败，正在修复...")
        fix(log)
    else:
        print("⚠️  已达最大迭代，请检查需求或日志")

if __name__ == "__main__":
    main()