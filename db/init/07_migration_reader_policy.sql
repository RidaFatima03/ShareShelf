-- Migration: move policy_id from User to Reader
-- Safe to run on an existing DB; it checks schema state first.

DELIMITER //
CREATE PROCEDURE migrate_policy_to_reader()
BEGIN
  DECLARE col_exists INT DEFAULT 0;
  DECLARE fk_exists INT DEFAULT 0;
  DECLARE default_policy_id INT DEFAULT NULL;

  -- Add Reader.policy_id if missing
  SELECT COUNT(*)
    INTO col_exists
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'Reader'
     AND COLUMN_NAME = 'policy_id';

  IF col_exists = 0 THEN
    ALTER TABLE Reader ADD COLUMN policy_id INT NULL;
  END IF;

  -- Backfill from User.policy_id if it exists
  SELECT COUNT(*)
    INTO col_exists
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'User'
     AND COLUMN_NAME = 'policy_id';

  IF col_exists = 1 THEN
    UPDATE Reader r
    JOIN User u ON u.user_id = r.reader_id
       SET r.policy_id = u.policy_id
     WHERE r.policy_id IS NULL
       AND u.policy_id IS NOT NULL;
  END IF;

  -- Pick a default policy for any remaining NULLs
  SELECT policy_id
    INTO default_policy_id
    FROM Policy
   ORDER BY policy_id
   LIMIT 1;

  IF default_policy_id IS NULL THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'No Policy rows exist. Create a Policy before migrating.';
  END IF;

  UPDATE Reader
     SET policy_id = default_policy_id
   WHERE policy_id IS NULL;

  -- Add FK if missing
  SELECT COUNT(*)
    INTO fk_exists
    FROM information_schema.KEY_COLUMN_USAGE
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'Reader'
     AND COLUMN_NAME = 'policy_id'
     AND REFERENCED_TABLE_NAME = 'Policy';

  IF fk_exists = 0 THEN
    ALTER TABLE Reader
      ADD CONSTRAINT fk_reader_policy
      FOREIGN KEY (policy_id) REFERENCES Policy(policy_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE;
  END IF;

  -- Enforce NOT NULL after backfill
  ALTER TABLE Reader MODIFY policy_id INT NOT NULL;

  -- Drop User.policy_id if it exists
  SELECT COUNT(*)
    INTO col_exists
    FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = DATABASE()
     AND TABLE_NAME = 'User'
     AND COLUMN_NAME = 'policy_id';

  IF col_exists = 1 THEN
    ALTER TABLE User DROP COLUMN policy_id;
  END IF;
END//
DELIMITER ;

CALL migrate_policy_to_reader();
DROP PROCEDURE migrate_policy_to_reader;
