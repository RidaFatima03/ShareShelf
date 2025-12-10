INSERT INTO User (
    user_first_name, user_middle_name, user_last_name,
    user_phone_number, user_email, user_password,
    status, joined_at, user_type
) VALUES
('John', 'A.', 'Doe', '5551112222', 'john.doe@example.com', SHA2('password1', 256), 'ACTIVE', '2023-10-01 09:15:00', 'Reader'),
('Jane', 'B.', 'Smith', '5553334444', 'jane.smith@example.com', SHA2('password2', 256), 'ACTIVE', '2023-09-20 10:30:00', 'Reader'),
('Michael', 'C.', 'Brown', '5555556666', 'michael.brown@example.com', SHA2('password3', 256), 'ACTIVE', '2023-08-12 14:00:00', 'Reader'),
('Sarah', 'D.', 'Miller', '5557778888', 'sarah.miller@example.com', SHA2('password4', 256), 'INACTIVE', '2023-07-01 11:45:00', 'Reader'),

('Emily', 'E.', 'Johnson', '5559990000', 'emily.johnson@example.com', SHA2('password5', 256), 'ACTIVE', '2023-06-10 13:30:00', 'Librarian'),
('Robert', 'F.', 'Wilson', '5551212121', 'robert.wilson@example.com', SHA2('password6', 256), 'ACTIVE', '2023-06-15 09:00:00', 'Librarian'),

('Alice', 'G.', 'Taylor', '5553434343', 'alice.taylor@example.com', SHA2('password7', 256), 'ACTIVE', '2023-05-10 15:00:00', 'Admin'),
('Melisa', '', 'Tanrikulu', '5369498281', 'melisatanrikulu07@gmail.com', SHA2('passwordMelisa99', 256), 'ACTIVE', '2023-05-15 12:30:00', 'Admin'),
('David', 'H.', 'Anderson', '5555656565', 'david.anderson@example.com', SHA2('password8', 256), 'ACTIVE', '2023-05-15 12:30:00', 'Admin');

INSERT INTO Reader (reader_id, is_approved)
VALUES
(1, TRUE),
(2, TRUE),
(3, TRUE),
(4, FALSE);

INSERT INTO Librarian (librarian_id) 
VALUES
(5),
(6);

INSERT INTO Admin (admin_id)
VALUES
(7),
(8);

INSERT INTO Author (author_name) VALUES
('Andy Weir'),
('Harper Lee'),
('J.K. Rowling'),
('Stieg Larsson'),
('Dan Brown'),
('Kristin Hannah'),
('George Orwell'),
('Gillian Flynn'),
('Cormac McCarthy'),
('Rebecca Yarros'),
('James Dashner'),
('Rick Riordan');

INSERT INTO Genre (genre_name)
VALUES
('Fantasy'),
('Science Fiction'),
('Classic Literature'),
('Mystery / Thriller'),
('Historical Fiction');

