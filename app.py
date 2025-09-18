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

def process_data(content):
    """
    处理数据内容，提取时间戳和数值
    """
    # 定义正则表达式模式
    # 使用非捕获组(?:...)来匹配时间格式中毫秒部分， 因为有可能没有毫秒
    pattern = r"\[(\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}(?::\d{3})?)\]\s*(-?\d+),(-?\d+),(-?\d+)"
    
    # 初始化列表存储数据
    timestamps = []
    values1 = []
    values2 = []
    values3 = []
    raw_lines = []
    
    # 处理每一行数据
    for line in content.splitlines():
        match1 = re.search(pattern1, line)
        match2 = re.search(pattern2, line)
        
        match = match1 if match1 else match2
        if match:
            time_str = match.group(1)
            val1 = int(match.group(2))
            val2 = int(match.group(3))
            val3 = int(match.group(4))
            
            # 转换时间字符串为 datetime 对象
            dt = parse_custom_datetime(time_str)
            if dt:
                timestamps.append(dt)
                values1.append(val1)
                values2.append(val2)
                values3.append(val3)
                raw_lines.append(line)
    
    return timestamps, values1, values2, values3, raw_lines

def create_interactive_plot(timestamps, values1, values2, values3):
    """
    创建交互式图表
    """
    # 创建子图
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Value 1', 'Value 2', 'Value 3'),
        vertical_spacing=0.1
    )
    
    # 添加三个数据系列
    fig.add_trace(
        go.Scatter(x=timestamps, y=values1, name='Value 1', line=dict(color='blue')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=values2, name='Value 2', line=dict(color='red')),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=timestamps, y=values3, name='Value 3', line=dict(color='green')),
        row=3, col=1
    )
    
    # 更新布局
    fig.update_layout(
        height=800,
        title_text="时间序列数据可视化",
        showlegend=True,
        hovermode='x unified'
    )
    
    # 更新x轴和y轴标签
    fig.update_xaxes(title_text="时间", row=3, col=1)
    fig.update_yaxes(title_text="数值", row=2, col=1)
    
    return fig

if uploaded_file is not None:
    # 读取文件内容
    content = uploaded_file.read().decode('utf-8')
    
    # 处理数据
    timestamps, values1, values2, values3, raw_lines = process_data(content)
    
    if timestamps:
        # 创建 DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value1': values1,
            'value2': values2,
            'value3': values3
        })
        
        st.success(f"成功加载 {len(df)} 条数据")
        
        # 显示数据统计
        st.subheader('数据统计')
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Value 1 平均值", f"{df['value1'].mean():.2f}")
            st.metric("Value 1 最小值", df['value1'].min())
            st.metric("Value 1 最大值", df['value1'].max())
        
        with col2:
            st.metric("Value 2 平均值", f"{df['value2'].mean():.2f}")
            st.metric("Value 2 最小值", df['value2'].min())
            st.metric("Value 2 最大值", df['value2'].max())
        
        with col3:
            st.metric("Value 3 平均值", f"{df['value3'].mean():.2f}")
            st.metric("Value 3 最小值", df['value3'].min())
            st.metric("Value 3 最大值", df['value3'].max())
        
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
            options=['value1', 'value2', 'value3'],
            default=['value1', 'value2', 'value3']
        )
        
        if selected_values:
            # 创建交互式图表
            st.subheader('交互式时间序列图')
            fig = create_interactive_plot(
                df['timestamp'], 
                df['value1'] if 'value1' in selected_values else [None]*len(df),
                df['value2'] if 'value2' in selected_values else [None]*len(df),
                df['value3'] if 'value3' in selected_values else [None]*len(df)
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
        st.error("未找到匹配的数据格式。请确保数据格式为: [YYYY-MM-DD_HH:MM:SS:sss] val1,val2,val3 或 [YYYY-MM-DD_HH:MM:SS] val1,val2,val3")
else:
    st.info("请上传数据文件")
    
    # 显示示例数据格式
    st.subheader("支持的数据格式示例:")
    st.code("""
[2025-09-17_19:31:00:123] 4,30,2078   # 带毫秒的格式
[2025-09-17_19:31:00] 4,30,2078       # 不带毫秒的格式
    """)