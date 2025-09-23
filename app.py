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


def csv_to_txt(csv_file_path, txt_file_path):
    """
    将CSV文件转换为特定格式的TXT文件

    参数:
    csv_file_path (str): 输入的CSV文件路径
    txt_file_path (str): 输出的TXT文件路径
    """
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csv_file:
            # 读取CSV文件
            csv_reader = csv.DictReader(csv_file)
            
            with open(txt_file_path, 'w', encoding='utf-8') as txt_file:
                # 写入TXT文件标题行
                txt_file.write("X axis,Y axis,Z axis,GNSS Accuracy,Speed,Azimuth,TIME\n")
                
                # 处理每一行数据
                for row in csv_reader:
                    # 提取并转换加速度数据
                    x_axis = row['Accel_X']
                    y_axis = row['Accel_Y']
                    z_axis = row['Accel_Z']
                    
                    # GNSS Accuracy和Azimuth置0
                    gnss_accuracy = "0"
                    azimuth = "0"
                    
                    # 计算速度 (sqrt(Horizontal_Speed^2 + Vertical_Speed^2))
                    horizontal_speed = float(row['Horizontal_Speed'])
                    vertical_speed = float(row['Vertical_Speed'])
                    speed = math.sqrt(horizontal_speed**2 + vertical_speed**2)
                    
                    # 转换时间格式 (添加固定日期20250909)
                    time_str = row['Time']
                    # 确保时间格式正确 (HH:MM:SS)
                    if len(time_str.split(':')) == 3:
                        hours, minutes, seconds = time_str.split(':')
                        # 添加前导零如果需要
                        hours = hours.zfill(2)
                        formatted_time = f"20250909{hours}{minutes}{seconds}"
                    else:
                        # 如果时间格式不正确，使用默认值
                        formatted_time = "20250909000000"
                    
                    # 写入转换后的数据行
                    txt_file.write(f"{x_axis},{y_axis},{z_axis},{gnss_accuracy},{speed:.1f},{azimuth},{formatted_time}\n")
                    
        print(f"转换完成! TXT文件已保存至: {txt_file_path}")
        
    except Exception as e:
        print(f"转换过程中发生错误: {str(e)}")


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
                val1 = float(parts[0])
                val2 = float(parts[1])
                val3 = float(parts[2])
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


def create_interactive_plot(timestamps, rv_x, rv_y, rv_z, rv_speed, cmp_x, cmp_y, cmp_z, cmp_speed):
    """
    创建交互式图表
    """
    # 创建单一坐标系，左轴为三轴，右轴为速度
    fig = go.Figure()
    # rv_X轴
    fig.add_trace(go.Scatter(x=timestamps, y=rv_x, name='X axis', line=dict(color='blue'), yaxis='y'))
    # rv_Y轴
    fig.add_trace(go.Scatter(x=timestamps, y=rv_y, name='Y axis', line=dict(color='red'), yaxis='y'))
    # rv_Z轴
    fig.add_trace(go.Scatter(x=timestamps, y=rv_z, name='Z axis', line=dict(color='green'), yaxis='y'))
    # cmp_X轴
    fig.add_trace(go.Scatter(x=timestamps, y=cmp_x, name='CMP X axis', line=dict(color='cyan'), yaxis='y'))
    # cmp_Y轴
    fig.add_trace(go.Scatter(x=timestamps, y=cmp_y, name='CMP Y axis', line=dict(color='magenta'), yaxis='y'))
    # cmp_Z轴
    fig.add_trace(go.Scatter(x=timestamps, y=cmp_z, name='CMP Z axis', line=dict(color='yellow'), yaxis='y'))

    # rv_Speed 右轴
    fig.add_trace(go.Scatter(x=timestamps, y=rv_speed, name='Speed', line=dict(color='orange'), yaxis='y2'))
    # cmp_Speed 右轴
    fig.add_trace(go.Scatter(x=timestamps, y=cmp_speed, name='CMP Speed', line=dict(color='purple'), yaxis='y2'))

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


def read_realvalue_file():
    """
    读取本地的 extra_RealData_GPS_ACC.txt 文件内容
    """
    try:
        with open('extra_RealData_GPS_ACC.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        st.error(f"读取 extra_RealData_GPS_ACC.txt 文件时出错: {str(e)}")
        return ""


if uploaded_file is not None:
    
    cmp_content = read_realvalue_file()
    cmp_timestamps, cmp_X, cmp_Y, cmp_Z, cmp_Speed, cmp_raw_lines = process_data(cmp_content)

    print(f"Uploaded file: {uploaded_file.name}")
    uploaded_file.seek(0)  # 确保文件指针在开头
    content = uploaded_file.read().decode('utf-8')
    # 处理数据
    timestamps, X, Y, Z, Speed, raw_lines = process_data(content)

    # 构建主数据DataFrame
    main_df = pd.DataFrame({
        'timestamp': timestamps,
        'X axis': X,
        'Y axis': Y,
        'Z axis': Z,
        'Speed': Speed
    })
    # 构建cmp数据DataFrame
    cmp_df = pd.DataFrame({
        'timestamp': cmp_timestamps,
        'cmp_X axis': cmp_X,
        'cmp_Y axis': cmp_Y,
        'cmp_Z axis': cmp_Z,
        'cmp_Speed': cmp_Speed
    })

    # 合并数据，按timestamp对齐
    df = pd.merge(main_df, cmp_df, on='timestamp', how='inner')

    if not df.empty:
        st.success(f"成功加载 {len(df)} 条合并数据（按时间戳对齐）")

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
            options=['X axis', 'Y axis', 'Z axis', 'Speed', 'cmp_X axis', 'cmp_Y axis', 'cmp_Z axis', 'cmp_Speed'],
            default=['X axis', 'Y axis', 'Z axis', 'Speed', 'cmp_X axis', 'cmp_Y axis', 'cmp_Z axis', 'cmp_Speed']
        )

        if selected_values:
            # 创建交互式图表
            st.subheader('交互式时间序列图')
            fig = create_interactive_plot(
                df['timestamp'], 
                df['X axis'] if 'X axis' in selected_values else [None]*len(df),
                df['Y axis'] if 'Y axis' in selected_values else [None]*len(df),
                df['Z axis'] if 'Z axis' in selected_values else [None]*len(df),
                df['Speed'] if 'Speed' in selected_values else [None]*len(df),
                df['cmp_X axis'] if 'cmp_X axis' in selected_values else [None]*len(df),
                df['cmp_Y axis'] if 'cmp_Y axis' in selected_values else [None]*len(df),
                df['cmp_Z axis'] if 'cmp_Z axis' in selected_values else [None]*len(df),
                df['cmp_Speed'] if 'cmp_Speed' in selected_values else [None]*len(df)
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
        st.error("未能提取任何有效数据，请检查文件格式是否正确或时间戳是否能对齐。")
else:
    st.info("请上传数据文件")
    
    # 显示示例数据格式
    st.subheader("支持的数据格式示例:")
    st.code(
        """
            [2025-09-17_19:31:00:123] 4,30,2078   # 带毫秒的格式
            [2025-09-17_19:31:00] 4,30,2078       # 不带毫秒的格式
        """)