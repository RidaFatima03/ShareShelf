CREATE TABLE IF NOT EXISTS Policy ( 
policy_id INT NOT NULL AUTO_INCREMENT,
name VARCHAR(100) NOT NULL,
loan_period_days INT NOT NULL,
renewals_allowed INT NOT NULL,
fine_per_day DECIMAL(10,2) NOT NULL,
max_concurrent_loans INT NOT NULL,
holds_limit_reservation INT NOT NULL,
PRIMARY KEY (policy_id)
);

CREATE TABLE IF NOT EXISTS User ( 
user_id INT NOT NULL AUTO_INCREMENT,
user_first_name VARCHAR(50) NOT NULL, 
user_middle_name VARCHAR(50) DEFAULT '',
user_last_name VARCHAR(50) NOT NULL,
user_phone_number VARCHAR(15) NOT NULL UNIQUE,
user_email VARCHAR(100) NOT NULL UNIQUE,
user_password VARCHAR(255) NOT NULL, 
status ENUM('Active', 'Inactive', 'Blocked') NOT NULL,
joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
user_type ENUM('Reader', 'Librarian', 'Admin') NOT NULL,
PRIMARY KEY (user_id)
); 

CREATE TABLE PasswordResetToken (
token_id VARCHAR(256) PRIMARY KEY,
user_id INT NOT NULL,
expires_at DATETIME NOT NULL,
used TINYINT(1) DEFAULT 0,
FOREIGN KEY (user_id) REFERENCES User(user_id)
  ON DELETE CASCADE
);

CREATE TABLE Reader ( 
reader_id INT NOT NULL,
policy_id INT NOT NULL,
PRIMARY KEY (reader_id),
FOREIGN KEY (reader_id) REFERENCES User(user_id)
  ON DELETE CASCADE
  ON UPDATE CASCADE,
FOREIGN KEY (policy_id) REFERENCES Policy(policy_id)
  ON DELETE RESTRICT
  ON UPDATE CASCADE
);

CREATE TABLE Reader_Rate ( 
rate_id INT NOT NULL AUTO_INCREMENT,
rating INT NOT NULL,
comment TEXT,
created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
rated_user_id INT NOT NULL,
rate_owner_id INT NOT NULL,
PRIMARY KEY (rate_id),
UNIQUE (rated_user_id, rate_owner_id),
FOREIGN KEY (rated_user_id) REFERENCES Reader(reader_id)
  ON DELETE CASCADE,
FOREIGN KEY (rate_owner_id) REFERENCES Reader(reader_id)
  ON DELETE CASCADE
);

CREATE TABLE User_Activity_Log ( 
log_id INT NOT NULL AUTO_INCREMENT, 
action_type VARCHAR(50) NOT NULL,
action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
details TEXT,
user_id INT NOT NULL,
PRIMARY KEY (log_id),
FOREIGN KEY (user_id) REFERENCES User(user_id)
  ON DELETE CASCADE
);

CREATE TABLE Log ( 
log_id INT NOT NULL AUTO_INCREMENT,
log_date DATETIME NOT NULL,
source VARCHAR(100) NOT NULL,
log_level VARCHAR(20) NOT NULL,
log_node VARCHAR(100) NOT NULL, 
log_message TEXT NOT NULL,
PRIMARY KEY (log_id)
);

CREATE TABLE Notification ( 
notification_id INT NOT NULL AUTO_INCREMENT,
notification_date DATETIME DEFAULT CURRENT_TIMESTAMP,
subject VARCHAR(255) NOT NULL,
details TEXT NOT NULL,
is_read BOOLEAN DEFAULT FALSE,
user_id INT NOT NULL,
PRIMARY KEY (notification_id),
FOREIGN KEY (user_id) REFERENCES User(user_id)
  ON DELETE CASCADE
);


CREATE TABLE Author ( 
author_id INT NOT NULL AUTO_INCREMENT,
author_name VARCHAR(100) NOT NULL,
PRIMARY KEY (author_id)
);

CREATE TABLE Genre ( 
genre_id INT NOT NULL AUTO_INCREMENT,
genre_name VARCHAR(50) NOT NULL,
PRIMARY KEY (genre_id)
);

