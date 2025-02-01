import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import math
from matplotlib.lines import Line2D
import dash
from dash import dcc, html
import base64
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# 讀取 CSV 檔案
file_path = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIF_VF_D.csv'

try:
    data = pd.read_csv(file_path)
except FileNotFoundError:
    raise FileNotFoundError(f"文件未找到: {file_path}")
except pd.errors.ParserError:
    raise ValueError("CSV 文件格式錯誤")

# 數據清理
data = data.replace([np.inf, -np.inf], np.nan)
data.dropna(inplace=True)

# 定義擬合函數為三次多項式
def polynomial(Vf, a, b, c, d):
    return a * Vf ** 3 + b * Vf ** 2 + c * Vf + d

# 選擇不同的接面溫度
temperatures = ['25℃', '150℃', '175℃']
colors = ['gray', 'skyblue', 'navy']

# 儲存斜率的字典
slopes = {}

# 定義要標記的特定點，包含標籤位置 (x_label, y_label)
marked_points = {
    '25℃': [
        {'If': 450, 'x_label': 1.4, 'y_label': 600},
        {'If': 820, 'x_label': 1.8, 'y_label': 950}
    ],
    '150℃': [
        {'If': 450, 'x_label': 1.5, 'y_label': 500},
        {'If': 820, 'x_label': 2.0, 'y_label': 850}
    ],
    '175℃': [
        {'If': 450, 'x_label': 1.55, 'y_label': 350},
        {'If': 820, 'x_label': 2.1, 'y_label': 750}
    ]
}

# 用於存儲所有標記點的信息，以便在圖例中添加
marked_points_info = []

# 收集所有 If 數據以計算 y 軸範圍
all_If = []
for temp in temperatures:
    If = data[f'If_{temp}']
    all_If.extend(If.tolist())

# 計算 y 軸的最小值和最大值，並設置一些邊距
y_min = math.floor(min(all_If) / 100) * 100  # 向下取整到最接近的 100 的倍數
y_max = 1000  # 根據標註位置調整 y_max 至至少 1000

# 設置主刻度和次刻度的間隔
major_tick_interval = 100
minor_tick_interval = 50

# 定義標記點的大小
marked_point_size = 50  # 調整標記點為更小的值

