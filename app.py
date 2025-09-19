import streamlit as st
import pandas as pd
import re
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# 设置页面标题和布局
st.set_page_config(page_title="时间序列数据可视化", layout="wide")
st.title("时间序列数据可视化")

# 文件上传组件
uploaded_file = st.file_uploader("上传数据文件", type=['txt'])

def parse_custom_datetime(time_str):
    """
    解析自定义格式的时间字符串为datetime对象
    支持两种格式: 
    1. YYYY-MM-DD_HH:MM:SS:sss (带毫秒)
    2. YYYY-MM-DD_HH:MM:SS (不带毫秒)
    """
    # print(f"Parsing time string: {time_str}")
    try:
        # 分割日期和时间部分
        parts = time_str.split('_')
        if len(parts) != 2:
            return None
            
        date_part = parts[0]
        time_parts = parts[1].split(':')
        
        # 处理时间部分
        if len(time_parts) == 4:  # 带毫秒的格式
            # 组合成标准格式
            standard_format = f"{date_part} {time_parts[0]}:{time_parts[1]}:{time_parts[2]}.{time_parts[3]}"
            return datetime.strptime(standard_format, "%Y-%m-%d %H:%M:%S.%f")
        elif len(time_parts) == 3:  # 不带毫秒的格式
            # 组合成标准格式
            standard_format = f"{date_part} {time_parts[0]}:{time_parts[1]}:{time_parts[2]}"
            return datetime.strptime(standard_format, "%Y-%m-%d %H:%M:%S")
        else:
            return None
    except Exception as e:
        st.error(f"解析时间字符串 '{time_str}' 时出错: {str(e)}")
        return None

def is_format1(line):
    # 验证文件格式是否正确
    expected_header = "X axis,Y axis,Z axis,GNSS Accuracy,Speed,Azimuth,TIME".strip()
    line = line.lstrip('\ufeff')  # 移除BOM标记
    line_items = line.strip().split(',')
    
    matche_count = 0
    for expected, actual in zip(expected_header.strip().split(','), line_items):
        if expected.strip() == actual.strip():
            matche_count += 1
        else:
            a = int(actual[0:1])
            b = int(actual[1:2])
            print(f"first char: {a}, second char: {b}")
            print(f"不匹配的列: 期望 '{expected.strip()}'，实际- '{actual.strip()}'")

    print(f"匹配的列数: {matche_count} / {len(expected_header.strip().split(','))}")
    if matche_count != len(expected_header.strip().split(',')):
        print(f"警告: 文件头不匹配。期望: {expected_header}，实际: {line}")
        return False
    return True

def process_data(content):
    """
    处理数据内容，提取时间戳和数值
    """
    
    # 初始化列表存储数据
    timestamps = []
    values1 = []    # X axis
    values2 = []    # Y axis
    values3 = []    # Z axis
    values4 = []    # Speed
    raw_lines = []
    first_line = True
    format1 = False
    
    # 处理每一行数据
    for line in content.splitlines():
        
        if first_line:
            format1 = is_format1(line)
            first_line = False
            continue
        line_num = content.splitlines().index(line) + 1  # 获取当前行号，便于调试
        # print(f"Processing line {line_num}: {line}")
        # print(f"Detected format1: {format1}, first_line: {first_line}")
        if format1 is True:
            first_line = False
            # 分割行数据
            parts = line.split(',')
            # print(f"Split into parts: {parts}, length: {len(parts)}")
            # 验证数据列数
            if len(parts) != 7:
                print(f"警告: 第{line_num}行数据列数不正确(应有7列，实际{len(parts)}列)，跳过该行")
                continue
            
            try:
                # 提取所需列数据
                val1 = int(parts[0])
                val2 = int(parts[1])
                val3 = int(parts[2])
                val4 = float(parts[4])  # Speed
                
                # 处理时间戳
                time_str = parts[6]
                if len(time_str) == 14:  # 验证时间戳长度
                    # 格式化时间字符串为更易读的格式: YYYY-MM-DD_HH:MM:SS
                    formatted_time = (f"{time_str[0:4]}-{time_str[4:6]}-{time_str[6:8]}_"
                                        f"{time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}")
                    #print(f"Formatted time: {formatted_time}")
                else:
                    print(f"警告: 第{line_num}行时间格式不正确: {time_str}")
                    formatted_time = time_str  # 仍保存原始值
                    raise ValueError("时间格式不正确")

            except ValueError as e:
                print(f"错误: 第{line_num}行数据格式不正确: {e}")
            
        else:
            # 定义正则表达式模式
            # 使用非捕获组(?:...)来匹配时间格式中毫秒部分， 因为有可能没有毫秒
            pattern = r"\[(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}(?::\d{3})?)\]\s*(-?\d+),(-?\d+),(-?\d+)"
            match = re.search(pattern, line)

            if match:
                formatted_time = match.group(1)
                val1 = int(match.group(2))
                val2 = int(match.group(3))
                val3 = int(match.group(4))
                val4 = 0.0  # Speed 列在这种格式中不存在，设为0
            else:
                print(f"警告: 行不匹配预期格式，跳过该行: {line}")
                continue  # 跳过不匹配的行

        # print(f"Extracted - Time: {formatted_time}, Values: {val1}, {val2}, {val3}")
        # 转换时间字符串为 datetime 对象
        dt = parse_custom_datetime(formatted_time)
        if dt:
            timestamps.append(dt)
            values1.append(val1)
            values2.append(val2)
            values3.append(val3)
            values4.append(val4)
            raw_lines.append(line)
    
    print(f"Total valid entries extracted: {len(timestamps)}")

    return timestamps, values1, values2, values3, values4, raw_lines