CREATE TABLE Book ( 
book_id INT NOT NULL AUTO_INCREMENT,
isbn VARCHAR(20) NOT NULL UNIQUE,
title VARCHAR(255) NOT NULL,
material_type VARCHAR(50) NOT NULL,
publisher VARCHAR(100),
publication_date DATE,
language VARCHAR(50),
physical_description VARCHAR(255),
summary TEXT,
average_rating DECIMAL(3,2) DEFAULT 0,
page_number INT,
PRIMARY KEY (book_id)
);

CREATE TABLE Book_Author (
book_id INT NOT NULL,
author_id INT NOT NULL,
PRIMARY KEY (book_id, author_id),
FOREIGN KEY (book_id) REFERENCES Book(book_id)
  ON DELETE CASCADE,
FOREIGN KEY (author_id) REFERENCES Author(author_id)
  ON DELETE RESTRICT
);

CREATE TABLE Book_Genre (
book_id INT NOT NULL,
genre_id INT NOT NULL,
PRIMARY KEY (book_id, genre_id),
FOREIGN KEY (book_id) REFERENCES Book(book_id)
  ON DELETE CASCADE,
FOREIGN KEY (genre_id) REFERENCES Genre(genre_id)
  ON DELETE RESTRICT
);

CREATE TABLE Review ( 
review_id INT NOT NULL AUTO_INCREMENT,
rating INT NOT NULL,
review_text TEXT,
created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
reader_id INT NOT NULL,
book_id INT NOT NULL,
PRIMARY KEY (review_id),
UNIQUE (reader_id, book_id),
FOREIGN KEY (reader_id) REFERENCES Reader(reader_id)
  ON DELETE CASCADE,
FOREIGN KEY (book_id) REFERENCES Book(book_id)
  ON DELETE CASCADE,
CHECK (rating BETWEEN 1 AND 5)
);

CREATE TABLE Location ( 
location_id INT NOT NULL AUTO_INCREMENT,
direction VARCHAR(50) NOT NULL,
collection VARCHAR(50) NOT NULL,
shelf_row VARCHAR(20) NOT NULL,
PRIMARY KEY (location_id),
UNIQUE (direction, collection, shelf_row)
);

CREATE TABLE Copy ( 
item_barcode VARCHAR(50) NOT NULL,
call_number VARCHAR(50),
acquisition_type ENUM('Purchase', 'Donation', 'Exchange', 'Other') NOT NULL,
status ENUM('Pending Approval', 'Available', 'On Loan', 'On Hold', 'Lost', 'Exchanged', 'Pending Handoff') DEFAULT 'Available',
added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
book_id INT NOT NULL,
location_id INT,
owner_id INT,
PRIMARY KEY (item_barcode),
FOREIGN KEY (book_id) REFERENCES Book(book_id)
  ON DELETE RESTRICT,
FOREIGN KEY (location_id) REFERENCES Location(location_id)
  ON DELETE RESTRICT,
FOREIGN KEY (owner_id) REFERENCES Reader(reader_id)
);

CREATE TABLE Checkout ( 
checkout_id INT NOT NULL AUTO_INCREMENT,
checkout_date DATETIME NOT NULL,
due_date DATETIME NOT NULL,
returned_date DATETIME DEFAULT NULL,
renew_count INT DEFAULT 0,
reader_id INT NOT NULL,
copy_id VARCHAR(50) NOT NULL,
PRIMARY KEY (checkout_id),
FOREIGN KEY (reader_id) REFERENCES Reader(reader_id)
  ON DELETE CASCADE,
FOREIGN KEY (copy_id) REFERENCES Copy(item_barcode)
  ON DELETE CASCADE
);

CREATE TABLE Fine ( 
fine_id INT NOT NULL AUTO_INCREMENT, 
checkout_id INT NOT NULL,
fine_reason VARCHAR(255) NOT NULL,
date_billed DATETIME DEFAULT CURRENT_TIMESTAMP,
payment_method VARCHAR(50),
date_paid DATETIME DEFAULT NULL,
amount DECIMAL(10,2) NOT NULL,
status ENUM('Unpaid', 'Paid') DEFAULT 'Unpaid',
PRIMARY KEY (fine_id),
FOREIGN KEY (checkout_id) REFERENCES Checkout(checkout_id)
  ON DELETE CASCADE
);

