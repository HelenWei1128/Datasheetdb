import subprocess
import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback, State, ALL
import ssl
import pandas as pd
import re
import os
import base64
import io
import json
from dash.exceptions import PreventUpdate
import logging
import requests

# 設置日誌記錄
logging.basicConfig(level=logging.INFO)

external_stylesheets = [dbc.themes.BOOTSTRAP, '/assets/styles.css']
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Power Module Datasheet"
server = app.server

# 忽略 SSL 驗證（僅建議在開發環境使用，生產環境應移除此行以確保安全）
ssl._create_default_https_context = ssl._create_unverified_context

# 讀取主要資料
csv_url = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/main/Datasheetdata04.csv'
df = pd.read_csv(csv_url)

# 去除欄位名稱的前後空白
df.columns = df.columns.str.strip()

# 確認 'Report Link' 欄位是否存在並處理
if 'Report Link' in df.columns:
    df['Report Link'] = df['Report Link'].fillna('')
    df['Report Link'] = df['Report Link'].apply(lambda x: f'[Report]({x})' if x else '')
else:
    df['Report Link'] = df['Parameter'].apply(
        lambda x: f'https://example.com/reports/{x.split("//")[-1].replace("/", "-")}' if pd.notna(x) else ''
    )
    df['Report Link'] = df['Report Link'].apply(lambda x: f'[Report]({x})' if x else '')

# 修改欄位名稱
df.rename(columns={'Q1 Men': 'Q1 Male'}, inplace=True)

# 嘗試自動解析 TimeStamp 欄位的日期時間格式
if 'TimeStamp' in df.columns:
    try:
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], errors='coerce')  # 自動解析日期格式
        df['Report Year'] = df['TimeStamp'].dt.year
    except Exception as e:
        print(f"日期解析失敗: {e}")
else:
    print("錯誤：找不到 'TimeStamp' 欄位。")
    exit(1)

# 獲取唯一的 Power 名稱，排除 NaN 並確保為字串，並進行排序
unique_powers = ['All'] + sorted(
    df["Power"].dropna().astype(str).unique(),
    key=lambda x: float(re.findall(r'(\d+)V', x)[0]) if re.findall(r'(\d+)V', x) else float('inf')
)

# 獲取唯一的模組名稱，排除 NaN 並確保為字串，並進行排序
unique_modules = ['All'] + sorted(df["Module"].dropna().astype(str).unique())

# 設定預設選擇
default_power = 'All'
default_module = 'All'

# 定義數值欄位
numeric_columns = [
    'Parameter', 'Report Year',
    'Conditions', 'Symbol', 'Values', 'Min', 'Typ', 'Max', 'Unit', 'User', 'TimeStamp', 'Version'
]

# 獲取最新一筆 datasheet 資料
latest_datasheet = df.sort_values(by='TimeStamp', ascending=False).head(1)

# 獲取最新四筆模組更新資料，僅包含 'Type Name'、'TimeStamp' 和 'Version'
latest_four = df.sort_values(by='TimeStamp', ascending=False).head(4)[['Type Name', 'TimeStamp', 'Version']]

# 讀取 Datasheetdatalist.csv 並處理
datasheet_csv_path = 'https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/main/Datasheetdatalist.csv'



try:
    # 如果路徑是 URL，則使用 requests 下載檔案內容
    if datasheet_csv_path.startswith("http://") or datasheet_csv_path.startswith("https://"):
        response = requests.get(datasheet_csv_path)
        response.raise_for_status()  # 若下載失敗則拋出例外
        datasheet_df = pd.read_csv(io.StringIO(response.text))
    else:
        # 本地檔案情況，先檢查是否存在
        if os.path.exists(datasheet_csv_path):
            datasheet_df = pd.read_csv(datasheet_csv_path)
        else:
            raise FileNotFoundError(f"找不到檔案 {datasheet_csv_path}")

    # 確保 'Type Name', 'TimeStamp', 'Version' 欄位存在
    required_columns = ['Type Name', 'TimeStamp', 'Version']
    if all(col in datasheet_df.columns for col in required_columns):
        try:
            # 嘗試自動解析 TimeStamp 欄位的日期時間格式
            datasheet_df['TimeStamp'] = pd.to_datetime(datasheet_df['TimeStamp'], errors='coerce')
        except Exception as e:
            print(f"Datasheet TimeStamp 解析失敗: {e}")

        # 排序並取得最新四筆資料
        datasheet_latest_four = datasheet_df.sort_values(by='TimeStamp', ascending=False).head(4)
        # 將 TimeStamp 轉換為字串以確保 DataTable 正確顯示
        datasheet_latest_four['TimeStamp'] = datasheet_latest_four['TimeStamp'].dt.strftime('%Y-%m-%d')
        # 格式化 'Type Name' 為可點擊的連結並添加圖示
        datasheet_latest_four['Type Name'] = datasheet_latest_four['Type Name'].apply(
            lambda x: f"![icon](/assets/inbox-document-text.png) [{x}](#)"
        )
    else:
        print("錯誤：'Datasheetdatalist.csv' 缺少必要的欄位。")
        datasheet_latest_four = pd.DataFrame(columns=['Type Name', 'TimeStamp', 'Version'])
except Exception as e:
    print(f"錯誤：無法讀取 CSV 檔案 {datasheet_csv_path}: {e}")
    datasheet_latest_four = pd.DataFrame(columns=['Type Name', 'TimeStamp', 'Version'])

# 定義 Dash 應用程式
app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Power Module Datasheet"

# 定義導航欄 (navbar)
navbar = html.Div(
    style={
        'backgroundColor': '#f8f9fa',
        'padding': '10px 20px',
        'borderBottom': '1px solid #dee2e6',
        'display': 'flex',
        'justifyContent': 'space-between',
        'alignItems': 'center',
        'marginBottom': '0'  # 移除與下方區塊的間隙
    },
    children=[
        html.Div(
            "Power Module Datasheet",
            style={'fontSize': '22px', 'fontWeight': 'bold', 'color': '#495057'}
        ),
        html.Div(
            children=[
                dcc.Link(
                    "Home", href='/',
                    style={
                        'margin': '0 10px',
                        'textDecoration': 'none',
                        'color': '#495057',
                        'fontSize': '16px'
                    }
                ),
                dbc.DropdownMenu(
                    label="Diagrams",
                    children=[
                        dbc.DropdownMenuItem("Diagrams 1", href='/diagrams1'),
                        dbc.DropdownMenuItem("Diagrams 2", href='/diagrams2'),
                        dbc.DropdownMenuItem("Diagrams 3", href='/diagrams3'),
                    ],
                    style={'margin': '0 10px', 'cursor': 'pointer'},
                    nav=True,
                ),
                dcc.Link(
                    "Contact", href='/contact',
                    style={
                        'margin': '0 10px',
                        'textDecoration': 'none',
                        'color': '#495057',
                        'fontSize': '16px'
                    }
                ),
            ],
            style={'display': 'flex', 'alignItems': 'center'}
        )
    ]
)

# 定義 About 區塊（新增顯示最新四筆模組更新及 Datasheet 資料）
about_section = html.Div(
    style={
        'backgroundColor': '#f8f9fa',
        'padding': '20px',
        'borderRadius': '8px',
        'marginBottom': '0',  # 移除與下方的空隙
        'marginTop': '0',  # 確保沒有上方空隙
        'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)'
    },
    children=[
        html.H2("About", style={'fontSize': '22px', 'fontWeight': 'bold', 'marginBottom': '10px'}),
        html.P(
            "Datasheet Module Database",
            style={'fontSize': '16px', 'color': '#6c757d'}
        ),

        # 新增的 Datasheet 區塊
        html.Div(
            [
                html.P("Recent Updates Status", style={'fontWeight': 'bold', 'marginBottom': '5px', 'textAlign': 'left'}),
                dash_table.DataTable(
                    id='datasheet-table',
                    columns=[
                        {"name": "Type Name", "id": "Type Name", "presentation": "markdown"},  # 保留 markdown
                        {"name": "TimeStamp", "id": "TimeStamp"},
                        {"name": "Version", "id": "Version"}
                    ],
                    data=datasheet_latest_four.to_dict('records'),
                    style_cell={
                        'textAlign': 'left',  # 所有欄位水平左對齊
                        'padding': '5px',    # 增加單元格內邊距
                        'fontSize': '14px',   # 調整字體大小
                        'fontFamily': 'Arial, sans-serif',  # 使用 Arial 字體
                        'verticalAlign': 'middle'  # 垂直居中對齊
                     },
                    style_cell_conditional=[
                        {
                             'if': {'column_id': 'Type Name'},
                             'textAlign': 'center'  # 將 Type Name 欄位置中
                        }
                    ],
                    style_header={
                        'backgroundColor': '#f8f9fa',
                        'fontWeight': 'bold'
                    },
                    style_as_list_view=True,
                    markdown_options={'html': True},  # 保留 HTML 支援
                    page_size=4,
                    style_table={
                        'width': '100%',  # 讓表格占滿容器寬度
                        'border': 'none',
                        'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '8px'
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': 'Type Name'},
                            'color': '#007bff',
                            'textDecoration': 'none',  # 移除底線
                            'cursor': 'pointer'
                        }
                    ],
                )
            ],
            style={'fontSize': '16px', 'color': '#495057', 'marginBottom': '10px'}
        ),
        html.Div(
            [
                dcc.Link("Test1", href='/run-hh4any', style={'display': 'block', 'marginBottom': '5px'}),
                dcc.Link("Test2", href='#', style={'display': 'block'}),
            ],
            style={'fontSize': '16px', 'color': '#007bff'}
        )
    ]
)

# 定義下拉選單 - Power
power_dropdown = html.Div(
    [
        dbc.Label("Select a Power", html_for="power-dropdown"),
        dcc.Dropdown(
            id="power-dropdown",
            options=[{'label': name, 'value': name} for name in unique_powers],
            value=default_power,
            clearable=False,
            maxHeight=600,
            optionHeight=50,
            style={'fontSize': '16px', 'color': '#495057', 'marginBottom': '10px'}
        ),
    ], className="mb-4",
)

# 定義下拉選單 - Module
module_dropdown = html.Div(
    [
        dbc.Label("Select a Module", html_for="module-dropdown"),
        dcc.Dropdown(
            id="module-dropdown",
            options=[{'label': name, 'value': name} for name in unique_modules],
            value=default_module,
            clearable=False,
            maxHeight=600,
            optionHeight=50,
            style={'fontSize': '16px', 'color': '#495057', 'marginBottom': '10px'}
        ),
    ], className="mb-4",
)