INSERT INTO Book (
    isbn, title, publisher, publication_date, language,
    physical_description, summary, page_number
) VALUES
('9780143127741', 'The Martian', 'Crown Publishing', '2014-02-11', 'English', 'Paperback, 5.5 x 8.2 inches', 'An astronaut stranded on Mars struggles to survive after being left behind by his crew.', 369),
('9780061120084', 'To Kill a Mockingbird', 'J.B. Lippincott & Co.', '1960-07-11', 'English', 'Hardcover, 6 x 9 inches', 'A young girl witnesses racial injustice in the Deep South.', 281),
('9780439139601', 'Harry Potter and the Goblet of Fire', 'Bloomsbury', '2000-07-08', 'English', 'Hardcover, illustrated', 'Harry competes in the dangerous Triwizard Tournament while facing the return of Lord Voldemort.', 734),
('9780307277671', 'The Girl with the Dragon Tattoo', 'Norstedts Förlag', '2005-08-01', 'Swedish', 'Paperback, 5.1 x 7.8 inches', 'A journalist and a hacker uncover corruption and family secrets in a dark Swedish mystery.', 465),
('9780385533225', 'Inferno', 'Doubleday', '2013-05-14', 'English', 'Hardcover, 6.5 x 9.5 inches', 'Robert Langdon races through Florence to stop a global catastrophe inspired by Dante''s Inferno.', 480),
('9781501128035', 'The Nightingale', 'St. Martin''s Press', '2015-02-03', 'English', 'Paperback, 5.5 x 8.2 inches', 'Two sisters in Nazi-occupied France risk everything to survive and resist the German occupation.', 440),
('9780141182575', '1984', 'Secker & Warburg', '1949-06-08', 'English', 'Paperback, 5 x 8 inches', 'A dystopian novel set in a totalitarian regime under constant surveillance.', 328),
('9780307588371', 'Gone Girl', 'Crown Publishing', '2012-06-05', 'English', 'Hardcover, 6 x 9 inches', 'A thriller about a man suspected of causing his wife''s mysterious disappearance.', 422),
('9780307476463', 'The Road', 'Vintage Books', '2006-09-26', 'English', 'Paperback, 5.2 x 8 inches', 'A father and son journey through a post-apocalyptic landscape of desolation and hope.', 287),
('9780590353427', 'Harry Potter and the Sorcerer''s Stone', 'Bloomsbury', '1997-06-26', 'English', 'Hardcover, 5.5 x 8.5 inches', 'A young boy discovers he''s a wizard and attends a magical school called Hogwarts.', 309),
('9781649374042', 'Fourth Wing', 'Red Tower Books', '2023-05-02', 'English', 'Hardcover, 6 x 9 inches', 'Violet Sorrengail enters the Rider Quadrant to become a dragon rider.', 500),
('9780385737944', 'The Maze Runner', 'Delacorte Press', '2009-10-06', 'English', 'Paperback, 5.5 x 8.2 inches', 'Thomas wakes up in a lift with no memory, trapped in a massive maze.', 375),
('9780786856299', 'Percy Jackson: The Lightning Thief', 'Disney Hyperion', '2005-06-28', 'English', 'Paperback, 5.2 x 8 inches', 'Percy Jackson discovers he is a demigod and must prevent a war between the gods.', 377);
 
-- Book → Author
INSERT INTO Book_Author (book_id, author_id) VALUES
-- Each book can have one or more authors
(1, 1),                             -- The Martian → Andy Weir
(2, 2),                             -- To Kill a Mockingbird → Harper Lee
(3, 3),                             -- Goblet of Fire → J.K. Rowling
(4, 4),                             -- The Girl with the Dragon Tattoo → Stieg Larsson
(5, 5),                             -- Inferno → Dan Brown
(6, 6),                             -- The Nightingale → Kristin Hannah
(7, 7),                             -- 1984 → George Orwell
(8, 8),                             -- Gone Girl → Gillian Flynn
(9, 9),                             -- The Road → Cormac McCarthy
(10, 3),                            -- Sorcerer’s Stone → J.K. Rowling
(11, 10),                           -- Fourth Wing -> Rebecca Yarros
(12, 11),                           -- Maze Runner -> James Dashner
(13, 12),                           -- Percy Jackson -> Rick Riordan

-- Books with multiple authors:
(5, 1),                             -- Inferno also credited to Andy Weir (hypothetical co-author)
(10, 5);                            -- Sorcerer’s Stone also listed with Dan Brown (for test variety)


