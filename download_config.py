# 下载配置文件
# 针对中国区域数据下载的优化配置

# 中国区域的地理范围 (大概范围)
CHINA_REGION = {
    'lat_min': 15.0,   # 最南纬度
    'lat_max': 55.0,   # 最北纬度  
    'lon_min': 70.0,   # 最西经度
    'lon_max': 140.0   # 最东经度
}

# 下载优化参数
DOWNLOAD_CONFIG = {
    'max_workers': 4,           # 最大并行下载线程数（建议2-8个）
    'max_retries': 3,           # 最大重试次数
    'timeout': 180,             # 下载超时时间（秒）
    'blocksize': 8192,          # 下载块大小（字节）
    'continuing': True,         # 支持断点续传
    'cover': False,             # 不覆盖已存在文件
}

# 时间筛选配置
TIME_CONFIG = {
    'target_hours': ['04'],     # 目标小时 ['04', '10', '16'] 可以添加更多时间点
    'target_minutes': ['10'],   # 目标分钟 ['00', '10', '20', '30', '40', '50']
}

# 数据类型优先级 (按优先级排序)
DATA_TYPE_PRIORITY = [
    'target_area',    # Target Area (Region 3) - 包含中国，2.5分钟时间分辨率
    'japan_area',     # Japan Area (Region 1&2) - 部分覆盖中国东部
    'full_disk'       # Full-disk - 全球数据，10分钟时间分辨率
]

# 文件名模式匹配
PATTERN_CONFIG = {
    'target_area': ['HS_H08_.*_FLDK_R30_.*'],      # Target Area模式
    'japan_area': ['HS_H08_.*_FLDK_R21_.*', 'HS_H08_.*_FLDK_R22_.*'],  # Japan Area模式
    'full_disk': ['HS_H08_.*_FLDK_R10_.*']         # Full-disk模式
}

# 波段选择 (如果API支持波段选择)
BAND_CONFIG = {
    'visible': [1, 2, 3],       # 可见光波段
    'infrared': [7, 8, 9, 10, 11, 12, 13, 14, 15, 16],  # 红外波段
    'all': list(range(1, 17))   # 所有波段
}