# 定義年選擇按鈕
year_radio = html.Div(
    [
        dbc.Label("Select Year", html_for="year-radio"),
        dbc.RadioItems(
            options=[{'label': str(int(year)), 'value': int(year)} for year in sorted(df['Report Year'].dropna().unique())],
            value=int(sorted(df['Report Year'].dropna().unique(), reverse=True)[0]),
            id="year-radio",
            style={'fontSize': '16px', 'color': '#495057', 'marginBottom': '10px'}
        ),
    ],
    className="mb-4",
)

# 定義 AgGrid 表格（主 AgGrid）
grid = html.Div(
    dag.AgGrid(
        id="grid",
        rowData=df.to_dict("records"),  # 初始顯示所有資料
        columnDefs=[
            {"field": "Module", "cellRenderer": "markdown", "linkTarget": "_blank", "initialWidth": 190,
             "pinned": "left",
             "cellStyle": {"textAlign": "center"}},
            {"field": "Power", "cellRenderer": "markdown", "linkTarget": "_blank", "floatingFilter": False},
            {"field": "Type Name", "cellRenderer": "markdown", "linkTarget": "_blank",
             "floatingFilter": False},
            {"field": "Item"}
        ] + [{"field": c} for c in numeric_columns],
        defaultColDef={
            "filter": True,
            "floatingFilter": True,
            "wrapHeaderText": True,
            "autoHeaderHeight": True,
            "initialWidth": 125,
            "headerClass": "header-centered"
        },
        dashGridOptions={
            "pagination": True,
            "paginationPageSize": 20
        },
        filterModel={'Report Year': {'filterType': 'number', 'type': 'equals', 'filter': 2024}},
        rowClassRules={
            "bg-secondary text-dark bg-opacity-25": "params.node.rowPinned === 'top' || params.node.rowPinned === 'bottom'"
        },
        style={"height": 1000, "width": "100%"}
    ),
    style={
        'backgroundColor': '#f8f9fa',
        'padding': '20px',
        'borderRadius': '8px',  # 修改邊角與 About 一致
        'marginBottom': '0',  # 移除與其他區塊的空隙
        'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)',
        'border': '1px solid #e9ecef',
        'marginTop': '-9px'  # 向上移動以減少空隙
    }
)

# 定義控制面板
control_panel = dbc.Card(
    dbc.CardBody(
        [
            about_section,
            year_radio,
            module_dropdown,
            power_dropdown,
        ],
        className="bg-light",
    ),
    style={
        'marginBottom': '0',
        'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)',
        'border': '1px solid #e9ecef',
        'marginTop': '0',  # 調整以減少與上方導航欄的距離
        'padding': '0'  # 確保 About 和其他區塊緊密對齊
    }
)

# 定義 Accordion (info)
info = dbc.Accordion([
    dbc.AccordionItem(dcc.Markdown(
        """
         Datasheet Module Database Beta is a pre-release version designed to support every stage of development.

         It enables teams to quickly search for and download the component information they need, simplifying the process of testing and validating designs.

         While there may be some minor issues or limitations, your feedback is invaluable in helping us improve and refine the system.

         Together, we’re building a tool to make your development process faster and more efficient!
        """
    ), title="Application Development", className="mb-1"),

    dbc.AccordionItem(
        html.Div([
            # Datasheet 資料查詢與管理
            dbc.Button(
                "・Datasheet Query & Management",
                id="collapse-datasheet-button",
                color="transparent",  # 移除 link 顏色
                style={
                    "whiteSpace": "pre-line",
                    "padding": "0",
                    "textAlign": "left",
                    "fontWeight": "bold",
                    "textDecoration": "none",  # 移除底線
                    "border": "none",
                    "backgroundColor": "transparent",
                    "color": "#495057",  # 設定文字顏色
                    "cursor": "pointer"
                }
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        "快速檢索與整理模組的技術規格及參數資料，深入分析與比較。\n"
                        "Quick retrieval and organization of module technical specifications and parameter data for detailed analysis and comparison."
                    ),
                    style={"marginBottom": "10px"}
                ),
                id="collapse-datasheet",
                is_open=False,
            ),

            # 測試數據可視化繪圖
            dbc.Button(
                "・Test Data Visualization & Plotting",
                id="collapse-visualization-button",
                color="transparent",
                style={
                    "whiteSpace": "pre-line",
                    "padding": "0",
                    "textAlign": "left",
                    "fontWeight": "bold",
                    "textDecoration": "none",
                    "border": "none",
                    "backgroundColor": "transparent",
                    "color": "#495057",
                    "cursor": "pointer"
                }
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        "測試結果的圖表生成工具，觀察數據趨勢、性能變化和異常點。\n"
                        "Provides tools for generating charts from test results, enabling observation of data trends, performance variations, and anomalies."
                    ),
                    style={"marginBottom": "10px"}
                ),
                id="collapse-visualization",
                is_open=False,
            ),

            # 圖表與流程圖分析
            dbc.Button(
                "・Diagrams Analysis",
                id="collapse-diagrams-button",
                color="transparent",
                style={
                    "whiteSpace": "pre-line",
                    "padding": "0",
                    "textAlign": "left",
                    "fontWeight": "bold",
                    "textDecoration": "none",
                    "border": "none",
                    "backgroundColor": "transparent",
                    "color": "#495057",
                    "cursor": "pointer"
                }
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        "支援多種類型的圖表和結構流程圖分析，幫助解讀產品架構與系統設計。\n"
                        "Supports analysis of various types of charts and structural diagrams to interpret product architecture and system design."
                    ),
                    style={"marginBottom": "10px"}
                ),
                id="collapse-diagrams",
                is_open=False,
            ),

            # 技術對標與性能評估
            dbc.Button(
                "・Technical Benchmarking & Performance",
                id="collapse-benchmarking-button",
                color="transparent",
                style={
                    "whiteSpace": "pre-line",
                    "padding": "0",
                    "textAlign": "left",
                    "fontWeight": "bold",
                    "textDecoration": "none",
                    "border": "none",
                    "backgroundColor": "transparent",
                    "color": "#495057",
                    "cursor": "pointer"
                }
            ),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        "基於數據進行跨產品或競品的性能對標與技術評估，助力產品改進與策略制定。\n"
                        "Conducts data-driven benchmarking and technical evaluations across products or competitors to facilitate product improvements and strategy development."
                    ),
                    style={"marginBottom": "10px"}
                ),
                id="collapse-benchmarking",
                is_open=False,
            ),
        ]),
        title="Interface Function",
        className="mb-1"  # 修改為更緊湊的下邊距
    ),

    dbc.AccordionItem(
        html.Div(
            style={
                'backgroundColor': '#f8f9fa',
                'padding': '20px',
                'borderRadius': '8px',
                'marginBottom': '20px',
                'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)'
            },
            children=[
                html.H2("Beta 0.0", style={'fontSize': '24px', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.P("測試版本", style={'fontSize': '16px', 'color': '#6c757d'})
            ]
        ),
        title="Version",
        className="mb-1"  # 修改為更緊湊的下邊距
    )
], start_collapsed=True, className="mb-4")  # 保持 Accordion 的下邊距

# 定義下方控制面板
# 定義 Toggle Analyze 區塊（保留註解，因為用戶要求不改動其他功能）
# toggle_analyze_section = html.Div(
#     [
#         dbc.Button("Toggle Analyze", id="toggle-analyze", color="primary", className="mt-2"),
#         dbc.Collapse(
#             html.Div(id="bar-chart-card", className="mt-4"),
#             id="analyze-collapse",
#             is_open=False
#         ),
#     ],
#     style={
#         'backgroundColor': '#f8f9fa',
#         'padding': '20px',
#         'borderRadius': '8px',
#         'marginBottom': '20px',
#         'boxShadow': '0px 1px 3px rgba(0, 0, 0, 0.1)'
#     }
# )

# 定義 Pay Gap 和 Bonus Gap 卡片的佈局，並在卡片之間添加間隔
paygap_bonusgap_cards = dbc.Row([
    dbc.Col(html.Div(id="paygap-card"), className="mb-3"),
    dbc.Col(html.Div(id="bonusgap-card"), className="mb-3")
], className="mb-4")

# 定義 Home 頁面的布局
home_layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col([
                control_panel,
                info,
                # toggle_analyze_section,  # 保留註解
                paygap_bonusgap_cards,
            ], md=3, style={'paddingRight': '10px', 'paddingTop': '0px', 'marginBottom': '0px'}),  # 調整 padding 和 margin
            dbc.Col([
                dcc.Markdown(id="title"),
                html.Div(id="no-data-message", className="text-danger mt-2"),
                grid
            ], md=9, style={'paddingLeft': '10px', 'paddingTop': '0px', 'marginBottom': '0px'})  # 調整 padding 和 margin
        ]),
    ],
    fluid=True,
    style={'padding': '0px', 'margin': '0px'}  # 確保容器的 padding 和 margin 為 0
)

# ================== Diagrams3 頁面的整合開始 ==================

# 定義公司和競爭對手的 PDF 檔案對應表（使用相對路徑）

company_pdfs = {
    "AEP820B08TFLTMM":"https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/main/2024AEP820B08TFLTMM0909.pdf"
}

competitor_pdfs = {
    "競爭者測試":"https://raw.githubusercontent.com/HelenWei1128/Datasheetdb/main/test.pdf"
}

# 對標競爭分析數據（示例數據，根據需要修改）
benchmark_data = [
    {"Parameter": "產品特性", "Company": "高", "Competitor A": "中", "Competitor B": "高", "Competitor C": "低"},
    {"Parameter": "價格策略", "Company": "中", "Competitor A": "高", "Competitor B": "低", "Competitor C": "中"},
    {"Parameter": "市場份額", "Company": "25%", "Competitor A": "30%", "Competitor B": "20%", "Competitor C": "15%"},
    {"Parameter": "客戶滿意度", "Company": "90%", "Competitor A": "85%", "Competitor B": "80%", "Competitor C": "70%"},
    {"Parameter": "銷售量", "Company": "1,000", "Competitor A": "1,200", "Competitor B": "800", "Competitor C": "600"},
    {"Parameter": "分銷渠道", "Company": "多", "Competitor A": "中", "Competitor B": "少", "Competitor C": "多"},
    {"Parameter": "品牌影響力", "Company": "高", "Competitor A": "高", "Competitor B": "中", "Competitor C": "低"}
]

