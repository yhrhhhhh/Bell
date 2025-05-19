import os
import sys
import django
import MySQLdb
from django.conf import settings
from datetime import datetime

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bell.settings')
django.setup()

def insert_status_history():
    """插入设备状态历史数据"""
    db_settings = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host=db_settings['HOST'] or 'localhost',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        database=db_settings['NAME']
    )
    cursor = conn.cursor()
    
    try:
        # 清空历史记录
        print("清空设备状态历史...")
        cursor.execute("DELETE FROM device_devicestatus")
        
        # 获取设备ID
        print("获取设备ID...")
        cursor.execute("SELECT id, set_temp, status, mode FROM device_device LIMIT 10")
        devices = cursor.fetchall()
        
        if not devices:
            print("没有找到设备数据！")
            return
        
        # 为每个设备创建历史记录
        print("插入设备状态历史...")
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for device in devices[:2]:  # 为前两个设备添加详细历史
            device_id = device[0]
            set_temp = device[1]
            status = device[2]
            mode = device[3]
            
            # 添加5个小时的历史记录
            for i in range(1, 6):
                temp = 25.0 + (i * 0.1)  # 温度略有变化
                timestamp = f"DATE_SUB('{now}', INTERVAL {i} HOUR)"
                
                sql = f"""
                INSERT INTO device_devicestatus (device_id, current_temp, set_temp, status, mode, timestamp)
                VALUES ({device_id}, {temp}, {set_temp}, '{status}', '{mode}', {timestamp})
                """
                cursor.execute(sql)
                print(f"为设备 {device_id} 添加了 {i} 小时前的历史记录")
        
        # 提交事务
        conn.commit()
        print("设备状态历史插入成功！")
        
    except Exception as e:
        print(f"插入状态历史时出错: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("开始插入设备状态历史...")
    insert_status_history()
    print("操作完成!") 