def create_interactive_plot(timestamps, values1, values2, values3, values4):
    """
    创建交互式图表
    """
    # 创建单一坐标系，左轴为三轴，右轴为速度
    fig = go.Figure()
    # X轴
    fig.add_trace(go.Scatter(x=timestamps, y=values1, name='X axis', line=dict(color='blue'), yaxis='y'))
    # Y轴
    fig.add_trace(go.Scatter(x=timestamps, y=values2, name='Y axis', line=dict(color='red'), yaxis='y'))
    # Z轴
    fig.add_trace(go.Scatter(x=timestamps, y=values3, name='Z axis', line=dict(color='green'), yaxis='y'))
    # Speed 右轴
    fig.add_trace(go.Scatter(x=timestamps, y=values4, name='Speed', line=dict(color='orange'), yaxis='y2'))

    fig.update_layout(
        height=800,
        title_text="时间序列数据可视化",
        showlegend=True,
        hovermode='x unified',
        xaxis=dict(title="时间"),
        yaxis=dict(title="三轴数值", side="left"),
        yaxis2=dict(title="速度", overlaying="y", side="right", showgrid=False)
    )
    return fig

if uploaded_file is not None:
    print(f"Uploaded file: {uploaded_file.name}")
    uploaded_file.seek(0)  # 确保文件指针在开头

    content = uploaded_file.read().decode('utf-8')
    # 处理数据
    timestamps, X, Y, Z, Speed, raw_lines = process_data(content)
    
    if timestamps:
        # 创建 DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'X axis': X,
            'Y axis': Y,
            'Z axis': Z,
            'Speed': Speed
        })
        
        st.success(f"成功加载 {len(df)} 条数据")
        
        # 显示数据统计
        st.subheader('数据统计')
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("X axis 平均值", f"{df['X axis'].mean():.2f}")
            st.metric("X axis 最小值", df['X axis'].min())
            st.metric("X axis 最大值", df['X axis'].max())

        with col2:
            st.metric("Y axis 平均值", f"{df['Y axis'].mean():.2f}")
            st.metric("Y axis 最小值", df['Y axis'].min())
            st.metric("Y axis 最大值", df['Y axis'].max())
        
        with col3:
            st.metric("Z axis 平均值", f"{df['Z axis'].mean():.2f}")
            st.metric("Z axis 最小值", df['Z axis'].min())
            st.metric("Z axis 最大值", df['Z axis'].max())
        
        with col4:
            st.metric("Speed", f"{df['Speed'].mean():.2f}")
            st.metric("Speed 最小值", df['Speed'].min())
            st.metric("Speed 最大值", df['Speed'].max())

        # 显示时间范围
        st.write(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        
        # 计算时间差
        time_diff = df['timestamp'].max() - df['timestamp'].min()
        total_seconds = time_diff.total_seconds()
        st.write(f"时间跨度: {total_seconds:.3f} 秒 ({total_seconds*1000:.3f} 毫秒)")
        
        # 显示原始数据
        if st.checkbox('显示原始数据'):
            st.subheader('原始数据')
            st.text_area("匹配的数据行", "\n".join(raw_lines), height=200)
        
        # 选择要可视化的数值列
        selected_values = st.multiselect(
            '选择要可视化的数值',
            options=['X axis', 'Y axis', 'Z axis', 'Speed'],
            default=['X axis', 'Y axis', 'Z axis', 'Speed']
        )
        
        if selected_values:
            # 创建交互式图表
            st.subheader('交互式时间序列图')
            fig = create_interactive_plot(
                df['timestamp'], 
                df['X axis'] if 'X axis' in selected_values else [None]*len(df),
                df['Y axis'] if 'Y axis' in selected_values else [None]*len(df),
                df['Z axis'] if 'Z axis' in selected_values else [None]*len(df),
                df['Speed'] if 'Speed' in selected_values else [None]*len(df)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示数据表格
            st.subheader('数据表格')
            st.dataframe(df[['timestamp'] + selected_values])
            
            # 提供数据下载
            csv = df[['timestamp'] + selected_values].to_csv(index=False)
            st.download_button(
                label="下载数据为CSV",
                data=csv,
                file_name="time_series_data.csv",
                mime="text/csv"
            )
    else:
        st.error("未能提取任何有效数据，请检查文件格式是否正确。")
else:
    st.info("请上传数据文件")
    
    # 显示示例数据格式
    st.subheader("支持的数据格式示例:")
    st.code(
        """
            [2025-09-17_19:31:00:123] 4,30,2078   # 带毫秒的格式
            [2025-09-17_19:31:00] 4,30,2078       # 不带毫秒的格式
        """)