-- Book → Genre
INSERT INTO Book_Genre (book_id, genre_id) VALUES
(1, 2),                             -- The Martian → Science Fiction
(1, 4),                             -- The Martian → Mystery/Thriller
(2, 3),                             -- To Kill a Mockingbird → Classic Literature
(3, 1),                             -- Goblet of Fire → Fantasy
(3, 4),                             -- Goblet of Fire → Mystery/Thriller
(4, 4),                             -- The Girl with the Dragon Tattoo → Mystery/Thriller
(5, 4),                             -- Inferno → Mystery/Thriller
(5, 3),                             -- Inferno → Classic Literature
(6, 5),                             -- The Nightingale → Historical Fiction
(6, 3),                             -- The Nightingale → Classic Literature
(7, 3),                             -- 1984 → Classic Literature
(7, 2),                             -- 1984 → Science Fiction
(8, 4),                             -- Gone Girl → Mystery/Thriller
(9, 2),                             -- The Road → Science Fiction
(9, 3),                             -- The Road → Classic Literature
(10, 1),                            -- Sorcerer’s Stone → Fantasy
(10, 2),                            -- Sorcerer’s Stone → Science Fiction
(11, 1),                            -- Fourth Wing -> Fantasy
(12, 2),                            -- Maze Runner -> Sci Fi
(13, 1);                            -- Percy Jackson -> Fantasy

INSERT INTO Location (direction, collection, shelf_row)
VALUES
('North Wing', 'Fiction', 'A1'),
('North Wing', 'Fiction', 'A2'),
('North Wing', 'Science Fiction', 'B1'),
('South Wing', 'Non-Fiction', 'C3'),
('South Wing', 'Biography', 'C2'),
('East Wing', 'Reference', 'R1'),
('East Wing', 'Periodicals', 'R2'),
('West Wing', 'Children', 'K1'),
('West Wing', 'Young Adult', 'K2'),
('Basement', 'Archives', 'AR1');

INSERT INTO Copy (
    item_barcode, material_type, call_number, acquisition_type,
    status, added_date, book_id, location_id
) VALUES
('BC001', 'Book', 'FIC-WEI-TM', 'Purchase', 'On Loan', '2023-11-01 10:15:00', 1, 1),
('BC013', 'Book', 'FIC-WEI-TM', 'Purchase', 'Available', '2023-11-01 10:15:00', 1, 1),
('BC002', 'Book', 'FIC-WEI-TM', 'Donation', 'On Loan', '2023-11-05 14:20:00', 1, 2),
('BC003', 'Book', 'FIC-LEE-TKM', 'Purchase', 'Available', '2023-10-20 09:30:00', 2, 4),
('BC004', 'Book', 'FIC-ROW-HP4', 'Purchase', 'On Hold', '2023-11-02 13:40:00', 3, 8),
('BC005', 'Book', 'FIC-ROW-HP4', 'Donation', 'Available', '2023-11-06 15:10:00', 3, 9),
('BC006', 'Book', 'MYS-LAR-GDT', 'Purchase', 'Available', '2023-10-28 11:00:00', 4, 6),
('BC007', 'Book', 'MYS-BRO-INF', 'Purchase', 'On Loan', '2023-11-04 17:25:00', 5, 7),
('BC008', 'Book', 'HIS-HAN-NI', 'Donation', 'Available', '2023-11-10 11:55:00', 6, 5),
('BC009', 'Book', 'CLA-ORW-1984', 'Purchase', 'Available', '2023-10-15 09:00:00', 7, 3),
('BC010', 'Book', 'THR-FLY-GG', 'Purchase', 'Lost', '2023-09-30 12:00:00', 8, 4),
('BC011', 'Book', 'SCI-MCC-ROAD', 'Purchase', 'Available', '2023-11-09 13:45:00', 9, 2),
('BC012', 'Book', 'FAN-ROW-HP1', 'Purchase', 'Available', '2023-11-08 10:10:00', 10, 8);

-- --- EXCHANGE COPIES (User Owned) ---
-- These show up in "My Books" for the owner and "Exchange Market" for others
INSERT INTO Copy (
  item_barcode, material_type, call_number, acquisition_type,
  status, added_date, book_id, location_id, owner_id
) VALUES
-- JOHN (User 1) owns these new books:
('EXCH001', 'Book', 'FAN-YAR-FW',  'Exchange', 'Available', '2025-10-20 10:15:00', 11, NULL, 1), -- Fourth Wing
('EXCH002', 'Book', 'SCI-DAS-MR',  'Exchange', 'Available', '2025-10-29 15:45:00', 12, NULL, 1), -- Maze Runner

