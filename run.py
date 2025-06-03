import requests, time, os, datetime, logging
import pytz
import json
import re
from collections import OrderedDict
from urllib.parse import quote

# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从环境变量获取配置信息
hf_token = os.environ["HF_TOKEN"]  # Hugging Face API Token
username = os.environ["USERNAME"]  # Hugging Face 用户名
space_list_str = os.environ.get("SPACE_LIST", "")  # 空间列表字符串
space_list = [space.strip() for space in space_list_str.split(",") if space.strip()]  # 解析空间列表
global_timeout_seconds = int(os.environ.get("GLOBAL_TIMEOUT_SECONDS", 1800))  # 全局超时时间
repo_id = os.environ.get("GITHUB_REPOSITORY")  # GitHub仓库ID

def validate_url(url):
    """
    验证URL是否有效
    
    Args:
        url (str): 要验证的URL
        
    Returns:
        bool: URL是否有效
    """
    # 检查URL长度（DNS标签限制）
    if len(url) > 253:
        return False
    
    # 检查域名部分的长度
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 检查域名长度
        if len(domain) > 253:
            return False
            
        # 检查每个子域名标签的长度（不能超过63个字符）
        labels = domain.split('.')
        for label in labels:
            if len(label) > 63 or len(label) == 0:
                return False
                
        # 检查是否包含有效字符
        if not re.match(r'^[a-zA-Z0-9.-]+$', domain):
            return False
            
        return True
    except Exception:
        return False

