# 高度优化的葵花8号中国区域数据下载器
# 导入包
from lb_toolkits.downloadcentre import downloadH8
from datetime import datetime, timedelta
import concurrent.futures
import os
import time
from threading import Lock
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OptimizedH8Downloader:
    """优化的葵花8号下载器，专门针对中国区域数据"""
    
    def __init__(self, username, password, data_path):
        self.username = username
        self.password = password
        self.data_path = data_path
        self.download_lock = Lock()
        
        # 优化参数
        self.max_workers = 4
        self.max_retries = 3
        self.timeout = 180
        self.blocksize = 16384  # 16KB块大小
        
        # 确保下载目录存在
        os.makedirs(data_path, exist_ok=True)
        
    def get_file_list_by_priority(self, start_time, end_time):
        """按优先级获取文件列表，优先下载中国区域数据"""
        down = downloadH8(username=self.username, password=self.password)
        
        # 数据类型优先级：Target Area > Japan Area > Full Disk
        data_types = [
            ('target_area', lambda: down.search_ahi8_l1_hsd(start_time, end_time, 
                                                            pattern=['HS_H08_.*_FLDK_R30_.*'])),
            ('japan_area', lambda: down.search_ahi8_l1_hsd(start_time, end_time, 
                                                           pattern=['HS_H08_.*_FLDK_R2._.*'])),
            ('netcdf_fallback', lambda: down.search_ahi8_l1_netcdf(start_time, end_time))
        ]
        
        for data_type, search_func in data_types:
            try:
                filelist = search_func()
                if filelist:
                    logger.info(f"使用 {data_type} 数据类型，找到 {len(filelist)} 个文件")
                    return filelist, data_type
            except Exception as e:
                logger.warning(f"{data_type} 数据获取失败: {str(e)}")
                continue
        
        logger.error("所有数据类型都无法获取文件列表")
        return [], None
    
    def filter_files_for_china(self, filelist, target_time="0410"):
        """筛选适合中国区域的文件"""
        filtered_files = []
        
        for file in filelist:
            name_parts = file.split("_")
            
            # 基本格式检查
            if len(name_parts) < 7:
                continue
                
            # 检查卫星标识
            if name_parts[1] != 'H08':
                continue
            
            # 检查时间匹配
            if len(name_parts[3]) >= 4:
                file_time = name_parts[3][:4]  # 取前4位HHMM
                if file_time == target_time:
                    filtered_files.append(file)
        
        logger.info(f"时间筛选后剩余文件: {len(filtered_files)} 个")
        return filtered_files
    
    def download_single_file(self, file_url):
        """下载单个文件，支持重试和错误处理"""
        filename = os.path.basename(file_url)
        file_path = os.path.join(self.data_path, filename)
        
        # 检查文件是否已存在
        if os.path.exists(file_path):
            logger.info(f"文件已存在，跳过: {filename}")
            return True
            
        for attempt in range(self.max_retries):
            try:
                down = downloadH8(username=self.username, password=self.password)
                
                start_time = time.time()
                
                # 使用优化参数下载
                down.download(
                    self.data_path, 
                    [file_url],
                    tries=2,
                    timeout=self.timeout,
                    blocksize=self.blocksize,
                    continuing=True,
                    cover=False
                )
                
                download_time = time.time() - start_time
                logger.info(f"下载成功: {filename} (耗时: {download_time:.2f}秒)")
                return True
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {filename}, 错误: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        logger.error(f"最终下载失败: {filename}")
        return False
    
    def download_batch(self, start_date_str, end_date_str, target_time="0410"):
        """批量下载指定时间段的数据"""
        start_time = datetime.strptime(start_date_str, "%Y%m%d%H%M")
        end_time = datetime.strptime(end_date_str, "%Y%m%d%H%M")
        
        logger.info(f"开始下载 {start_date_str} 到 {end_date_str} 的数据")
        
        # 获取文件列表
        filelist, data_type = self.get_file_list_by_priority(start_time, end_time)
        if not filelist:
            logger.error("未找到任何文件")
            return
        
        # 筛选文件
        filtered_files = self.filter_files_for_china(filelist, target_time)
        if not filtered_files:
            logger.error("筛选后无可下载文件")
            return
        
        logger.info(f"准备下载 {len(filtered_files)} 个文件")
        
        # 并行下载
        successful_downloads = 0
        failed_downloads = 0
        
        start_download_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有下载任务
            future_to_file = {
                executor.submit(self.download_single_file, file_url): file_url 
                for file_url in filtered_files
            }
            
            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_file):
                file_url = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        successful_downloads += 1
                    else:
                        failed_downloads += 1
                except Exception as exc:
                    logger.error(f'文件 {file_url} 下载异常: {exc}')
                    failed_downloads += 1
        
        total_download_time = time.time() - start_download_time
        
        logger.info(f"下载完成!")
        logger.info(f"成功: {successful_downloads}, 失败: {failed_downloads}")
        logger.info(f"总耗时: {total_download_time:.2f}秒")
        logger.info(f"平均每文件: {total_download_time/len(filtered_files):.2f}秒")

# 使用示例
if __name__ == '__main__':
    # 配置参数
    username = '2208157100_qq.com'
    password = 'SP+wari8'
    data_path = '/root/Himawari-8/dataset_images'
    
    # 创建下载器实例
    downloader = OptimizedH8Downloader(username, password, data_path)
    
    # 下载数据
    start = '201807010000'  # 开始时间
    end   = '201807020000'  # 结束时间（建议先测试一天的数据）
    
    downloader.download_batch(start, end, target_time="0410")
