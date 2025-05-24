from django.db import connection

def clean_indexes():
    with connection.cursor() as cursor:
        # 删除重复的索引
        cursor.execute("DROP INDEX IF EXISTS device_device_device_id_8b28e36a ON device_device")
        cursor.execute("DROP INDEX IF EXISTS device_uuid_unique_idx ON device_device")
        cursor.execute("DROP INDEX IF EXISTS device_device_uuid_id_e47f7e3f ON device_device")
        
        # 删除重复的约束
        cursor.execute("ALTER TABLE device_device DROP CONSTRAINT IF EXISTS unique_device_uuid")
        cursor.execute("ALTER TABLE device_device DROP CONSTRAINT IF EXISTS device_uuid_unique_idx")

if __name__ == '__main__':
    clean_indexes() 