# 定義對標競爭分析的欄位
benchmark_columns = [
    {"name": "Parameter", "id": "Parameter"},
    {"name": "Company", "id": "Company"},
    {"name": "Competitor A", "id": "Competitor A"},
    {"name": "Competitor B", "id": "Competitor B"},
    {"name": "Competitor C", "id": "Competitor C"}
]

# 定義解析上傳文件的函數
def parse_contents(contents, filename):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            return pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

# 定義回調函數：當公司下拉選單改變時更新公司 PDF 和下載按鈕
def callbacks_diagrams3(app):
    # 回調函數：當公司下拉選單改變時更新公司 PDF 和下載按鈕
    @app.callback(
        [
            Output('company-pdf', 'src'),
            Output('download-company-pdf-btn', 'style')
        ],
        Input('company-dropdown', 'value')
    )
    def update_company_pdf(selected_url):
        if selected_url:
            # 使用相對路徑
            return selected_url, {'display': 'inline-block'}
        # 如果未選擇，清空 iframe 並隱藏下載按鈕
        return "", {'display': 'none'}

    # 回調函數：下載公司 PDF（本地文件）
    @app.callback(
        Output("download-company-pdf", "data"),
        Input("download-company-pdf-btn", "n_clicks"),
        State('company-dropdown', 'value'),
        prevent_initial_call=True,
    )
    def download_company_pdf(n_clicks, selected_url):
        if n_clicks and selected_url:
            try:
                # 將相對路徑轉換為本地文件系統路徑
                file_path = os.path.join(os.getcwd(), selected_url)
                if not os.path.exists(file_path):
                    logging.error(f"文件不存在: {file_path}")
                    return dash.no_update
                # 讀取本地 PDF 文件
                with open(file_path, 'rb') as f:
                    pdf_bytes = f.read()
                return dcc.send_bytes(pdf_bytes, os.path.basename(file_path))
            except Exception as e:
                logging.error(f"讀取公司文件時出錯: {e}")
                return dash.no_update
        return dash.no_update

    # 回調函數：當競爭對手下拉選單改變時更新競爭對手 PDF 和下載按鈕
    @app.callback(
        [
            Output('competitor-pdf', 'src'),
            Output('download-competitor-pdf-btn', 'style')
        ],
        Input('competitor-dropdown', 'value')
    )
    def update_competitor_pdf(selected_url):
        if selected_url:
            # 使用相對路徑
            return selected_url, {'display': 'inline-block'}
        # 如果未選擇，清空 iframe 並隱藏下載按鈕
        return "", {'display': 'none'}

    # 回調函數：下載競爭對手 PDF（本地文件）
    @app.callback(
        Output("download-competitor-pdf", "data"),
        Input("download-competitor-pdf-btn", "n_clicks"),
        State('competitor-dropdown', 'value'),
        prevent_initial_call=True,
    )
    def download_competitor_pdf(n_clicks, selected_url):
        if n_clicks and selected_url:
            try:
                # 將相對路徑轉換為本地文件系統路徑
                file_path = os.path.join(os.getcwd(), selected_url)
                if not os.path.exists(file_path):
                    logging.error(f"文件不存在: {file_path}")
                    return dash.no_update
                # 讀取本地 PDF 文件
                with open(file_path, 'rb') as f:
                    pdf_bytes = f.read()
                return dcc.send_bytes(pdf_bytes, os.path.basename(file_path))
            except Exception as e:
                logging.error(f"讀取競爭對手文件時出錯: {e}")
                return dash.no_update
        return dash.no_update

    # 回調函數：下載對標競爭分析為 CSV
    @app.callback(
        Output("download-dataframe-csv", "data"),
        Input("download-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def download_csv(n_clicks):
        if n_clicks:
            df = pd.DataFrame(benchmark_data)
            return dcc.send_data_frame(df.to_csv, "benchmark_data.csv")
        return dash.no_update

    return

# 定義 Diagrams3 頁面的佈局
diagrams3_layout = dbc.Container([
    dbc.Row([
        # 左側框架（公司）
        dbc.Col([
            html.H3("Actron Datasheet"),
            dcc.Dropdown(
                id='company-dropdown',
                options=[{'label': k, 'value': v} for k, v in company_pdfs.items()],
                placeholder="Select Datasheet",
                style={'margin-bottom': '20px'}
            ),
            html.Iframe(
                id='company-pdf',
                src="",  # 初始為空
                style={"width": "100%", "height": "600px", "border": "none"}
            ),
            # 下載按鈕（本地 PDF）
            dbc.Button("下載 PDF", id='download-company-pdf-btn', color="primary", className="mt-2", style={'display': 'none'}),
            # 下載組件（本地 PDF）
            dcc.Download(id='download-company-pdf')
        ], width=6),

        # 右側框架（競爭對手）
        dbc.Col([
            html.H3("Benchmarking Reference Materials"),
            dcc.Dropdown(
                id='competitor-dropdown',
                options=[{'label': k, 'value': v} for k, v in competitor_pdfs.items()],
                placeholder="選擇競爭對手資料",
                style={'margin-bottom': '20px'}
            ),
            html.Iframe(
                id='competitor-pdf',
                src="",  # 初始為空
                style={"width": "100%", "height": "600px", "border": "none"}
            ),
            # 下載按鈕（本地 PDF）
            dbc.Button("下載 PDF", id='download-competitor-pdf-btn', color="primary", className="mt-2", style={'display': 'none'}),
            # 下載組件（本地 PDF）
            dcc.Download(id='download-competitor-pdf')
        ], width=6),
    ]),

    html.Hr(),  # 分隔線

    dbc.Row([
        dbc.Col([
            html.H3("對標競爭分析"),
            dash_table.DataTable(
                id='benchmark-table',
                columns=benchmark_columns,
                data=benchmark_data,
                style_table={'overflowX': 'auto'},
                style_header={
                    'backgroundColor': '#f7f7f7',  # 淺灰色背景
                    'fontWeight': 'bold',
                    'border': '1px solid #ddd'
                },
                style_cell={
                    'padding': '10px',
                    'textAlign': 'left',
                    'minWidth': '150px', 'width': '150px', 'maxWidth': '150px',
                    'backgroundColor': '#ffffff',
                    'border': '1px solid #ddd',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '14px',
                },
                filter_action="native",  # 啟用過濾
                sort_action="native",  # 啟用排序
                page_action="none",  # 不啟用分頁，因為數據量不大
                style_data_conditional=[]
            ),
            dbc.Button("下載表格為 CSV", id="download-button", color="secondary", className="mt-3"),
            dcc.Download(id="download-dataframe-csv")
        ], width=12)
    ], style={'margin-top': '50px'})
], fluid=True)

# 定義 Diagrams2 頁面的佈局（空白頁）
diagrams2_layout = dbc.Container([
    html.H2("Diagrams 2"),
    html.P("這是 Diagrams 2 的空白頁。"),

    # 一開始就啟動另一個 python 進程，執行 hh4any.py
    #html.Div(id='subprocess-feedback'),
], fluid=True)

# 定義 Diagrams1 頁面的佈局（整合 diagrams1 的內容）
def create_upload_card(card_title, subtitle, upload_id, graph_id):
    return dbc.Card(
        dbc.CardBody([
            html.H5(card_title, className="card-title", style={'textAlign': 'left'}),
            html.H6(subtitle, className="card-subtitle mb-2 text-muted", style={'textAlign': 'left'}),
            dcc.Upload(
                id=upload_id,
                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                }
            ),
            dcc.Graph(id=graph_id, config={'displayModeBar': False}),
            # 新增按鈕區域，傳入 graph_id 以便創建唯一 ID
            create_flet_like_buttons(graph_id)
        ]),
        className="shadow-sm border mb-4"
    )

def create_flet_like_buttons(graph_id):
    return dbc.Row([
        dbc.Col(
            dbc.Button(
                "Data",
                id={'type': 'Data', 'index': graph_id},  # graph_id 例如 'graph-tj25'
                color="primary",
                style={
                    'borderRadius': '10px',
                    'padding': '10px 40px',
                    'margin': '5px',
                    'boxShadow': '2px 2px 5px rgba(0,0,0,0.3)'
                },
                className="me-2",
                n_clicks=0
            ),
            width="auto"
        ),
        dbc.Col(
            dbc.Button(
                "Save Picture",
                id={'type': 'button2', 'graph_id': graph_id},
                color="secondary",
                style={
                    'borderRadius': '10px',
                    'padding': '10px 40px',
                    'margin': '5px',
                    'boxShadow': '2px 2px 5px rgba(0,0,0,0.3)'
                },
                className="me-2",
                n_clicks=0
            ),
            width="auto"
        )
    ], justify="start", className="g-0")

# 定義 Diagrams1 的整合佈局
diagrams1_layout = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(create_upload_card("IGBT, Output characteristics", "VGE = 15V, IC = f(VCE)", "upload-tj25",
                                           "graph-tj25"), md=6),
                dbc.Col(create_upload_card("IGBT, Output characteristics", "Tj = 25°C, IC = f(VCE)", "upload-tj150",
                                           "graph-tj150"), md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("IGBT, Output characteristics", "Tj = 150°C, IC = f(VCE)", "upload-tj175",
                                           "graph-tj175"), md=6),
                dbc.Col(create_upload_card("Diode, Forward characteristics", "IF = f(VF)", "upload-tjD", "graph-tjD"),
                        md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("IGBT, Switching losses vs. IC",
                                           "VGE = -8V / +15V, RG,on = 2.5 Ω, RG,off = 5.0 Ω, VCE = 400V, Eon & Eoff = f(Ic)",
                                           "upload-tjE", "graph-tjE"), md=6),
                dbc.Col(create_upload_card("IGBT, Switching losses vs. RG",
                                           "VGE = -8V / +15V, VCE = 400V, IC = 300A, Eon & Eoff = f(RG)", "upload-tjF",
                                           "graph-tjF"), md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("IGBT Capacitance characteristics",
                                           "VGE = 0V, Tj = 25°C, f = 100kHz, C = f(VCE)", "upload-tjG", "graph-tjG"),
                        md=6),
                dbc.Col(create_upload_card("NTC-Thermistor-temperature characteristics", "R = f(TNTC)", "upload-extra1",
                                           "graph-extra1"), md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("Diode, Switching losses vs. IF", "RG = 2.5 Ω, VR = 400V, Erec = f(IF)",
                                           "upload-extra2", "graph-extra2"), md=6),
                dbc.Col(create_upload_card("Diode, Switching losses vs. RG", "IF = 300A, VR = 400V, Erec = f(RG)",
                                           "upload-extra3", "graph-extra3"), md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("Reverse bias safe operating area (RBSOA)",
                                           "VGE = -8V / + 15V, RG,off = 5.0 Ω, Tj = 175°C", "upload-extra4",
                                           "graph-extra4"), md=6),
                dbc.Col(create_upload_card("IGBT Total Gate Charge characteristic",
                                           "VCE = 400 V, IC = 300A, Tj = 25°C, VGE = f(QG)", "upload-extra5",
                                           "graph-extra5"), md=6),
            ], justify="center", className="mb-4"),
            dbc.Row([
                dbc.Col(create_upload_card("IGBT Transient thermal impedance",
                                           "ZthJF = f(tP), ΔV/Δt = 10 dm3/min, TF = 70°C", "upload-extra6",
                                           "graph-extra6"), md=6),
                dbc.Col(create_upload_card("Diode Transient thermal impedance",
                                           "ZthJF = f(tP), ΔV/Δt = 10 dm3/min, TF = 70°C", "upload-extra7",
                                           "graph-extra7"), md=6),
            ], justify="center", className="mb-4"),
        ], width=10, className="mx-auto")  # 設定主區域寬度為10，並居中
    ]),
    # 新增模態窗口，用於顯示 CSV 數據
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("CSV Data")),
            dbc.ModalBody(id="modal-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="data-modal",
        is_open=False,
        size="xl",
        scrollable=True,
    ),
    # 新增下載組件和儲存組件
    dcc.Download(id='download-image'),
    dcc.Store(id='download-store'),
])

