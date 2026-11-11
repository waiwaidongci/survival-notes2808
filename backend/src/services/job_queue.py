"""研究队列投递：Redis 键与幂等投递规则集中在此。"""
from redis import Redis
from ..config.settings import REDIS_URL
queue=Redis.from_url(REDIS_URL,decode_responses=True)
JOB_QUEUE="survival:jobs"
ENQUEUE_LOCK="survival:enqueue-lock"

def enqueue_job(rid:int):
    """先移除可能残留的同 ID 任务再投递，重复投递不会在队列里产生两份。"""
    queue.lrem(JOB_QUEUE,0,str(rid))
    queue.rpush(JOB_QUEUE,rid)
