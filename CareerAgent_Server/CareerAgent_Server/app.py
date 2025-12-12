from flask import Flask, request, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, ListFlowable, ListItem
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY
import os
import datetime

app = Flask(__name__)

# 1. 注册字体
FONT_PATH = 'font.ttc'
FONT_NAME = 'MyChineseFont'
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))

# 2. 颜色定义
GDUT_BLUE = colors.HexColor('#004098')

# 3. 辅助函数：页眉页脚
def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GDUT_BLUE)
    canvas.setLineWidth(1)
    canvas.line(2 * cm, A4[1] - 2.5 * cm, A4[0] - 2 * cm, A4[1] - 2.5 * cm)
    canvas.setFont(FONT_NAME, 9)
    canvas.setFillColor(colors.gray)
    canvas.drawString(2 * cm, A4[1] - 2.2 * cm, "GDUT Career Navigator | 广工职业技能领航员")
    page_num = canvas.getPageNumber()
    text = "Page %s" % page_num
    canvas.drawRightString(A4[0] - 2 * cm, 2 * cm, text)
    canvas.restoreState()

# 4. 辅助函数：列表处理 (已修复 List/Str 问题)
def text_to_list(input_data, style):
    if not input_data:
        return [Paragraph("暂无内容", style)]
    
    raw_lines = []
    if isinstance(input_data, list):
        raw_lines = [str(x) for x in input_data]
    elif isinstance(input_data, str):
        raw_lines = input_data.split('\n')
    else:
        raw_lines = [str(input_data)]

    items = []
    for line in raw_lines:
        clean_line = line.strip()
        for prefix in ['- ', '* ', '• ', '1. ', '2. ', '3. ', '4. ', '5. ']:
            if clean_line.startswith(prefix):
                clean_line = clean_line[len(prefix):]
                break
        if clean_line:
            items.append(ListItem(Paragraph(clean_line, style)))
            
    return ListFlowable(items, bulletType='bullet', start='circle', leftIndent=20)

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.json
        
        # 获取参数
        target_job = data.get('target_job', '未指定岗位')
        matched_courses = data.get('matched_courses', '')
        gap_skills = data.get('gap_skills', '')
        online_courses = data.get('online_courses', '')
        competitions = data.get('competitions', '')
        projects = data.get('projects', '')
        advice = data.get('advice', '')

        # --- 关键修改：文件保存路径 ---
        # 确保目录存在
        save_dir = os.path.join(app.root_path, 'static', 'reports')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        filename = f"Career_Plan_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(save_dir, filename)
        # ---------------------------

        # 生成 PDF 内容 (与之前保持一致)
        doc = SimpleDocTemplate(
            filepath, 
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=3*cm, bottomMargin=3*cm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontName=FONT_NAME, fontSize=24, leading=30, textColor=GDUT_BLUE, spaceAfter=20)
        h1_style = ParagraphStyle('CustomH1', parent=styles['Heading1'], fontName=FONT_NAME, fontSize=16, leading=20, textColor=GDUT_BLUE, spaceBefore=15, spaceAfter=10, borderBottomWidth=1, borderColor=colors.lightgrey)
        body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontName=FONT_NAME, fontSize=11, leading=18, alignment=TA_JUSTIFY, spaceAfter=10)
        list_text_style = ParagraphStyle('ListText', parent=body_style, leftIndent=0)

        elements = []
        
       # --- 修复 Logo 显示逻辑 ---
        logo_path = 'gdut_logo.png'
        if os.path.exists(logo_path):
            # 1. 增加高度限制 (从 1.2cm 改为 2.5cm)，给校徽留出空间
            # 2. preserveAspectRatio=True: 保持原图比例，不压扁
            # 3. width=5*cm: 限制最大宽度
            im = Image(logo_path, width=5*cm, height=2.5*cm)
            im.hAlign = 'LEFT'
            # 这一步很关键：告诉 ReportLab 保持宽高比
            im._restrictSize(5*cm, 2.5*cm)
            elements.append(im)
            elements.append(Spacer(1, 0.5*cm))
        # ------------------------

        elements.append(Paragraph(f"职业生涯规划书：{target_job}", title_style))
        elements.append(Paragraph(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d')}", body_style))
        elements.append(Spacer(1, 1*cm))

        elements.append(Paragraph("1. 技能差距分析", h1_style))
        elements.append(text_to_list(gap_skills, list_text_style))

        elements.append(Paragraph("2. 广工校内课程匹配", h1_style))
        elements.append(text_to_list(matched_courses, list_text_style))
        
        elements.append(Paragraph("3. 高含金量竞赛推荐", h1_style))
        elements.append(text_to_list(competitions, list_text_style))

        elements.append(Paragraph("4. 课外提升资源", h1_style))
        elements.append(text_to_list(online_courses, list_text_style))
        
        if projects:
            elements.append(Paragraph("<b>推荐项目：</b>", body_style))
            elements.append(text_to_list(projects, list_text_style))

        elements.append(Paragraph("5. 综合行动指南", h1_style))
        elements.append(Paragraph(str(advice).replace('\n', '<br/>'), body_style))

        doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

        # --- 关键修改：返回 JSON 链接 ---
        # 你的公网IP是 106.52.100.81，端口 5000
        download_url = f"http://106.52.100.81:5000/static/reports/{filename}"
        
        print(f"PDF生成成功: {download_url}") # 在日志里打印一下
        
        return jsonify({
            "result": f"报告已生成！请点击链接下载：\n{download_url}",
            "download_url": download_url
        })
        # ---------------------------
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)