# 定義 Contact 頁面的佈局
contact_layout = dbc.Container(
    [
        html.H2("聯絡我們", className="mt-4"),
        html.P("這是聯絡頁面的內容。"),
    ],
    fluid=True,
)

# 定義 Diagrams3 頁面的佈局（整合 diagrams3 的內容）
# 定義回調函數：Diagrams3 的功能
callbacks_diagrams3(app)

# 定義回調函數：根據 URL 顯示對應的頁面
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)

def display_page(pathname):
    if pathname.startswith('/details/'):
        # 提取 Type Name
        type_name = pathname.split('/details/')[1]
        # 這裡可以根據 Type Name 顯示詳細頁面
        return dbc.Container([
            html.H2(f"Details for {type_name}", className="mt-4"),
            html.P(f"這是 {type_name} 的詳細頁面。"),
            dcc.Link("返回首頁", href='/')
        ], fluid=True)
    elif pathname == '/diagrams1':
        return diagrams1_layout
    elif pathname == '/diagrams2':
        return diagrams2_layout
    elif pathname == '/diagrams3':
        return diagrams3_layout  # 顯示 Diagrams3 頁面
    elif pathname == '/contact':
        return contact_layout
    else:
        return home_layout

# 定義回調函數：根據選擇過濾並更新 AgGrid 的 rowData
@app.callback(
    Output("grid", "rowData"),
    Output("store-selected", "data"),
    Output("no-data-message", "children"),
    Input("module-dropdown", "value"),
    Input("year-radio", "value"),
    Input("power-dropdown", "value"),
)
def update_grid(selected_module, selected_year, selected_power):
    print(f"選擇的模組: {selected_module}, 年份: {selected_year}, Power: {selected_power}")

    # 過濾條件
    filter_conditions = (df['Report Year'] == selected_year)

    if selected_module != 'All':
        filter_conditions &= (df["Module"] == selected_module)

    if selected_power != 'All':
        selected_power_str = str(selected_power).strip()
        df["Power"] = df["Power"].astype(str).str.strip()
        filter_conditions &= (df["Power"] == selected_power_str)

    # 過濾資料
    filtered_df = df[filter_conditions].copy()

    # 如果需要按照 Power 數值排序（假設 'Power' 是以數字加 'V' 表示，如 '123V'）
    if not filtered_df.empty:
        filtered_df['Power_num'] = filtered_df['Power'].str.extract(r'(\d+)V', expand=False).astype(float)
        filtered_df['Power_num'] = filtered_df['Power_num'].fillna(float('inf'))
        filtered_df = filtered_df.sort_values(by='Power_num', ascending=True)
        filtered_df = filtered_df.drop(columns=['Power_num'])

    # 將 DataFrame 轉換為字典列表
    records = filtered_df.fillna('').to_dict("records")

    if not records:
        no_data_message = "沒有符合條件的資料。"
    else:
        no_data_message = ""

    store_data = records[:1] if records else []

    return records, store_data, no_data_message

# 定義回調函數：生成柱狀圖
@app.callback(
    Output("bar-chart-card", "children"),
    Input("store-selected", "data")
)
def make_bar_chart(data):
    if not data:
        fig = {}
    else:
        data = data[0]
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        male_percentages = [data.get(f'{q} Male', 0) for q in quarters]
        female_percentages = [data.get(f'{q} Female', 0) for q in quarters]

        quarter_labels = {
            'Q1': 'Lower (Q1)',
            'Q2': 'Lower Middle (Q2)',
            'Q3': 'Upper Middle (Q3)',
            'Q4': 'Upper (Q4)'
        }
        custom_labels = [quarter_labels[q] for q in quarters]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=custom_labels,
            x=male_percentages,
            name='Male',
            orientation='h',
            marker=dict(color='#19A0AA'),
            text=male_percentages,
            textfont_size=14,
            textposition='inside',
        ))

        fig.add_trace(go.Bar(
            y=custom_labels,
            x=female_percentages,
            name='Female',
            orientation='h',
            marker=dict(color='#F15F36'),
            text=female_percentages,
            textfont_size=14,
            textposition='inside',
        ))

        fig.update_layout(
            xaxis=dict(ticksuffix='%'),
            yaxis=dict(title='Quartile', categoryorder='array', categoryarray=quarters),
            barmode='stack',
            template='plotly_white',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=-0.25,
                xanchor='center',
                x=0.5,
                traceorder='normal'
            ),
            margin=dict(l=10, r=10, t=10, b=10),
        )

    return dbc.Card([
        dbc.CardHeader(html.H2("Analyze"), className="text-center"),
        dcc.Graph(figure=fig, style={"height": 250}, config={'displayModeBar': False})
    ])

# 定義回調函數：處理 Type Name 的點擊事件
@app.callback(
    Output('url', 'pathname'),  # 使用 pathname 來導航
    Input('datasheet-table', 'active_cell'),
    State('datasheet-table', 'data'),
)
def navigate_on_click(active_cell, data):
    if active_cell:
        row = active_cell['row']
        column = active_cell['column_id']
        if column == 'Type Name':
            # 提取 Type Name（移除前綴的圖示 Markdown）
            type_name = re.sub(r'^!\[icon\]\(/assets/inbox-document-text\.png\)\s+', '', data[row]['Type Name'])
            # 定義要導航到的 URL，這裡以 '/details/{Type Name}' 為例，您可以更改為實際的連結
            target_path = f"/details/{type_name}"
            return target_path
    return dash.no_update

# 定義回調函數：切換各個 Collapse 的顯示狀態
@app.callback(
    [
        Output("collapse-datasheet", "is_open"),
        Output("collapse-visualization", "is_open"),
        Output("collapse-diagrams", "is_open"),
        Output("collapse-benchmarking", "is_open"),
    ],
    [
        Input("collapse-datasheet-button", "n_clicks"),
        Input("collapse-visualization-button", "n_clicks"),
        Input("collapse-diagrams-button", "n_clicks"),
        Input("collapse-benchmarking-button", "n_clicks"),
    ],
    [
        State("collapse-datasheet", "is_open"),
        State("collapse-visualization", "is_open"),
        State("collapse-diagrams", "is_open"),
        State("collapse-benchmarking", "is_open"),
    ],
)
def toggle_collapse(n_datasets, n_visualization, n_diagrams, n_benchmarking,
                   is_open_datasets, is_open_visualization, is_open_diagrams, is_open_benchmarking):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, False, False, False
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "collapse-datasheet-button":
        return not is_open_datasets, is_open_visualization, is_open_diagrams, is_open_benchmarking
    elif button_id == "collapse-visualization-button":
        return is_open_datasets, not is_open_visualization, is_open_diagrams, is_open_benchmarking
    elif button_id == "collapse-diagrams-button":
        return is_open_datasets, is_open_visualization, not is_open_diagrams, is_open_benchmarking
    elif button_id == "collapse-benchmarking-button":
        return is_open_datasets, is_open_visualization, is_open_diagrams, not is_open_benchmarking
    return False, False, False, False

# ================== Diagrams1 的整合開始 ==================

# 回調函數：A 卡片
@app.callback(
    Output('graph-tj25', 'figure'),
    Input('upload-tj25', 'contents'),
    State('upload-tj25', 'filename')
)
def update_graph_a(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 確保 CSV 欄位名稱對應正確
    temperatures = {
        'Tj = 25℃': {'ic_col': 'IC_Tj = 25℃', 'vce_col': 'VCE_Tj = 25℃', 'dash': 'solid'},
        'Tj = 150℃': {'ic_col': 'IC_Tj = 150℃', 'vce_col': 'VCE_Tj = 150℃', 'dash': 'dash'},
        'Tj = 175℃': {'ic_col': 'IC_Tj = 175℃', 'vce_col': 'VCE_Tj = 175℃', 'dash': 'dashdot'}
    }

    # 檢查 CSV 是否包含這些欄位，並添加曲線
    for temp, params in temperatures.items():
        ic_col = params['ic_col']
        vce_col = params['vce_col']

        if ic_col in df.columns and vce_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[vce_col], y=df[ic_col],
                mode='lines',
                name=temp,
                line=dict(color='black', dash=params['dash'])  # 設定線型
            ))
        else:
            print(f"❌ 缺少欄位: {ic_col} 或 {vce_col}")

    # 設定圖例位置到左上角
    fig.update_layout(
        title="Static",
        xaxis_title="V<sub>CE</sub> (V)",
        yaxis_title="I<sub>C</sub> (A)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",

        # 設定 X 軸範圍、刻度 & 框線
        xaxis=dict(
            range=[0, 3.0],  # 設定範圍 0 ~ 3.0
            tickvals=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),

        # 設定 Y 軸範圍、刻度 & 框線
        yaxis=dict(
            range=[0, 1600],  # 設定範圍 0 ~ 1600
            tickvals=[0, 200, 400, 600, 800, 1000, 1200, 1400, 1600],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),
    )

    return fig



