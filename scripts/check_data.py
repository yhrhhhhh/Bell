import os
import sys
import django
import MySQLdb
from django.conf import settings

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bell.settings')
django.setup()

from device.models import Building, Floor, Device, DeviceStatus

def check_tables():
    """检查数据库中的表"""
    db_settings = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host=db_settings['HOST'] or 'localhost',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        database=db_settings['NAME']
    )
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    print("数据库中的表:")
    for table in tables:
        print(f"  - {table}")
    
    # 检查设备表
    if 'device_device' in tables:
        cursor.execute("DESCRIBE device_device")
        columns = cursor.fetchall()
        print("\n设备表(device_device)的列:")
        for column in columns:
            print(f"  - {column[0]}: {column[1]}")
    
    cursor.close()
    conn.close()

def check_data_directly():
    """直接查询数据库中的数据"""
    db_settings = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host=db_settings['HOST'] or 'localhost',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        database=db_settings['NAME']
    )
    cursor = conn.cursor()
    
    # 检查建筑
    try:
        cursor.execute("SELECT COUNT(*) FROM device_building")
        building_count = cursor.fetchone()[0]
        print(f"\n建筑数量: {building_count}")
        
        if building_count > 0:
            cursor.execute("SELECT id, name, code FROM device_building LIMIT 5")
            buildings = cursor.fetchall()
            for building in buildings:
                print(f"  - {building[0]}: {building[1]} ({building[2]})")
    except Exception as e:
        print(f"查询建筑表时出错: {str(e)}")
    
    # 检查楼层
    try:
        cursor.execute("SELECT COUNT(*) FROM device_floor")
        floor_count = cursor.fetchone()[0]
        print(f"\n楼层数量: {floor_count}")
        
        if floor_count > 0:
            cursor.execute("""
                SELECT f.id, f.name, f.floor_number, b.name
                FROM device_floor f
                JOIN device_building b ON f.building_id = b.id
                LIMIT 5
            """)
            floors = cursor.fetchall()
            for floor in floors:
                print(f"  - {floor[0]}: {floor[3]}-{floor[1]} (楼层号: {floor[2]})")
    except Exception as e:
        print(f"查询楼层表时出错: {str(e)}")
    
    # 检查设备
    try:
        cursor.execute("SELECT COUNT(*) FROM device_device")
        device_count = cursor.fetchone()[0]
        print(f"\n设备数量: {device_count}")
        
        if device_count > 0:
            cursor.execute("""
                SELECT id, name, status, current_temp
                FROM device_device
                LIMIT 5
            """)
            devices = cursor.fetchall()
            for device in devices:
                print(f"  - {device[0]}: {device[1]} (状态: {device[2]}, 温度: {device[3]}°C)")
    except Exception as e:
        print(f"查询设备表时出错: {str(e)}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    print("====== 检查数据库表结构 ======")
    check_tables()
    
    print("\n====== 直接查询数据 ======")
    check_data_directly()
    
    print("\n检查完成!") 