# 繪製擬合並創建圖形的函數
def create_figure():
    fig, ax = plt.subplots(figsize=(12, 8))

    for temp, color in zip(temperatures, colors):
        Vf = data[f'Vf_{temp}']
        If = data[f'If_{temp}']

        # 擬合數據
        popt, _ = curve_fit(polynomial, Vf, If)

        # 繪製原始數據點為實線
        label_data = f'Data Tj={temp}'
        ax.plot(Vf, If, '-', label=label_data, color=color, linewidth=2, alpha=1)

        # 繪製擬合曲線為實線
        x_fit = np.linspace(min(Vf), max(Vf), 500)  # 使用 500 個點繪製擬合曲線
        y_fit = polynomial(x_fit, *popt)
        label_fit = f'Fit Tj={temp}'
        ax.plot(x_fit, y_fit, '-', color=color, linewidth=1, alpha=0.7)  # 使用實線繪製擬合曲線

        # 標記並標註特定的 If 點
        for point in marked_points[temp]:
            target_If = point['If']
            x_label = point['x_label']
            y_label = point['y_label']

            # 在數據中找到最接近的 If 值的索引
            closest_idx = (np.abs(If - target_If)).argmin()
            actual_If = If.iloc[closest_idx]
            actual_Vf = Vf.iloc[closest_idx]

            # 繪製紫色標記點
            ax.scatter(actual_Vf, actual_If, color='purple', marker='o', s=marked_point_size, edgecolors='none',
                       zorder=5)

            # 添加數值標註，IF 在前，VF 在後，並使用指定的標籤位置和斷行
            ax.annotate(f'IF={actual_If:.2f} A\nVF={actual_Vf:.4f} V',
                        (x_label, y_label),
                        xycoords='data',
                        textcoords='data',
                        ha='left',
                        va='bottom',
                        fontsize=9,
                        color='black',
                        bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3))

            # 儲存標記點的信息
            marked_points_info.append({
                'temp': temp,
                'Vf': actual_Vf,
                'If': actual_If,
                'x_label': x_label,
                'y_label': y_label
            })

        # 計算 R²、MSE 和 MAE
        residuals = If - polynomial(Vf, *popt)
        ss_res = np.sum(residuals ** 2)  # 殘差平方和（Residual Sum of Squares）
        ss_tot = np.sum((If - np.mean(If)) ** 2)  # 總變異平方和（Total Sum of Squares）
        r_squared = 1 - (ss_res / ss_tot)
        mse = np.mean(residuals ** 2)
        mae = np.mean(np.abs(residuals))

        # 顯示擬合參數和指標（左下角，黑色文字），每個溫度單獨標示
        ax.text(0.02, 0.05 + 0.10 * temperatures.index(temp),
                f'Temperature {temp}\nR² = {r_squared:.3f}\nMSE = {mse:.3f}\nMAE = {mae:.3f}',
                color='black', fontsize=10, transform=ax.transAxes,
                verticalalignment='bottom', horizontalalignment='left')

    # 設置 y 軸刻度範圍和次小刻度
    ax.set_ylim(y_min, y_max)
    major_ticks = np.arange(y_min, y_max + major_tick_interval, major_tick_interval)
    minor_ticks = np.arange(y_min, y_max + minor_tick_interval, minor_tick_interval)
    ax.set_yticks(major_ticks)
    ax.yaxis.set_minor_locator(plt.MultipleLocator(minor_tick_interval))

    # 設置細緻的網格
    ax.grid(which='both', linestyle='--', linewidth=0.5, alpha=0.7)  # 主網格的樣式
    ax.minorticks_on()  # 開啟次刻度
    ax.grid(which='minor', linestyle=':', linewidth=0.5, alpha=0.5)  # 次網格的樣式

    # 設置標籤和標題
    ax.set_xlabel('VF (V)', fontsize=14)
    ax.set_ylabel('IF (A)', fontsize=14)
    ax.set_title('IF vs VF Non-linear Fit', fontsize=19, fontweight='bold')
    ax.set_xlim(left=min(data[[f'Vf_{temp}' for temp in temperatures]].min()),
                right=max(data[[f'Vf_{temp}' for temp in temperatures]].max()))
    fig.tight_layout()

    # 創建自定義圖例
    temperature_patches = [Line2D([0], [0], linestyle='-', linewidth=3, color=color, label=f'Data Tj={temp}')
                           for temp, color in zip(temperatures, colors)]
    fit_patches = [Line2D([0], [0], linestyle='-', linewidth=1, color=color, label=f'Fit Tj={temp}')
                   for temp, color in zip(temperatures, colors)]
    handles = temperature_patches + fit_patches

    # 添加自定義圖例項目說明紫色標記點
    for point in marked_points_info:
        temp = point['temp']
        Vf_val = point['Vf']
        If_val = point['If']
        label = f'{temp} IF={If_val:.2f} A, VF={Vf_val:.4f} V'
        # 創建一個紫色的點作為圖例項目
        marker = Line2D([0], [0], marker='o', color='w', label=label,
                        markerfacecolor='purple', markeredgecolor='none', markersize=5)  # 調整 markersize 為 5
        handles.append(marker)

    # 添加圖例
    ax.legend(handles=handles, fontsize=10, loc='upper left', bbox_to_anchor=(0, 1),
              title='Data, Fits & Marked Points')

    return fig






# 創建圖形並轉換為 base64
fig = create_figure()
img_io = io.BytesIO()
FigureCanvas(fig).print_png(img_io)
encoded_image = base64.b64encode(img_io.getvalue()).decode()

# 創建 Dash 應用
app = dash.Dash(__name__)