# 回調函數：B 卡片
@app.callback(
    Output('graph-tj150', 'figure'),
    Input('upload-tj150', 'contents'),
    State('upload-tj150', 'filename')
)
def update_graph_b(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 確保 CSV 欄位名稱對應正確
    voltages = {
        'VGE = 9V': {'ic_col': 'IC_9V', 'vce_col': 'VCE_9V', 'dash': 'solid'},
        'VGE = 11V': {'ic_col': 'IC_11V', 'vce_col': 'VCE_11V', 'dash': 'dash'},
        'VGE = 13V': {'ic_col': 'IC_13V', 'vce_col': 'VCE_13V', 'dash': 'dot'},
        'VGE = 15V': {'ic_col': 'IC_15V', 'vce_col': 'VCE_15V', 'dash': 'dashdot'},
        'VGE = 17V': {'ic_col': 'IC_17V', 'vce_col': 'VCE_17V', 'dash': 'longdash'},
        'VGE = 19V': {'ic_col': 'IC_19V', 'vce_col': 'VCE_19V', 'dash': 'longdashdot'}
    }

    # 檢查 CSV 是否包含欄位，生成曲線
    for vge, params in voltages.items():
        ic_col = params['ic_col']
        vce_col = params['vce_col']

        if ic_col in df.columns and vce_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[vce_col], y=df[ic_col],
                mode='lines',
                name=vge,
                line=dict(color='black', dash=params['dash'])  # 設定線型
            ))
        else:
            print(f"❌ 缺少欄位: {ic_col} 或 {vce_col}")

    # 設定圖例位置到左上角
    fig.update_layout(
        title="Static",
        xaxis_title="V<sub>CE</sub> (V)",
        yaxis_title="I<sub>C</sub> (A)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",

        # 設定 X 軸範圍、刻度 & 框線
        xaxis=dict(
            range=[0, 3.5],  # 設定範圍 0 ~ 3.5
            tickvals=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),

        # 設定 Y 軸範圍、刻度 & 框線
        yaxis=dict(
            range=[0, 1600],  # 設定範圍 0 ~ 1600
            tickvals=[0, 200, 400, 600, 800, 1000, 1200, 1400, 1600],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),
    )

    return fig



# 回調函數：C 卡片
@app.callback(
    Output('graph-tj175', 'figure'),
    Input('upload-tj175', 'contents'),
    State('upload-tj175', 'filename')
)
def update_graph_c(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # CSV 欄位名稱對應正確
    voltages = {
        'VGE = 9V': {'ic_col': 'IC_9V', 'vce_col': 'VCE_9V', 'dash': 'solid'},
        'VGE = 11V': {'ic_col': 'IC_11V', 'vce_col': 'VCE_11V', 'dash': 'dash'},
        'VGE = 13V': {'ic_col': 'IC_13V', 'vce_col': 'VCE_13V', 'dash': 'dot'},
        'VGE = 15V': {'ic_col': 'IC_15V', 'vce_col': 'VCE_15V', 'dash': 'dashdot'},
        'VGE = 17V': {'ic_col': 'IC_17V', 'vce_col': 'VCE_17V', 'dash': 'longdash'},
        'VGE = 19V': {'ic_col': 'IC_19V', 'vce_col': 'VCE_19V', 'dash': 'longdashdot'}
    }

    # 檢查 CSV 是否包含這些欄位，並添加曲線
    for vge, params in voltages.items():
        ic_col = params['ic_col']
        vce_col = params['vce_col']

        if ic_col in df.columns and vce_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[vce_col], y=df[ic_col],
                mode='lines',
                name=vge,
                line=dict(color='black', dash=params['dash'])  # 設定線型
            ))
        else:
            print(f"❌ 缺少欄位: {ic_col} 或 {vce_col}")

    # 設定圖例位置到左上角
    fig.update_layout(
        title="Static",
        xaxis_title="V<sub>CE</sub> (V)",
        yaxis_title="I<sub>C</sub> (A)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",

        # 設定 X 軸範圍、刻度 & 框線
        xaxis=dict(
            range=[0, 3.5],  # 設定範圍 0 ~ 3.5
            tickvals=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),

        # 設定 Y 軸範圍、刻度 & 框線
        yaxis=dict(
            range=[0, 1600],  # 設定範圍 0 ~ 1600
            tickvals=[0, 200, 400, 600, 800, 1000, 1200, 1400, 1600],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),
    )

    return fig



# 回調函數：D 卡片
@app.callback(
    Output('graph-tjD', 'figure'),
    Input('upload-tjD', 'contents'),
    State('upload-tjD', 'filename')
)
def update_graph_d(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 設定三條線的樣式
    conditions = {
        'Tj = 25℃': {'if_col': 'If_25℃', 'vf_col': 'Vf_25℃', 'dash': 'solid'},
        'Tj = 150℃': {'if_col': 'If_150℃', 'vf_col': 'Vf_150℃', 'dash': 'dash'},
        'Tj = 175℃': {'if_col': 'If_175℃', 'vf_col': 'Vf_175℃', 'dash': 'dashdot'}
    }

    for condition, params in conditions.items():
        if_col = params['if_col']
        vf_col = params['vf_col']

        if if_col in df.columns and vf_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[vf_col], y=df[if_col],
                mode='lines',
                name=condition,
                line=dict(color='black', dash=params['dash'])  # 設定線型
            ))

    # 設定圖例位置到左上角
    fig.update_layout(
        title="Static",
        xaxis_title="V<sub>F</sub> (V)",
        yaxis_title="I<sub>F</sub> (A)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",

        # 設定 X 軸範圍、刻度 & 框線
        xaxis=dict(
            range=[0, 3.5],  # 設定範圍 0 ~ 3.5
            tickvals=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),

        # 設定 Y 軸範圍、刻度 & 框線
        yaxis=dict(
            range=[0, 1600],  # 設定範圍 0 ~ 1600
            tickvals=[0, 200, 400, 600, 800, 1000, 1200, 1400, 1600],  # 設定刻度
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True,  # 設定四周框線
            showline=True, linewidth=1, linecolor='black'
        ),
    )

    return fig



# E 卡片的回調函數
@app.callback(
    Output('graph-tjE', 'figure'),
    Input('upload-tjE', 'contents'),
    State('upload-tjE', 'filename')
)
def update_graph_e(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 定義 6 條不同的曲線對應的 Eon/Eoff
    line_styles = {
        #'Eon_25℃': {'ic_col': 'IC(A)_25℃', 'e_col': 'Eon(mJ)_25℃', 'dash': 'solid'},
        #'Eoff_25℃': {'ic_col': 'IC(A)_25℃', 'e_col': 'Eoff(mJ)_25℃', 'dash': 'dash'},
        'Eon_150℃': {'ic_col': 'IC(A)_150℃', 'e_col': 'Eon(mJ)_150℃', 'dash': 'dot'},
        'Eoff_150℃': {'ic_col': 'IC(A)_150℃', 'e_col': 'Eoff(mJ)_150℃', 'dash': 'dashdot'},
        'Eon_175℃': {'ic_col': 'IC(A)_175℃', 'e_col': 'Eon(mJ)_175℃', 'dash': 'longdash'},
        'Eoff_175℃': {'ic_col': 'IC(A)_175℃', 'e_col': 'Eoff(mJ)_175℃', 'dash': 'longdashdot'}
    }

    # 依序添加線條
    for name, params in line_styles.items():
        ic_col = params['ic_col']
        e_col = params['e_col']

        if ic_col in df.columns and e_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[ic_col], y=df[e_col],
                mode='lines',
                name=name,
                line=dict(color='black', dash=params['dash'])
            ))

    # 加入 X 軸與 Y 軸的 0 軸線
    zero_line_shapes = [
        dict(type='line', x0=0, x1=0, y0=0, y1=1, xref='x', yref='paper', line=dict(color='black', width=1)),
        dict(type='line', x0=0, x1=1, y0=0, y1=0, xref='paper', yref='y', line=dict(color='black', width=1))
    ]

    # 設定 X 軸與 Y 軸範圍，符合圖片設定
    fig.update_layout(
        title="Switching Losses vs IC(A)",
        xaxis_title="I<sub>C</sub>(A)",
        yaxis_title="E (mJ)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black',
            range=[0, 1400], tickvals=list(range(0, 1401, 200)),
            mirror=True, showline=True, linewidth=1, linecolor='black'  # 四周黑色框線
        ),
        yaxis=dict(
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black',
            range=[0, 140], tickvals=list(range(0, 141, 20)),
            mirror=True, showline=True, linewidth=1, linecolor='black'  # 四周黑色框線
        ),
        shapes=zero_line_shapes  # 加入 0 軸線
    )

    return fig


