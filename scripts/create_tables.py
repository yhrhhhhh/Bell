import os
import sys
import django
import MySQLdb
from django.conf import settings

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bell.settings')
django.setup()

def create_tables():
    """直接在数据库中创建缺少的表"""
    db_settings = settings.DATABASES['default']
    conn = MySQLdb.connect(
        host=db_settings['HOST'] or 'localhost',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        database=db_settings['NAME']
    )
    cursor = conn.cursor()
    
    # 创建建筑表
    building_table_sql = """
    CREATE TABLE IF NOT EXISTS `device_building` (
      `id` bigint NOT NULL AUTO_INCREMENT,
      `name` varchar(100) NOT NULL,
      `code` varchar(50) NOT NULL,
      `description` longtext,
      `create_time` datetime(6) NOT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `code` (`code`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """
    
    # 创建楼层表
    floor_table_sql = """
    CREATE TABLE IF NOT EXISTS `device_floor` (
      `id` bigint NOT NULL AUTO_INCREMENT,
      `name` varchar(50) NOT NULL,
      `floor_number` int NOT NULL,
      `description` longtext,
      `create_time` datetime(6) NOT NULL,
      `building_id` bigint NOT NULL,
      PRIMARY KEY (`id`),
      KEY `device_floor_building_id_fk` (`building_id`),
      CONSTRAINT `device_floor_building_id_fk` FOREIGN KEY (`building_id`) REFERENCES `device_building` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
    """
    
    try:
        print("创建建筑表...")
        cursor.execute(building_table_sql)
        print("建筑表创建成功！")
        
        print("创建楼层表...")
        cursor.execute(floor_table_sql)
        print("楼层表创建成功！")
        
        # 提交事务
        conn.commit()
    except Exception as e:
        print(f"创建表时出错: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    print("开始创建缺少的表...")
    create_tables()
    print("操作完成!") 