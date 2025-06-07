from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def check_online_status():
    """检查设备在线状态"""
    from device.models import Topic, Device
    # 设置时间阈值（生产环境建议用hours=1，测试用seconds=2）
    threshold = timezone.now() - timedelta(hours=1)

    updated_topics = Topic.objects.filter(
        updated_at__lt=threshold,
        online_status=True
    ).update(online_status=False)

    offline_topics = Topic.objects.filter(online_status=False)

    device_updated = Device.objects.filter(
        uuid__in=offline_topics.values_list('id', flat=True)
    ).update(online_status=False)

    logger.info(
        f"Marked {updated_topics} topics as offline, "
        f"updated {device_updated} associated devices"
    )


# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# 每小时执行一次（生产环境配置）
scheduler.add_job(
    check_online_status,
    'interval',
    hours=1,
    id='device_online_check',
    replace_existing=True
)

# 安全启动
try:
    scheduler.start()
    logger.info("Device status scheduler started")
except Exception as e:
    logger.error(f"Scheduler failed: {e}")