# F 卡片的回調函數
@app.callback(
    Output('graph-tjF', 'figure'),
    Input('upload-tjF', 'contents'),
    State('upload-tjF', 'filename')
)
def update_graph_f(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 定義 6 條不同的曲線對應的 Eon/Eoff
    line_styles = {
        #'Eon_25℃': {'rg_col': 'RG_25℃', 'e_col': 'Eon(mJ)_25℃', 'dash': 'solid'},
        #'Eoff_25℃': {'rg_col': 'RG_25℃', 'e_col': 'Eoff(mJ)_25℃', 'dash': 'dash'},
        'Eon_150℃': {'rg_col': 'RG_150℃', 'e_col': 'Eon(mJ)_150℃', 'dash': 'dot'},
        'Eoff_150℃': {'rg_col': 'RG_150℃', 'e_col': 'Eoff(mJ)_150℃', 'dash': 'dashdot'},
        'Eon_175℃': {'rg_col': 'RG_175℃', 'e_col': 'Eon(mJ)_175℃', 'dash': 'longdash'},
        'Eoff_175℃': {'rg_col': 'RG_175℃', 'e_col': 'Eoff(mJ)_175℃', 'dash': 'longdashdot'}
    }

    # 依序添加線條
    for name, params in line_styles.items():
        rg_col = params['rg_col']
        e_col = params['e_col']

        if rg_col in df.columns and e_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[rg_col], y=df[e_col],
                mode='lines',
                name=name,
                line=dict(color='black', dash=params['dash'])
            ))

    # 加入 X 軸與 Y 軸的 0 軸線
    zero_line_shapes = [
        dict(type='line', x0=0, x1=0, y0=0, y1=1, xref='x', yref='paper', line=dict(color='black', width=1)),
        dict(type='line', x0=0, x1=1, y0=0, y1=0, xref='paper', yref='y', line=dict(color='black', width=1))
    ]

    # 設定 X 軸與 Y 軸範圍，符合圖片設定
    fig.update_layout(
        title="Switching Losses vs RG",
        xaxis_title="R<sub>G</sub> (Ω)",
        yaxis_title="E (mJ)",
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(
            x=0.01,  # 左上角對齊
            y=0.99,  # 靠近頂部
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        plot_bgcolor="white",
        xaxis=dict(
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black',
            range=[0, 25], tickvals=list(range(0, 26, 2)),
            mirror=True, showline=True, linewidth=1, linecolor='black'  # 四周黑色框線
        ),
        yaxis=dict(
            showgrid=True, gridcolor='lightgray',
            zeroline=True, zerolinecolor='black',
            range=[0, 120], tickvals=list(range(0, 121, 20)),
            mirror=True, showline=True, linewidth=1, linecolor='black'  # 四周黑色框線
        ),
        shapes=zero_line_shapes  # 加入 0 軸線
    )

    return fig

# 回調函數：G 卡片
@app.callback(
    Output('graph-tjG', 'figure'),
    Input('upload-tjG', 'contents'),
    State('upload-tjG', 'filename')
)
def update_graph_g(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or not {'VCE', 'Cies', 'Coes', 'Cres'}.issubset(df.columns):
        return go.Figure()

    fig = go.Figure()

    # 添加三條不同線型的曲線
    fig.add_trace(go.Scatter(
        x=df['VCE'], y=df['Cies'],
        mode='lines', name='Cies',
        line=dict(color='black', width=2, dash='solid')  # 實線
    ))

    fig.add_trace(go.Scatter(
        x=df['VCE'], y=df['Coes'],
        mode='lines', name='Coes',
        line=dict(color='black', width=2, dash='dash')  # 虛線
    ))

    fig.add_trace(go.Scatter(
        x=df['VCE'], y=df['Cres'],
        mode='lines', name='Cres',
        line=dict(color='black', width=2, dash='dashdot')  # 點畫線
    ))

    # 設定圖表格式，確保與圖片一致
    fig.update_layout(
        title="Dynamic Capacitance Characteristics",
        xaxis_title="V<sub>CE</sub> (V)",
        yaxis_title="C (nF)",
        margin=dict(l=40, r=20, t=30, b=40),
        legend_title="Conditions",
        plot_bgcolor="white",
        font=dict(size=12),
        xaxis=dict(
            showgrid=True, gridcolor='lightgray', gridwidth=0.5,
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True, linecolor="black", linewidth=1,
            ticks="inside", ticklen=5,
            range=[0, 800], tickvals=list(range(0, 801, 100))
        ),
        yaxis=dict(
            showgrid=True, gridcolor='lightgray', gridwidth=0.5,
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            mirror=True, linecolor="black", linewidth=1,
            ticks="inside", ticklen=5,
            type='log', range=[-1, 2],
            tickvals=[0.1, 1, 10, 100], tickmode='array'
        ),
        legend=dict(bordercolor="black", borderwidth=1),
    )

    return fig


# 回調函數：H 卡片
@app.callback(
    Output('graph-extra1', 'figure'),
    Input('upload-extra1', 'contents'),
    State('upload-extra1', 'filename')
)
def update_graph_h(contents, filename):
    if contents is None:
        return go.Figure()

    # 解析上傳的數據
    df = parse_contents(contents, filename)
    if df is None:
        return go.Figure()

    # 檢查必要的欄位是否存在
    expected_columns = {'TNTC(℃)', 'R(Ω)'}
    if not expected_columns.issubset(df.columns):
        print("數據缺少必要的欄位:", expected_columns)
        return go.Figure()

    # 創建圖表
    fig = go.Figure()

    # 繪製黑色實線曲線
    fig.add_trace(go.Scatter(
        x=df['TNTC(℃)'],
        y=df['R(Ω)'],
        mode='lines',   # 僅使用線條
        name='R(typ)',   # 圖例名稱
        line=dict(color='black', width=2)  # 黑色實線，寬度 2
    ))

    # 設定圖表樣式和軸刻度
    fig.update_layout(
        title="NTC-Thermistor Temperature Characteristics",
        xaxis_title="T<sub>NTC</sub> (℃)",
        yaxis_title="R (Ω)",
        margin=dict(l=50, r=50, t=50, b=50),  # 調整邊距以容納框線
        plot_bgcolor="white",
        font=dict(size=12),  # 設定整體字體大小
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            tickmode='array',
            tickvals=[0, 25, 50, 75, 100, 125, 150, 175],  # 設定 x 軸刻度
            title_font=dict(size=16),
            showline=True,       # 顯示 x 軸線
            mirror=True,         # 軸線鏡像對稱（四周都有線）
            linecolor='black',   # 軸線顏色
            linewidth=2,         # 軸線寬度
            zeroline=True,       # 顯示 x 軸零線
            zerolinecolor='black',  # 設定零線顏色
            zerolinewidth=2      # 零線寬度
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray',
            type='log',  # 使用對數刻度
            tickmode='array',
            tickvals=[100000, 10000, 1000, 100, 10],  # 調整 y 軸區間
            title_font=dict(size=16),
            showline=True,       # 顯示 y 軸線
            mirror=True,         # 軸線鏡像對稱（四周都有線）
            linecolor='black',   # 軸線顏色
            linewidth=2,         # 軸線寬度
            zeroline=True,       # 顯示 y 軸零線
            zerolinecolor='black',  # 設定零線顏色
            zerolinewidth=2      # 零線寬度
        ),
        legend=dict(
            title="",  # 移除圖例標題
            x=0.02,    # x 座標 (0 左邊, 1 右邊)
            y=0.98,    # y 座標 (0 底部, 1 頂部)
            xanchor="left",  # x 座標錨點
            yanchor="top",   # y 座標錨點
            bgcolor="rgba(255, 255, 255, 0.8)",  # 半透明白色背景
            bordercolor="black",  # 黑色邊框
            borderwidth=1,        # 邊框寬度
            font=dict(size=12),    # 字體大小
            orientation="v",       # 垂直排列
            traceorder="normal",   # 圖例順序
        ),
        showlegend=True,  # 確保顯示圖例
        shapes=[
             #水平參考線（x 軸）
            dict(
                type="line",
                x0=0,
                y0=1,
                x1=175,
                y1=1,
                line=dict(color="black", width=1, dash="dash")
            ),
             #垂直參考線（y 軸）
            dict(
                type="line",
                x0=50,
                y0=10,
                x1=50,
                y1=100000,
                line=dict(color="black", width=1, dash="dash")
            )
        ]
    )

    return fig




# 回調函數：I 卡片
@app.callback(
    Output('graph-extra2', 'figure'),
    Input('upload-extra2', 'contents'),
    State('upload-extra2', 'filename')
)
def update_graph_i(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 定義每條線段的對應欄位與線型樣式
    line_styles = {
        'Erec, Tj = 25℃': {'ic_col': 'IC(A)', 'erec_col': 'Erec(mJ)', 'dash': 'solid'},
        'Erec, Tj = 150℃': {'ic_col': 'IC(A).1', 'erec_col': 'Erec(mJ).1', 'dash': 'dash'},
        'Erec, Tj = 175℃': {'ic_col': 'IC(A).2', 'erec_col': 'Erec(mJ).2', 'dash': 'dot'}
    }

    # 確保數據中包含所需的欄位
    required_columns = set(sum([[v['ic_col'], v['erec_col']] for v in line_styles.values()], []))
    if not required_columns.issubset(df.columns):
        print("缺少必要的欄位:", required_columns - set(df.columns))
        return go.Figure()

    # 依據定義的樣式逐條添加線段
    for set_name, params in line_styles.items():
        fig.add_trace(go.Scatter(
            x=df[params['ic_col']],
            y=df[params['erec_col']],
            mode='lines',
            name=set_name,
            line=dict(color='black', dash=params['dash'])
        ))

    # 加入 X 軸與 Y 軸的 0 軸線 (黑色框線)
    zero_line_shapes = [
        dict(type='line', x0=0, x1=0, y0=0, y1=1, xref='x', yref='paper', line=dict(color='black', width=1)),
        dict(type='line', x0=0, x1=1, y0=0, y1=0, xref='paper', yref='y', line=dict(color='black', width=1))
    ]

    # 設定 X 軸與 Y 軸範圍、刻度與格式
    fig.update_layout(
        title="Erec vs IF(A)",
        xaxis_title="I<sub>F</sub> (A)",
        yaxis_title="E (mJ)",
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="white",
        xaxis=dict(
            range=[0, 1400],  # 設定 X 軸範圍
            tickvals=list(range(0, 1401, 200)),  # 設定刻度 0, 200, 400, ..., 1400
            showgrid=True, gridcolor='lightgray',
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        yaxis=dict(
            range=[0, 16],  # 設定 Y 軸範圍
            tickvals=list(range(0, 17, 2)),  # 設定刻度 0, 2, 4, ..., 16
            showgrid=True, gridcolor='lightgray',
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        legend=dict(
            x=0.02, y=0.98,
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        shapes=zero_line_shapes
    )

    return fig


# 回調函數：J 卡片
@app.callback(
    Output('graph-extra3', 'figure'),
    Input('upload-extra3', 'contents'),
    State('upload-extra3', 'filename')
)
def update_graph_j(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)
    if df is None or len(df.columns) < 2:
        return go.Figure()

    fig = go.Figure()

    # 定義 Erec 在不同溫度下的線條樣式
    line_styles = {
        'Erec 25℃': {'rg_col': 'RG_25℃', 'erec_col': 'Erec(mJ)_25℃', 'dash': 'solid'},
        'Erec 150℃': {'rg_col': 'RG_150℃', 'erec_col': 'Erec(mJ)_150℃', 'dash': 'dash'},
        'Erec 175℃': {'rg_col': 'RG_175℃', 'erec_col': 'Erec(mJ)_175℃', 'dash': 'dot'}
    }

    # 確保數據中包含所需的欄位
    required_columns = set(sum([[v['rg_col'], v['erec_col']] for v in line_styles.values()], []))
    if not required_columns.issubset(df.columns):
        print("缺少必要的欄位:", required_columns - set(df.columns))
        return go.Figure()

    # 依據定義的樣式逐條添加線段
    for set_name, params in line_styles.items():
        fig.add_trace(go.Scatter(
            x=df[params['rg_col']],
            y=df[params['erec_col']],
            mode='lines',
            name=set_name,
            line=dict(color='black', dash=params['dash'])
        ))

    # 加入 X 軸與 Y 軸的 0 軸線 (黑色框線)
    zero_line_shapes = [
        dict(type='line', x0=0, x1=0, y0=0, y1=1, xref='x', yref='paper', line=dict(color='black', width=1)),
        dict(type='line', x0=0, x1=1, y0=0, y1=0, xref='paper', yref='y', line=dict(color='black', width=1))
    ]

    # 設定 X 軸與 Y 軸範圍、刻度與格式
    fig.update_layout(
        title="Erec vs RG (Ω)",
        xaxis_title="R<sub>G</sub> (Ω)",
        yaxis_title="E (mJ)",
        margin=dict(l=40, r=20, t=40, b=40),
        plot_bgcolor="white",
        xaxis=dict(
            range=[0, 25],  # 設定 X 軸範圍
            tickvals=list(range(0, 26, 5)),  # 設定刻度 0, 5, 10, ..., 25
            showgrid=True, gridcolor='lightgray',
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        yaxis=dict(
            range=[0, 16],  # 設定 Y 軸範圍
            tickvals=list(range(0, 17, 2)),  # 設定刻度 0, 2, 4, ..., 16
            showgrid=True, gridcolor='lightgray',
            showline=True, linewidth=1, linecolor='black', mirror=True
        ),
        legend=dict(
            x=0.02, y=0.98,
            bgcolor="white",
            bordercolor="black",
            borderwidth=2
        ),
        shapes=zero_line_shapes
    )

    return fig



# 回調函數：K 卡片
@app.callback(
    Output('graph-extra4', 'figure'),
    Input('upload-extra4', 'contents'),
    State('upload-extra4', 'filename')
)
def update_graph_k(contents, filename):
    if contents is None:
        return go.Figure()

    df = parse_contents(contents, filename)

    # 確保數據包含必要的欄位
    required_columns = ['VCE_Chip', 'IC_Chip', 'VCE_Module', 'IC_Module']
    if df is None or not all(col in df.columns for col in required_columns):
        print("Missing required columns:", df.columns)
        return go.Figure()

    fig = go.Figure()

    # 添加 Chip 線
    fig.add_trace(go.Scatter(
        x=df['VCE_Chip'], y=df['IC_Chip'],
        mode='lines', name='IC, Chip',
        line=dict(color='black', dash='solid')  # 實線
    ))

    # 添加 Module 線
    fig.add_trace(go.Scatter(
        x=df['VCE_Module'], y=df['IC_Module'],
        mode='lines', name='IC, Module',
        line=dict(color='black', dash='dash')  # 虛線
    ))


    # 更新圖表佈局
    fig.update_layout(
        title="",  # 不需要標題
        xaxis_title="V<sub>CE</sub> (V)",  # X 軸標籤
        yaxis_title="I<sub>C</sub> (A)",  # Y 軸標籤
        margin=dict(l=60, r=20, t=20, b=50),  # 控制邊界間距
        plot_bgcolor="white",  # 白色背景
        font=dict(size=12),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            linecolor="black",  # X 軸線條顏色
            linewidth=1,
            mirror=True,  # 顯示上方和下方軸線
            tickvals=list(range(0, 901, 100)),  # 設定刻度
            range=[0, 800]  # 設定 X 軸範圍
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgray",
            linecolor="black",  # Y 軸線條顏色
            linewidth=1,
            mirror=True,  # 顯示左方和右方軸線
            tickvals=list(range(0, 1901, 200)),  # 設定刻度
            range=[0, 1800]  # 設定 Y 軸範圍
        ),
        legend=dict(
            x=0.02, y=0.89,  # 圖例位置
            bgcolor="white",  # 白色背景
            bordercolor="black",  # 黑色邊框
            borderwidth=2  # 邊框寬度
        )
    )

    return fig


# 回調函數：L 卡片
@app.callback(
    Output('graph-extra5', 'figure'),
    Input('upload-extra5', 'contents'),
    State('upload-extra5', 'filename')
)
def update_graph_l(contents, filename):
    if contents is None:
        return go.Figure()

    # 解析上傳的數據
    df = parse_contents(contents, filename)

    # 確保數據包含必要的欄位
    required_columns = ['QG(μC)_25℃', 'VGE(V)_25℃']
    if df is None or not all(col in df.columns for col in required_columns):
        print("缺少必要的欄位:", required_columns)
        return go.Figure()

    # 創建圖表
    fig = go.Figure()

    # 添加曲線
    fig.add_trace(go.Scatter(
        x=df['Q<sub>G</sub>(μC)_25℃'],
        y=df['V<sub>GE</sub>(V)_25℃'],
        mode='lines',
        name='Gate Charge(QG)',  # 設置曲線名稱
        line=dict(color='black', width=2)  # 黑色實線
    ))

    # 更新圖表樣式
    fig.update_layout(
        title="",  # 移除標題
        xaxis_title="QG (μC)",  # x軸標籤
        yaxis_title="VGE (V)",  # y軸標籤
        margin=dict(l=50, r=20, t=10, b=50),  # 邊距調整
        plot_bgcolor="white",  # 白色背景
        font=dict(size=12),  # 字體大小
        xaxis=dict(
            showgrid=True, gridcolor='lightgray', gridwidth=1,
            mirror=True, linecolor="black", linewidth=1,
            ticks="inside", ticklen=5,
            range=[0, 2], tickvals=[0.0, 0.4, 0.8, 1.2, 1.6, 2.0]  # 設定範圍
        ),
        yaxis=dict(
            showgrid=True, gridcolor='lightgray', gridwidth=1,
            mirror=True, linecolor="black", linewidth=1,
            ticks="inside", ticklen=5,
            range=[-8, 16], tickvals=[-8, -4, 0, 4, 8, 12, 16]  # 設定範圍
        ),
        legend=dict(
            title="",  # 移除圖例標題
            x=0.02,  # x座標 (0 左邊, 1 右邊)
            y=0.98,  # y座標 (0 底部, 1 頂部)
            xanchor="left",  # x座標錨點
            yanchor="top",   # y座標錨點
            bgcolor="rgba(255, 255, 255, 0.8)",  # 半透明白色背景
            bordercolor="black",  # 黑色邊框
            borderwidth=1,  # 邊框寬度
            font=dict(size=12),  # 字體大小
            orientation="v",  # 垂直排列
            traceorder="normal",  # 圖例順序
        ),
        showlegend=True  # 確保顯示圖例
    )

    return fig




# M 卡片的回調函數
@app.callback(
    Output('graph-extra6', 'figure'),
    Input('upload-extra6', 'contents'),
    State('upload-extra6', 'filename')
)
def update_graph_m(contents, filename):
    if contents is None:
        return go.Figure()

    # 解析上傳的數據
    df = parse_contents(contents, filename)

    # 確保數據包含必要的欄位
    required_columns = ['t [s]', 'Zth (t)']
    if df is None or not all(col in df.columns for col in required_columns):
        return go.Figure()

    # 建立圖表
    fig = go.Figure()

    # 添加折線圖
    fig.add_trace(go.Scatter(
        x=df['t [s]'],
        y=df['Zth (t)'],
        mode='lines',
        name='ZthJF : IGBT',
        line=dict(color='black', width=2)  # 設定線條顏色與寬度
    ))

    # 更新 x 軸與 y 軸的設定，使用對數刻度
    fig.update_xaxes(
        type="log",  # 設置對數刻度
        title_text="tP (s)",  # x 軸標題
        tickvals=[1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1],  # 主要刻度位置
        ticktext=["1µ", "10µ", "100µ", "1m", "10m", "100m", "1", "10"],  # 刻度標籤
        showgrid=True,  # 顯示網格線
        gridcolor="lightgray"  # 網格線顏色
    )
    fig.update_yaxes(
        type="log",  # 設置對數刻度
        title_text="Zth (K/W)",  # y 軸標題
        tickvals=[1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0],  # 主要刻度位置
        ticktext=["10⁻⁵", "10⁻⁴", "10⁻³", "10⁻²", "10⁻¹", "1"],  # 刻度標籤
        showgrid=True,  # 顯示網格線
        gridcolor="lightgray"  # 網格線顏色
    )

    # 更新圖表佈局
    fig.update_layout(
        title="ZthJF vs tP",  # 圖表標題
        xaxis_title="t<sub>P</sub> (s)",  # x 軸標題
        yaxis_title="Z<sub>th</sub> (K/W)",  # y 軸標題
        showlegend=True,  # 顯示圖例
        margin=dict(l=20, r=20, t=30, b=20),  # 圖表邊距
        plot_bgcolor="white",  # 背景顏色
        xaxis=dict(showgrid=True, gridcolor='lightgray'),  # x 軸網格線
        yaxis=dict(showgrid=True, gridcolor='lightgray'),  # y 軸網格線
    )

    return fig


# N卡片的回調函數
@app.callback(
    Output('graph-extra7', 'figure'),
    Input('upload-extra7', 'contents'),
    State('upload-extra7', 'filename')
)
def update_graph_n(contents, filename):
    if contents is None:
        return go.Figure()

    # 解析上傳的數據
    df = parse_contents(contents, filename)

    # 確保數據包含必要的欄位
    required_columns = ['t [s]', 'Zth (t)']
    if df is None or not all(col in df.columns for col in required_columns):
        return go.Figure()

    # 建立圖表
    fig = go.Figure()

    # 添加折線圖
    fig.add_trace(go.Scatter(
        x=df['t<sub>p</sub> [s]'],
        y=df['Z<sub>th</sub> (t)'],
        mode='lines',
        name='ZthJF : Diode',
        line=dict(color='black', width=2)  # 設定線條顏色與寬度
    ))

    # 更新 x 軸與 y 軸的設定，使用對數刻度
    fig.update_xaxes(
        type="log",  # 設置對數刻度
        title_text="tP (s)",  # x 軸標題
        tickvals=[1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1],  # 主要刻度位置
        ticktext=["1µ", "10µ", "100µ", "1m", "10m", "100m", "1", "10"],  # 刻度標籤
        showgrid=True,  # 顯示網格線
        gridcolor="lightgray"  # 網格線顏色
    )
    fig.update_yaxes(
        type="log",  # 設置對數刻度
        title_text="Zth (K/W)",  # y 軸標題
        tickvals=[1e-4, 1e-3, 1e-2, 1e-1, 1e0],  # 主要刻度位置
        ticktext=["10⁻⁴", "10⁻³", "10⁻²", "10⁻¹", "1"],  # 刻度標籤
        showgrid=True,  # 顯示網格線
        gridcolor="lightgray"  # 網格線顏色
    )

    # 更新圖表佈局
    fig.update_layout(
        title="ZthJF vs tP (Diode)",  # 圖表標題
        xaxis_title="tP (s)",  # x 軸標題
        yaxis_title="Zth (K/W)",  # y 軸標題
        showlegend=True,  # 顯示圖例
        margin=dict(l=20, r=20, t=30, b=20),  # 圖表邊距
        plot_bgcolor="white",  # 背景顏色
        xaxis=dict(showgrid=True, gridcolor='lightgray'),  # x 軸網格線
        yaxis=dict(showgrid=True, gridcolor='lightgray'),  # y 軸網格線
    )

    return fig

# 回調函數：處理 CSV Data 模態窗口
@app.callback(
    [Output("data-modal", "is_open"),
     Output("modal-body", "children")],
    [
        Input({'type': 'Data', 'index': ALL}, 'n_clicks'),
        Input("close-modal", "n_clicks")
    ],
    [
        # 所有 upload 的 contents 和 filename
        State('upload-tj25', 'contents'),
        State('upload-tj150', 'contents'),
        State('upload-tj175', 'contents'),
        State('upload-tjD', 'contents'),
        State('upload-tjE', 'contents'),
        State('upload-tjF', 'contents'),
        State('upload-tjG', 'contents'),
        State('upload-extra1', 'contents'),
        State('upload-extra2', 'contents'),
        State('upload-extra3', 'contents'),
        State('upload-extra4', 'contents'),
        State('upload-extra5', 'contents'),
        State('upload-extra6', 'contents'),
        State('upload-extra7', 'contents'),
        State('upload-tj25', 'filename'),
        State('upload-tj150', 'filename'),
        State('upload-tj175', 'filename'),
        State('upload-tjD', 'filename'),
        State('upload-tjE', 'filename'),
        State('upload-tjF', 'filename'),
        State('upload-tjG', 'filename'),
        State('upload-extra1', 'filename'),
        State('upload-extra2', 'filename'),
        State('upload-extra3', 'filename'),
        State('upload-extra4', 'filename'),
        State('upload-extra5', 'filename'),
        State('upload-extra6', 'filename'),
        State('upload-extra7', 'filename'),
    ]
)
def toggle_modal(Data_n_clicks, close_n_clicks,
                contents_tj25, contents_tj150, contents_tj175,
                contents_tjD, contents_tjE, contents_tjF,
                contents_tjG, contents_extra1, contents_extra2,
                contents_extra3, contents_extra4, contents_extra5,
                contents_extra6, contents_extra7,
                filenames_tj25, filenames_tj150, filenames_tj175,
                filenames_tjD, filenames_tjE, filenames_tjF,
                filenames_tjG, filenames_extra1, filenames_extra2,
                filenames_extra3, filenames_extra4, filenames_extra5,
                filenames_extra6, filenames_extra7):
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, ""
    else:
        triggered_prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

        try:
            # 嘗試解析為 JSON dict
            triggered_id = json.loads(triggered_prop_id)
        except json.JSONDecodeError:
            # 如果無法解析，則為簡單的字符串 ID
            triggered_id = triggered_prop_id

        if triggered_id == "close-modal":
            return False, ""
        elif isinstance(triggered_id, dict) and triggered_id.get('type') == 'Data':
            index = triggered_id.get('index')  # 例如 'graph-tj25'
            # 更新 contents_map 使用 graph_id 作為鍵
            contents_map = {
                'graph-tj25': (contents_tj25, filenames_tj25),
                'graph-tj150': (contents_tj150, filenames_tj150),
                'graph-tj175': (contents_tj175, filenames_tj175),
                'graph-tjD': (contents_tjD, filenames_tjD),
                'graph-tjE': (contents_tjE, filenames_tjE),
                'graph-tjF': (contents_tjF, filenames_tjF),
                'graph-tjG': (contents_tjG, filenames_tjG),
                'graph-extra1': (contents_extra1, filenames_extra1),
                'graph-extra2': (contents_extra2, filenames_extra2),
                'graph-extra3': (contents_extra3, filenames_extra3),
                'graph-extra4': (contents_extra4, filenames_extra4),
                'graph-extra5': (contents_extra5, filenames_extra5),
                'graph-extra6': (contents_extra6, filenames_extra6),
                'graph-extra7': (contents_extra7, filenames_extra7),
            }

            contents, filename = contents_map.get(index, (None, None))
            if contents is not None:
                df_modal = parse_contents(contents, filename)
                if df_modal is not None:
                    # 移除全為空的欄位和列
                    df_clean = df_modal.dropna(axis=1, how='all').dropna(axis=0, how='all')

                    # 將清理後的 DataFrame 轉換為表格
                    table = dbc.Table.from_dataframe(df_clean, striped=True, bordered=True, hover=True, size="sm")
                    return True, table
            return False, ""
        else:
            return dash.no_update

# 定義回調函數：下載圖表圖片
@app.callback(
    Output('download-image', 'data'),
    [
        Input({'type': 'button2', 'graph_id': 'graph-tj25'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tj150'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tj175'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tjD'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tjE'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tjF'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-tjG'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra1'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra2'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra3'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra4'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra5'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra6'}, 'n_clicks'),
        Input({'type': 'button2', 'graph_id': 'graph-extra7'}, 'n_clicks'),
    ],
    [
        State('graph-tj25', 'figure'),
        State('graph-tj150', 'figure'),
        State('graph-tj175', 'figure'),
        State('graph-tjD', 'figure'),
        State('graph-tjE', 'figure'),
        State('graph-tjF', 'figure'),
        State('graph-tjG', 'figure'),
        State('graph-extra1', 'figure'),
        State('graph-extra2', 'figure'),
        State('graph-extra3', 'figure'),
        State('graph-extra4', 'figure'),
        State('graph-extra5', 'figure'),
        State('graph-extra6', 'figure'),
        State('graph-extra7', 'figure'),
    ],
    prevent_initial_call=True
)
def download_graph(*args):
    # 分離 Inputs 和 States
    input_n_clicks = args[:14]
    states = args[14:]

    # 使用 callback_context 來確定哪個按鈕被點擊
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate
    else:
        triggered_prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            triggered_id = json.loads(triggered_prop_id)
        except json.JSONDecodeError:
            triggered_id = None

        if isinstance(triggered_id, dict) and triggered_id.get('type') == 'button2':
            graph_id = triggered_id.get('graph_id')
            # Map graph_id 到對應的 figure
            graph_map = {
                'graph-tj25': states[0],
                'graph-tj150': states[1],
                'graph-tj175': states[2],
                'graph-tjD': states[3],
                'graph-tjE': states[4],
                'graph-tjF': states[5],
                'graph-tjG': states[6],
                'graph-extra1': states[7],
                'graph-extra2': states[8],
                'graph-extra3': states[9],
                'graph-extra4': states[10],
                'graph-extra5': states[11],
                'graph-extra6': states[12],
                'graph-extra7': states[13],
            }

            figure = graph_map.get(graph_id)
            if figure:
                # 使用 Plotly 的 to_image 生成 PNG 圖片
                img_bytes = go.Figure(figure).to_image(format="png")
                # 傳送圖片進行下載
                return dcc.send_bytes(img_bytes, filename=f"{graph_id}.png")

    raise PreventUpdate

# ================== Diagrams1 的整合結束 ==================

# 定義回調函數：啟動 subprocess（Diagrams2 頁面）
@app.callback(
    Output("subprocess-feedback", "children"),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def run_subprocess(pathname):
    if pathname == '/diagrams2':
        try:
            # 檢查是否已經有該子進程在運行
            # 您可以使用更複雜的機制來管理子進程，例如儲存進程 ID
            subprocess.Popen(["python", "hh4any.py"])
            return "hh4any.py 已經在後台啟動 (port=8051?) ，請另開瀏覽器視窗查看。"
        except Exception as e:
            logging.error(f"啟動 hh4any.py 失敗: {e}")
            return f"啟動 hh4any.py 失敗: {e}"
    return ""

# 定義應用的整體佈局
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id="store-selected", data={}),
    navbar,
    html.Div(id='page-content', style={'padding': '0 20px'})  # 調整間距以達到與上方標題緊密相連的效果
])

# 定義回調函數：啟動 subprocess 僅在訪問 Diagrams2 時
# 已經在 run_subprocess 中處理

# 最後執行 Dash 應用程式
if __name__ == "__main__":
    try:
        # 檢查公司 PDF 文件
        missing_company_pdfs = []
        for label, path in company_pdfs.items():
            # 若 path 是 URL，直接檢查 HTTP 狀態
            if path.startswith("http://") or path.startswith("https://"):
                try:
                    response = requests.head(path, allow_redirects=True, timeout=5)
                    if response.status_code != 200:
                        logging.error(f"公司 PDF 文件缺失: {path} (HTTP status code: {response.status_code})")
                        missing_company_pdfs.append(path)
                except Exception as e:
                    logging.error(f"公司 PDF 文件檢查失敗: {path} ({e})")
                    missing_company_pdfs.append(path)
            else:
                # 本地檔案，組合路徑檢查
                file_path = os.path.join(os.getcwd(), path)
                if not os.path.exists(file_path):
                    logging.error(f"公司 PDF 文件缺失: {file_path}")
                    missing_company_pdfs.append(file_path)

        if missing_company_pdfs:
            raise FileNotFoundError(f"以下公司 PDF 文件缺失: {missing_company_pdfs}")
        else:
            logging.info("所有公司 PDF 文件均存在。")

        # 檢查競爭對手 PDF 文件
        missing_competitor_pdfs = []
        for label, path in competitor_pdfs.items():
            if path.startswith("http://") or path.startswith("https://"):
                try:
                    response = requests.head(path, allow_redirects=True, timeout=5)
                    if response.status_code != 200:
                        logging.error(f"競爭對手 PDF 文件缺失: {path} (HTTP status code: {response.status_code})")
                        missing_competitor_pdfs.append(path)
                except Exception as e:
                    logging.error(f"競爭對手 PDF 文件檢查失敗: {path} ({e})")
                    missing_competitor_pdfs.append(path)
            else:
                file_path = os.path.join(os.getcwd(), path)
                if not os.path.exists(file_path):
                    logging.error(f"競爭對手 PDF 文件缺失: {file_path}")
                    missing_competitor_pdfs.append(file_path)

        if missing_competitor_pdfs:
            raise FileNotFoundError(f"以下競爭對手 PDF 文件缺失: {missing_competitor_pdfs}")
        else:
            logging.info("所有競爭對手 PDF 文件均存在。")

        # 運行應用
        # 假設 app 是已建立的 Dash 應用
        app.run_server(debug=True)



    except FileNotFoundError as e:
        logging.error(e)
        print(e)