CREATE TABLE Material ( 
material_id INT NOT NULL AUTO_INCREMENT,
isbn VARCHAR(20) NOT NULL,
title VARCHAR(255) NOT NULL,
publisher VARCHAR(100),
publication_date DATE,
author VARCHAR(100),
PRIMARY KEY (material_id) 
);

CREATE TABLE Request ( 
request_id INT NOT NULL AUTO_INCREMENT,
request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
request_type ENUM('Hold', 'Borrow', 'Book Request', 'Donation', 'Exchange'),
expire_date DATETIME,
status ENUM('Pending', 'Approved', 'Rejected', 'Expired', 'Completed', 'Cancelled') DEFAULT 'Pending',

material_id INT NULL,
reader_id INT NOT NULL,
copy_id VARCHAR(50) NULL,

PRIMARY KEY (request_id),

FOREIGN KEY (material_id) REFERENCES Material(material_id) ON DELETE CASCADE,
FOREIGN KEY (reader_id)  REFERENCES Reader(reader_id)     ON DELETE CASCADE,
FOREIGN KEY (copy_id)    REFERENCES Copy(item_barcode)    ON DELETE CASCADE,

CHECK (
  (request_type IN ('Hold','Borrow','Exchange') AND copy_id IS NOT NULL AND material_id IS NULL)
  OR
  (request_type IN ('Book Request', 'Donation') AND material_id IS NOT NULL AND copy_id IS NULL)
)
);

CREATE TABLE Exchange_Request (
exchange_request_id INT NOT NULL AUTO_INCREMENT,
request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
status ENUM('Pending', 'Approved', 'Rejected', 'Completed', 'Cancelled') DEFAULT 'Pending',

owner_copy_id VARCHAR(50) NOT NULL,
requester_id INT NOT NULL,
requester_copy_id VARCHAR(50) NULL,

requester_confirmed BOOLEAN DEFAULT FALSE,
owner_confirmed BOOLEAN DEFAULT FALSE,

PRIMARY KEY (exchange_request_id),

FOREIGN KEY (owner_copy_id) REFERENCES Copy(item_barcode) ON DELETE CASCADE,
FOREIGN KEY (requester_id) REFERENCES Reader(reader_id) ON DELETE CASCADE,
FOREIGN KEY (requester_copy_id) REFERENCES Copy(item_barcode) ON DELETE SET NULL
);

CREATE TABLE Request_Status_History (
history_id INT NOT NULL AUTO_INCREMENT,
request_id INT NOT NULL,
status ENUM('Pending', 'Approved', 'Rejected', 'Expired', 'Completed', 'Cancelled') NOT NULL,
changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
PRIMARY KEY (history_id),
FOREIGN KEY (request_id) REFERENCES Request(request_id) ON DELETE CASCADE
);

DELIMITER //
CREATE TRIGGER request_status_history_insert
AFTER INSERT ON Request
FOR EACH ROW
BEGIN
  INSERT INTO Request_Status_History (request_id, status, changed_at)
  VALUES (NEW.request_id, NEW.status, NOW());
END//

CREATE TRIGGER request_status_history_update
AFTER UPDATE ON Request
FOR EACH ROW
BEGIN
  IF NEW.status <> OLD.status THEN
    INSERT INTO Request_Status_History (request_id, status, changed_at)
    VALUES (NEW.request_id, NEW.status, NOW());
  END IF;
END//
DELIMITER ;

-- Scheduled job to expire requests automatically (requires event scheduler enabled)
CREATE EVENT IF NOT EXISTS expire_requests
ON SCHEDULE EVERY 1 DAY
DO
  UPDATE Request
  SET status = 'Expired'
  WHERE expire_date IS NOT NULL
    AND expire_date <= NOW()
    AND status IN ('Pending', 'Approved');
