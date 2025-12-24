INSERT INTO Policy (
  name, loan_period_days, renewals_allowed, fine_per_day,
  max_concurrent_loans, holds_limit_reservation
) VALUES
('Standard Policy', 14, 2, 0.5, 5, 5);

INSERT INTO User (
    user_first_name, user_middle_name, user_last_name,
    user_phone_number, user_email, user_password,
    status, user_type
) VALUES
-- Reader (id=1)
('Melisa', '', 'Tanrikulu', '5555556666', 'melisa.tanrikulu@example.com', SHA2('melisatanrikulu', 256), 'Active', 'Reader'),
-- Librarian (id=2)
('Emily', 'E.', 'Johnson', '5559990000', 'emily.johnson@example.com', SHA2('password', 256), 'Active', 'Librarian'),
-- Admin (id=3)
('Admin', '', 'Admin', '5555656565', 'admin.admin@example.com', SHA2('adminadmin', 256), 'Active', 'Admin'),
-- Reader (id=4)
('Jane', '', 'Smith', '5555557777', 'jane.smith@example.com', SHA2('janesmith', 256), 'Active', 'Reader');

INSERT INTO Reader (reader_id, policy_id)
VALUES
(1, 1),
(4, 1);

INSERT INTO Author (author_name) VALUES
('Andy Weir'),
('Harper Lee'),
('J.K. Rowling'),
('Dan Brown'),
('Kristin Hannah'),
('George Orwell'),
('Gillian Flynn');

INSERT INTO Genre (genre_name)
VALUES
('Fantasy'),
('Science Fiction'),
('Classic Literature'),
('Mystery / Thriller'),
('Historical Fiction');

INSERT INTO Book (
    isbn, title, publisher, publication_date, language, material_type,
    physical_description, summary, page_number
) VALUES
('9780143127741', 'The Martian', 'Crown Publishing', '2014-02-11', 'English', 'Book', 'Paperback, 5.5 x 8.2 inches', 'An astronaut stranded on Mars struggles to survive after being left behind by his crew.', 369),
('9780061120084', 'To Kill a Mockingbird', 'J.B. Lippincott & Co.', '1960-07-11', 'English', 'Book', 'Hardcover, 6 x 9 inches', 'A young girl witnesses racial injustice in the Deep South.', 281),
('9780439139601', 'Harry Potter and the Goblet of Fire', 'Bloomsbury', '2000-07-08', 'English', 'Book', 'Hardcover, illustrated', 'Harry competes in the dangerous Triwizard Tournament while facing the return of Lord Voldemort.', 734),
('9780385533225', 'Inferno', 'Doubleday', '2013-05-14', 'English', 'Book', 'Hardcover, 6.5 x 9.5 inches', 'Robert Langdon races through Florence to stop a global catastrophe inspired by Dante''s Inferno.', 480),
('9781501128035', 'The Nightingale', 'St. Martin''s Press', '2015-02-03', 'English', 'Book', 'Paperback, 5.5 x 8.2 inches', 'Two sisters in Nazi-occupied France risk everything to survive and resist the German occupation.', 440),
('9780141182575', '1984', 'Secker & Warburg', '1949-06-08', 'English', 'Book', 'Paperback, 5 x 8 inches', 'A dystopian novel set in a totalitarian regime under constant surveillance.', 328),
('9780307588371', 'Gone Girl', 'Crown Publishing', '2012-06-05', 'English', 'Book', 'Hardcover, 6 x 9 inches', 'A thriller about a man suspected of causing his wife''s mysterious disappearance.', 422);

INSERT INTO Book_Author (book_id, author_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5),
(6, 6),
(7, 7);

INSERT INTO Book_Genre (book_id, genre_id) VALUES
(1, 2),
(1, 4),
(2, 3),
(3, 1),
(3, 4),
(4, 4),
(5, 5),
(6, 3),
(6, 2),
(7, 4);

INSERT INTO Location (direction, collection, shelf_row)
VALUES
('North Wing', 'Fiction', 'A1'),
('North Wing', 'Fiction', 'A2'),
('North Wing', 'Science Fiction', 'B1'),
('South Wing', 'Non-Fiction', 'C3');

