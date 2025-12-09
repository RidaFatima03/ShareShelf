DELIMITER //

DROP TRIGGER IF EXISTS after_review_insert //
CREATE TRIGGER after_review_insert
AFTER INSERT ON Review
FOR EACH ROW
BEGIN
    UPDATE Book
    SET average_rating = (
        SELECT COALESCE(AVG(rating), 0)
        FROM Review
        WHERE book_id = NEW.book_id
    )
    WHERE book_id = NEW.book_id;
END //

DROP TRIGGER IF EXISTS after_review_delete //
CREATE TRIGGER after_review_delete
AFTER DELETE ON Review
FOR EACH ROW
BEGIN
    UPDATE Book
    SET average_rating = (
        SELECT COALESCE(AVG(rating), 0)
        FROM Review
        WHERE book_id = OLD.book_id
    )
    WHERE book_id = OLD.book_id;
END //

DELIMITER ;