-- JANE (User 2) owns this new book:
('EXCH003', 'Book', 'FAN-RIO-PJ','Exchange', 'Available', '2025-10-25 14:00:00', 13, NULL, 2); -- Percy Jackson


INSERT INTO Review (rating, review_text, reader_id, book_id)
VALUES
(5, 'Absolutely loved it! The science felt real and the humor was great.', 1, 1), -- The Martian
(4, 'A timeless story about justice and childhood. A must-read classic.', 2, 2), -- To Kill a Mockingbird
(5, 'My favorite book in the series. So intense and emotional!', 3, 3), -- Harry Potter and the Goblet of Fire
(3, 'Interesting mystery but a bit slow in the middle.', 1, 4), -- The Girl with the Dragon Tattoo
(4, 'Fast-paced and filled with symbolism. Loved the historical tie-ins.', 2, 5), -- Inferno
(5, 'Heartbreaking and beautifully written. Could not put it down.', 3, 6), -- The Nightingale
(4, 'A chilling look at totalitarianism. Still relevant today.', 4, 7), -- 1984
(3, 'Twists were good, but the ending didn’t satisfy me.', 2, 8), -- Gone Girl
(4, 'Dark but hopeful. The writing style is hauntingly simple.', 1, 9), -- The Road
(1, 'Very bad.', 2, 9), -- The Road
(5, 'The dragons are amazing!', 1, 11), -- Fourth Wing
(4, 'Kept me guessing until the end.', 2, 12), -- Maze Runner
(5, 'Best childhood memories.', 3, 13); -- Percy Jackson

INSERT INTO Checkout (
  checkout_date, due_date, returned_date, renew_count, reader_id, copy_id
) VALUES
-- Reader 1 checks out BC001
('2025-10-28 10:05:00', '2025-11-11 23:59:59', NULL, 0, 1, 'BC001'),

-- Reader 2 checks out BC002 (returned on time)
('2025-10-20 14:30:00', '2025-11-03 23:59:59', '2025-11-02 16:10:00', 0, 2, 'BC002'),

-- Reader 3 checks out BC003 (renewed once, still out)
('2025-10-15 09:10:00', '2025-10-29 23:59:59', NULL, 1, 3, 'BC003'),

-- Reader 1 checks out BC004 (reserved copy, returned late)
('2025-09-25 13:45:00', '2025-10-09 23:59:59', '2025-10-12 11:20:00', 0, 1, 'BC004'),

-- Reader 4 checks out BC005 (renewed twice, still out)
('2025-10-05 11:00:00', '2025-10-19 23:59:59', NULL, 2, 4, 'BC005'),

-- Reader 2 checks out BC006 (returned on time)
('2025-08-30 10:00:00', '2025-09-13 23:59:59', '2025-09-12 09:50:00', 0, 2, 'BC006'),

-- Reader 3 checks out BC007 (was checked out before; returned)
('2025-09-10 17:25:00', '2025-09-24 23:59:59', '2025-09-22 12:05:00', 0, 3, 'BC007'),

-- Reader 1 checks out BC008 (magazine, short loan, returned)
('2025-11-01 09:00:00', '2025-11-08 23:59:59', '2025-11-06 10:00:00', 0, 1, 'BC008'),

-- Reader 4 checks out BC009 (lost previously, now available; still out)
('2025-10-22 08:45:00', '2025-11-05 23:59:59', NULL, 0, 4, 'BC009'),

-- Reader 2 checks out BC010 (overdue)
('2025-10-10 12:00:00', '2025-10-24 23:59:59', NULL, 0, 2, 'BC010'),

-- Reader 3 checks out BC011 (renewed once, returned)
('2025-10-12 13:45:00', '2025-10-26 23:59:59', '2025-10-25 18:30:00', 1, 3, 'BC011'),

