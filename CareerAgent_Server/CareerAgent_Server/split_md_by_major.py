import os
import re

# ================= 配置区 =================
# 1. 你的源文件名称
INPUT_FILE = '大学课程结构化知识库_RAG 专用.md' 
# 2. 输出文件夹名称
OUTPUT_DIR = 'knowledge_base_by_major'
# =========================================

def split_markdown():
    # 1. 创建输出目录
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 已创建输出目录: {OUTPUT_DIR}")

    # 2. 读取源文件
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 错误：找不到文件 '{INPUT_FILE}'，请确认文件是否在当前目录下。")
        return

    # 3. 按“课程：”关键词进行切分
    # 这里的逻辑是：把大文本切成一个个小块，每一块代表一门课
    # 假设每门课都以 "课程：" 开头
    course_blocks = content.split('课程：')

    # 用于存储拆分后的数据： { "计算机科学": ["课程内容A", "课程内容B"], ... }
    major_dict = {}
    
    print(f"🔍 正在分析 {len(course_blocks)} 个文本块...")

    for block in course_blocks:
        if not block.strip():
            continue # 跳过空块

        # 补回被切掉的"课程："前缀
        full_block = "课程：" + block

        # 4. 提取专业名称
        # 目标行格式： - 所属专业：数据科学与大数据技术 (必修)
        # 我们需要提取 "数据科学与大数据技术"
        match = re.search(r'-\s*所属专业：(.*?)(?:\(|（|\s|$)', block)
        
        if match:
            major_name = match.group(1).strip()
            
            # 简单清洗：去掉可能的残留符号
            major_name = major_name.replace('*', '').strip()
            
            if major_name:
                if major_name not in major_dict:
                    major_dict[major_name] = []
                major_dict[major_name].append(full_block)
        else:
            # 如果这块内容没找到专业（可能是文件头部的介绍），暂时忽略或存入杂项
            pass

    # 5. 写入文件
    print(f"✅ 识别到 {len(major_dict)} 个专业，开始写入文件...")
    
    for major, courses in major_dict.items():
        # 构建新文件的内容
        # 加上文件头，有助于 RAG 识别
        file_content = f"# {major}专业 - 课程技能图谱\n\n"
        file_content += f"> 该文档包含 {major} 专业的课程列表、核心技能点及对应岗位。\n\n"
        file_content += "---\n\n"
        file_content += "".join(courses) # 拼接所有课程块

        # 保存文件
        # 处理文件名中可能存在的非法字符
        safe_filename = major.replace('/', '_').replace('\\', '_')
        file_path = os.path.join(OUTPUT_DIR, f"{safe_filename}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        print(f"  - 已生成: {safe_filename}.md ({len(courses)} 门课)")

    print(f"\n🎉 全部完成！请查看文件夹: {OUTPUT_DIR}")

if __name__ == '__main__':
    split_markdown()