def check_space_with_browser_emulation(space_name):
    """
    模拟浏览器访问指定的Hugging Face空间
    
    Args:
        space_name (str): 空间名称
        
    Returns:
        tuple: (是否成功, 耗时秒数)
    """
    # 构建完整的空间URL
    full_space_url = f"https://{username}-{space_name}.hf.space"
    
    # 验证URL有效性
    if not validate_url(full_space_url):
        logging.error(f"❌空间{space_name}的URL无效或过长: {full_space_url}")
        return False, 0.0
    
    logging.info(f"开始模拟浏览器访问空间: {space_name}")
    start_time = time.time()
    
    try:
        # 添加更多的请求头来模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 发送HTTP GET请求检查空间状态
        response = requests.get(full_space_url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        duration = time.time() - start_time
        logging.info(f"✅空间{space_name}访问正常, 耗时: {duration:.2f}秒")
        return True, duration
        
    except requests.exceptions.ConnectionError as e:
        duration = time.time() - start_time
        if "Failed to parse" in str(e) or "label empty or too long" in str(e):
            logging.error(f"❌空间{space_name}URL解析失败 (可能是名称过长), 耗时: {duration:.2f}秒")
        else:
            logging.error(f"❌空间{space_name}连接失败, 耗时: {duration:.2f}秒: {e}")
        return False, duration
        
    except requests.exceptions.Timeout as e:
        duration = time.time() - start_time
        logging.error(f"❌空间{space_name}访问超时, 耗时: {duration:.2f}秒")
        return False, duration
        
    except requests.exceptions.HTTPError as e:
        duration = time.time() - start_time
        status_code = e.response.status_code if e.response else "未知"
        logging.error(f"❌空间{space_name}HTTP错误 (状态码: {status_code}), 耗时: {duration:.2f}秒")
        return False, duration
        
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        logging.error(f"❌空间{space_name}请求失败, 耗时: {duration:.2f}秒: {e}")
        return False, duration
        
    except Exception as e:
        duration = time.time() - start_time
        logging.exception(f"❌空间{space_name}发生未知错误, 耗时: {duration:.2f}秒: {e}")
        return False, duration

def check_space_name_validity(space_name):
    """
    检查空间名称是否有效
    
    Args:
        space_name (str): 空间名称
        
    Returns:
        bool: 名称是否有效
    """
    # 检查空间名称长度（避免URL过长）
    max_space_name_length = 50  # 设置合理的限制
    if len(space_name) > max_space_name_length:
        logging.warning(f"⚠️空间名称过长: {space_name} (长度: {len(space_name)})")
        return False
    
    # 检查用户名+空间名的组合长度
    combined_length = len(username) + 1 + len(space_name)  # +1 for the dash
    if combined_length > 63:  # DNS标签限制
        logging.warning(f"⚠️用户名和空间名组合过长: {username}-{space_name} (长度: {combined_length})")
        return False
    
    # 检查是否包含有效字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', space_name):
        logging.warning(f"⚠️空间名称包含无效字符: {space_name}")
        return False
    
    return True

def rebuild_space(space_name):
    """
    重新构建指定的Hugging Face空间
    
    Args:
        space_name (str): 空间名称
        
    Returns:
        tuple: (是否成功, 耗时秒数)
    """
    full_space_name = f"{username}/{space_name}"
    logging.info(f"开始重新构建空间: {full_space_name}")
    
    # API端点URL
    rebuild_url = f"https://huggingface.co/api/spaces/{full_space_name}/restart?factory=true"
    status_url = f"https://huggingface.co/api/spaces/{full_space_name}/runtime"
    
    # 设置请求头
    headers = {"Authorization": f"Bearer {hf_token}", "Content-Type": "application/json"}
    
    start_time = time.time()
    
    # 发送重建请求
    try:
        response = requests.post(rebuild_url, headers=headers, timeout=30)
        response.raise_for_status()
        logging.info(f"✅空间{space_name}重新构建请求发送成功")
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        logging.error(f"❌空间{space_name}重新构建请求失败, 耗时: {duration:.2f}秒: {e}")
        return False, duration
    
    # 循环检查构建状态
    attempt = 0
    max_attempts = 10  # 最大尝试次数
    
    while time.time() - start_time < 600 and attempt < max_attempts:  # 10分钟超时
        time.sleep(30)  # 等待30秒再检查
        
        try:
            # 获取空间状态
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_response.raise_for_status()
            status_data = status_response.json()
            stage = status_data.get("stage", "")
            
            logging.info(f"空间{space_name}当前状态: {stage}")
            
            # 检查构建状态
            if stage == "RUNNING":
                duration = time.time() - start_time
                logging.info(f"✅空间{space_name}已成功重新构建, 耗时: {duration:.2f}秒!")
                return True, duration
            elif "ERROR" in stage:
                duration = time.time() - start_time
                logging.error(f"❌空间{space_name}构建失败, 耗时: {duration:.2f}秒: {stage}")
                return False, duration
                
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            logging.error(f"❌空间{space_name}状态请求失败, 耗时: {duration:.2f}秒: {e}")
            return False, duration
        except Exception as e:
            duration = time.time() - start_time
            logging.exception(f"❌空间{space_name}发生未知错误, 耗时: {duration:.2f}秒: {e}")
            return False, duration
            
        attempt += 1
    
    # 超时或达到最大尝试次数
    duration = time.time() - start_time
    logging.warning(f"⚠️空间{space_name}构建状态未知 (超时或达到最大尝试次数), 耗时: {duration:.2f}秒")
    return False, duration

def generate_data_and_html(results):
    """
    生成JSON数据文件和HTML页面
    
    Args:
        results (list): 检查结果列表
        
    Returns:
        str: 格式化的时间字符串
    """
    logging.info("开始生成数据文件和HTML页面")
    
    # 确保docs目录存在
    os.makedirs("docs", exist_ok=True)
    
    # 获取当前时间（CST时区）
    current_time_utc = datetime.datetime.now(pytz.utc)
    current_time_cst = current_time_utc.astimezone(pytz.timezone('Asia/Shanghai'))
    formatted_time = current_time_cst.strftime('%Y-%m-%d %H:%M:%S')
    
    # 数据文件路径
    data_file = "docs/data.js"
    html_file = "docs/index.html"
    
    # 读取现有数据或创建新数据结构
    existing_data = OrderedDict()
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 提取JSON数据部分（去掉变量声明）
                json_start = content.find('{')
                if json_start != -1:
                    json_str = content[json_start:]
                    existing_data = json.loads(json_str)
                    # 转换为OrderedDict以保持顺序
                    existing_data = OrderedDict(existing_data)
                    logging.info(f"已加载现有数据，包含 {len(existing_data)} 条记录")
        except Exception as e:
            logging.warning(f"读取现有数据文件失败: {e}")
            existing_data = OrderedDict()
    
    # 添加当前检查结果
    current_results = {}
    for r in results:
        # 标记无效的空间名称
        space_name = r['space']
        if r.get('invalid_name', False):
            space_name += " (名称无效)"
            
        if r["result"] is not None:
            current_results[space_name] = {
                "status": r['result'], 
                "duration": f"{r['duration']:.2f}秒",
                "error_type": r.get('error_type', '')
            }
        else:
            current_results[space_name] = {
                "status": False, 
                "duration": f"{r['duration']:.2f}秒",
                "error_type": r.get('error_type', 'unknown')
            }
    
    existing_data[formatted_time] = current_results
    
    # 保持最新的50条记录
    if len(existing_data) > 50:
        # 移除最旧的记录
        keys_to_remove = list(existing_data.keys())[:-50]
        for key in keys_to_remove:
            del existing_data[key]
    
    # 生成JavaScript数据文件
    js_content = f"const spaceStatusData = {json.dumps(existing_data, ensure_ascii=False, indent=2)};"
    
    with open(data_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    logging.info(f"数据文件已生成: {data_file}")
    
    # 生成HTML文件（如果不存在）
    if not os.path.exists(html_file):
        html_content = generate_html_template()
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"HTML文件已生成: {html_file}")
    else:
        logging.info(f"HTML文件已存在，无需重新生成: {html_file}")
    
    return formatted_time

def generate_html_template():
    """
    生成HTML模板内容
    
    Returns:
        str: HTML模板字符串
    """
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hugging Face空间状态</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            background-color: #f5f5f5;
        }}
        
        .container {{
            width: 100%;
            max-width: 900px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            min-width: 150px;
            margin: 5px;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        
        .log-entry {{ 
            margin-bottom: 15px;
            border: 1px solid #e0e0e0;
            padding: 20px;
            border-radius: 10px;
            background: #fafafa;
            transition: all 0.3s ease;
        }}
        
        .log-entry:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        .timestamp {{ 
            font-weight: bold; 
            font-size: 1.1em;
            color: #555;
            margin-bottom: 10px;
            display: block;
        }}
        
        .space-result {{
            display: inline-block;
            margin: 5px 10px 5px 0;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            position: relative;
        }}
        
        .success {{ 
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        
        .failure {{ 
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        
        .invalid-name {{
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }}
        
        .error-tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s;
            z-index: 1000;
        }}
        
        .space-result:hover .error-tooltip {{
            opacity: 1;
            visibility: visible;
        }}
        
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #666;
            font-size: 14px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        
        .footer a {{
            color: #007BFF;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            .stats {{
                flex-direction: column;
            }}
            
            .stat-card {{
                margin: 10px 0;
            }}
            
            .log-entry {{
                padding: 15px;
                font-size: 14px;
            }}
            
            .footer {{
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Hugging Face空间状态监控</h1>
        
        <div class="stats">
            <div class="stat-card">
                <span class="stat-number" id="total-checks">-</span>
                <div>总检查次数</div>
            </div>
            <div class="stat-card">
                <span class="stat-number" id="success-rate">-</span>
                <div>成功率</div>
            </div>
            <div class="stat-card">
                <span class="stat-number" id="last-update">-</span>
                <div>最后更新</div>
            </div>
        </div>
        
        <div id="content" class="loading">
            正在加载数据...
        </div>
    </div>

    <script src="data.js"></script>
    <script>
        // 获取错误类型的显示文本
        function getErrorTypeText(errorType) {{
            const errorTypes = {{
                'url_invalid': 'URL无效',
                'name_too_long': '名称过长',
                'connection_error': '连接失败',
                'timeout': '访问超时',
                'http_error': 'HTTP错误',
                'parse_error': 'URL解析失败',
                'unknown': '未知错误'
            }};
            return errorTypes[errorType] || '未知错误';
        }}

        // 加载并显示数据
        function loadData() {{
            if (typeof spaceStatusData === 'undefined') {{
                document.getElementById('content').innerHTML = 
                    '<div class="loading">❌ 数据加载失败，请稍后刷新页面重试</div>';
                return;
            }}

            const contentDiv = document.getElementById('content');
            const timestamps = Object.keys(spaceStatusData).reverse(); // 最新的在前
            
            if (timestamps.length === 0) {{
                contentDiv.innerHTML = '<div class="loading">📋 暂无监控数据</div>';
                return;
            }}

            // 计算统计信息
            let totalChecks = 0;
            let successCount = 0;
            
            timestamps.forEach(timestamp => {{
                const results = spaceStatusData[timestamp];
                Object.values(results).forEach(result => {{
                    totalChecks++;
                    if (result.status) successCount++;
                }});
            }});
            
            const successRate = totalChecks > 0 ? Math.round((successCount / totalChecks) * 100) : 0;
            const lastUpdate = timestamps[0].split(' ')[1];
            
            // 更新统计卡片
            document.getElementById('total-checks').textContent = totalChecks;
            document.getElementById('success-rate').textContent = successRate + '%';
            document.getElementById('last-update').textContent = lastUpdate;

            // 生成日志条目HTML
            let html = '';
            timestamps.forEach(timestamp => {{
                const results = spaceStatusData[timestamp];
                html += `<div class="log-entry">`;
                html += `<span class="timestamp">🕒 ${{timestamp}}</span>`;
                
                Object.entries(results).forEach(([space, result]) => {{
                    let statusClass = result.status ? 'success' : 'failure';
                    const statusIcon = result.status ? '✅' : '❌';
                    
                    // 检查是否是无效名称
                    if (space.includes('(名称无效)')) {{
                        statusClass = 'invalid-name';
                    }}
                    
                    html += `<div class="space-result ${{statusClass}}">`;
                    html += `${{statusIcon}} ${{space}}: ${{result.duration}}`;
                    
                    // 添加错误提示
                    if (!result.status && result.error_type) {{
                        html += `<div class="error-tooltip">${{getErrorTypeText(result.error_type)}}</div>`;
                    }}
                    
                    html += `</div>`;
                }});
                
                html += '</div>';
            }});
            
            contentDiv.innerHTML = html;
        }}

        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>"""

# 主程序执行部分
if __name__ == "__main__":
    logging.info("开始执行Hugging Face空间监控脚本")
    
    start_time = time.time()
    results = []
    
    # 遍历每个空间进行检查
    for space in space_list:
        # 检查全局超时
        if time.time() - start_time > global_timeout_seconds:
            logging.warning(f"⚠️全局超时（{global_timeout_seconds}秒），剩余空间未处理")
            break
        
        logging.info(f"正在处理空间: {space}")
        
        # 首先检查空间名称有效性
        if not check_space_name_validity(space):
            results.append({
                "space": space,
                "result": False,
                "duration": 0.0,
                "invalid_name": True,
                "error_type": "name_too_long"
            })
            continue
        
        # 先检查空间状态
        status, duration = check_space_with_browser_emulation(space)
        
        if not status:
            # 如果空间无法访问，尝试重建
            logging.info(f"空间 {space} 访问失败，尝试重建...")
            rebuild_result, rebuild_duration = rebuild_space(space)
            results.append({
                "space": space, 
                "result": rebuild_result, 
                "duration": rebuild_duration,
                "error_type": "connection_error" if not rebuild_result else ""
            })
        else:
            # 空间正常运行
            results.append({
                "space": space, 
                "result": status, 
                "duration": duration
            })
    
    # 生成报告
    formatted_time = generate_data_and_html(results)
    logging.info(f"监控完成，时间: {formatted_time}")
    
    # 设置GitHub Actions输出
    exit_code = 1 if any(r['result'] is False for r in results) else 0
    
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            print(f"exit_code={exit_code}", file=f)
    
    # 输出最终结果
    success_count = sum(1 for r in results if r['result'] is True)
    total_count = len(results)
    invalid_count = sum(1 for r in results if r.get('invalid_name', False))
    
    logging.info(f"监控结果: {success_count}/{total_count} 个空间运行正常")
    if invalid_count > 0:
        logging.warning(f"发现 {invalid_count} 个无效的空间名称")
    
    if exit_code != 0:
        logging.error("存在失败的空间，脚本以错误码退出")
        exit(1)
    else:
        logging.info("所有空间运行正常，脚本成功完成")
        exit(0)