ALTER TABLE watchdog_watchdog
    RENAME TO notifikace_projekty_pes;
ALTER TABLE notifikace_projekty_pes
ADD CONSTRAINT unique_pes UNIQUE (user_id, object_id, content_type_id);
