import logging

# 创建logger实例
logger = logging.getLogger('example')

# 设置日志级别
logger.setLevel(logging.DEBUG)

# 创建控制台处理器，将日志输出到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# 将日志格式应用到处理器
console_handler.setFormatter(formatter)
# 将处理器添加到logger实例中
logger.addHandler(console_handler)

# 记录日志信息
logger.debug('debug')
logger.info('info')
logger.warning('warning')
logger.error('error')
logger.critical('critical')