# 定義應用佈局
app.layout = html.Div(
    style={
        'display': 'flex',
        'padding': '20px',
        'flexWrap': 'wrap',  # 允許換行，以提升響應式
    },
    children=[
        # 左側顯示圖片
        html.Div(
            children=[
                html.Img(
                    src=f'data:image/png;base64,{encoded_image}',
                    style={'width': '100%', 'height': 'auto'}  # 調整圖片寬度
                ),
            ],
            style={
                'flex': '1',
                'padding-right': '40px',
                'minWidth': '900px'
            }
        ),

        # 右側文本框
        html.Div(
            style={
                'flex': '1',
                'minWidth': '380px'
            },
            children=[
                # 定義主標題
                html.H3(
                    children=['不同溫度下 IF與VF 關係'],
                    style={
                        'margin-bottom': '10px',
                        'color': '#003366',  # 深藍色
                        'margin-top': '0px',
                        'font-size': '26px',  # 調整字體大小
                        'font-weight': 'bold'  # 加粗
                    }
                ),
                # 定義段落並允許斷行
                html.P(
                    children=[
                        "不同溫度的數據（25℃、150℃、175℃）顯示了 VF 與 IF 的非線性關係。"
                    ],
                    style={
                        'white-space': 'pre-line',  # 允許斷行
                        'color': '#333333',  # 深灰色
                        'margin-top': '10px',
                        'margin-bottom': '20px',
                        'font-size': '18px'  # 調整字體大小
                    }
                ),

                # 擬合曲線的準確性
                html.H3(
                    children=['擬合曲線的準確性'],
                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                ),
                html.Details([
                    html.Summary(
                        '數據匯入',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
**從表格中提取 VF 和 IF 的數據**，根據不同溫度（25°C、150°C、175°C）分別建立數據集。這些數據會用於擬合三次多項式模型。

**數學表示**

模型為：

$$
IF = a \cdot VF^3 + b \cdot VF^2 + c \cdot VF + d
$$

其中：
- **VF**：順向電壓（自變量）。
- **IF**：順向電流（因變量）。
''', mathjax=True)
                ]),
                html.Details([
                    html.Summary(
                        '數據處理：擬合方法',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
**擬合的數學過程**：

**目標**：找到一組最佳係數 \(a, b, c, d\)，使得三次多項式

$$
IF = a \cdot VF^3 + b \cdot VF^2 + c \cdot VF + d
$$

的曲線盡可能貼合測量數據。

**使用方法**：常見的方法是**最小二乘法**，它通過最小化以下誤差函數來找到最佳係數：

$$
\text{誤差} = \sum_{i=1}^{n} \left(IF_{\text{實測},i} - IF_{\text{預測},i}\right)^2
$$

其中：
$$
- IF_{\text{實測},i} ：第 i 個數據點的實測電流值。
$$
$$
- F_{\text{預測},i} ：第 i 個數據點的模型預測值。
$$
$$
- n：數據點總數。
$$

**工具**：
- 使用程式（如 Python 的 `curve_fit`）來執行上述計算。
''', mathjax=True)
                ]),

                # 多溫度數據擬合
                html.Details([
                    html.Summary(
                        '多溫度數據擬合',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
對**不同溫度下**的數據進行擬合，計算出係數 \(a, b, c, d\)。這些係數後可將它們帶入公式，對任意 **VF** 計算 **IF**：

$$
IF = a \cdot VF^3 + b \cdot VF^2 + c \cdot VF + d
$$
''', mathjax=True)
                ]),

                # 評估指標的解釋
                html.H3(
                    children=['評估指標的解釋'],
                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                ),
                html.Details([
                    html.Summary(
                        'R²（決定係數）',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
**R²（決定係數）** 用來衡量擬合模型解釋數據變異的能力。值域為：

$$
0 \leq R² \leq 1
$$

- **\( R² = 1 \)**：表示模型完美擬合數據，所有數據點都在模型曲線上。
- **\( R² \) 越接近 1**：表示模型對數據的擬合越好，能解釋更多的變異。
- **\( R² \) 接近 0**：表示模型無法有效解釋數據的變異，擬合效果較差。

**計算公式**：

$$
R² = 1 - \frac{\text{SS}_{res}}{\text{SS}_{tot}}
$$

其中：
$$
{SS}_{res}：殘差平方和（Residual Sum of Squares）。
$$
$$
{SS}_{tot}：總變異平方和（Total Sum of Squares）。
$$

**如何解讀**：
- **\( R² = 1 \)**：模型完美擬合數據。
- **\( R² = 0 \)**：模型無法解釋任何變異。
- **\( R² \) 接近 1**，但仍有較高的 MSE 或 MAE，可能表示數據內部存在離群點。
''', mathjax=True)
                ]),
                html.Details([
                    html.Summary(
                        'MSE（均方誤差）',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
**MSE（均方誤差Mean Squared Error）** 是衡量模型預測值與真實值之間差距的平均平方誤差。

**計算公式**：

$$
\text{MSE} = \frac{1}{n} \sum_{i=1}^n (y_i - \hat{y}_i)^2
$$

其中：
$$
y_i：真實值。
$$
$$
\hat{y}_i：模型預測值。
$$
$$
n：數據點總數。
$$

**如何解讀**：
- **MSE 越小**：表示模型預測的精確性越高。
- **單位**：與目標變數（如 IF）的平方單位一致，因此對於單位較大的數據，MSE 數值也會較大。
- **優點**：適合用來檢查模型對數據整體的擬合精度。
- **缺點**：容易受到離群點的影響。
''', mathjax=True)
                ]),
                html.Details([
                    html.Summary(
                        'MAE（平均絕對誤差）',
                        style={
                            'font-size': '18px',
                            'font-weight': 'bold',
                            'color': '#003366',
                        }
                    ),
                    dcc.Markdown(r'''
**MAE（平均絕對誤差Mean Absolute Error）** 是衡量模型預測值與真實值之間差距的平均絕對誤差。

**計算公式**：

$$
\text{MAE} = \frac{1}{n} \sum_{i=1}^n |y_i - \hat{y}_i|
$$

其中：
$$
y_i：真實值。
$$
$$
\hat{y}_i：模型預測值。
$$
$$
n：數據點總數。
$$

**如何解讀**：
- **MAE 越小**：表示模型對數據的擬合越準確。
- **單位**：具有直觀的物理單位（如 IF 單位為安培）。
- **優點**：對於離群點的影響較小，因此適合用於評估模型的穩定性。
''', mathjax=True)
                ]),

                # 斜率的計算
                html.H3(
                    children=['斜率的計算'],
                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                ),
                html.P(
                    children=[
                        "在不同溫度下，擬合曲線的斜率反映了VF與IF之間的變化率。",
                        html.Br(),
                        "例如，在VF=0時和VF=627時的斜率分別計算如下：",
                        html.Br(),
                        r"斜率 (VF=0): 由擬合函數的一次項係數 \(c\) 決定。",
                        html.Br(),
                        "斜率 (VF=627): 由擬合函數的一階導數計算得到，公式如下：",
                        html.Br(),
                        dcc.Markdown(r'''
$$
m = 3aVf^2 + 2bVf + c
$$

其中，\(a\), \(b\), \(c\) 是擬合參數。
''', mathjax=True)
                    ],
                    style={'font-size': '18px', 'color': '#333333'}
                ),

                # 擬合參數與指標說明
                html.H3(
                    children=['擬合參數與指標'],
                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                ),
                html.P(
                    children=[
                        "每條擬合曲線旁邊標註了擬合方程式及其指標：",
                        html.Br(),
                        r"- **擬合方程式**：\( y = ax^3 + bx^2 + cx + d \)",
                        html.Br(),
                        "- **R²**：決定係數，用於衡量擬合的準確性。值越接近1表示擬合效果越好。",
                        "- **MSE**：均方誤差，反映擬合誤差的平均水平。",
                        html.Br(),
                        "- **MAE**：平均絕對誤差，反映擬合誤差的平均絕對值。"
                    ],
                    style={'font-size': '18px', 'color': '#333333'}
                ),

                # 標記點說明
                html.H3(
                    children=['標記點說明'],
                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                ),
                html.P(
                    children=[
                        "圖中紫色標記點代表特定的IF和VF值，並在圖表中進行了標註。",
                        html.Br(),
                        "這些標記點有助於直觀地了解在特定IF值下對應的VF值，反之亦然。"
                    ],
                    style={'font-size': '18px', 'color': '#333333'}
                ),

            ]
        ),
    ]
)

# 運行 Dash 應用
if __name__ == '__main__':
    app.run_server(debug=True)