-- Reader 4 checks out BC012 (still out)
('2025-11-08 10:10:00', '2025-11-22 23:59:59', NULL, 0, 4, 'BC012');

INSERT INTO Notification (notification_date, subject, details, is_read, user_id)
VALUES
-- Reader notifications
('2025-11-12 10:40:00', 'Book Due Soon', 'Your book "The Martian" is due in 2 days. Please return or renew to avoid fines.', FALSE, 1),
('2025-11-14 10:30:00', 'Overdue Notice', 'Your book "The Road" is now overdue. A fine will be applied to your account.', FALSE, 1),
('2025-11-14 10:50:00', 'Reservation Ready', 'The book "1984" you reserved is now available for pickup.', TRUE, 2),
('2025-11-15 10:30:00', 'Checkout Confirmation', 'You have successfully checked out "To Kill a Mockingbird". Due date: 2025-11-20.', TRUE, 2),
('2025-11-13 10:20:00', 'Review Response', 'Your review for "Harry Potter and the Goblet of Fire" has been liked by the librarian.', FALSE, 3),

-- Librarian notifications
('2025-11-13 10:20:00', 'New Book Added', 'You successfully added "The Nightingale" to the catalog.', TRUE, 5),
('2025-11-13 10:50:00', 'Overdue Report', 'A new overdue report is ready for review.', FALSE, 5),

-- Admin notifications
('2025-11-13 10:20:00', 'System Backup Completed', 'Database backup was successfully completed at 2025-11-12 02:00:00.', TRUE, 7),
('2025-11-14 10:20:00', 'User Account Approved', 'Reader Jane Smith has been approved and can now borrow books.', TRUE, 7),
('2025-11-15 10:20:00', 'Policy Update', 'Loan period for Readers has been updated to 21 days.', FALSE, 8);

INSERT INTO Fine (checkout_id, fine_reason, payment_method, date_paid, amount, status)
VALUES
-- Reader 1 (John Doe)
(1, 'Overdue: "The Martian" returned 3 days late.', 'Cash', '2025-11-14 10:30:00', 4.50, 'Paid'),
(4, 'Overdue: "The Girl with the Dragon Tattoo" returned 2 days late.', 'Credit Card', '2025-10-14 11:10:00', 3.00, 'Paid'),

-- Reader 2 (Jane Smith)
(2, 'Damaged: "To Kill a Mockingbird" cover torn.', NULL, NULL, 8.00, 'Unpaid'),
(10, 'Overdue: "Gone Girl" overdue by 5 days.', NULL, NULL, 7.50, 'Unpaid'),

-- Reader 3 (Michael Brown)
(3, 'Overdue: "Harry Potter and the Goblet of Fire" not yet returned.', NULL, NULL, 5.00, 'Unpaid'),
(11, 'Overdue: "Inferno" returned 1 day late.', 'Online Payment', '2025-10-27 09:45:00', 1.50, 'Paid'),

-- Reader 4 (Sarah Miller)
(5, 'Lost: "1984" declared lost after 45 days.', 'Cash', '2025-11-01 15:00:00', 20.00, 'Paid'),
(9, 'Overdue: "The Road" overdue by 4 days.', NULL, NULL, 6.00, 'Unpaid'),
(12, 'Overdue: "Harry Potter and the Sorcerer''s Stone" overdue by 2 days.', 'Credit Card', '2025-11-25 14:10:00', 2.50, 'Paid');

INSERT INTO Material (isbn, title, publisher, publication_date, author)
VALUES
('9781524763138', 'Becoming', 'Crown Publishing', '2018-11-13', 'Michelle Obama'),
('9780553386790', 'Dune', 'Ace Books', '1965-08-01', 'Frank Herbert'),
('9780062315008', 'The Alchemist', 'HarperOne', '1993-05-01', 'Paulo Coelho'),
('9780385472579', 'The Things They Carried', 'Houghton Mifflin', '1990-03-28', 'Tim O’Brien'),
('9780307474278', 'The Lost Symbol', 'Doubleday', '2009-09-15', 'Dan Brown');

