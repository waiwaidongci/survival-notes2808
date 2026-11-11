"""研究归档文件：与数据库记录始终对应同一份输入和结果。

- 原子写入（临时文件 + os.replace），中断不会留下半截 JSON；
- 保存文件内容 SHA256 到 survival_runs.artifact_hash；
- 读取时校验哈希，缺失或不符则按数据库中的结果重写（对账自愈）。
"""
import hashlib,json,os,tempfile
from pathlib import Path
from ..models import SurvivalRun
from .run_snapshot import ARTIFACT_DIR


def artifact_path(run_id:int) -> Path:
    return Path(ARTIFACT_DIR) / f"run-{run_id}.json"


def dump_archive(run:SurvivalRun) -> str:
    """归档单文件同时包含固化输入与计算结果，返回文件内容 SHA256。"""
    payload={
        "run_id":run.id,
        "name":run.name,
        "owner":run.owner,
        "created_at":run.created_at,
        "input_hash":run.input_hash,
        "input_snapshot":run.input_snapshot,
        "result":run.result,
    }
    text=json.dumps(payload,ensure_ascii=False,sort_keys=True,allow_nan=False)
    digest=hashlib.sha256(text.encode("utf-8")).hexdigest()
    target=artifact_path(run.id)
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f".run-{run.id}.",suffix=".tmp",dir=target.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return digest


def file_sha256(path:Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):h.update(chunk)
    return h.hexdigest()


def verify_artifact(run:SurvivalRun) -> bool:
    path=Path(run.artifact_path) if run.artifact_path else artifact_path(run.id)
    if not path.exists() or not run.artifact_hash:return False
    return file_sha256(path)==run.artifact_hash


def ensure_artifact(run:SurvivalRun) -> Path:
    """确保归档文件存在且与数据库结果一致；不一致时按数据库重建并回写哈希。"""
    path=artifact_path(run.id)
    if not verify_artifact(run):
        run.artifact_hash=dump_archive(run)
        run.artifact_path=str(path)
    return path


def read_archive(run:SurvivalRun) -> dict:
    ensure_artifact(run)
    return json.loads(artifact_path(run.id).read_text(encoding="utf-8"))
