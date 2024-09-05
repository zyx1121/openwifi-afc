## OpenWiFi AFC

### Structure

```
openwifi-afc
├── openwifi_afc
│   ├── __init__.py
│   ├── __main__.py
│   ├── afc.py
│   └── openwifi.py
├── afc.toml
├── pyproject.toml
└── README.md
```

### Requirements

- [AFC Server](https://github.com/open-afc-project/openafc)
- [Poetry](https://github.com/python-poetry/poetry)

### Getting Started

使用 [Poetry](https://github.com/python-poetry/poetry) 作為專案管理工具，請在 Zedboard 上安裝。

- 連線到 Zedboard
  ```bash!
  ssh root@192.168.88.122
  ```

- 下載專案
  ```bash!
  git clone https://github.com/zyx1121/openwifi-afc openwifi_afc
  ```

- 進入 `openwifi_afc` 目錄
  ```bash!
  cd openwifi_afc
  ```

- 安裝依賴的 Python 版本與套件
  ```bash!
  poetry install
  ```

- 設置 `afc.toml`
  ```toml=
  [connection]
  base_url = 'https://140.118.123.217/fbrat/'         # AFC server base url
  method_url = 'ap-afc/availableSpectrumInquirySec'   # AFC method url
  login_url = 'user/sign-in'                          # AFC login url
  timeout = 10                                        # AFC request timeout

  [account]
  username = 'admin@afc.com'                          # AFC username
  password = 'openafc'                                # AFC password

  [ap]
  serialNumber = 'TestSerialNumber'                   # AFC AP serial number
  rulesetId = 'US_47_CFR_PART_15_SUBPART_E'           # AFC AP ruleset id
  certificationId = 'TestCertificationId'             # AFC AP certification id

  latitude = 25.0119                                  # AFC AP latitude
  longitude = 121.5414                                # AFC AP longitude
  majorAxis = 10                                      # AFC AP major axis
  minorAxis = 10                                      # AFC AP minor axis
  orientation = 0                                     # AFC AP orientation

  height = 100                                        # AFC AP height
  heightType = "AGL"                                  # AFC AP height type
  verticalUncertainty = 5                             # AFC AP vertical uncertainty

  indoorDeployment = 0                                # AFC AP indoor deployment
  ```
  > 替換 `afc.toml` 中的設定為實際 AFC Server 與 AP 的資訊

- 執行 `openwifi_afc`
  ```bash!
  poetry run python openwifi_afc
  ```
### Usage

執行 `openwifi_afc` 後，會自動與 AFC Server 進行通訊，請求可用頻道並啟動 AP

再來就可以輸入命令切換頻道

```bash!
openwifi-afc> set 5
```