INSERT INTO Request (request_type, expire_date, status, material_id, reader_id, book_id, exchange_book_id)
VALUES
-- Hold Requests (existing books)
('Hold', '2025-11-20 23:59:59', 'Pending', NULL, 1, 3, NULL),
('Hold', '2025-11-18 23:59:59', 'Approved', NULL, 2, 7, NULL),
('Hold', '2025-11-25 23:59:59', 'Pending', NULL, 3, 1, NULL),

-- Borrow Requests (existing books)
('Borrow', '2025-11-30 23:59:59', 'Approved', NULL, 1, 2, NULL),
('Borrow', '2025-11-28 23:59:59', 'Pending', NULL, 4, 6, NULL),

-- New Material Requests
('New Material', NULL, 'Pending', 1, 2, NULL, NULL),
('New Material', NULL, 'Approved', 2, 3, NULL, NULL),
('New Material', NULL, 'Rejected', 3, 1, NULL, NULL),
('New Material', NULL, 'Pending', 4, 4, NULL, NULL),
('New Material', NULL, 'Approved', 5, 3, NULL, NULL),

-- **EXCHANGE REQUESTS**
-- 1. Jane (Reader 2) requests John's "Fourth Wing" (Book 11). 
--    This will show up as an "Incoming Request" when you log in as John.
('Exchange', NULL, 'Pending', NULL, 2, 11, NULL); 

INSERT INTO Log (log_date, source, log_level, log_node, log_message)
VALUES
('2025-11-10 09:15:30', 'UserModule', 'INFO', 'AuthService', 'User John Doe (ID: 1) successfully logged in.'),
('2025-11-10 09:17:42', 'BookModule', 'INFO', 'CatalogService', 'Book "The Martian" added to the catalog by Librarian (ID: 5).'),
('2025-11-10 09:20:11', 'BookModule', 'WARN', 'InventoryCheck', 'Book "1984" (Barcode: BC009) marked as LOST.'),
('2025-11-10 10:02:55', 'CheckoutModule', 'INFO', 'TransactionHandler', 'Reader (ID: 2) borrowed "Gone Girl" (Barcode: BC010).'),
('2025-11-10 10:15:03', 'NotificationService', 'INFO', 'EmailWorker', 'Overdue notice sent to Reader (ID: 3) for "Inferno".'),
('2025-11-10 11:22:27', 'SystemMonitor', 'ERROR', 'DatabaseNode-1', 'Connection timeout detected. Reconnecting...'),
('2025-11-10 11:24:12', 'SystemMonitor', 'INFO', 'DatabaseNode-1', 'Database connection re-established successfully.'),
('2025-11-10 12:10:45', 'ExchangeModule', 'INFO', 'ExchangeService', 'Reader (ID: 1) exchanged "The Martian" (BC020) with Reader (ID: 2).'),
('2025-11-10 13:05:33', 'RequestModule', 'INFO', 'RequestProcessor', 'Reader (ID: 4) requested new material "Dune".'),
('2025-11-10 13:20:17', 'Security', 'WARN', 'LoginGuard', 'Failed login attempt for user_email=jane.smith@email.com.'),
('2025-11-10 13:25:42', 'Security', 'INFO', 'LoginGuard', 'Account lockout triggered for user_email=jane.smith@email.com after 3 failed attempts.'),
('2025-11-10 14:01:09', 'AdminModule', 'INFO', 'BackupManager', 'System backup completed successfully. File: backup_2025_11_10.zip'),
('2025-11-10 15:44:18', 'FineModule', 'INFO', 'PaymentProcessor', 'Reader (ID: 2) paid fine $7.50 via Credit Card for "Gone Girl".'),
('2025-11-10 16:00:00', 'PolicyModule', 'INFO', 'PolicyUpdater', 'Loan period for Readers changed from 14 to 21 days by Admin (ID: 7).'),
('2025-11-10 16:30:25', 'NotificationService', 'INFO', 'PushWorker', 'Push notification sent: "Your book is due tomorrow." to Reader (ID: 1).'),
('2025-11-10 17:05:55', 'Maintenance', 'INFO', 'SystemCleanup', 'Deleted 25 expired requests older than 30 days.'),
('2025-11-10 18:25:44', 'UserModule', 'INFO', 'ProfileService', 'Reader (ID: 3) updated account email to michael.brown@email.com.'),
('2025-11-10 19:10:22', 'Analytics', 'INFO', 'ReportGenerator', 'Generated daily report: Total checkouts = 58, New users = 3.'),
('2025-11-10 20:12:40', 'SystemMonitor', 'ERROR', 'CacheNode-2', 'Redis cache unreachable. Switching to backup cache.'),
('2025-11-10 20:15:09', 'SystemMonitor', 'INFO', 'CacheNode-2', 'Redis cache reconnected after 3 minutes downtime.');

