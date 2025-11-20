CREATE INDEX idx_book_title           ON Book(title);
CREATE INDEX idx_book_isbn            ON Book(isbn);
CREATE INDEX idx_book_language        ON Book(language);
CREATE INDEX idx_author_name          ON Author(author_name);
CREATE INDEX idx_genre_name           ON Genre(genre_name);
CREATE INDEX idx_copy_book_status     ON Copy(book_id, status);
CREATE INDEX idx_copy_book_acq        ON Copy(book_id, acquisition_type);
CREATE INDEX idx_review_book          ON Review(book_id);
CREATE INDEX idx_book_avg_rating 	  ON Book(average_rating);