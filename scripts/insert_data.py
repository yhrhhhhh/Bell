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

def insert_test_data():
    """插入测试数据"""
    db_settings = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host=db_settings['HOST'] or 'localhost',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        database=db_settings['NAME']
    )
    cursor = conn.cursor()
    
    try:
        # 清空表中的数据
        print("清空现有数据...")
        cursor.execute("DELETE FROM device_devicestatus")
        cursor.execute("DELETE FROM device_device")
        cursor.execute("DELETE FROM device_floor")
        cursor.execute("DELETE FROM device_building")
        
        # 插入建筑数据
        print("插入建筑数据...")
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        building_sql = """
        INSERT INTO device_building (name, code, description, create_time) VALUES 
        ('党政大楼', 'DZ001', '行政办公主楼', %s),
        ('教学楼', 'JX001', '主教学楼', %s)
        """
        cursor.execute(building_sql, (now, now))
        print("建筑数据插入成功！")
        
        # 插入楼层数据
        print("插入楼层数据...")
        floor_sql = """
        INSERT INTO device_floor (building_id, name, floor_number, description, create_time) VALUES 
        (1, '1层', 1, '党政大楼1层', %s),
        (1, '2层', 2, '党政大楼2层', %s),
        (1, '3层', 3, '党政大楼3层', %s),
        (2, '1层', 1, '教学楼1层', %s),
        (2, '2层', 2, '教学楼2层', %s),
        (2, '3层', 3, '教学楼3层', %s),
        (2, '4层', 4, '教学楼4层', %s)
        """
        cursor.execute(floor_sql, (now, now, now, now, now, now, now))
        print("楼层数据插入成功！")
        
        # 插入设备数据
        print("插入设备数据...")
        device_sql = """
        INSERT INTO device_device (name, device_id, location, room_id, floor_id, building_id, current_temp, set_temp, status, mode, is_auto, running_time, last_updated, create_time) VALUES 
        ('党政大楼-1层-设备1', 'DEVDZ00101', '党政大楼1层', 1, 1, 1, 25.5, 24.0, 'running', 'cooling', 0, 12.5, %s, %s),
        ('党政大楼-1层-设备2', 'DEVDZ00102', '党政大楼1层', 2, 1, 1, 26.2, 25.0, 'stopped', 'fan', 1, 0.0, %s, %s),
        ('党政大楼-1层-设备3', 'DEVDZ00103', '党政大楼1层', 3, 1, 1, 24.8, 23.0, 'running', 'cooling', 0, 32.7, %s, %s),
        ('党政大楼-2层-设备1', 'DEVDZ00201', '党政大楼2层', 1, 2, 1, 27.3, 25.0, 'running', 'cooling', 0, 45.2, %s, %s),
        ('党政大楼-2层-设备2', 'DEVDZ00202', '党政大楼2层', 2, 2, 1, 24.5, 25.0, 'stopped', 'heating', 0, 0.0, %s, %s),
        ('党政大楼-2层-设备3', 'DEVDZ00203', '党政大楼2层', 3, 2, 1, 25.8, 26.0, 'fault', 'cooling', 1, 5.5, %s, %s),
        ('党政大楼-2层-设备4', 'DEVDZ00204', '党政大楼2层', 4, 2, 1, 28.0, 24.0, 'running', 'cooling', 0, 78.3, %s, %s),
        ('党政大楼-3层-设备1', 'DEVDZ00301', '党政大楼3层', 1, 3, 1, 25.0, 25.0, 'running', 'fan', 0, 23.1, %s, %s),
        ('党政大楼-3层-设备2', 'DEVDZ00302', '党政大楼3层', 2, 3, 1, 26.6, 24.0, 'running', 'cooling', 0, 47.8, %s, %s),
        ('教学楼-1层-设备1', 'DEVJX00101', '教学楼1层', 1, 4, 2, 24.3, 23.0, 'running', 'cooling', 0, 67.5, %s, %s),
        ('教学楼-1层-设备2', 'DEVJX00102', '教学楼1层', 2, 4, 2, 28.1, 24.0, 'running', 'cooling', 0, 47.8, %s, %s),
        ('教学楼-1层-设备3', 'DEVJX00103', '教学楼1层', 3, 4, 2, 25.7, 26.0, 'running', 'heating', 1, 12.3, %s, %s),
        ('教学楼-2层-设备1', 'DEVJX00201', '教学楼2层', 1, 5, 2, 26.7, 25.0, 'running', 'cooling', 0, 23.4, %s, %s),
        ('教学楼-2层-设备2', 'DEVJX00202', '教学楼2层', 2, 5, 2, 24.9, 23.0, 'stopped', 'fan', 0, 0.0, %s, %s),
        ('教学楼-3层-设备1', 'DEVJX00301', '教学楼3层', 1, 6, 2, 25.3, 25.0, 'running', 'cooling', 0, 36.7, %s, %s),
        ('教学楼-3层-设备2', 'DEVJX00302', '教学楼3层', 2, 6, 2, 28.0, 26.0, 'running', 'dehumidify', 1, 19.2, %s, %s),
        ('教学楼-3层-设备3', 'DEVJX00303', '教学楼3层', 3, 6, 2, 26.9, 24.0, 'fault', 'cooling', 0, 0.5, %s, %s),
        ('教学楼-4层-设备1', 'DEVJX00401', '教学楼4层', 1, 7, 2, 25.5, 24.0, 'running', 'cooling', 0, 56.3, %s, %s),
        ('教学楼-4层-设备2', 'DEVJX00402', '教学楼4层', 2, 7, 2, 26.2, 25.0, 'running', 'cooling', 0, 48.9, %s, %s)
        """
        params = []
        for _ in range(19):  # 19个设备，每个设备需要两个时间参数
            params.extend([now, now])
        cursor.execute(device_sql, params)
        print("设备数据插入成功！")
        
        # 插入设备状态历史
        print("插入设备状态历史...")
        status_sql = """
        INSERT INTO device_devicestatus (device_id, current_temp, set_temp, status, mode, timestamp) VALUES 
        (1, 25.2, 24.0, 'running', 'cooling', DATE_SUB(%s, INTERVAL 5 HOUR)),
        (1, 25.5, 24.0, 'running', 'cooling', DATE_SUB(%s, INTERVAL 4 HOUR)),
        (1, 25.7, 24.0, 'running', 'cooling', DATE_SUB(%s, INTERVAL 3 HOUR)),
        (1, 25.6, 24.0, 'running', 'cooling', DATE_SUB(%s, INTERVAL 2 HOUR)),
        (1, 25.5, 24.0, 'running', 'cooling', DATE_SUB(%s, INTERVAL 1 HOUR)),
        (2, 27.0, 25.0, 'running', 'fan', DATE_SUB(%s, INTERVAL 12 HOUR)),
        (2, 26.8, 25.0, 'running', 'fan', DATE_SUB(%s, INTERVAL 10 HOUR)),
        (2, 26.5, 25.0, 'running', 'fan', DATE_SUB(%s, INTERVAL 8 HOUR)),
        (2, 26.3, 25.0, 'running', 'fan', DATE_SUB(%s, INTERVAL 6 HOUR)),
        (2, 26.2, 25.0, 'stopped', 'fan', DATE_SUB(%s, INTERVAL 4 HOUR))
        """
        status_params = [now] * 10
        cursor.execute(status_sql, status_params)
        print("设备状态历史插入成功！")
        
        # 提交事务
        conn.commit()
    except Exception as e:
        print(f"插入数据时出错: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("开始插入测试数据...")
    insert_test_data()
    print("测试数据插入完成!") 