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

-- Create scheduled job to create/update overdue fines daily
CREATE EVENT IF NOT EXISTS update_overdue_fines
ON SCHEDULE EVERY 1 DAY
DO
BEGIN
  INSERT INTO Fine (checkout_id, fine_reason, amount, status)
  SELECT c.checkout_id, 'Overdue', 0, 'Unpaid'
  FROM Checkout c
  JOIN Reader r ON c.reader_id = r.reader_id
  JOIN Policy p ON r.policy_id = p.policy_id
  WHERE c.returned_date IS NULL
    AND c.due_date < NOW()
    AND NOT EXISTS (
      SELECT 1 FROM Fine f
      WHERE f.checkout_id = c.checkout_id AND f.status = 'Unpaid'
    );

  UPDATE Fine f
  JOIN Checkout c ON f.checkout_id = c.checkout_id
  JOIN Reader r ON c.reader_id = r.reader_id
  JOIN Policy p ON r.policy_id = p.policy_id
  SET f.amount = ROUND(GREATEST(DATEDIFF(NOW(), c.due_date), 0) * p.fine_per_day, 2)
  WHERE c.returned_date IS NULL
    AND c.due_date < NOW()
    AND f.status = 'Unpaid';
END$$
DELIMITER ;