INSERT INTO user_activity_log (action_type, action_date, details, user_id)
VALUES
-- Reader activities
('Login', '2025-11-10 08:30:15', 'Reader John Doe logged into the system.', 1),
('Borrow', '2025-11-10 09:02:45', 'Borrowed book "The Martian" (Copy BC001).', 1),
('Return', '2025-11-11 14:10:22', 'Returned book "The Martian" (Copy BC001) on time.', 1),
('Review', '2025-11-11 15:45:30', 'Posted a 5-star review for "The Martian".', 1),
('Logout', '2025-11-11 16:00:00', 'Reader John Doe logged out.', 1),

('Login', '2025-11-10 09:10:00', 'Reader Jane Smith logged into the system.', 2),
('Borrow', '2025-11-10 09:15:45', 'Borrowed book "Gone Girl" (Copy BC010).', 2),
('Fine Payment', '2025-11-12 10:25:10', 'Paid fine of $7.50 for overdue "Gone Girl".', 2),
('Logout', '2025-11-12 10:30:00', 'Reader Jane Smith logged out.', 2),

('Login', '2025-11-10 10:00:05', 'Reader Michael Brown logged into the system.', 3),
('Borrow', '2025-11-10 10:10:32', 'Borrowed book "Inferno" (Copy BC007).', 3),
('Exchange', '2025-11-11 13:15:00', 'Exchanged book "The Nightingale" (Copy BC023) with Reader Sarah Miller.', 3),
('Logout', '2025-11-11 13:30:00', 'Reader Michael Brown logged out.', 3),

('Login', '2025-11-11 08:55:00', 'Reader Sarah Miller logged into the system.', 4),
('Borrow', '2025-11-11 09:05:45', 'Borrowed book "1984" (Copy BC009).', 4),
('Review', '2025-11-12 11:20:30', 'Added a 4-star review for "1984".', 4),
('Logout', '2025-11-12 11:30:00', 'Reader Sarah Miller logged out.', 4),

-- Librarian activities
('Login', '2025-11-10 08:00:00', 'Librarian Alice Johnson logged into the system.', 5),
('Add Book', '2025-11-10 08:10:15', 'Added new book "The Nightingale" to the catalog.', 5),
('Approve Request', '2025-11-10 09:45:00', 'Approved book hold request for Reader Jane Smith.', 5),
('Logout', '2025-11-10 17:00:00', 'Librarian Alice Johnson logged out.', 5),

-- Admin activities
('Login', '2025-11-09 22:00:00', 'Admin Robert White logged into the admin panel.', 7),
('Policy Update', '2025-11-09 22:15:10', 'Updated loan policy: Reader loan period set to 21 days.', 7),
('System Backup', '2025-11-10 02:00:00', 'Scheduled system backup completed successfully.', 7),
('Logout', '2025-11-10 02:10:00', 'Admin Robert White logged out.', 7);


UPDATE Book b
SET average_rating = (
    SELECT COALESCE(AVG(rating), 0)
    FROM Review r
    WHERE r.book_id = b.book_id
);