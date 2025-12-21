-- Ensure the scheduler is on inside MySQL
SET GLOBAL event_scheduler = ON;

-- Create scheduled job to expire requests automatically
CREATE EVENT IF NOT EXISTS expire_requests
ON SCHEDULE EVERY 1 MINUTE
DO
  UPDATE Request
  SET status = 'Expired'
  WHERE expire_date IS NOT NULL
    AND expire_date <= NOW()
    AND status IN ('Pending', 'Approved');
