from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = '清理设备表中的重复索引和约束'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # 删除重复的索引
                cursor.execute("ALTER TABLE device_device DROP INDEX IF EXISTS device_device_device_id_8b28e36a")
                self.stdout.write(self.style.SUCCESS('成功删除索引 device_device_device_id_8b28e36a'))
                
                cursor.execute("ALTER TABLE device_device DROP INDEX IF EXISTS device_uuid_unique_idx")
                self.stdout.write(self.style.SUCCESS('成功删除索引 device_uuid_unique_idx'))
                
                cursor.execute("ALTER TABLE device_device DROP INDEX IF EXISTS device_device_uuid_id_e47f7e3f")
                self.stdout.write(self.style.SUCCESS('成功删除索引 device_device_uuid_id_e47f7e3f'))
                
                # 删除重复的约束
                cursor.execute("ALTER TABLE device_device DROP INDEX IF EXISTS unique_device_uuid")
                self.stdout.write(self.style.SUCCESS('成功删除约束 unique_device_uuid'))
                
                cursor.execute("ALTER TABLE device_device DROP INDEX IF EXISTS device_uuid_unique_idx")
                self.stdout.write(self.style.SUCCESS('成功删除约束 device_uuid_unique_idx'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'发生错误: {str(e)}')) 