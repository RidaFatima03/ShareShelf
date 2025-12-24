-- Ensure the scheduler is on inside MySQL
SET GLOBAL event_scheduler = ON;

-- Create scheduled job to expire requests automatically
DELIMITER $$
CREATE EVENT IF NOT EXISTS expire_requests
ON SCHEDULE EVERY 1 MINUTE
DO
BEGIN
  INSERT INTO Notification (user_id, subject, details)
  SELECT r.reader_id,
         'Request expired',
         CONCAT('Your ', r.request_type, ' request for ',
                COALESCE(b.title, m.title, 'item'),
                ' has expired.')
  FROM Request r
  LEFT JOIN Copy c ON r.copy_id = c.item_barcode
  LEFT JOIN Book b ON c.book_id = b.book_id
  LEFT JOIN Material m ON r.material_id = m.material_id
  WHERE r.expire_date IS NOT NULL
    AND r.expire_date <= NOW()
    AND r.status IN ('Pending', 'Approved');

  UPDATE Request
  SET status = 'Expired'
  WHERE expire_date IS NOT NULL
    AND expire_date <= NOW()
    AND status IN ('Pending', 'Approved');
END$$
DELIMITER ;