INSERT INTO Copy (
    item_barcode, call_number, acquisition_type,
    status, added_date, book_id, location_id
) VALUES
('BC001', 'FIC-WEI-TM', 'Purchase', 'Available', '2023-11-01 10:15:00', 1, 1),
('BC002', 'FIC-LEE-TKM', 'Purchase', 'Available', '2023-10-20 09:30:00', 2, 4),
('BC003', 'FIC-ROW-HP4', 'Purchase', 'Available', '2023-11-02 13:40:00', 3, 2),
('BC004', 'MYS-BRO-INF', 'Purchase', 'Available', '2023-11-04 17:25:00', 4, 3),
('BC005', 'HIS-HAN-NI', 'Purchase', 'Available', '2023-11-10 11:55:00', 5, 1),
('BC006', 'CLA-ORW-1984', 'Purchase', 'Available', '2023-10-15 09:00:00', 6, 3),
('BC007', 'THR-FLY-GG', 'Purchase', 'Available', '2023-09-30 12:00:00', 7, 4);

-- Exchange copies (user owned)
INSERT INTO Copy (
  item_barcode, call_number, acquisition_type,
  status, added_date, book_id, location_id, owner_id
) VALUES
('EXCH001', 'FAN-ROW-HP4', 'Exchange', 'Pending Approval', '2025-10-20 10:15:00', 3, NULL, 1),
('EXCH002', 'SCI-WEI-TM', 'Exchange', 'Available', '2025-10-21 10:15:00', 1, NULL, 4);

INSERT INTO Material (isbn, title, publisher, publication_date, author)
VALUES
('9781524763138', 'Becoming', 'Crown Publishing', '2018-11-13', 'Michelle Obama'),
('9780553386790', 'Dune', 'Ace Books', '1965-08-01', 'Frank Herbert');

INSERT INTO Request (request_date, expire_date, request_type, status, material_id, reader_id, copy_id)
VALUES
-- Hold and borrow requests for specific copies
('2025-11-06 09:00:00', NULL, 'Hold', 'Pending', NULL, 1, 'BC002'),
('2025-11-05 12:00:00', '2025-11-19 12:00:00', 'Borrow', 'Approved', NULL, 1, 'BC001'),
-- Book request and donation (material only)
('2025-11-04 09:45:00', '2025-11-18 09:45:00', 'Book Request', 'Pending', 1, 1, NULL),
('2025-11-05 10:05:00', '2025-11-19 10:05:00', 'Donation', 'Pending', 2, 1, NULL),
-- Exchange approval request for EXCH001
('2025-11-06 18:00:00', '2025-11-20 18:00:00', 'Exchange', 'Pending', NULL, 1, 'EXCH001');

INSERT INTO Exchange_Request (request_date, status, owner_copy_id, requester_id)
VALUES
('2025-11-06 19:00:00', 'Pending', 'EXCH002', 1);

INSERT INTO Review (rating, review_text, reader_id, book_id)
VALUES
(5, 'Loved the science and humor.', 1, 1),
(4, 'A classic with strong themes.', 1, 2);

INSERT INTO Checkout (
  checkout_date, due_date, returned_date, renew_count, reader_id, copy_id
) VALUES
('2025-10-28 10:05:00', '2025-11-11 23:59:59', NULL, 0, 1, 'BC001');

INSERT INTO Notification (notification_date, subject, details, is_read, user_id)
VALUES
('2025-11-12 10:40:00', 'Book Due Soon', 'Your book "The Martian" is due in 2 days.', FALSE, 1),
('2025-11-13 10:20:00', 'New Exchange Copy', 'An exchange copy is pending approval.', FALSE, 2),
('2025-11-13 10:20:00', 'System Backup Completed', 'Database backup completed.', TRUE, 3),
('2025-11-13 11:00:00', 'Exchange Request Sent', 'Your exchange request has been sent.', FALSE, 4);

INSERT INTO Fine (checkout_id, fine_reason, payment_method, date_paid, amount, status)
VALUES
(1, 'Overdue: "The Martian" returned 3 days late.', 'Cash', '2025-11-14 10:30:00', 4.50, 'Paid');

INSERT INTO Log (log_date, source, log_level, log_node, log_message)
VALUES
('2025-11-10 09:15:30', 'UserModule', 'INFO', 'AuthService', 'User Melisa (ID: 1) successfully logged in.'),
('2025-11-10 09:20:11', 'BookModule', 'WARN', 'InventoryCheck', 'Book "1984" (Barcode: BC006) marked as LOST.');

INSERT INTO User_Activity_Log (action_type, action_date, details, user_id)
VALUES
('Login', '2025-11-10 08:30:15', 'Reader Melisa logged into the system.', 1),
('Login', '2025-11-10 08:00:00', 'Librarian Emily Johnson logged into the system.', 2),
('Login', '2025-11-09 22:00:00', 'Admin Admin logged into the admin panel.', 3),
('Login', '2025-11-10 09:10:00', 'Reader Jane Smith logged into the system.', 4);

UPDATE Book b
SET average_rating = (
    SELECT COALESCE(AVG(rating), 0)
    FROM Review r
    WHERE r.book_id = b.book_id
);
