import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit
import base64
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
from IFVF02 import encoded_image

# 創建 Dash 應用，並設置 external_stylesheets 指向 Bootstrap 和自定義 CSS
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'],
                suppress_callback_exceptions=True)
server = app.server  # 如果需要部署到伺服器

# 固定數據文件路徑（右側損耗分析）
#DATA_FILE_PATH = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AIC_VCE_A.csv'  # 修改為您的文件路徑

DATA_FILE_PATH = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIC_VCE_A.csv'
DATA_FILE_PATH1 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIC_VCE_family_25C_B.csv'
DATA_FILE_PATH3 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIF_VF_D.csv'
DATA_FILE_PATH4 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AEon&Eoff(IC)_E.csv'  # 修改為您的文件路徑
DATA_FILE_PATH5 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AEon&Eoff(Rg)_F.csv'  # 修改為您的文件路徑
DATA_FILE_PATH6 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AErec(Rg)_J.csv'  # 修改為您的文件路徑
DATA_FILE_PATH7 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AGatecharge_L.csv'  # 修改為您的文件路徑
DATA_FILE_PATH8 = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AZthtrialIGBT_M.csv'  # 修改為您的文件路徑

#DATA_FILE_PATH1 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AIC_VCE_family_25C_B.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH3 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AIF_VF_D.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH4 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AEon&Eoff(IC)_E.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH5 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AEon&Eoff(RG)_F.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH6 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AErec(RG)_J.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH7 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AGatecharge_L.csv'  # 修改為您的文件路徑
#DATA_FILE_PATH8 = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AZthtrialIGBT_M.csv'  # 修改為您的文件路徑



# 解析上傳文件的函數
def parse_contents(contents, filename):
    ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        extension = filename.split('.')[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("不支持的文件類型")
        if 'csv' in extension:
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in extension:
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

# 從固定路徑讀取數據的函數
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return pd.DataFrame()  # 返回空的 DataFrame

# 熱阻分析 (Thermal Resistance)
def calc_thermal_resistance(Tj, Pd):
    Tc = 25  # 假設環境溫度為常數25℃
    Tj = np.array(Tj)
    Pd = np.array(Pd)
    return (Tj - Tc) / Pd

# 開關損耗分析 (Switching Loss)
def calc_switching_loss(VCE, IC, switching_time):
    return 0.5 * VCE * IC * switching_time

# 導通損耗 (Conduction Loss)
def calc_conduction_loss(VCE, IC):
    return VCE * IC

# 靜態電阻 (Static Resistance)
def calc_static_resistance(VCE, IC):
    return VCE / IC

# 數據趨勢分析與擬合 (Data Trend and Curve Fitting)
def linear_model(VCE, a, b):
    return a * VCE + b

# 定義擬合函數
def poly3_func(x, a, b, c, d):
    return a * x ** 3 + b * x ** 2 + c * x + d

# 計算 R² 的函數
def calculate_r_squared(y_true, y_pred):
    residuals = y_true - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    return r_squared

# 計算點到點斜率的函數
def calculate_point_to_point_slope(x, y):
    slopes = np.diff(y) / np.diff(x)
    return slopes

# 定義按鈕樣式為長條矩形
def create_flet_like_buttons():
    return dbc.Row([
        dbc.Col(
            dbc.Button(
                "Button 1",
                color="primary",
                style={
                    'borderRadius': '10px',
                    'padding': '10px 40px',
                    'margin': '5px',
                    'boxShadow': '2px 2px 5px rgba(0,0,0,0.3)'
                },
                className="me-2"
            ),
            width="auto"
        ),
        dbc.Col(
            dbc.Button(
                "Button 2",
                color="secondary",
                style={
                    'borderRadius': '10px',
                    'padding': '10px 40px',
                    'margin': '5px',
                    'boxShadow': '2px 2px 5px rgba(0,0,0,0.3)'
                },
                className="me-2"
            ),
            width="auto"
        )
    ], justify="start", className="g-0")

# 創建上傳卡片，增加參數以控制是否包含按鈕，以及圖表和卡片的樣式
def create_upload_card(card_title, subtitle, upload_id, graph_id, dropdown_id, include_buttons=True, graph_style=None,
                       card_style=None):
    children = [
        html.H5(card_title, className="card-title", style={'textAlign': 'left'}),
        html.H6(subtitle, className="card-subtitle mb-2 text-muted", style={'textAlign': 'left'}),

        # 添加下拉選單
        html.Div([
            html.Label("選擇分析項目:", style={'fontSize': '16px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id=dropdown_id,
                options=[
                    {'label': 'VGE = 15V, IC = f(VCE)', 'value': 'VGE_15V_IC_f_VCE'},  # 選單一 - 修改 value
                    {'label': 'Tj = 25°C, IC = f(VCE)', 'value': 'Tj_25C_IC_f_VCE'},  # 選單二
                    {'label': 'Tj = 150°C, IC = f(VCE)', 'value': 'Tj_150C_IC_f_VCE'},  # 選單三
                    {'label': 'Tj = 175°C, IC = f(VCE)', 'value': 'Tj_175C_IC_f_VCE'}  # 選單四
                ],
                value='Tj_25C_IC_f_VCE',  # 默認選擇選單二
                clearable=False,
                style={'width': '100%'}
            )
        ], className='custom-dropdown'),

        # 上傳組件
        dcc.Upload(
            id=upload_id,
            children=html.Div(['拖曳檔案或 ', html.A('選擇檔案')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
            }
        ),

        # 圖表
        dcc.Graph(id=graph_id, style=graph_style)
    ]

    if include_buttons:
        children.append(create_flet_like_buttons())

    return dbc.Card(
        dbc.CardBody(children, style=card_style),  # 添加卡片樣式
        className="shadow-sm border mb-4"
    )

# 繪製三次多項式擬合圖並顯示積分區域
def create_figure(file_path):
    df = pd.read_csv(file_path)
    temps = [25, 150, 175]
    colors = ['gray', 'skyblue', 'navy']
    markers = ['x', 'x', 'x']

    fig, ax = plt.subplots(figsize=(12, 8))
    for temp, color, marker in zip(temps, colors, markers):
        vce_col = f'VCE_Tj = {temp}℃'
        ic_col = f'IC_Tj = {temp}℃'
        vce = df[vce_col].dropna()
        ic = df[ic_col].dropna()

        if len(vce) == 0 or len(ic) == 0:
            continue  # 跳過沒有數據的溫度

        # 擬合三次多項式
        try:
            popt_poly3, _ = curve_fit(poly3_func, vce, ic)
            vce_fit = np.linspace(min(vce), max(vce), 80)
            ic_fit_poly3 = poly3_func(vce_fit, *popt_poly3)
            r_squared_poly3 = calculate_r_squared(ic, poly3_func(vce, *popt_poly3))
        except Exception as e:
            print(f"Error fitting data for Tj={temp}℃: {e}")
            continue

        # 計算線性區域的斜率 (VCE < 1.5V)
        linear_region_mask = vce < 1.5
        vce_linear = vce[linear_region_mask]
        ic_linear = ic[linear_region_mask]
        if len(vce_linear) > 1:
            slopes_linear = calculate_point_to_point_slope(vce_linear, ic_linear)
            average_slope_linear = np.mean(slopes_linear)
        else:
            average_slope_linear = np.nan

        # 計算飽和區域的斜率 (VCE >= 1.5V)
        saturation_region_mask = vce >= 1.5
        vce_saturation = vce[saturation_region_mask]
        ic_saturation = ic[saturation_region_mask]
        if len(vce_saturation) > 1:
            slopes_saturation = calculate_point_to_point_slope(vce_saturation, ic_saturation)
            average_slope_saturation = np.mean(slopes_saturation)
        else:
            average_slope_saturation = np.nan

        # 繪製原始數據與擬合曲線
        ax.plot(vce, ic, linestyle='-', color=color, label=f'Tj = {temp}°C')
        ax.plot(vce_fit, ic_fit_poly3, linestyle=':', color=color, alpha=0.7, label=f'Fit, R² = {r_squared_poly3:.3f}')

        # 計算線性區域的能量
        energy_linear = np.trapz(ic_linear, vce_linear)
        ax.fill_between(vce_linear, ic_linear, alpha=0.2, color=color, label=f'Linear Region E = {energy_linear:.0f} J')

        # 計算飽和區域的能量
        energy_saturation = np.trapz(ic_saturation, vce_saturation)
        ax.fill_between(vce_saturation, ic_saturation, alpha=0.1, color=color,
                        label=f'Saturation Region E = {energy_saturation:.0f} J')

        # 添加斜率到圖例
        if not np.isnan(average_slope_linear):
            ax.plot([], [], ' ', label=f'Linear Slope = {average_slope_linear:.2f}')
        if not np.isnan(average_slope_saturation):
            ax.plot([], [], ' ', label=f'Saturation Slope = {average_slope_saturation:.2f}')

    # 設定圖形標題與標籤
    ax.set_title('I-V Characteristic Curve & Linear Regions', fontsize=21, fontweight='bold', pad=20)
    ax.set_xlabel('VCE (V)', fontsize=16, color='black')
    ax.set_ylabel('IC (A)', fontsize=16, color='black')

    ax.axvline(x=1.5, color='orange', linestyle='--', linewidth=2, label='Saturation Threshold: 1.5 V')
    ax.text(0.30, ax.get_ylim()[1]*0.1, 'Linear Region', fontsize=12, fontweight='bold')
    ax.text(2.0, ax.get_ylim()[1]*0.3, 'Saturation Region', fontsize=12, fontweight='bold', color='red')


    # 圖例設定
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.minorticks_on()

    # 將 matplotlib 圖轉換為 base64
    img_io = io.BytesIO()
    FigureCanvas(fig).print_png(img_io)
    encoded_image = base64.b64encode(img_io.getvalue()).decode()

    plt.close(fig)  # 關閉圖表以釋放資源

    return encoded_image

# 繪製能量損失柱狀圖
def create_figure_tab2():
    # 定義功率條件
    vce_conditions = [1.4, 1.5, 1.6]
    ic_condition = 820

    power_25_given = vce_conditions[0] * ic_condition
    power_150_given = vce_conditions[1] * ic_condition
    power_175_given = vce_conditions[2] * ic_condition

    fig, ax = plt.subplots(figsize=(8, 6))

    temperatures = ['25℃', '150℃', '175℃']
    energy_values = [power_25_given, power_150_given, power_175_given]

    bars = ax.bar(temperatures, energy_values, color=['gray', 'lightblue', 'navy'], width=0.6)
    ax.set_xlabel('Junction Temperature (°C)', fontsize=12)
    ax.set_ylabel('Total Energy Loss (J)', fontsize=12)
    ax.set_title('Total Energy Loss at Different Junction Temperatures', fontsize=14, fontweight='bold', pad=20)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 10, f'{int(height)} J',
                ha='center', va='bottom', fontsize=10)
        ax.axvline(x=bar.get_x() + bar.get_width() / 2, ymin=0, ymax=height / ax.get_ylim()[1],
                   color='white', linestyle='-', linewidth=1.5, alpha=0.3)

    ax.axhline(y=np.mean(energy_values), color='red', linestyle='--', linewidth=1.5, label='Average Energy Loss')
    ax.legend(fontsize=10, loc='upper left')
    ax.yaxis.set_minor_locator(plt.MultipleLocator(100))
    ax.tick_params(axis='y', which='minor', length=4, labelsize=0)

    # 將 matplotlib 圖轉換為 base64
    img_io = io.BytesIO()
    FigureCanvas(fig).print_png(img_io)
    encoded_image = base64.b64encode(img_io.getvalue()).decode()
    plt.close(fig)  # 關閉圖表以釋放資源
    return encoded_image

# 生成 Tab1 圖表的 base64 編碼
encoded_image_tab1 = create_figure(DATA_FILE_PATH)
# 生成 Tab2 圖表的 base64 編碼
encoded_image_tab2 = create_figure_tab2()


# 創建損耗分析卡片（右側，從固定路徑讀取數據）
# 讀取並處理數據
def load_data_zth(file_path):
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error loading Zth data from {file_path}: {e}")
        return pd.DataFrame()  # 返回空的 DataFrame

# Card_8
def create_loss_analysis_card8():
    # 讀取數據
    df = load_data_zth(DATA_FILE_PATH8)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card8.")  # 偵錯用
        return go.Figure(), [], []

        # 取出最前、最後一筆
    first_row = df.iloc[0]
    last_row = df.iloc[-1]

    # 若有需要自訂 highlight條件，可在此設定
    # 舉例：標示 t[s] < 1e-5 之類

   # highlight_conditions = [
        # demo condition
       # {'t [s]': 1.00E-06, 'ΔTj (t)': 15.36089512},
   # ]

    style_data_conditional = [
        {
            'if': {
                # 讓「t [s]」和「ΔTj (t)」同時匹配第一筆
                'filter_query': (
                    f'{{t [s]}} = {first_row["t [s]"]} '
                    f'&& {{ΔTj (t)}} = {first_row["ΔTj (t)"]}'
                )
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        },
        {
            'if': {
                # 讓「t [s]」和「ΔTj (t)」同時匹配最後一筆
                'filter_query': (
                    f'{{t [s]}} = {last_row["t [s]"]} '
                    f'&& {{ΔTj (t)}} = {last_row["ΔTj (t)"]}'
                )
            },
            'backgroundColor': 'lightgreen',
            'color': 'black'
        }
    ]

    # 卡片本體
    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("Zth, Thermal Impedance vs. time",
                    style={'textAlign': 'left', 'marginBottom': '16px'}),


            # RadioItems 或 Dropdown（看需求）
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'Zth vs t (IGBT)', 'value': 'ZTH_IGBT'}
                           # {'label': 'Zth vs t (Diode)', 'value': 'ZTH_DIODE'}
                            # 視需要增減
                        ],
                        value='ZTH_IGBT',  # 預設
                        id='zth-radio8',
                        inline=True,
                        className='custom-radio'
                    ),
                    width=12,
                    className='fixed-radio-container'
                )
            ], className="mb-3"),

            # 圖片或圖表區
            html.Div(
                children=[
                    # 若是用靜態圖檔
                    # html.Img(
                    #     id='zth-image8',
                    #     src='/assets/ZTH_IGBT.png',
                    #     style={'width': '70%', 'height': 'auto', 'border': '1px solid lightgray'}
                    # ),

                    # 若是動態Plotly圖表
                    dcc.Graph(
                        id='zth-graph8',
                        style={'height': '400px'},
                        config={'displayModeBar': False,  # 顯示工具列
                                'displaylogo': False  # 是否隱藏 Plotly 的 logo
                                }
                    ),

                ],
                style={'padding': '20px', 'textAlign': 'center'}
            ),

            html.Div(id='zth-title8',
                     style={'textAlign': 'center',
                            'fontSize': '20px',
                            'marginTop': '10px'}),

            # 範圍滑桿(若有需要)
            html.Div([
                html.Label("Time Range (s)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='zth-time-slider8',
                    min=-6,  # 例如對數刻度
                    max=1,   # 依實際數據
                    step=1,
                    marks={i: f"1e{i}" for i in range(-6, 2)},
                    value=[-6, 1],
                    allowCross=False,
                    className='zth-time-slider'
                ),
                html.Div(id='zth-time-output8',
                         style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),

            # 數據表格
            dash_table.DataTable(
                id='zth-table8',
                style_table={'overflowX': 'auto'},
                page_size=15,
                filter_action='native',
                style_data_conditional=style_data_conditional,
                # 欄位會在回調裡動態生成
                columns=[],
                data=[],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': 16,
                    'textAlign': 'center',
                    'padding': '5px'
                }
            ),

            # 如需 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='zth-additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        html.P("這是 Zth Analysis 的頁籤一。"),
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是 Zth Analysis 的頁籤二。"),
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )






#Card_7
def create_loss_analysis_card7():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH7)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card7.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'If25℃', 'IC (A)': 447.51},
        {'溫度': 'Vf25℃', 'IC (A)': 819.11},
        {'溫度': 'If150℃', 'IC (A)': 451.644},
        {'溫度': 'Vf150℃', 'IC (A)': 823.824},
        {'溫度': 'If175℃', 'IC (A)': 450.026},
        {'溫度': 'Vf175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("IGBT Total gate charge characteristic ", style={'textAlign': 'left', 'marginBottom': '16px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'VCE = 400V, IC = 450A, Tj = 25°C, VGE = f(QG)', 'value': 'GATECHARGEL'}
                        ],
                        value='GATECHARGEL',  # 默認選擇
                        id='gatechargel6',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image7',
                        src='/assets/GATECHARGEL.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title7', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph7',
                    options=[
                       # {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                       # {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                       # {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                       {'label': 'Tj = 25℃', 'value': 'ifvf_all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 VGE 範圍 (V)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider7',
                    min=-8,  # 修改為 -100
                    max=30,  # 假設最大IC值為1800A
                    step=5,  # 設置步長為10A
                    marks={i: str(i) for i in range(-8, 30, 5)},
                    value=[-8, 30],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 QG 範圍 (μC)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider7',
                    min=0,  # 修改為 -1
                    max=3,  # 調整為15V
                    step=1,  # 設置步長為1V
                    marks={i: str(i) for i in range(0,3,1)},  # 標記從-1到15
                    value=[0, 3],  # 默認值為-1到15V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph7', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                                'displaylogo': False     # 是否隱藏 Plotly 的 logo
                              }),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table7',
                    options=[
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},  # 修正50℃為150℃
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table7',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "QG (μC)", "id": "QG (μC)"},
                    {"name": "VGE (V)", "id": "VGE (V)"}  # 新增的欄位

                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card7_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        html.P("這是頁籤一的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )




#++++
#Card_6
def create_loss_analysis_card6():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH6)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card6.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'If25℃', 'IC (A)': 447.51},
        {'溫度': 'Vf25℃', 'IC (A)': 819.11},
        {'溫度': 'If150℃', 'IC (A)': 451.644},
        {'溫度': 'Vf150℃', 'IC (A)': 823.824},
        {'溫度': 'If175℃', 'IC (A)': 450.026},
        {'溫度': 'Vf175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("Diode, Switching losses vs. RG ", style={'textAlign': 'left', 'marginBottom': '16px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'IF = 450A, VR = 400V, Erec = f(RG)', 'value': 'ERECRGH'}
                        ],
                        value='ERECRGH',  # 默認選擇
                        id='erecrg-radio5',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image6',
                        src='/assets/ERECRGH.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto', 'border': '1px solid lightgray'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title6', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph6',
                    options=[
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 RG 範圍 (Ω)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider6',
                    min=0,  # 修改為 -100
                    max=30,  # 假設最大IC值為1800A
                    step=5,  # 設置步長為10A
                    marks={i: str(i) for i in range(0, 30, 5)},
                    value=[0, 30],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 EREC 範圍 (MJ)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider6',
                    min=0,  # 修改為 -1
                    max=20,  # 調整為15V
                    step=5,  # 設置步長為1V
                    marks={i: str(i) for i in range(0, 20,5)},  # 標記從-1到15
                    value=[0, 20],  # 默認值為-1到15V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph6', style={'margin-bottom': '50px'},
            config={'displayModeBar': False,  # 顯示工具列
                    'displaylogo': False  # 是否隱藏 Plotly 的 logo
                    }
    ),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table6',
                    options=[
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},  # 修正50℃為150℃
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table6',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "RG (Ω)", "id": "RG (Ω)"},
                    {"name": "EREC (mJ)", "id": "EREC (mJ)"}  # 新增的欄位

                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card6_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        html.P("這是頁籤一的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )




#++++
#Card_5
def create_loss_analysis_card5():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH5)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card5.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'If25℃', 'IC (A)': 447.51},
        {'溫度': 'Vf25℃', 'IC (A)': 819.11},
        {'溫度': 'If150℃', 'IC (A)': 451.644},
        {'溫度': 'Vf150℃', 'IC (A)': 823.824},
        {'溫度': 'If175℃', 'IC (A)': 450.026},
        {'溫度': 'Vf175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("Eon, Eoff(Rg) Curve ", style={'textAlign': 'left', 'marginBottom': '16px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'Eon, Eoff = f(Rg)', 'value': 'EONEOFFRG'}
                        ],
                        value='EONEOFFRG',  # 默認選擇
                        id='eoneoffrg-radio5',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image5',
                        src='/assets/EONEOFFRGF.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto', 'border': '1px solid lightgray'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title5', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph5',
                    options=[
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 Eon, Eoff 範圍 (mJ)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider5',
                    min=0,  # 修改為 -100
                    max=100,  # 假設最大IC值為1800A
                    step=10,  # 設置步長為10A
                    marks={i: str(i) for i in range(0, 100, 10)},
                    value=[0, 100],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 IC 範圍 (A)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider5',
                    min=0,  # 修改為 -1
                    max=100,  # 調整為15V
                    step=10,  # 設置步長為1V
                    marks={i: str(i) for i in range(0, 100,10)},  # 標記從-1到15
                    value=[0, 100],  # 默認值為-1到15V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph5', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                              'displaylogo': False  # 是否隱藏 Plotly 的 logo
                              }
                      ),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table5',
                    options=[
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},  # 修正50℃為150℃
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table5',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "IC (A)", "id": "IC (A)"},
                    {"name": "VCE (V)", "id": "VCE (V)"},
                    {"name": "VCE2 (V)", "id": "VCE2 (V)"}  # 新增的欄位
                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card5_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        html.P("這是頁籤一的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )






#Card_4
def create_loss_analysis_card4():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH4)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card4.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'If25℃', 'IC (A)': 447.51},
        {'溫度': 'Vf25℃', 'IC (A)': 819.11},
        {'溫度': 'If150℃', 'IC (A)': 451.644},
        {'溫度': 'Vf150℃', 'IC (A)': 823.824},
        {'溫度': 'If175℃', 'IC (A)': 450.026},
        {'溫度': 'Vf175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("Eon, Eoff(IC) Curve ", style={'textAlign': 'left', 'marginBottom': '16px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'Eon, Eoff = f(Ic)', 'value': 'EONEOFFIC'}
                        ],
                        value='EONEOFFIC',  # 默認選擇
                        id='eoneoffic-radio4',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image4',
                        src='/assets/EONEOFFICE.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title4', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph4',
                    options=[
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 Eon, Eoff 範圍 (mJ)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider4',
                    min=-100,  # 修改為 -100
                    max=1800,  # 假設最大IC值為1800A
                    step=10,  # 設置步長為10A
                    marks={i: str(i) for i in range(0, 1801, 100)},
                    value=[0, 1800],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 IC 範圍 (A)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider4',
                    min=0,  # 修改為 -1
                    max=140,  # 調整為15V
                    step=10,  # 設置步長為1V
                    marks={i: str(i) for i in range(0, 140,20)},  # 標記從-1到15
                    value=[0, 140],  # 默認值為-1到15V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph4', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                              'displaylogo': False  # 是否隱藏 Plotly 的 logo
                              }
                      ),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table4',
                    options=[
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},  # 修正50℃為150℃
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table4',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "IC (A)", "id": "IC (A)"},
                    {"name": "VCE (V)", "id": "VCE (V)"},
                    {"name": "VCE2 (V)", "id": "VCE2 (V)"}  # 新增的欄位
                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card4_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        html.P("這是頁籤一的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )

def create_loss_analysis_card3():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH3)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card3.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'If25℃', 'IC (A)': 447.51},
        {'溫度': 'Vf25℃', 'IC (A)': 819.11},
        {'溫度': 'If150℃', 'IC (A)': 451.644},
        {'溫度': 'Vf150℃', 'IC (A)': 823.824},
        {'溫度': 'If175℃', 'IC (A)': 450.026},
        {'溫度': 'Vf175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("IF, VF Curve", style={'textAlign': 'left', 'marginBottom': '16px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'If = f(VF)', 'value': 'VGE_15V_IC_f_VCE'}
                        ],
                        value='VGE_15V_IC_f_VCE',  # 默認選擇
                        id='icvce-radio3',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image3',
                        src='/assets/IFVFD.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto', 'border': '1px solid lightgray'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title3', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph3',
                    options=[
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 IF 範圍 (A)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider3',
                    min=-100,  # 修改為 -100
                    max=1800,  # 假設最大IC值為1800A
                    step=10,  # 設置步長為10A
                    marks={i: str(i) for i in range(0, 1801, 100)},
                    value=[0, 1800],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 VF 範圍 (V)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider3',
                    min=-1,  # 修改為 -1
                    max=4,  # 調整為4V
                    step=0.1,  # 設置步長為0.1V
                    marks={i: str(i) for i in range(-1, 5)},  # 標記從-1到4
                    value=[-1, 4],  # 默認值為-1到4V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph3', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                              'displaylogo': False  # 是否隱藏 Plotly 的 logo
                              }
                      ),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table3',
                    options=[
                        {'label': '所有溫度', 'value': 'ifvf_all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 50℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='ifvf_all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table3',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "IC (A)", "id": "IC (A)"},
                    {"name": "VCE (V)", "id": "VCE (V)"}
                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card3_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        # 新增圖像區塊
                        html.Div(
                            children=[
                                html.Img(
                                    src=f'data:image/png;base64,{encoded_image}',
                                    className='zoomable',  # 添加放大鏡CSS類
                                    style={'width': '100%', 'height': 'auto'}  # 調整寬度為100%
                                ),
                            ],
                            style={
                                'padding': '20px',
                                'textAlign': 'center'
                            }
                        ),

                        # 新增文本區塊
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

                        # 移除存檔按鈕和下載組件
                        # html.Div([
                        #     dbc.Button("存檔", id='save-tab1', color="light", style={'margin-top': '20px'}),
                        #     dcc.Download(id="download-tab1")
                        # ], style={'textAlign': 'center', 'padding': '20px'})
                    ])
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )

def create_loss_analysis_card():
    # 讀取並處理數據
    df = load_data(DATA_FILE_PATH)
    if df.empty:
        print("DataFrame is empty in create_loss_analysis_card.")  # 調試輸出

    # 定義需要標記的條件
    highlight_conditions = [
        {'溫度': 'Tj = 25℃', 'IC (A)': 447.51},
        {'溫度': 'Tj = 25℃', 'IC (A)': 819.11},
        {'溫度': 'Tj = 150℃', 'IC (A)': 451.644},
        {'溫度': 'Tj = 150℃', 'IC (A)': 823.824},
        {'溫度': 'Tj = 175℃', 'IC (A)': 450.026},
        {'溫度': 'Tj = 175℃', 'IC (A)': 824.324},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{溫度}} = "{cond["溫度"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightblue',
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams", className="card-title"),
            html.H5("Temperature IC-VCE Curve", style={'textAlign': 'left', 'marginBottom': '20px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'VGE = 15V, IC = f(VCE)', 'value': 'VGE_15V_IC_f_VCE'}
                        ],
                        value='VGE_15V_IC_f_VCE',  # 默認選擇
                        id='icvce-radio1',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image1',
                        src='/assets/ICVCE15V.png',  # 默認圖片
                        style={'width': '70%', 'height': 'auto'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title1', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 溫度選擇與範圍滑桿
            html.Div([
                html.Label("選擇溫度 (圖表)", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph',
                    options=[
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'},
                        {'label': '所有溫度', 'value': 'all_temperatures'}  # 將「所有溫度」設為選項
                    ],
                    value='all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 IC 範圍 (A)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider',
                    min=-100,  # 修改為 -100
                    max=1800,  # 假設最大IC值為1800A
                    step=10,  # 設置步長為10A
                    marks={i: str(i) for i in range(0, 1801, 100)},
                    value=[0, 1800],
                    allowCross=False,
                    className='ic-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_ic-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 VCE 範圍 (V)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider',
                    min=-1,  # 修改為 -1
                    max=4,  # 調整為4V
                    step=0.1,  # 設置步長為0.1V
                    marks={i: str(i) for i in range(-1, 5)},  # 標記從-1到4
                    value=[-1, 4],  # 默認值為-1到4V
                    allowCross=False,
                    className='vce-slider'  # 自定義CSS類名
                ),
                html.Div(id='loss_vce-output', style={'margin-top': '10px'})
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表
            dcc.Graph(id='loss_loss-graph', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                              'displaylogo': False  # 是否隱藏 Plotly 的 logo
                              }
                      ),  # 損耗分析圖表
            # 溫度選擇表格
            html.Div([
                html.Label("選擇溫度", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table',
                    options=[
                        {'label': '所有溫度', 'value': 'all_temperatures'},  # 將「所有溫度」設為選項
                        {'label': 'Tj = 25℃', 'value': 'Tj_25C_IC_f_VCE'},
                        {'label': 'Tj = 150℃', 'value': 'Tj_150C_IC_f_VCE'},
                        {'label': 'Tj = 175℃', 'value': 'Tj_175C_IC_f_VCE'}
                    ],
                    value='all_temperatures',  # 默認顯示所有溫度
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格
            dash_table.DataTable(
                id='loss_loss-table',
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',  # 啟用過濾功能
                columns=[  # 預設欄位，稍後動態更新
                    {"name": "Index", "id": "編號"},
                    {"name": "Temperature (°C)", "id": "溫度"},
                    {"name": "IC (A)", "id": "IC (A)"},
                    {"name": "VCE (V)", "id": "VCE (V)"}
                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional
            ),
            # Card1_新增 Tabs 區塊
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析", className="card-title"),
            dcc.Tabs(id='additional-tabs', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        # 新增圖像區塊
                        html.Div(
                            children=[
                                html.Img(
                                    src=f'data:image/png;base64,{encoded_image_tab1}',
                                    className='zoomable',  # 添加放大鏡CSS類
                                    style={'width': '100%', 'height': 'auto'}  # 調整寬度為100%
                                ),
                            ],
                            style={
                                'padding': '20px',
                                'textAlign': 'center'
                            }
                        ),

                        # 新增文本區塊
                        html.Div(
                            children=[
                                # 定義主標題
                                html.H3(
                                    children=['I-V特性曲線圖表中，具體分析的項目包括：'],
                                    style={
                                        'margin-bottom': '0px',
                                        'color': '#02294f',  # 深藍色
                                        'margin-top': '20px',
                                        'font-size': '20px',  # 調整字體大小
                                        'font-weight': 'bold'  # 加粗
                                    }
                                ),
                                # 定義段落並允許斷行
                                html.P(
                                    children=[
                                        "線性區與飽和區的劃分：",
                                        html.Br(),
                                        "線性區域：當電壓VCE較低時，IGBT處於線性區域，電流IC與VCE的關係基本線性。該區域的斜率代表輸出電阻特性。",
                                        html.Br(),
                                        "飽和區域：當VCE增加到一定值（飽和門檻），IGBT進入飽和狀態，IC與VCE之間的變化變得非線性。",
                                    ],
                                    style={
                                        'white-space': 'pre-line',  # 允許斷行
                                        'color': '#333333',  # 深灰色
                                        'margin-top': '0px',
                                        'margin-bottom': '20px',
                                        'font-size': '14px'  # 調整字體大小
                                    }
                                ),
                                # 能量E的計算
                                html.H3(
                                    children=['能量E的計算：'],
                                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.Details([
                                    html.Summary(
                                        '顯示計算公式',
                                        style={
                                            'font-size': '16px',
                                            'font-weight': 'bold',
                                            'color': '#003366',
                                        }
                                    ),
                                    dcc.Markdown(r'''
                                        線性區域和飽和區域能量E：這些值是通過對對應區域的電壓和電流積分求得，具體公式：

                                        $$
                                        E = \int_{V_{\text{start}}}^{V_{\text{end}}} IC \cdot dV_{CE}
                                        $$

                                        其中，$V_{\text{start}}$ 和 $V_{\text{end}}$ 分別代表積分的起始和結束電壓。這是對應區域的能量耗散。
                                    ''', mathjax=True)
                                ]),
                                # 斜率的計算
                                html.H3(
                                    children=['斜率的計算：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.P(
                                    children=[
                                        "在線性區域中計算斜率：斜率（m）可以通過取兩個點的電流和電壓值計算，具體公式：",
                                        html.Br(),
                                        dcc.Markdown(r'''
                                            $$
                                            m = \frac{\Delta IC}{\Delta V_{CE}}
                                            $$
                                            這個斜率代表了元件的電導率。
                                        ''', mathjax=True)
                                    ],
                                    style={'font-size': '14px', 'color': '#333333'}
                                ),
                                # 擬合曲線與決定係數R²
                                html.H3(
                                    children=['擬合曲線與決定係數R²：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.P(
                                    children=[
                                        "擬合曲線使用多項式或其他擬合方法，以求得電流與電壓的擬合方程。使用的擬合算法例如線性回歸或多項式回歸，並計算決定係數R²來評估擬合的準確性。",
                                        html.Br(),
                                        "例如，假設使用二次多項式擬合，擬合方程可以表示為：",
                                        html.Br(),
                                        dcc.Markdown(r'''
                                            $$
                                            IC = a \cdot V_{CE}^2 + b \cdot V_{CE} + c
                                            $$
                                            再通過最小二乘法來求得參數 $a, b, c$。
                                        ''', mathjax=True),
                                        html.Br(),
                                        "這些分析幫助我們理解IGBT在不同結溫和工作狀態下的性能，並為進一步優化和設計提供參考。"
                                    ],
                                    style={'font-size': '14px', 'color': '#333333'}
                                ),
                                # 新增的 R² 說明段落
                                html.H3(
                                    children=['R²（決定係數）的詳細說明：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.Details([
                                    html.Summary(
                                        '顯示 R² 的解釋',
                                        style={
                                            'font-size': '14px',
                                            'font-weight': 'bold',
                                            'color': '#003366',
                                        }
                                    ),
                                    dcc.Markdown(r'''
                                        **R²（決定係數）** 是用來評估擬合曲線的準確度的指標。R²的值範圍從 0 到 1：

                                        - **R² = 1**：代表擬合非常完美，所有數據點都精確地落在擬合曲線上。
                                        - **R² 越接近 1**：表示擬合曲線越能解釋數據變化，準確度越高。
                                        - **R² 接近 0**：表示擬合曲線無法很好地解釋數據變化，擬合效果較差。

                                        在圖中，每條擬合曲線的旁邊都有標記R²值，這些值用來顯示該曲線對數據的擬合程度。例如，圖中顯示的R²值為 1.000，說明這些擬合曲線對應的數據點幾乎完全匹配，擬合效果非常好。

                                        **R²的計算公式如下：**

                                        $$
                                        R^2 = 1 - \frac{\sum{(y_i - \hat{y}_i)^2}}{\sum{(y_i - \overline{y})^2}}
                                        $$

                                        其中：

                                        - $y_i$ 是實際數據點值。
                                        - $\hat{y}_i$ 是擬合曲線上的預測值。
                                        - $\overline{y}$ 是實際數據的平均值。

                                        這個公式用來衡量擬合的誤差（分子部分）與總變異（分母部分）之間的比率。當擬合誤差越小時，R²越接近1。
                                    ''', mathjax=True)
                                ]),
                            ],
                            style={'padding': '15px', 'font-size': '14px'}  # 全局縮小字體大小
                        ),

                        # 移除存檔按鈕和下載組件
                        # html.Div([
                        #     dbc.Button("存檔", id='save-tab1', color="light", style={'margin-top': '20px'}),
                        #     dcc.Download(id="download-tab1")
                        # ], style={'textAlign': 'center', 'padding': '20px'})
                    ])
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        # 圖像區塊
                        html.Div(
                            children=[
                                html.Img(
                                    src=f'data:image/png;base64,{encoded_image_tab2}',
                                    className='zoomable',  # 添加放大鏡CSS類
                                    style={'width': '90%', 'height': 'auto'}  # 調整寬度為90%
                                ),
                            ],
                            style={
                                'padding': '20px',
                                'textAlign': 'center'
                            }
                        ),

                        # 文本區塊
                        html.Div(
                            children=[
                                html.P(
                                    '圖表在三個不同結點溫度（25°C、150°C、175°C）下總能量損失，'
                                    '縱軸是能量損失（J），橫軸顯示的是結點溫度，每個條形柱代表一個特定溫度下的能量損失，'
                                    '並且每個柱形頂部標示了具體的能量損失值，紅色的虛線標示了平均能量損失值對比基準。'
                                ),
                                html.Ul([
                                    html.Li('25°C：總能量損失為 1148 J'),
                                    html.Li('150°C：總能量損失為 1230 J'),
                                    html.Li('175°C：總能量損失為 1312 J'),
                                    html.Li(
                                        '平均能量損失基準線：紅色虛線表示平均能量損失，大約為 1200 J，'
                                        '25°C 時的能量損失低於平均值，而 150°C 和 175°C 均超過了平均值。'
                                    )
                                ]),
                                html.H3('功率計算：',
                                        style={'font-size': '18px', 'font-weight': 'bold', 'color': '#003366'}),
                                dcc.Markdown(r'''
                                **功率計算公式**：

                                $$
                                P = V_{CE} \times IC
                                $$
                                ''', mathjax=True),
                                html.Details([
                                    html.Summary(
                                        '計算範例',
                                        style={'cursor': 'pointer', 'font-weight': 'bold'}
                                    ),
                                    dcc.Markdown(r'''
                                        25°C：
                                        $$
                                        P_{25} = 1.4 \times 820 = 1148 \, W
                                        $$

                                        150°C：
                                        $$
                                        P_{150} = 1.5 \times 820 = 1230 \, W
                                        $$

                                        175°C：
                                        $$
                                        P_{175} = 1.6 \times 820 = 1312 \, W
                                        $$
                                    ''', mathjax=True)
                                ]),
                                html.H3('能量損耗計算：',
                                        style={'font-size': '18px', 'font-weight': 'bold', 'color': '#003366'}),
                                dcc.Markdown(r'''
                                **能量損耗計算公式**：

                                $$
                                E = P \times t
                                $$
                                ''', mathjax=True),
                                html.Details([
                                    html.Summary(
                                        '計算範例',
                                        style={'cursor': 'pointer', 'font-weight': 'bold'}
                                    ),
                                    dcc.Markdown(r'''
                                        25°C：
                                        $$
                                        E_{25} = 1148 \, W \times 1 \, s = 1148 \, J
                                        $$

                                        150°C：
                                        $$
                                        E_{150} = 1230 \, W \times 1 \, s = 1230 \, J
                                        $$

                                        175°C：
                                        $$
                                        E_{175} = 1312 \, W \times 1 \, s = 1312 \, J
                                        $$
                                    ''', mathjax=True)
                                ]),
                                html.H3('能效分析',
                                        style={'font-size': '18px', 'font-weight': 'bold', 'color': '#003366'}),
                                dcc.Markdown(r'''
                                **能效計算公式**：

                                $$
                                \eta = \frac{E_{in} - E_{loss}}{E_{in}} \times 100\%
                                $$
                                ''', mathjax=True),
                                html.Details([
                                    html.Summary(
                                        '計算範例',
                                        style={'cursor': 'pointer', 'font-weight': 'bold'}
                                    ),
                                    dcc.Markdown(r'''
                                        假設在 25°C 時：
                                        $$
                                        E_{in} = 1500 \, J, \quad E_{loss} = 1148 \, J
                                        $$

                                        能效：
                                        $$
                                        \eta_{25} = \frac{1500 - 1148}{1500} \times 100\% = 23.47\%
                                        $$

                                        這表示系統在 25°C 時能有效利用 23.47% 的輸入能量。
                                    ''', mathjax=True)
                                ])
                            ],
                            style={'padding': '15px', 'font-size': '14px', 'line-height': '1.6'}
                        ),
                        # 移除存檔按鈕和下載組件
                        # html.Div([
                        #     dbc.Button("存檔", id='save-tab2', color="light", style={'margin-top': '20px'}),
                        #     dcc.Download(id="download-tab2")
                        # ], style={'textAlign': 'center', 'padding': '20px'})
                    ])
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )

# 新增的 Characteristics Diagrams2 卡片創建函數
def create_loss_analysis_card2():
    # 讀取並處理數據
    # 根據需求，這裡暫不讀取數據

    # 定義需要標記的條件（根據實際需求修改）
    highlight_conditions = [
        {'Voltage (V)': '11V', 'IC (A)': 443.24},
        {'Voltage (V)': '11V', 'IC (A)': 813.68},
        {'Voltage (V)': '13V', 'IC (A)': 500.00},
        {'Voltage (V)': '13V', 'IC (A)': 900.00},
        {'Voltage (V)': '15V', 'IC (A)': 500.00},
        {'Voltage (V)': '15V', 'IC (A)': 900.00},
        {'Voltage (V)': '17V', 'IC (A)': 500.00},
        {'Voltage (V)': '17V', 'IC (A)': 900.00},
        {'Voltage (V)': '19V', 'IC (A)': 500.00},
        {'Voltage (V)': '19V', 'IC (A)': 900.00},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{Voltage (V)}} = "{cond["Voltage (V)"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightgreen',  # 不同顏色以區分
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    return dbc.Card(
        dbc.CardBody([
            html.H5("Characteristics Diagrams2", className="card-title"),

            html.H5("Voltage IC-VCE Curve", style={'textAlign': 'left', 'marginBottom': '20px'}),

            # Radio 按鈕置中，並應用自定義 CSS 類
            dbc.Row([
                dbc.Col(
                    dbc.RadioItems(
                        options=[
                            {'label': 'Tj = 25℃, IC = f(VCE)', 'value': 'Tj_25C_IC_f_VCE'},
                            {'label': 'Tj = 150℃, IC = f(VCE)', 'value': 'Tj_150C_IC_f_VCE'}
                            # 如果需要更多選項，可以在這裡添加
                        ],
                        value='Tj_25C_IC_f_VCE',  # 默認選擇
                        id='icvce-radio2',
                        inline=True,
                        className='custom-radio'  # 添加自定義 CSS 類名
                    ),
                    width=12,
                    className='fixed-radio-container'  # 添加固定高度的容器類名
                )
            ], className="mb-3"),

            # 圖片顯示
            html.Div(
                children=[
                    html.Img(
                        id='icvce-image2',
                        src='/assets/ICVCE25.png',  # 默認圖片，將在回調中更新
                        style={'width': '70%', 'height': 'auto'}
                    ),
                ],
                style={
                    'padding': '20px',
                    'textAlign': 'center'
                }
            ),

            # 標題顯示在圖片下方
            html.Div(id='icvce-title2', style={'textAlign': 'center', 'fontSize': '20px', 'marginTop': '10px'}),

            # 電壓選擇與範圍滑桿（使用不同的ID）
            html.Div([
                html.Label("選擇電壓 (圖表)", style={'fontSize': '18px'}),  # 原有設置標籤名稱選擇IC, VCE (圖表)
                dcc.Dropdown(
                    id='loss_temperature-dropdown-graph2',  # 新的ID
                    options=[
                        {'label': '9V', 'value': 'IC_9V_VCE_9V'},
                        {'label': '11V', 'value': 'IC_11V_VCE_11V'},
                        {'label': '13V', 'value': 'IC_13V_VCE_13V'},
                        {'label': '15V', 'value': 'IC_15V_VCE_15V'},
                        {'label': '17V', 'value': 'IC_17V_VCE_17V'},
                        {'label': '19V', 'value': 'IC_19V_VCE_19V'},
                        {'label': '所有電壓', 'value': 'all_voltages'}  # 新增「所有電壓」選項
                    ],
                    value='all_voltages',  # 默認選擇「所有電壓」
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 IC 範圍 (A)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_ic-range-slider2',  # 新的ID
                    min=-100,  # 修改為 -100
                    max=1700,
                    step=10,
                    marks={i: str(i) for i in range(-100, 1701, 100)},
                    value=[-100, 1700],
                    allowCross=False,
                    className='ic-slider'
                ),
                html.Div(id='loss_ic-output2', style={'margin-top': '10px'})  # 新的ID
            ], style={'margin': '20px 0'}),
            html.Div([
                html.Label("選擇 VCE 範圍 (V)", style={'fontSize': '18px'}),
                dcc.RangeSlider(
                    id='loss_vce-range-slider2',  # 新的ID
                    min=-1,  # 修改為 -1
                    max=4,  # 調整為4V
                    step=0.1,  # 設置步長為0.1V
                    marks={i: str(i) for i in range(-1, 5)},  # 標記從-1到4
                    value=[-1, 4],  # 默認值為-1到4V
                    allowCross=False,
                    className='vce-slider'
                ),
                html.Div(id='loss_vce-output2', style={'margin-top': '10px'})  # 新的ID
            ], style={'margin': '20px 0'}),
            # 損耗分析圖表（使用不同的ID）
            dcc.Graph(id='loss_loss-graph2', style={'margin-bottom': '50px'},
                      config={'displayModeBar': False,  # 顯示工具列
                              'displaylogo': False  # 是否隱藏 Plotly 的 logo
                              }
                      ),
            # 電壓選擇表格
            html.Div([
                html.Label("選擇電壓", style={'fontSize': '18px'}),
                dcc.Dropdown(
                    id='loss_temperature-dropdown-table2',  # 新的ID
                    options=[
                        {'label': '9V', 'value': 'IC_9V_VCE_9V'},
                        {'label': '11V', 'value': 'IC_11V_VCE_11V'},
                        {'label': '13V', 'value': 'IC_13V_VCE_13V'},
                        {'label': '15V', 'value': 'IC_15V_VCE_15V'},
                        {'label': '17V', 'value': 'IC_17V_VCE_17V'},
                        {'label': '19V', 'value': 'IC_19V_VCE_19V'},
                        {'label': '所有電壓', 'value': 'all_voltages'}  # 新增「所有電壓」選項
                    ],
                    value='all_voltages',  # 默認選擇「所有電壓」
                    clearable=False
                ),
            ], style={'margin': '20px 0'}),
            # 損耗分析表格（使用不同的ID）
            dash_table.DataTable(
                id='loss_loss-table2',  # 新的ID
                style_table={'overflowX': 'auto'},
                page_size=30,
                filter_action='native',
                columns=[
                    {"name": "Index", "id": "編號"},
                    {"name": "Voltage (V)", "id": "Voltage (V)"},  # 修正欄位ID
                    {"name": "IC (A)", "id": "IC (A)"},
                    {"name": "VCE (V)", "id": "VCE (V)"}
                ],
                style_cell={
                    'fontFamily': 'Arial, sans-serif',  # 與其他字體一致
                    'fontSize': 17,  # 字體大小
                    'textAlign': 'center',  # 預設文本對齊方式
                    'padding': '5px'  # 單元格內邊距
                },
                style_data_conditional=style_data_conditional  # 使用新的樣式條件
            ),
            # Card2_新增 Tabs 區塊（可以根據需要修改）
            html.Hr(style={'margin': '20px 0'}),
            html.H5("相關分析2", className="card-title"),
            dcc.Tabs(id='additional-tabs2', value='tab-1', children=[
                dcc.Tab(label='Tab 1', value='tab-1', children=[
                    html.Div([
                        # 新增圖像區塊
                        html.Div(
                            children=[
                                html.Img(
                                    src=f'data:image/png;base64,{encoded_image_tab2}',  # 修改為 encoded_image_tab2
                                    className='zoomable',  # 添加放大鏡CSS類
                                    style={'width': '100%', 'height': 'auto'}
                                ),
                            ],
                            style={
                                'padding': '20px',
                                'textAlign': 'center'
                            }
                        ),

                        # 新增文本區塊
                        html.Div(
                            children=[
                                # 定義主標題
                                html.H3(
                                    children=['I-V特性曲線圖表中，具體分析的項目包括：'],
                                    style={
                                        'margin-bottom': '0px',
                                        'color': '#02294f',
                                        'margin-top': '20px',
                                        'font-size': '20px',
                                        'font-weight': 'bold'
                                    }
                                ),
                                # 定義段落並允許斷行
                                html.P(
                                    children=[
                                        "線性區與飽和區的劃分：",
                                        html.Br(),
                                        "線性區域：當電壓VCE較低時，IGBT處於線性區域，電流IC與VCE的關係基本線性。該區域的斜率代表輸出電阻特性。",
                                        html.Br(),
                                        "飽和區域：當VCE增加到一定值（飽和門檻），IGBT進入飽和狀態，IC與VCE之間的變化變得非線性。",
                                    ],
                                    style={
                                        'white-space': 'pre-line',
                                        'color': '#333333',
                                        'margin-top': '0px',
                                        'margin-bottom': '20px',
                                        'font-size': '14px'
                                    }
                                ),
                                # 能量E的計算
                                html.H3(
                                    children=['能量E的計算：'],
                                    style={'font-size': '20px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.Details([
                                    html.Summary(
                                        '顯示計算公式',
                                        style={
                                            'font-size': '16px',
                                            'font-weight': 'bold',
                                            'color': '#003366',
                                        }
                                    ),
                                    dcc.Markdown(r'''
                                        線性區域和飽和區域能量E：這些值是通過對對應區域的電壓和電流積分求得，具體公式：

                                        $$
                                        E = \int_{V_{\text{start}}}^{V_{\text{end}}} IC \cdot dV_{CE}
                                        $$

                                        其中，$V_{\text{start}}$ 和 $V_{\text{end}}$ 分別代表積分的起始和結束電壓。這是對應區域的能量耗散。
                                    ''', mathjax=True)
                                ]),
                                # 斜率的計算
                                html.H3(
                                    children=['斜率的計算：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.P(
                                    children=[
                                        "在線性區域中計算斜率：斜率（m）可以通過取兩個點的電流和電壓值計算，具體公式：",
                                        html.Br(),
                                        dcc.Markdown(r'''
                                            $$
                                            m = \frac{\Delta IC}{\Delta V_{CE}}
                                            $$
                                            這個斜率代表了元件的電導率。
                                        ''', mathjax=True)
                                    ],
                                    style={'font-size': '14px', 'color': '#333333'}
                                ),
                                # 擬合曲線與決定係數R²
                                html.H3(
                                    children=['擬合曲線與決定係數R²：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.P(
                                    children=[
                                        "擬合曲線使用多項式或其他擬合方法，以求得電流與電壓的擬合方程。使用的擬合算法例如線性回歸或多項式回歸，並計算決定係數R²來評估擬合的準確性。",
                                        html.Br(),
                                        "例如，假設使用二次多項式擬合，擬合方程可以表示為：",
                                        html.Br(),
                                        dcc.Markdown(r'''
                                            $$
                                            IC = a \cdot V_{CE}^2 + b \cdot V_{CE} + c
                                            $$
                                            再通過最小二乘法來求得參數 $a, b, c$。
                                        ''', mathjax=True),
                                        html.Br(),
                                        "這些分析幫助我們理解IGBT在不同結溫和工作狀態下的性能，並為進一步優化和設計提供參考。"
                                    ],
                                    style={'font-size': '14px', 'color': '#333333'}
                                ),
                                # 新增的 R² 說明段落
                                html.H3(
                                    children=['R²（決定係數）的詳細說明：'],
                                    style={'font-size': '16px', 'font-weight': 'bold', 'color': '#003366'}
                                ),
                                html.Details([
                                    html.Summary(
                                        '顯示 R² 的解釋',
                                        style={
                                            'font-size': '14px',
                                            'font-weight': 'bold',
                                            'color': '#003366',
                                        }
                                    ),
                                    dcc.Markdown(r'''
                                        **R²（決定係數）** 是用來評估擬合曲線的準確度的指標。R²的值範圍從 0 到 1：

                                        - **R² = 1**：代表擬合非常完美，所有數據點都精確地落在擬合曲線上。
                                        - **R² 越接近 1**：表示擬合曲線越能解釋數據變化，準確度越高。
                                        - **R² 接近 0**：表示擬合曲線無法很好地解釋數據變化，擬合效果較差。

                                        在圖中，每條擬合曲線的旁邊都有標記R²值，這些值用來顯示該曲線對數據的擬合程度。例如，圖中顯示的R²值為 1.000，說明這些擬合曲線對應的數據點幾乎完全匹配，擬合效果非常好。

                                        **R²的計算公式如下：**

                                        $$
                                        R^2 = 1 - \frac{\sum{(y_i - \hat{y}_i)^2}}{\sum{(y_i - \overline{y})^2}}
                                        $$

                                        其中：

                                        - $y_i$ 是實際數據點值。
                                        - $\hat{y}_i$ 是擬合曲線上的預測值。
                                        - $\overline{y}$ 是實際數據的平均值。

                                        這個公式用來衡量擬合的誤差（分子部分）與總變異（分母部分）之間的比率。當擬合誤差越小時，R²越接近1。
                                    ''', mathjax=True)
                                ]),
                            ],
                            style={'padding': '15px', 'font-size': '14px'}  # 全局縮小字體大小
                        ),

                        # 移除存檔按鈕和下載組件
                        # html.Div([
                        #     dbc.Button("存檔", id='save-tab1-2', color="light", style={'margin-top': '20px'}),
                        #     dcc.Download(id="download-tab1-2")
                        # ], style={'textAlign': 'center', 'padding': '20px'})
                    ])
                ]),
                dcc.Tab(label='Tab 2', value='tab-2', children=[
                    html.Div([
                        html.P("這是頁籤二的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 3', value='tab-3', children=[
                    html.Div([
                        html.P("這是頁籤三的內容。"),
                        dbc.Button("存檔", id='save-tab3', color="success"),
                        dcc.Download(id="download-tab3")
                    ], style={'padding': '20px'})
                ]),
                dcc.Tab(label='Tab 4', value='tab-4', children=[
                    html.Div([
                        html.P("這是頁籤四的內容。"),
                        dbc.Button("存檔", id='save-tab4', color="success"),
                        dcc.Download(id="download-tab4")
                    ], style={'padding': '20px'})
                ]),
            ])
        ]),
        className="shadow-sm border mb-4",
        style={'padding': '10px'}
    )



# 定義佈局
app.layout = html.Div([
    # 第一個區塊：標題區
    html.Div([
        html.H1("Diagrams Analysis", style={'textAlign': 'center', 'marginBottom': '-3px' , 'fontSize': '28px','color': '#495057' }),
        #html.Hr(style={'borderWidth': '2px'}),  # 添加分隔線
    ], style={'padding': '20px', 'backgroundColor': '#f8f9fa'}),  # 添加背景顏色

    # 第二個區塊：下拉選單區
    dbc.Row([
        dbc.Col([
            # 使用單一 Row 包含四個 Column，以減少間距
            dbc.Row([
                dbc.Col([
                    html.Label("PRODUCT"),
                    dcc.Dropdown(
                        id='category1-dropdown',
                        options=[
                            {'label': 'HPD IGBT', 'value': 'HPD IGBT'},
                            {'label': 'IGBT ED3', 'value': 'IGBT ED3'},
                            {'label': 'IGBT EP2', 'value': 'IGBT EP2'},
                            {'label': 'SiC ED3', 'value': 'SiC ED3'},
                            {'label': 'SiC HPD', 'value': 'SiC HPD'},
                            {'label': 'SiC SSC', 'value': 'SiC SSC'}
                        ],
                        value='HPD IGBT',
                        clearable=False,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                ], width=3, style={'paddingRight': '10px'}),

                dbc.Col([
                    html.Label("POWER"),
                    dcc.Dropdown(
                        id='category2-dropdown',
                        options=[],  # 初始為空，根據 PRODUCT 更新
                        clearable=False,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                ], width=3, style={'paddingRight': '10px'}),

                dbc.Col([
                    html.Label("DEVICE TYPE"),
                    dcc.Dropdown(
                        id='device-type-dropdown',
                        options=[],  # 初始為空，根據 POWER 更新
                        clearable=False,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                ], width=3, style={'paddingRight': '10px'}),

                dbc.Col([
                    html.Label("PROPERTY"),
                    dcc.Dropdown(
                        id='property-dropdown',
                        options=[],  # 初始為空，根據 DEVICE TYPE 更新
                        disabled=True,
                        clearable=False,
                        style={'marginBottom': '10px', 'width': '100%'}
                    ),
                ], width=3),
            ], className="g-1"),  # 最小化 gutter
        ], width=12),
    ], style={'padding': '20px', 'backgroundColor': '#f1f1f1'}),

    # 主要卡片區域
    #dbc.Row([
        # 使用 justify="center" 來置中子列
        #dbc.Row([
           # dbc.Col([
                # 損耗分析卡片
              #  create_loss_analysis_card()
           # ], md=5, className='mb-4'),  # 半寬

           # dbc.Col([
                # 新增的損耗分析卡片
               # create_loss_analysis_card2()
          #  ], md=5, className='mb-4')  # 半寬
       # ], justify="center")  # 置中對齊
   # ], className="mb-4"),

    dbc.Row([
        dbc.Col(
            html.Div(id='cards-container'),  # 動態容器
            width=12
        )
    ], className="mb-4"),

    # 新增的額外 Tabs 區塊
    # (已經在 create_loss_analysis_card 和 create_loss_analysis_card2 中定義，無需再次定義)
])

# 根據 PRODUCT 更新 POWER 選項的回調函數
@app.callback(
    Output('category2-dropdown', 'options'),
    Input('category1-dropdown', 'value')
)
def update_power_options(selected_product):
    print(f"Selected PRODUCT: {selected_product}")  # 調試輸出
    power_options = {
        'HPD IGBT': [
            {'label': '750V820A', 'value': '750V820A'},
            {'label': '750V550A', 'value': '750V550A'},
            {'label': '1200V820A', 'value': '1200V820A'}
        ],
        'IGBT ED3': [
            {'label': '1200V450A', 'value': '1200V450A'},
            {'label': '1200V600A', 'value': '1200V600A'}
        ],
        'IGBT EP2': [
            {'label': '1200V75A', 'value': '1200V75A'}
        ],
        'SiC ED3': [
            {'label': '1200V450A', 'value': '1200V450A'},
            {'label': '1200V600A', 'value': '1200V600A'}
        ],
        'SiC HPD': [
            {'label': '1200V400A', 'value': '1200V400A'}
        ],
        'SiC SSC': [
            {'label': '1200V600A', 'value': '1200V600A'}
        ]
    }
    options = power_options.get(selected_product, [])
    print(f"Updated POWER options: {options}")  # 調試輸出
    return options

# 根據 POWER 更新 DEVICE TYPE 選項
@app.callback(
    Output('device-type-dropdown', 'options'),
    Input('category2-dropdown', 'value')
)
def update_device_type_options(selected_power):
    print(f"Selected POWER: {selected_power}")  # 調試輸出
    if selected_power:
        device_options = [
            {'label': 'IGBT', 'value': 'IGBT'},
            {'label': 'Diode', 'value': 'Diode'},
            {'label': 'ROSBA', 'value': 'ROSBA'},
            {'label': 'NTC', 'value': 'NTC'}
        ]
        print(f"Updated DEVICE TYPE options: {device_options}")  # 調試輸出
        return device_options
    else:
        print("No POWER selected.")  # 調試輸出
        return []

# 根據 DEVICE TYPE 更新 PROPERTY 選項的回調函數
@app.callback(
    [Output('property-dropdown', 'options'),
     Output('property-dropdown', 'disabled')],
    Input('device-type-dropdown', 'value')
)
def update_property_options(selected_device_type):
    print(f"Selected DEVICE TYPE: {selected_device_type}")  # 調試輸出
    if selected_device_type == 'IGBT':
        property_options = [
            {'label': 'IC, VCE', 'value': 'IC_VCE'},
            {'label': 'IF, VF', 'value': 'IF_VF'},
            {'label': 'Eon, Eoff (IC)', 'value': 'Eon_Eoff_IC'},
            {'label': 'Eon, Eoff (RG)', 'value': 'Eon_Eoff_RG'},
            {'label': 'Erec (RG)', 'value': 'Erec_RG'},
            {'label': 'VGE, QG', 'value': 'VGE_QG'},
            {'label': 'Zth, Tp', 'value': 'Zth_Tp'}
        ]
    elif selected_device_type == 'Diode':
        property_options = [
            {'label': 'IV, VF', 'value': 'IV_VF'},
            {'label': 'EREC (IC)', 'value': 'EREC_IC'},
            {'label': 'EREC (RG)', 'value': 'EREC_RG'},
            {'label': 'Zth, TP', 'value': 'Zth_TP'}
        ]
    elif selected_device_type == 'ROSBA':
        property_options = [
            {'label': 'ROSBA', 'value': 'ROSBA'}
        ]
    elif selected_device_type == 'NTC':
        property_options = [
            {'label': 'NTC', 'value': 'NTC'}
        ]
    else:
        property_options = []

    if property_options:
        print(f"Updated PROPERTY options: {property_options}")  # 調試輸出
        return property_options, False
    else:
        print("No DEVICE TYPE selected.")  # 調試輸出
        return [], True

# 根據 property-dropdown 更新主要卡片區域


@app.callback(
    Output('cards-container', 'children'),
    Input('property-dropdown', 'value')
)
def update_cards(selected_property):
    print(f"Selected PROPERTY: {selected_property}")  # 調試輸出
    if selected_property == 'IF_VF':
        print("Displaying create_loss_analysis_card3")  # 調試輸出
        return dbc.Row([
            dbc.Col(
                create_loss_analysis_card3(),
                md=5,
                className='mb-4'
            )
        ], justify="center")  # 置中對齊
    elif selected_property == 'Eon_Eoff_IC':
            print("Displaying create_loss_analysis_card4")  # 調試輸出
            return dbc.Row([
                dbc.Col(
                    create_loss_analysis_card4(),
                    md=5,
                    className='mb-4'
                )
            ], justify="center")  # 置中對齊
    elif selected_property == 'Eon_Eoff_RG':
            print("Displaying create_loss_analysis_card5")  # 調試輸出
            return dbc.Row([
                dbc.Col(
                    create_loss_analysis_card5(),
                    md=5,
                    className='mb-4'
                )
            ], justify="center")  # 置中對齊
    elif selected_property == 'Erec_RG':
            print("Displaying create_loss_analysis_card6")  # 調試輸出
            return dbc.Row([
                dbc.Col(
                    create_loss_analysis_card6(),
                    md=5,
                    className='mb-4'
                )
            ], justify="center")  # 置中對齊
    elif selected_property == 'VGE_QG':
            print("Displaying create_loss_analysis_card7")  # 調試輸出
            return dbc.Row([
                dbc.Col(
                    create_loss_analysis_card7(),
                    md=5,
                    className='mb-4'
                )
            ], justify="center")  # 置中對齊
    elif selected_property == 'Zth_Tp':
            print("Displaying create_loss_analysis_card8")  # 調試輸出Card_8
            return dbc.Row([
                dbc.Col(
                    create_loss_analysis_card8(),
                    md=5,
                    className='mb-4'
                )
            ], justify="center")  # 置中對齊Zth_Tp
    else:
        print("Displaying create_loss_analysis_card and create_loss_analysis_card2")  # 調試輸出
        return dbc.Row([
            dbc.Col(
                create_loss_analysis_card(),
                md=5,
                className='mb-4'
            ),
            dbc.Col(
                create_loss_analysis_card2(),
                md=5,
                className='mb-4'
            )
        ], justify="center")  # 置中對齊






 # 750V820AZTH_IGBT_M,create_loss_analysis_card8(),update_loss_analysis8()
@app.callback(
    [Output('zth-graph8', 'figure'),
     Output('zth-table8', 'data'),
     Output('zth-table8', 'columns')],
    [Input('zth-radio8', 'value'),
     Input('zth-time-slider8', 'value')]
)
def update_loss_analysis8(selected_radio, time_range):
    """
    根據 selected_radio (ZTH_IGBT / ZTH_DIODE 等) 與 time_range
    更新圖表與表格
    """
    df = load_data_zth(DATA_FILE_PATH8)
    if df.empty:
        # 回傳空圖
        return go.Figure(), [], []

    # 1) 篩選資料：根據 time_range
    #   time_range 可能是 [-6, 1] 代表要顯示 1e-6 ~ 1e1 之間
    t_min = 10**(time_range[0])  # 例如 1e-6
    t_max = 10**(time_range[1])  # 例如 1e1
    df_filtered = df[(df['t [s]'] >= t_min) & (df['t [s]'] <= t_max)]

    # 2) 繪製圖表
    fig = go.Figure()
    # 假設要畫 「t [s]」 vs 「Zth(t)」
    fig.add_trace(go.Scatter(
        x=df_filtered['t [s]'],
        y=df_filtered['Zth (t)'],
        mode='lines+markers',
        name='Zth'
    ))
    # 可視情況繪製其它曲線 (如 ΔTj(t))

    fig.update_layout(
        title=f"Zth vs Time ({selected_radio})",
        xaxis_type='log',
        yaxis_type='log',
        xaxis_title="Time t [s]",
        yaxis_title="Zth (K/W)",
        template='plotly_white',
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)'
        )
    )

    # 3) 準備表格資料
    #   依需求挑欄位顯示
    columns = [
        {"name": "t [s]", "id": "t [s]"},
        {"name": "Zth (t)", "id": "Zth (t)"},
        {"name": "ΔTj (t)", "id": "ΔTj (t)"},
        # 也可自行增減
    ]
    # 要先確認 df_filtered 中是否含有這些欄位
    table_data = df_filtered.to_dict('records')

    return fig, table_data, columns


#++++
 # 750V820AGATECHARGE_L,create_loss_analysis_card7(),update_loss_analysis7()
@app.callback(
    [Output('loss_loss-graph7', 'figure'),
     Output('loss_loss-table7', 'data'),
     Output('loss_loss-table7', 'columns')],
    [Input('loss_temperature-dropdown-graph7', 'value'),
     Input('loss_ic-range-slider7', 'value'),
     Input('loss_vce-range-slider7', 'value'),
     Input('loss_temperature-dropdown-table7', 'value')]
)
def update_loss_analysis7(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis7 triggered with: selected_temp_graph={selected_temp_graph}, QG_range={ic_range}, VCE_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH7)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "QG (μC)", "id": "QG (μC)"},
            {"name": "VCE (V)", "id": "VCE (V)"},

        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df
    print("U4-2305.")  # 調試輸出
    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    #for temp in ['25℃', '150℃', '175℃']:
    for temp in ['25℃']:
        qg_col = f'VGE(V)_{temp}'
        print(f"U4 qg_col: {qg_col}")
        vce_col = f'QG(μC)_{temp}'  # Eon card6
        print(f"U4 Vce_col: {vce_col}")
        #vce_col2 = f'Eoff(mJ)_{temp}'  # Eoff card6
        #print(f"U4 Eoff_col: {vce_col2}")
    if qg_col in df_filtered.columns and vce_col in df_filtered.columns:
            conditions.append(
                (df_filtered[qg_col] >= ic_range[0]) & (df_filtered[qg_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
                #(df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
    )

    if selected_temp_graph == 'ifvf_all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for ifvf_all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'

        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            QG_col = f'QG(μC)_{temp_str}'
            VGE_col = f'VGE(V)_{temp_str}'
            # vce_col2 = f'Eoff(mJ)_{temp_str}'
            # if qg_col in df_filtered.columns and QG_col in df_filtered.columns and VGE_col1 in df_filtered.columns:
            if VGE_col in df_filtered.columns and QG_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[QG_col] >= ic_range[0]) & (df_filtered[QG_col] <= ic_range[1]) &
                    (df_filtered[VGE_col] >= vce_range[0]) & (df_filtered[VGE_col] <= vce_range[1])
                    # (df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
                    ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {QG_col} and/or {VGE_col} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    if df_filtered.empty:
        print("Filtered DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "QG (μC)", "id": "QG (μC)"},
            {"name": "VGE (V)", "id": "VGE (V)"}
            #{"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['QG(μC)_25℃'].tolist(),
            'VCE': df_filtered['VGE(V)_25℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['QG(μC)_25℃'].tolist(),
            'VCE': df_filtered['VGE(V)_25℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['QG(μC)_25℃'].tolist(),
            'VCE': df_filtered['VGE(V)_25℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點（交換 x 和 y）
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 447.51, 'y': 1.1547, 'text': "450A<br>RG: 447.51<br>EREC: 1.1547"},
            {'x': 819.11, 'y': 1.3847, 'text': "820A<br>RG: 819.11<br>EREC: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 451.644, 'y': 1.263, 'text': "450A<br>RG: 451.644<br>EREC: 1.263"},
            {'x': 823.824, 'y': 1.678, 'text': "820A<br>RG: 823.824<br>EREC: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 450.026, 'y': 1.303, 'text': "450A<br>RG: 450.026<br>EREC: 1.303"},
            {'x': 824.324, 'y': 1.764, 'text': "820A<br>RG: 824.324<br>EREC: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'ifvf_all_temperatures' or temp_key == selected_temp_graph:
            # 確保有數據
            if not data['Temperature']:
                print(f"No data for {temp_key}, skipping.")
                continue

            # 設置圖表模式
            if selected_temp_graph == 'ifvf_all_temperatures':
                mode_vce = 'lines'  # 不顯示標記點
                #mode_vce2 = 'lines'  # 不顯示標記點
            else:
                mode_vce = 'lines+markers'  # 顯示標記點
                #mode_vce2 = 'lines+markers'  # 顯示標記點

            # 添加 VCE (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE'],  # 交換後的 Y 軸數據
                mode=mode_vce,
                name=f"{data['Temperature'][0]} QG",
                line=dict(color=color_mapping[temp_key], width=2, dash='solid'),
                marker=dict(size=6)
            ))

            # 添加 VCE2 (V) 曲線
            #fig.add_trace(go.Scatter(
                #x=data['IC'],  # 交換後的 X 軸數據
                #y=data['VCE2'],  # 交換後的 Y 軸數據
                #mode=mode_vce2,
                #name=f"{data['Temperature'][0]} VCE2",
                #line=dict(color=color_mapping[temp_key], width=2, dash='dash'),  # 使用虛線區分
                #marker=dict(size=6)
            #))

            # **新增：僅在非「所有溫度」時添加標註（交換 x 和 y）**
            if selected_temp_graph != 'ifvf_all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局（更新標題和軸標籤）
    if selected_temp_graph != 'ifvf_all_temperatures':
        title = f"Eon, Eoff vs RG for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "VGE vs QG"  # 更新標題

    fig.update_layout(
        title=title,
        xaxis_title="QG (μC)",  # 更新 X 軸標籤
        yaxis_title="VGE (V)",  # 更新 Y 軸標籤
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=0.2,  # 設置刻度間隔為200
            range=[0, 2],  # 調整X軸範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=2,  # 根據新的 Y 軸數據調整刻度間隔
            tick0=-8,  # 設置起始刻度為0
            range=[-8, 20],  # 調整範圍為0到140V以匹配滑桿
            zeroline=False,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'ifvf_all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            valid_data = [
                {
                    '編號': idx + 1 + len(table_data),
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}",
                    #'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce) in enumerate(zip(data['Temperature'], data['IC'], data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            table_data = [
                {
                    '編號': idx + 1,
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}"
                    #'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
        else:
            table_data = []

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "QG(μC)", "id": "IC (A)"},
        {"name": "VGE (V)", "id": "VCE (V)"}
        #{"name": "EOFF (MJ)", "id": "VCE2 (V)"}
    ]

    fig.add_hline(
        y=-8,
        line_color='black',
        line_width=3,
        #annotation_text=None  # 或乾脆不寫此參數
    )

    return fig, table_data, columns






#++++
 # 750V820AEREC(RG)_H,create_loss_analysis_card6(),update_loss_analysis6()
@app.callback(
    [Output('loss_loss-graph6', 'figure'),
     Output('loss_loss-table6', 'data'),
     Output('loss_loss-table6', 'columns')],
    [Input('loss_temperature-dropdown-graph6', 'value'),
     Input('loss_ic-range-slider6', 'value'),
     Input('loss_vce-range-slider6', 'value'),
     Input('loss_temperature-dropdown-table6', 'value')]
)
def update_loss_analysis6(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis6 triggered with: selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, erec_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH6)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "RG (Ω)", "id": "RG (Ω)"},
            {"name": "EREC (mJ)", "id": "EREC (mJ)"},

        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df
    print("U4-2305.")  # 調試輸出
    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    for temp in ['25℃', '150℃', '175℃']:
        rg_col = f'RG_{temp}'
        print(f"U4 rg_col: {rg_col}")
        erec_col = f'Erec(mJ)_{temp}'  # Eon card6
        print(f"U4 Erec_col: {erec_col}")
        #vce_col2 = f'Eoff(mJ)_{temp}'  # Eoff card6
        #print(f"U4 Eoff_col: {vce_col2}")
    if rg_col in df_filtered.columns and erec_col in df_filtered.columns:
            conditions.append(
                (df_filtered[rg_col] >= ic_range[0]) & (df_filtered[rg_col] <= ic_range[1]) &
                (df_filtered[erec_col] >= vce_range[0]) & (df_filtered[erec_col] <= vce_range[1])
                #(df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
    )

    if selected_temp_graph == 'ifvf_all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for ifvf_all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'
        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            RG_col = f'RG(Ω)_{temp_str}'
            EREC_col = f'EREC(mJ)_{temp_str}'
            #vce_col2 = f'Eoff(mJ)_{temp_str}'
            if rg_col in df_filtered.columns and RG_col in df_filtered.columns and EREC_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[rg_col] >= ic_range[0]) & (df_filtered[rg_col] <= ic_range[1]) &
                    (df_filtered[EREC_col] >= vce_range[0]) & (df_filtered[EREC_col] <= vce_range[1])
                    #(df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {rg_col} and/or {erec_col} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    if df_filtered.empty:
        print("Filtered DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "RG (Ω)", "id": "RG (Ω)"},
            {"name": "EREC (mJ)", "id": "EREC (mJ)"}
            #{"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['RG_25℃'].tolist(),
            'VCE': df_filtered['Erec(mJ)_25℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['RG_150℃'].tolist(),
            'VCE': df_filtered['Erec(mJ)_150℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['RG_175℃'].tolist(),
            'VCE': df_filtered['Erec(mJ)_175℃'].tolist(),
            #'VCE2': df_filtered['Eoff(mJ)_175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點（交換 x 和 y）
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 447.51, 'y': 1.1547, 'text': "450A<br>RG: 447.51<br>EREC: 1.1547"},
            {'x': 819.11, 'y': 1.3847, 'text': "820A<br>RG: 819.11<br>EREC: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 451.644, 'y': 1.263, 'text': "450A<br>RG: 451.644<br>EREC: 1.263"},
            {'x': 823.824, 'y': 1.678, 'text': "820A<br>RG: 823.824<br>EREC: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 450.026, 'y': 1.303, 'text': "450A<br>RG: 450.026<br>EREC: 1.303"},
            {'x': 824.324, 'y': 1.764, 'text': "820A<br>RG: 824.324<br>EREC: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'ifvf_all_temperatures' or temp_key == selected_temp_graph:
            # 確保有數據
            if not data['Temperature']:
                print(f"No data for {temp_key}, skipping.")
                continue

            # 設置圖表模式
            if selected_temp_graph == 'ifvf_all_temperatures':
                mode_vce = 'lines'  # 不顯示標記點
                #mode_vce2 = 'lines'  # 不顯示標記點
            else:
                mode_vce = 'lines+markers'  # 顯示標記點
                #mode_vce2 = 'lines+markers'  # 顯示標記點

            # 添加 VCE (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE'],  # 交換後的 Y 軸數據
                mode=mode_vce,
                name=f"{data['Temperature'][0]} RG",
                line=dict(color=color_mapping[temp_key], width=2, dash='solid'),
                marker=dict(size=6)
            ))

            # 添加 VCE2 (V) 曲線
            #fig.add_trace(go.Scatter(
                #x=data['IC'],  # 交換後的 X 軸數據
                #y=data['VCE2'],  # 交換後的 Y 軸數據
                #mode=mode_vce2,
                #name=f"{data['Temperature'][0]} VCE2",
                #line=dict(color=color_mapping[temp_key], width=2, dash='dash'),  # 使用虛線區分
                #marker=dict(size=6)
            #))

            # **新增：僅在非「所有溫度」時添加標註（交換 x 和 y）**
            if selected_temp_graph != 'ifvf_all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局（更新標題和軸標籤）
    if selected_temp_graph != 'ifvf_all_temperatures':
        title = f"Eon, Eoff vs RG for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "EREC vs RG"  # 更新標題

    fig.update_layout(
        title=title,
        xaxis_title="RG (Ω)",  # 更新 X 軸標籤
        yaxis_title="EREC (mJ)",  # 更新 Y 軸標籤
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=5,  # 設置刻度間隔為200
            range=[0, 25],  # 調整X軸範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=2,  # 根據新的 Y 軸數據調整刻度間隔
            tick0=0,  # 設置起始刻度為0
            range=[0, 15],  # 調整範圍為0到140V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'ifvf_all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            valid_data = [
                {
                    '編號': idx + 1 + len(table_data),
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}"
                    #'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce) in enumerate(zip(data['Temperature'], data['IC'], data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            table_data = [
                {
                    '編號': idx + 1,
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}"
                    #'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
        else:
            table_data = []

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "RG(Ω)", "id": "IC (A)"},
        {"name": "EREC (MJ)", "id": "VCE (V)"}
        #{"name": "EOFF (MJ)", "id": "VCE2 (V)"}
    ]

    return fig, table_data, columns



#++++
# 750V820AEon & Eoff(RG)_E,create_loss_analysis_card5(),update_loss_analysis5()
@app.callback(
    [Output('loss_loss-graph5', 'figure'),
     Output('loss_loss-table5', 'data'),
     Output('loss_loss-table5', 'columns')],
    [Input('loss_temperature-dropdown-graph5', 'value'),
     Input('loss_ic-range-slider5', 'value'),
     Input('loss_vce-range-slider5', 'value'),
     Input('loss_temperature-dropdown-table5', 'value')]
)
def update_loss_analysis5(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis4 triggered with: selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, vce_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH5)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"},
            {"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df
    print("U4-2305.")  # 調試輸出
    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    for temp in ['25℃', '150℃', '175℃']:
        ic_col = f'RG_{temp}'
        print(f"U4 ic_col: {ic_col}")
        vce_col = f'Eon(mJ)_{temp}'  # Eon card4
        print(f"U4 Eon_col: {vce_col}")
        vce_col2 = f'Eoff(mJ)_{temp}'  # Eoff card4
        print(f"U4 Eoff_col: {vce_col2}")
        if ic_col in df_filtered.columns and vce_col in df_filtered.columns and vce_col2 in df_filtered.columns:
            conditions.append(
                (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1]) &
                (df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
            )

    if selected_temp_graph == 'ifvf_all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for ifvf_all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'
        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            ic_col = f'IC(A)_{temp_str}'
            vce_col = f'Eon(mJ)_{temp_str}'
            vce_col2 = f'Eoff(mJ)_{temp_str}'
            if ic_col in df_filtered.columns and vce_col in df_filtered.columns and vce_col2 in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                    (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1]) &
                    (df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {ic_col} and/or {vce_col} and/or {vce_col2} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    if df_filtered.empty:
        print("Filtered DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"},
            {"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['RG_25℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_25℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['RG_150℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_150℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['RG_175℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_175℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點（交換 x 和 y）
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 447.51, 'y': 1.1547, 'text': "450A<br>IC: 447.51<br>VCE: 1.1547"},
            {'x': 819.11, 'y': 1.3847, 'text': "820A<br>IC: 819.11<br>VCE: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 451.644, 'y': 1.263, 'text': "450A<br>IC: 451.644<br>VCE: 1.263"},
            {'x': 823.824, 'y': 1.678, 'text': "820A<br>IC: 823.824<br>VCE: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 450.026, 'y': 1.303, 'text': "450A<br>IC: 450.026<br>VCE: 1.303"},
            {'x': 824.324, 'y': 1.764, 'text': "820A<br>IC: 824.324<br>VCE: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'ifvf_all_temperatures' or temp_key == selected_temp_graph:
            # 確保有數據
            if not data['Temperature']:
                print(f"No data for {temp_key}, skipping.")
                continue

            # 設置圖表模式
            if selected_temp_graph == 'ifvf_all_temperatures':
                mode_vce = 'lines'  # 不顯示標記點
                mode_vce2 = 'lines'  # 不顯示標記點
            else:
                mode_vce = 'lines+markers'  # 顯示標記點
                mode_vce2 = 'lines+markers'  # 顯示標記點

            # 添加 VCE (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE'],  # 交換後的 Y 軸數據
                mode=mode_vce,
                name=f"{data['Temperature'][0]} VCE",
                line=dict(color=color_mapping[temp_key], width=2, dash='solid'),
                marker=dict(size=6)
            ))

            # 添加 VCE2 (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE2'],  # 交換後的 Y 軸數據
                mode=mode_vce2,
                name=f"{data['Temperature'][0]} VCE2",
                line=dict(color=color_mapping[temp_key], width=2, dash='dash'),  # 使用虛線區分
                marker=dict(size=6)
            ))

            # **新增：僅在非「所有溫度」時添加標註（交換 x 和 y）**
            if selected_temp_graph != 'ifvf_all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局（更新標題和軸標籤）
    if selected_temp_graph != 'ifvf_all_temperatures':
        title = f"Eon, Eoff vs RG for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "Eon, Eoff vs RG"  # 更新標題

    fig.update_layout(
        title=title,
        xaxis_title="RG",  # 更新 X 軸標籤
        yaxis_title="E (mJ)",  # 更新 Y 軸標籤
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=5,  # 設置刻度間隔為200
            range=[0, 25],  # 調整X軸範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=20,  # 根據新的 Y 軸數據調整刻度間隔
            tick0=0,  # 設置起始刻度為0
            range=[0, 120],  # 調整範圍為0到140V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'ifvf_all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            valid_data = [
                {
                    '編號': idx + 1 + len(table_data),
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}",
                    'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce, vce2) in enumerate(zip(data['Temperature'], data['IC'], data['VCE'], data['VCE2']))
                if not (pd.isna(ic) or pd.isna(vce) or pd.isna(vce2))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            table_data = [
                {
                    '編號': idx + 1,
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}",
                    'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce, vce2) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE'], temp_data['VCE2']))
                if not (pd.isna(ic) or pd.isna(vce) or pd.isna(vce2))
            ]
        else:
            table_data = []

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "RG", "id": "IC (A)"},
        {"name": "EON (MJ)", "id": "VCE (V)"},
        {"name": "EOFF (MJ)", "id": "VCE2 (V)"}
    ]

    return fig, table_data, columns




# 750V820AEon & Eoff(IC)_E,create_loss_analysis_card4(),update_loss_analysis4()
@app.callback(
    [Output('loss_loss-graph4', 'figure'),
     Output('loss_loss-table4', 'data'),
     Output('loss_loss-table4', 'columns')],
    [Input('loss_temperature-dropdown-graph4', 'value'),
     Input('loss_ic-range-slider4', 'value'),
     Input('loss_vce-range-slider4', 'value'),
     Input('loss_temperature-dropdown-table4', 'value')]
)
def update_loss_analysis4(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis4 triggered with: selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, vce_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH4)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"},
            {"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df
    print("U4-2305.")  # 調試輸出
    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    for temp in ['25℃', '150℃', '175℃']:
        ic_col = f'IC(A)_{temp}'
        print(f"U4 ic_col: {ic_col}")
        vce_col = f'Eon(mJ)_{temp}'  # Eon card4
        print(f"U4 Eon_col: {vce_col}")
        vce_col2 = f'Eoff(mJ)_{temp}'  # Eoff card4
        print(f"U4 Eoff_col: {vce_col2}")
        if ic_col in df_filtered.columns and vce_col in df_filtered.columns and vce_col2 in df_filtered.columns:
            conditions.append(
                (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1]) &
                (df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
            )

    if selected_temp_graph == 'ifvf_all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for ifvf_all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'
        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            ic_col = f'IC(A)_{temp_str}'
            vce_col = f'Eon(mJ)_{temp_str}'
            vce_col2 = f'Eoff(mJ)_{temp_str}'
            if ic_col in df_filtered.columns and vce_col in df_filtered.columns and vce_col2 in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                    (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1]) &
                    (df_filtered[vce_col2] >= vce_range[0]) & (df_filtered[vce_col2] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {ic_col} and/or {vce_col} and/or {vce_col2} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    if df_filtered.empty:
        print("Filtered DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"},
            {"name": "VCE2 (V)", "id": "VCE2 (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['IC(A)_25℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_25℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['IC(A)_150℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_150℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['IC(A)_175℃'].tolist(),
            'VCE': df_filtered['Eon(mJ)_175℃'].tolist(),
            'VCE2': df_filtered['Eoff(mJ)_175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點（交換 x 和 y）
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 447.51, 'y': 1.1547, 'text': "450A<br>IC: 447.51<br>VCE: 1.1547"},
            {'x': 819.11, 'y': 1.3847, 'text': "820A<br>IC: 819.11<br>VCE: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 451.644, 'y': 1.263, 'text': "450A<br>IC: 451.644<br>VCE: 1.263"},
            {'x': 823.824, 'y': 1.678, 'text': "820A<br>IC: 823.824<br>VCE: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 450.026, 'y': 1.303, 'text': "450A<br>IC: 450.026<br>VCE: 1.303"},
            {'x': 824.324, 'y': 1.764, 'text': "820A<br>IC: 824.324<br>VCE: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'ifvf_all_temperatures' or temp_key == selected_temp_graph:
            # 確保有數據
            if not data['Temperature']:
                print(f"No data for {temp_key}, skipping.")
                continue

            # 設置圖表模式
            if selected_temp_graph == 'ifvf_all_temperatures':
                mode_vce = 'lines'  # 不顯示標記點
                mode_vce2 = 'lines'  # 不顯示標記點
            else:
                mode_vce = 'lines+markers'  # 顯示標記點
                mode_vce2 = 'lines+markers'  # 顯示標記點

            # 添加 VCE (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE'],  # 交換後的 Y 軸數據
                mode=mode_vce,
                name=f"{data['Temperature'][0]} VCE",
                line=dict(color=color_mapping[temp_key], width=2, dash='solid'),
                marker=dict(size=6)
            ))

            # 添加 VCE2 (V) 曲線
            fig.add_trace(go.Scatter(
                x=data['IC'],  # 交換後的 X 軸數據
                y=data['VCE2'],  # 交換後的 Y 軸數據
                mode=mode_vce2,
                name=f"{data['Temperature'][0]} VCE2",
                line=dict(color=color_mapping[temp_key], width=2, dash='dash'),  # 使用虛線區分
                marker=dict(size=6)
            ))

            # **新增：僅在非「所有溫度」時添加標註（交換 x 和 y）**
            if selected_temp_graph != 'ifvf_all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局（更新標題和軸標籤）
    if selected_temp_graph != 'ifvf_all_temperatures':
        title = f"Eon, Eoff vs IC for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "Eon, Eoff vs IC"  # 更新標題

    fig.update_layout(
        title=title,
        xaxis_title="IC (A)",  # 更新 X 軸標籤
        yaxis_title="E (mJ)",  # 更新 Y 軸標籤
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=200,  # 設置刻度間隔為200
            range=[0, 1800],  # 調整X軸範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=20,  # 根據新的 Y 軸數據調整刻度間隔
            tick0=0,  # 設置起始刻度為0
            range=[0, 140],  # 調整範圍為0到140V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'ifvf_all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            valid_data = [
                {
                    '編號': idx + 1 + len(table_data),
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}",
                    'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce, vce2) in enumerate(zip(data['Temperature'], data['IC'], data['VCE'], data['VCE2']))
                if not (pd.isna(ic) or pd.isna(vce) or pd.isna(vce2))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC、VCE 或 VCE2 為 NaN 的行
            table_data = [
                {
                    '編號': idx + 1,
                    '溫度': temp,
                    'IC (A)': f"{ic:.3f}",
                    'VCE (V)': f"{vce:.4f}",
                    'VCE2 (V)': f"{vce2:.4f}"
                }
                for idx, (temp, ic, vce, vce2) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE'], temp_data['VCE2']))
                if not (pd.isna(ic) or pd.isna(vce) or pd.isna(vce2))
            ]
        else:
            table_data = []

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "IC (A)", "id": "IC (A)"},
        {"name": "EON (MJ)", "id": "VCE (V)"},
        {"name": "EOFF (MJ)", "id": "VCE2 (V)"}
    ]

    return fig, table_data, columns




# hi7582ifvf,create_loss_analysis_card3(),update_loss_analysis3()
@app.callback(
    [Output('loss_loss-graph3', 'figure'),
     Output('loss_loss-table3', 'data'),
     Output('loss_loss-table3', 'columns')],
    [Input('loss_temperature-dropdown-graph3', 'value'),
     Input('loss_ic-range-slider3', 'value'),
     Input('loss_vce-range-slider3', 'value'),
     Input('loss_temperature-dropdown-table3', 'value')]
)
def update_loss_analysis3(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis3 triggered with: selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, vce_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH3)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df
    print("U3-1825.")  # 調試輸出
    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    for temp in ['25℃', '150℃', '175℃']:
        ic_col = f'If_{temp}'
        print(f"U3 ic_col: {ic_col}")
        vce_col = f'Vf_{temp}'
        print(f"U3 vce_col: {vce_col}")
        if ic_col in df_filtered.columns and vce_col in df_filtered.columns:
            conditions.append(
                (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
            )

    if selected_temp_graph == 'ifvf_all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for ifvf_all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'
        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            ic_col = f'If_{temp_str}'
            vce_col = f'Vf_{temp_str}'
            if ic_col in df_filtered.columns and vce_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                    (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {ic_col} and/or {vce_col} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['If_25℃'].tolist(),
            'VCE': df_filtered['Vf_25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['If_150℃'].tolist(),
            'VCE': df_filtered['Vf_150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['If_175℃'].tolist(),
            'VCE': df_filtered['Vf_175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 1.1547, 'y': 447.51, 'text': "450A<br>IC: 447.51<br>VCE: 1.1547"},
            {'x': 1.3847, 'y': 819.11, 'text': "820A<br>IC: 819.11<br>VCE: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 1.263, 'y': 451.644, 'text': "450A<br>IC: 451.644<br>VCE: 1.263"},
            {'x': 1.678, 'y': 823.824, 'text': "820A<br>IC: 823.824<br>VCE: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 1.303, 'y': 450.026, 'text': "450A<br>IC: 450.026<br>VCE: 1.303"},
            {'x': 1.764, 'y': 824.324, 'text': "820A<br>IC: 824.324<br>VCE: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'ifvf_all_temperatures' or temp_key == selected_temp_graph:
            # 設置圖表模式
            if selected_temp_graph == 'ifvf_all_temperatures':
                mode = 'lines'  # 不顯示標記點
            else:
                mode = 'lines+markers'  # 顯示標記點

            fig.add_trace(go.Scatter(
                x=data['VCE'],
                y=data['IC'],
                mode=mode,
                name=data['Temperature'][0],
                line=dict(color=color_mapping[temp_key], width=2),
                marker=dict(size=4)  # 設置標記點大小為4
            ))

            # **新增：僅在非「所有溫度」時添加標註**
            if selected_temp_graph != 'ifvf_all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局
    if selected_temp_graph != 'ifvf_all_temperatures':
        title = f"IF vs VF for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "IF vs VF"  # 移除「所有溫度」的標籤

    fig.update_layout(
        title=title,
        xaxis_title="VF (V)",
        yaxis_title="IF (A)",
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=0.8,  # 設置刻度間隔
            range=[-1, 4],  # 調整範圍為-1到4V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=400,
            tick0=-100,  # 設置起始刻度為 -100
            range=[-100, 1700],  # 調整範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'ifvf_all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC 或 VCE 為 NaN 的行
            valid_data = [
                {'編號': idx + 1 + len(table_data), '溫度': temp, 'IF (A)': ic, 'VF (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(data['Temperature'], data['IC'], data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC 或 VCE 為 NaN 的行
            table_data = [
                {'編號': idx + 1, '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}
            table_data = []

    # 定義表格欄位
    columns = [
        {"name": "Index", "id": "編號", "type": "numeric"},
        {"name": "Temperature (°C)", "id": "溫度", "type": "text"},
        {"name": "IF (A)", "id": "IC (A)", "type": "numeric"},
        {"name": "VF (V)", "id": "VCE (V)", "type": "numeric"}
    ]

    if selected_temp_table == 'ifvf_all_temperatures':
        # Concatenate all temperatures' data
        table_data = []

        for temp_key, data in temperature_data.items():
            ic_values = [f"{ic:.3f}" for ic in data['IC']]
            vce_values = [f"{vce:.4f}" for vce in data['VCE']]
            temp_values = data['Temperature']
            table_data.extend([{'編號': idx + 1 + len(table_data), '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                               for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))])

    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}

        ic_values = [f"{ic:.3f}" for ic in temp_data['IC']]  # 保留IC數值小數點後三位
        vce_values = [f"{vce:.4f}" for vce in temp_data['VCE']]  # 保留VCE數值小數點後四位
        temp_values = temp_data['Temperature']

        # 構建表格數據
        table_data = [{'編號': idx + 1, '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                      for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))]

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "IF (A)", "id": "IC (A)"},
        {"name": "VF (V)", "id": "VCE (V)"}
    ]

    return fig, table_data, columns




# Callback for Characteristics Diagrams (Tab1)
@app.callback(
    [Output('loss_loss-graph', 'figure'),
     Output('loss_loss-table', 'data'),
     Output('loss_loss-table', 'columns')],
    [Input('loss_temperature-dropdown-graph', 'value'),
     Input('loss_ic-range-slider', 'value'),
     Input('loss_vce-range-slider', 'value'),
     Input('loss_temperature-dropdown-table', 'value')]
)
def update_loss_analysis(selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis triggered with: selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, vce_range={vce_range}, selected_temp_table={selected_temp_table}")

    df = load_data(DATA_FILE_PATH)
    if df.empty:
        print("DataFrame is empty.")  # 調試輸出
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Temperature (°C)", "id": "溫度"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 過濾數據中的負值
    df_filtered = df

    # 假設 DATA_FILE_PATH 包含 Tj = 25°C, 150°C, 175°C 的數據
    conditions = []
    for temp in ['25℃', '150℃', '175℃']:
        ic_col = f'IC_Tj = {temp}'
        vce_col = f'VCE_Tj = {temp}'
        if ic_col in df_filtered.columns and vce_col in df_filtered.columns:
            conditions.append(
                (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
            )

    if selected_temp_graph == 'all_temperatures':
        # 對所有溫度進行過濾
        combined_condition = False
        for condition in conditions:
            combined_condition |= condition
        df_filtered = df_filtered[combined_condition]
        print(f"Filtered DataFrame for all_temperatures: {df_filtered.shape[0]} rows.")  # 調試輸出
    else:
        temp_key = selected_temp_graph  # e.g., 'Tj_25C_IC_f_VCE'
        # 從 temp_key 中提取溫度
        temp_parts = temp_key.split('_')
        if len(temp_parts) >= 3:
            temp_str = temp_parts[1]  # '25C'
            temp_str = temp_str.replace('C', '℃')  # '25℃'
            ic_col = f'IC_Tj = {temp_str}'
            vce_col = f'VCE_Tj = {temp_str}'
            if ic_col in df_filtered.columns and vce_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                    (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {ic_col} and/or {vce_col} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame

    # 初始化圖表
    fig = go.Figure()

    # 整理數據
    temperature_data = {
        'Tj_25C_IC_f_VCE': {
            'IC': df_filtered['IC_Tj = 25℃'].tolist(),
            'VCE': df_filtered['VCE_Tj = 25℃'].tolist(),
            'Temperature': ['Tj = 25℃'] * len(df_filtered)
        },
        'Tj_150C_IC_f_VCE': {
            'IC': df_filtered['IC_Tj = 150℃'].tolist(),
            'VCE': df_filtered['VCE_Tj = 150℃'].tolist(),
            'Temperature': ['Tj = 150℃'] * len(df_filtered)
        },
        'Tj_175C_IC_f_VCE': {
            'IC': df_filtered['IC_Tj = 175℃'].tolist(),
            'VCE': df_filtered['VCE_Tj = 175℃'].tolist(),
            'Temperature': ['Tj = 175℃'] * len(df_filtered)
        },
    }

    # 定義目標數據點
    target_currents = {
        'Tj_25C_IC_f_VCE': [
            {'x': 1.1547, 'y': 447.51, 'text': "450A<br>IC: 447.51<br>VCE: 1.1547"},
            {'x': 1.3847, 'y': 819.11, 'text': "820A<br>IC: 819.11<br>VCE: 1.3847"}
        ],
        'Tj_150C_IC_f_VCE': [
            {'x': 1.263, 'y': 451.644, 'text': "450A<br>IC: 451.644<br>VCE: 1.263"},
            {'x': 1.678, 'y': 823.824, 'text': "820A<br>IC: 823.824<br>VCE: 1.678"}
        ],
        'Tj_175C_IC_f_VCE': [
            {'x': 1.303, 'y': 450.026, 'text': "450A<br>IC: 450.026<br>VCE: 1.303"},
            {'x': 1.764, 'y': 824.324, 'text': "820A<br>IC: 824.324<br>VCE: 1.764"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'Tj_25C_IC_f_VCE': 'gray',
        'Tj_150C_IC_f_VCE': 'skyblue',
        'Tj_175C_IC_f_VCE': 'navy'
    }

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'all_temperatures' or temp_key == selected_temp_graph:
            # 設置圖表模式
            if selected_temp_graph == 'all_temperatures':
                mode = 'lines'  # 不顯示標記點
            else:
                mode = 'lines+markers'  # 顯示標記點

            fig.add_trace(go.Scatter(
                x=data['VCE'],
                y=data['IC'],
                mode=mode,
                name=data['Temperature'][0],
                line=dict(color=color_mapping[temp_key], width=2),
                marker=dict(size=4)  # 設置標記點大小為4
            ))

            # **新增：僅在非「所有溫度」時添加標註**
            if selected_temp_graph != 'all_temperatures':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局
    if selected_temp_graph != 'all_temperatures':
        title = f"IC vs VCE for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "IC vs VCE"  # 移除「所有溫度」的標籤

    fig.update_layout(
        title=title,
        xaxis_title="VCE (V)",
        yaxis_title="IC (A)",
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=0.8,  # 設置刻度間隔
            range=[-1, 4],  # 調整範圍為-1到4V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=400,
            tick0=-100,  # 設置起始刻度為 -100
            range=[-100, 1700],  # 調整範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'all_temperatures':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC 或 VCE 為 NaN 的行
            valid_data = [
                {'編號': idx + 1 + len(table_data), '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(data['Temperature'], data['IC'], data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC 或 VCE 為 NaN 的行
            table_data = [
                {'編號': idx + 1, '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}
            table_data = []

    # 定義表格欄位
    columns = [
        {"name": "Index", "id": "編號", "type": "numeric"},
        {"name": "Temperature (°C)", "id": "溫度", "type": "text"},
        {"name": "IC (A)", "id": "IC (A)", "type": "numeric"},
        {"name": "VCE (V)", "id": "VCE (V)", "type": "numeric"}
    ]

    if selected_temp_table == 'all_temperatures':
        # Concatenate all temperatures' data
        table_data = []

        for temp_key, data in temperature_data.items():
            ic_values = [f"{ic:.3f}" for ic in data['IC']]
            vce_values = [f"{vce:.4f}" for vce in data['VCE']]
            temp_values = data['Temperature']
            table_data.extend([{'編號': idx + 1 + len(table_data), '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                               for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))])

    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}

        ic_values = [f"{ic:.3f}" for ic in temp_data['IC']]  # 保留IC數值小數點後三位
        vce_values = [f"{vce:.4f}" for vce in temp_data['VCE']]  # 保留VCE數值小數點後四位
        temp_values = temp_data['Temperature']

        # 構建表格數據
        table_data = [{'編號': idx + 1, '溫度': temp, 'IC (A)': ic, 'VCE (V)': vce}
                      for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))]

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Temperature (°C)", "id": "溫度"},
        {"name": "IC (A)", "id": "IC (A)"},
        {"name": "VCE (V)", "id": "VCE (V)"}
    ]

    return fig, table_data, columns

# Callback for Characteristics Diagrams2 (Tab1-2)
@app.callback(
    [Output('loss_loss-graph2', 'figure'),
     Output('loss_loss-table2', 'data'),
     Output('loss_loss-table2', 'columns')],
    [Input('icvce-radio2', 'value'),
     Input('loss_temperature-dropdown-graph2', 'value'),
     Input('loss_ic-range-slider2', 'value'),
     Input('loss_vce-range-slider2', 'value'),
     Input('loss_temperature-dropdown-table2', 'value')]
)
def update_loss_analysis2(selected_radio, selected_temp_graph, ic_range, vce_range, selected_temp_table):
    print(f"update_loss_analysis2 triggered with: selected_radio={selected_radio}, selected_temp_graph={selected_temp_graph}, ic_range={ic_range}, vce_range={vce_range}, selected_temp_table={selected_temp_table}")

    # 根據選擇的 Radio 按鈕設置 file 路徑
    if selected_radio == 'Tj_25C_IC_f_VCE':
        file_path = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIC_VCE_family_25C_B.csv'
    elif selected_radio == 'Tj_150C_IC_f_VCE':
        file_path = '/Users/helen/PycharmProjects/Simulation_Tools/data/750V820AIC_VCE_family_150C_C.csv'
    else:
        # 默認路徑或處理其他選項
        file_path = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/refs/heads/main/750V820AIC_VCE_family_25C_B.csv'

    # 讀取 CSV 文件
    try:
        df = pd.read_csv(file_path)
        print(f"CSV 文件 {file_path} 讀取成功，包含 {df.shape[0]} 行和 {df.shape[1]} 列。")
    except Exception as e:
        print(f"讀取 CSV 文件時出錯：{e}")
        # 返回空的圖表和表格
        empty_fig = go.Figure()
        empty_data = []
        empty_columns = [
            {"name": "Index", "id": "編號"},
            {"name": "Voltage (V)", "id": "Voltage (V)"},
            {"name": "IC (A)", "id": "IC (A)"},
            {"name": "VCE (V)", "id": "VCE (V)"}
        ]
        return empty_fig, empty_data, empty_columns

    # 數據處理
    df_filtered = df.copy()

    # 假設 CSV 文件有 'IC_9V', 'VCE_9V', etc. 的列
    temp_key = selected_temp_graph  # e.g., 'IC_9V_VCE_9V'
    print(f"temp_key format: {temp_key}")
    if temp_key != 'all_voltages':
        parts = temp_key.split('_')  # ['IC', '9V', 'VCE', '9V']
        if len(parts) >= 4:
            ic_col = f"{parts[0]}_{parts[1]}"  # 'IC_9V'
            vce_col = f"{parts[2]}_{parts[3]}"  # 'VCE_9V'
            if ic_col in df_filtered.columns and vce_col in df_filtered.columns:
                df_filtered = df_filtered[
                    (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                    (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
                ]
                print(f"Filtered DataFrame for {temp_key}: {df_filtered.shape[0]} rows.")  # 調試輸出
            else:
                print(f"Columns {ic_col} and/or {vce_col} not found in DataFrame.")  # 調試輸出
                df_filtered = pd.DataFrame()  # 清空 DataFrame
        else:
            print(f"Unexpected temp_key format: {temp_key}")  # 調試輸出
            df_filtered = pd.DataFrame()  # 清空 DataFrame
    else:
        # 對所有電壓進行過濾
        ic_cols = [col for col in df_filtered.columns if col.startswith('IC_')]
        vce_cols = [col for col in df_filtered.columns if col.startswith('VCE_')]
        condition = False
        for ic_col, vce_col in zip(ic_cols, vce_cols):
            condition |= (
                (df_filtered[ic_col] >= ic_range[0]) & (df_filtered[ic_col] <= ic_range[1]) &
                (df_filtered[vce_col] >= vce_range[0]) & (df_filtered[vce_col] <= vce_range[1])
            )
        df_filtered = df_filtered[condition]
        print(f"Filtered DataFrame for all_voltages: {df_filtered.shape[0]} rows.")  # 調試輸出

    if temp_key == 'all_voltages':
        # 準備所有電壓的數據
        temperature_data = {}
        for ic_col, vce_col in zip([col for col in df.columns if col.startswith('IC_')],
                                   [col for col in df.columns if col.startswith('VCE_')]):
            temp_label = ic_col.split('_')[1]  # '9V'
            temperature_data[ic_col + '_' + vce_col] = {
                'IC': df_filtered[ic_col].tolist(),
                'VCE': df_filtered[vce_col].tolist(),
                'Temperature': [temp_label] * len(df_filtered)
            }
    else:
        # 準備特定電壓的數據
        temperature_data = {
            temp_key: {
                'IC': df_filtered[f'{parts[0]}_{parts[1]}'].tolist(),
                'VCE': df_filtered[f'{parts[2]}_{parts[3]}'].tolist(),
                'Temperature': [parts[1]] * len(df_filtered)
            }
        }

    # 定義需要標記的條件
    highlight_conditions = [
        {'Voltage (V)': '11V', 'IC (A)': 443.24},
        {'Voltage (V)': '11V', 'IC (A)': 813.68},
        {'Voltage (V)': '13V', 'IC (A)': 500.00},
        {'Voltage (V)': '13V', 'IC (A)': 900.00},
        {'Voltage (V)': '15V', 'IC (A)': 500.00},
        {'Voltage (V)': '15V', 'IC (A)': 900.00},
        {'Voltage (V)': '17V', 'IC (A)': 500.00},
        {'Voltage (V)': '17V', 'IC (A)': 900.00},
        {'Voltage (V)': '19V', 'IC (A)': 500.00},
        {'Voltage (V)': '19V', 'IC (A)': 900.00},
    ]

    # 生成 style_data_conditional
    style_data_conditional = [
        {
            'if': {
                'filter_query': f'{{Voltage (V)}} = "{cond["Voltage (V)"]}" && {{IC (A)}} = {cond["IC (A)"]}',
            },
            'backgroundColor': 'lightgreen',  # 不同顏色以區分
            'color': 'black'
        }
        for cond in highlight_conditions
    ]

    # 準備繪圖數據
    target_currents = {
        'IC_11V_VCE_11V': [
            {'x': 1.203, 'y': 443.242, 'text': "450A<br>IC: 443.242<br>VCE: 1.203"},
            {'x': 1.486, 'y': 813.684, 'text': "820A<br>IC: 813.684<br>VCE: 1.486"}
        ],
        'IC_13V_VCE_13V': [
            {'x': 1.173, 'y': 446.866, 'text': "450A<br>IC: 446.866<br>VCE: 1.173"},
            {'x': 1.420, 'y': 819.316, 'text': "820A<br>IC: 819.316<br>VCE: 1.420"}
        ],
        'IC_15V_VCE_15V': [
            {'x': 1.154, 'y': 447.51, 'text': "450A<br>IC: 447.510<br>VCE: 1.154"},
            {'x': 1.384, 'y': 819.11, 'text': "820A<br>IC: 819.110<br>VCE: 1.384"}
        ],
        'IC_17V_VCE_17V': [
            {'x': 1.144, 'y': 447.714, 'text': "450A<br>IC: 447.714<br>VCE: 1.144"},
            {'x': 1.361, 'y': 818.736, 'text': "820A<br>IC: 818.736<br>VCE: 1.361"}
        ],
        'IC_19V_VCE_19V': [
            {'x': 1.138, 'y': 449.998, 'text': "450A<br>IC: 449.998<br>VCE: 1.138"},
            {'x': 1.344, 'y': 811.420, 'text': "820A<br>IC: 811.420<br>VCE: 1.344"}
        ]
    }

    # 定義顏色對應
    color_mapping = {
        'IC_9V_VCE_9V': '#D3D3D3',
        'IC_11V_VCE_11V': '#8FBC8F',
        'IC_13V_VCE_13V': '#FF8C00',
        'IC_15V_VCE_15V': '#00CED1',
        'IC_17V_VCE_17V': '#9370DB',
        'IC_19V_VCE_19V': 'navy'
    }

    # 初始化圖表
    fig = go.Figure()

    # 繪製曲線
    for temp_key, data in temperature_data.items():
        if selected_temp_graph == 'all_voltages' or temp_key == selected_temp_graph:
            # 設置圖表模式
            if selected_temp_graph == 'all_voltages':
                mode = 'lines'  # 不顯示標記點
            else:
                mode = 'lines+markers'  # 顯示標記點

            fig.add_trace(go.Scatter(
                x=data['VCE'],
                y=data['IC'],
                mode=mode,
                name=data['Temperature'][0],
                line=dict(color=color_mapping.get(temp_key, 'blue'), width=2),
                marker=dict(size=4)  # 設置標記點大小為4
            ))

            # **新增：僅在非「所有電壓」時添加標註**
            if selected_temp_graph != 'all_voltages':
                for point in target_currents.get(temp_key, []):
                    fig.add_annotation(
                        x=point['x'], y=point['y'],
                        text=point['text'],
                        showarrow=True,
                        arrowhead=2,
                        ax=0,  # 箭頭的x坐標
                        ay=-30,  # 箭頭的y坐標，距離標籤
                        font=dict(size=12, color='black'),  # 將字體顏色設為黑色
                        bgcolor='rgba(255, 255, 255, 0.7)',  # 半透明背景
                        bordercolor='rgba(255, 255, 255, 0)',  # 無邊框顏色
                        borderwidth=1,
                        borderpad=4
                    )

    # 設置圖表布局
    if selected_temp_graph != 'all_voltages':
        title = f"IC vs VCE for {selected_temp_graph.replace('_', ' ')}"
    else:
        title = "IC vs VCE"  # 移除「所有電壓」的標籤

    fig.update_layout(
        title=title,
        xaxis_title="VCE (V)",
        yaxis_title="IC (A)",
        margin=dict(l=40, r=40, t=60, b=40),  # 增加邊距
        paper_bgcolor='white',  # 設置背景顏色為白色
        plot_bgcolor='white',  # 設置圖表區域背景為白色
        font=dict(
            family="Arial, sans-serif",
            size=14,
            color="black"
        ),
        titlefont=dict(size=20, color='black'),  # 主標題字體大小和顏色
        xaxis=dict(
            showgrid=True,  # 顯示網格線
            gridcolor='lightgrey',  # 網格線顏色
            tickmode='linear',
            dtick=0.8,  # 設置刻度間隔
            range=[-1, 4],  # 調整範圍為-1到4V以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            tickmode='linear',
            dtick=400,
            tick0=-100,  # 設置起始刻度為 -100
            range=[-100, 1700],  # 調整範圍以匹配滑桿
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=2,
            showticklabels=True,
        ),
        legend=dict(
            x=1,
            y=0.99,
            bgcolor='rgba(255,255,255,0)',
            bordercolor='rgba(0,0,0,0)'
        )
    )

    # 準備表格數據
    table_data = []
    if selected_temp_table == 'all_voltages':
        for temp_key, data in temperature_data.items():
            # 過濾掉 IC 或 VCE 為 NaN 的行
            valid_data = [
                {'編號': idx + 1 + len(table_data), 'Voltage (V)': temp, 'IC (A)': ic, 'VCE (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(data['Temperature'], data['IC'], data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
            table_data.extend(valid_data)
    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
            # 過濾掉 IC 或 VCE 為 NaN 的行
            table_data = [
                {'編號': idx + 1, 'Voltage (V)': temp, 'IC (A)': ic, 'VCE (V)': vce}
                for idx, (temp, ic, vce) in enumerate(zip(temp_data['Temperature'], temp_data['IC'], temp_data['VCE']))
                if not (pd.isna(ic) or pd.isna(vce))
            ]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}
            table_data = []

    # 定義表格欄位
    columns = [
        {"name": "Index", "id": "編號", "type": "numeric"},
        {"name": "Voltage (V)", "id": "Voltage (V)", "type": "text"},
        {"name": "IC (A)", "id": "IC (A)", "type": "numeric"},
        {"name": "VCE (V)", "id": "VCE (V)", "type": "numeric"}
    ]

    if selected_temp_table == 'all_voltages':
        # Concatenate all voltages' data
        table_data = []

        for temp_key, data in temperature_data.items():
            ic_values = [f"{ic:.3f}" for ic in data['IC']]
            vce_values = [f"{vce:.4f}" for vce in data['VCE']]
            temp_values = data['Temperature']
            table_data.extend([{'編號': idx + 1 + len(table_data), 'Voltage (V)': temp, 'IC (A)': ic, 'VCE (V)': vce}
                               for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))])

    else:
        if selected_temp_table in temperature_data:
            temp_data = temperature_data[selected_temp_table]
        else:
            temp_data = {'IC': [], 'VCE': [], 'Temperature': []}

        ic_values = [f"{ic:.3f}" for ic in temp_data['IC']]  # 保留IC數值小數點後三位
        vce_values = [f"{vce:.4f}" for vce in temp_data['VCE']]  # 保留VCE數值小數點後四位
        temp_values = temp_data['Temperature']

        # 構建表格數據
        table_data = [{'編號': idx + 1, 'Voltage (V)': temp, 'IC (A)': ic, 'VCE (V)': vce}
                      for idx, (temp, ic, vce) in enumerate(zip(temp_values, ic_values, vce_values))]

    # 定義表格欄位（保持不變）
    columns = [
        {"name": "Index", "id": "編號"},
        {"name": "Voltage (V)", "id": "Voltage (V)"},
        {"name": "IC (A)", "id": "IC (A)"},
        {"name": "VCE (V)", "id": "VCE (V)"}
    ]

    return fig, table_data, columns

# 回調函數：處理四個頁籤的存檔功能
# 已移除 download-tab1、download-tab2 和 download-tab1-2 的相關回調函數


# 更新顯示的IC範圍輸出
@app.callback(
    Output('loss_ic-output4', 'children'),
    Input('loss_ic-range-slider4', 'value')
)
def update_loss_ic_output4(ic_range):
    print(f"IC Range Updated: {ic_range}")  # 調試輸出
    return f"目前 IC 範圍: {ic_range[0]} A 至 {ic_range[1]} A"

# 更新顯示的VCE範圍輸出
@app.callback(
    Output('loss_vce-output4', 'children'),
    Input('loss_vce-range-slider4', 'value')
)
def update_loss_vce_output4(vce_range):
    print(f"VCE Range Updated: {vce_range}")  # 調試輸出
    return f"目前 VCE 範圍: {vce_range[0]} V 至 {vce_range[1]} V"


# 更新顯示的IC範圍輸出
@app.callback(
    Output('loss_ic-output3', 'children'),
    Input('loss_ic-range-slider3', 'value')
)
def update_loss_ic_output3(ic_range):
    print(f"IC Range Updated: {ic_range}")  # 調試輸出
    return f"目前 IC 範圍: {ic_range[0]} A 至 {ic_range[1]} A"

# 更新顯示的VCE範圍輸出
@app.callback(
    Output('loss_vce-output3', 'children'),
    Input('loss_vce-range-slider3', 'value')
)
def update_loss_vce_output3(vce_range):
    print(f"VCE Range Updated: {vce_range}")  # 調試輸出
    return f"目前 VCE 範圍: {vce_range[0]} V 至 {vce_range[1]} V"

# 更新顯示的IC範圍輸出
@app.callback(
    Output('loss_ic-output', 'children'),
    Input('loss_ic-range-slider', 'value')
)
def update_loss_ic_output(ic_range):
    print(f"IC Range Updated: {ic_range}")  # 調試輸出
    return f"目前 IC 範圍: {ic_range[0]} A 至 {ic_range[1]} A"

# 更新顯示的VCE範圍輸出
@app.callback(
    Output('loss_vce-output', 'children'),
    Input('loss_vce-range-slider', 'value')
)
def update_loss_vce_output(vce_range):
    print(f"VCE Range Updated: {vce_range}")  # 調試輸出
    return f"目前 VCE 範圍: {vce_range[0]} V 至 {vce_range[1]} V"

# 更新顯示的IC範圍輸出
@app.callback(
    Output('loss_ic-output2', 'children'),
    Input('loss_ic-range-slider2', 'value')
)
def update_loss_ic_output2(ic_range):
    print(f"IC Range Updated: {ic_range}")  # 調試輸出
    return f"目前 IC 範圍: {ic_range[0]} A 至 {ic_range[1]} A"

@app.callback(
    Output('loss_vce-output2', 'children'),
    Input('loss_vce-range-slider2', 'value')
)
def update_loss_vce_output2(vce_range):
    print(f"VCE Range Updated: {vce_range}")  # 調試輸出
    return f"目前 VCE 範圍: {vce_range[0]} V 至 {vce_range[1]} V"



@app.callback(
    [Output('eoneoffic-image4', 'src'),
     Output('eoneoffic-title4', 'children')],
    Input('eoneoffic-radio4', 'value')
)
def update_icvce_image4(selected_radio):
    print(f"Selected Radio Option4: {selected_radio}")  # 調試輸出
    # 根據選擇的值返回相應的圖片路徑和標題
    image_mapping = {
        'EONEOFFIC': ('EONEOFFICE.png', 'VGE = -8V / + 15V,RG,on = 2.5 Ω,RG,off = 5.0 Ω, VCE = 400V')
    }

    image_filename, title = image_mapping.get(selected_radio, ('EONEOFFICE.png', 'VGE = 15V, IC = f(VCE)'))

    # 生成圖片完整路徑
    image_src = f'/assets/{image_filename}'

    print(f"Image Source4: {image_src}, Title4: {title}")  # 調試輸出

    return image_src, title



@app.callback(
    [Output('icvce-image3', 'src'),
     Output('icvce-title3', 'children')],
    Input('icvce-radio3', 'value')
)
def update_icvce_image3(selected_radio):
    print(f"Selected Radio Option3: {selected_radio}")  # 調試輸出
    # 根據選擇的值返回相應的圖片路徑和標題
    image_mapping = {
        'VGE_15V_IC_f_VCE': ('IFVFD.png', 'If = f(VF)')
    }

    image_filename, title = image_mapping.get(selected_radio, ('IFVFD.png', 'VGE = 15V, IC = f(VCE)'))

    # 生成圖片完整路徑
    image_src = f'/assets/{image_filename}'

    print(f"Image Source1: {image_src}, Title3: {title}")  # 調試輸出

    return image_src, title


# 回調函數：根據 Characteristics Diagrams 的 RadioItems 選擇更新圖片和標題
@app.callback(
    [Output('icvce-image1', 'src'),
     Output('icvce-title1', 'children')],
    Input('icvce-radio1', 'value')
)
def update_icvce_image1(selected_radio):
    print(f"Selected Radio Option1: {selected_radio}")  # 調試輸出
    # 根據選擇的值返回相應的圖片路徑和標題
    image_mapping = {
        'VGE_15V_IC_f_VCE': ('ICVCE15V.png', 'VGE = 15V, IC = f(VCE)')
    }

    image_filename, title = image_mapping.get(selected_radio, ('ICVCE15V.png', 'VGE = 15V, IC = f(VCE)'))

    # 生成圖片完整路徑
    image_src = f'/assets/{image_filename}'

    print(f"Image Source1: {image_src}, Title1: {title}")  # 調試輸出

    return image_src, title

# 回調函數：根據 Characteristics Diagrams2 的 RadioItems 選擇更新圖片和標題
@app.callback(
    [Output('icvce-image2', 'src'),
     Output('icvce-title2', 'children')],
    Input('icvce-radio2', 'value')
)
def update_icvce_image2(selected_radio):
    print(f"Selected Radio Option2: {selected_radio}")  # 調試輸出
    # 根據選擇的值返回相應的圖片路徑和標題
    image_mapping = {
        'Tj_25C_IC_f_VCE': ('ICVCE25.png', 'Tj = 25℃, IC = f(VCE)'),
        'Tj_150C_IC_f_VCE': ('ICVCE150.png', 'Tj = 150℃, IC = f(VCE)')
    }

    image_filename, title = image_mapping.get(selected_radio, ('ICVCE25.png', 'Tj = 25℃, IC = f(VCE)'))

    # 生成圖片完整路徑
    image_src = f'/assets/{image_filename}'

    print(f"Image Source2: {image_src}, Title2: {title}")  # 調試輸出

    return image_src, title

# 啟動應用程式
if __name__ == '__main__':
    app.run_server(debug=True)

