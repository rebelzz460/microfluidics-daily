import requests
import datetime
from jinja2 import Template
import os

# --- 配置部分 ---
# 关键词 (微流控)
KEYWORDS = "microfluidic"
# 目标期刊 (精确匹配名称)
TARGET_JOURNALS = [
    "Nature",
    "Science",
    "Proceedings of the National Academy of Sciences",  # PNAS的全称
    "Nature Communications",  # 建议加上这个，Nature子刊，微流控内容很多
    "Science Advances"  # Science子刊
]


# --- 获取数据 (OpenAlex API) ---
def fetch_papers():
    # 获取过去7天的日期
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    # OpenAlex API 构建查询
    # 筛选：标题或摘要包含关键词，且发布日期在最近7天
    url = f"https://api.openalex.org/works?filter=default.search:{KEYWORDS},from_publication_date:{seven_days_ago}&per-page=50&sort=publication_date:desc"

    try:
        response = requests.get(url)
        data = response.json()

        filtered_papers = []

        for item in data.get('results', []):
            # 获取期刊名称
            source = item.get('primary_location', {}).get('source', {})
            if not source:
                continue
            journal_name = source.get('display_name', '')

            # 筛选：必须属于我们指定的顶级期刊
            # 使用简单的字符串包含检查，防止细微的大小写或后缀差异
            is_top_journal = any(tj.lower() in journal_name.lower() for tj in TARGET_JOURNALS)

            if is_top_journal:
                # 提取我们需要的信息
                paper = {
                    'title': item.get('title'),
                    'journal': journal_name,
                    'date': item.get('publication_date'),
                    'link': item.get('doi'),  # DOI链接通常最稳定
                    'abstract': item.get('abstract_inverted_index')  # OpenAlex摘要是倒排索引，这里简化处理，若无直接摘要可略过
                }
                filtered_papers.append(paper)

        return filtered_papers

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []


# --- 生成 HTML ---
def generate_html(papers):
    # 使用 Tailwind CSS 美化界面
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>微流控每日精选 (Top Journals)</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 text-gray-800">
        <div class="max-w-3xl mx-auto py-10 px-4">
            <header class="mb-10 text-center">
                <h1 class="text-3xl font-bold text-blue-800 mb-2">🧬 Daily Microfluidics Picks</h1>
                <p class="text-sm text-gray-500">Sources: Nature, Science, PNAS | Updated: {{ today }}</p>
            </header>

            {% if papers %}
                <div class="space-y-6">
                {% for paper in papers %}
                    <div class="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500 hover:shadow-lg transition">
                        <div class="flex justify-between items-start mb-2">
                            <span class="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-0.5 rounded">{{ paper.journal }}</span>
                            <span class="text-gray-400 text-sm">{{ paper.date }}</span>
                        </div>
                        <h2 class="text-xl font-bold mb-3">
                            <a href="{{ paper.link }}" target="_blank" class="hover:text-blue-600 hover:underline">{{ paper.title }}</a>
                        </h2>
                        <a href="{{ paper.link }}" target="_blank" class="text-sm text-blue-500 hover:text-blue-700 font-medium">Read Paper &rarr;</a>
                    </div>
                {% endfor %}
                </div>
            {% else %}
                <div class="text-center py-20 bg-white rounded-lg shadow">
                    <p class="text-gray-500">今天这些期刊没有微流控相关的新论文发布。</p>
                </div>
            {% endif %}

            <footer class="mt-10 text-center text-xs text-gray-400">
                Powered by OpenAlex API & GitHub Actions
            </footer>
        </div>
    </body>
    </html>
    """

    template = Template(html_template)
    html_content = template.render(papers=papers, today=datetime.date.today())

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


# --- 主程序 ---
if __name__ == "__main__":
    print("开始抓取论文...")
    papers = fetch_papers()
    print(f"找到 {len(papers)} 篇相关论文。")
    generate_html(papers)
    print("HTML 生成完毕。")