-- 研究输入固化与归档对账（在 001_initial.sql 之后执行）。
-- 新库由 ORM metadata 直接建表；已有库先由启动逻辑回填，再补唯一索引。
-- 回填逻辑见 src/services/recovery_service.py，会为旧研究补齐 input_snapshot/input_hash 与归档文件。
-- input_hash 可空且唯一：未回填旧研究为 NULL（唯一索引允许多个 NULL），新研究必有哈希。

ALTER TABLE survival_runs
    ADD COLUMN input_snapshot JSON NULL,
    ADD COLUMN input_hash VARCHAR(64) NULL,
    ADD COLUMN artifact_path VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN artifact_hash VARCHAR(64) NOT NULL DEFAULT '',
    ADD COLUMN running_at VARCHAR(64) NOT NULL DEFAULT '';

-- 回填完成后再加唯一索引；重复输入的历史研究由回填逻辑分配 #legacy-{id} 后缀。
CREATE UNIQUE INDEX uq_survival_runs_input_hash ON survival_runs (input_hash);
