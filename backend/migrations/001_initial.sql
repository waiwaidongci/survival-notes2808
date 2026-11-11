-- Metadata bootstraps new tables. Apply reviewed migrations for future upgrades.
CREATE INDEX specimen_cohort_idx ON specimens (cohort_id);
CREATE INDEX note_run_status_idx ON maintenance_notes (run_id,status);
