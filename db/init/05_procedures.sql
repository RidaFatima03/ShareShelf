DELIMITER //

DROP PROCEDURE IF EXISTS SearchBooks //

CREATE PROCEDURE SearchBooks(
    IN p_keyword        VARCHAR(255),
    IN p_title          VARCHAR(255),
    IN p_author         VARCHAR(255),
    IN p_isbn           VARCHAR(32),
    IN p_genre          VARCHAR(100),
    IN p_language       VARCHAR(50),
    IN p_availability   VARCHAR(20),
    IN p_acquisition    VARCHAR(20),
    IN p_min_avg_rating DECIMAL(3,2),
    IN p_limit          INT,
    IN p_offset         INT
)
BEGIN
    SELECT
        b.book_id,
        b.title,
        b.isbn,
        b.publisher,
        b.publication_date,
        b.language,
        b.average_rating,
        GROUP_CONCAT(DISTINCT g.genre_name SEPARATOR ', ') AS genres,
        GROUP_CONCAT(DISTINCT a.author_name SEPARATOR ', ') AS authors,
        
        COUNT(DISTINCT CASE WHEN c.acquisition_type != 'Exchange' THEN c.item_barcode END) AS total_library_copies,
        
        SUM(CASE WHEN c.status = 'Available' AND c.acquisition_type != 'Exchange' THEN 1 ELSE 0 END) AS available_copies
        
    FROM Book AS b
    JOIN Book_Author AS ba ON ba.book_id = b.book_id
    JOIN Author AS a ON a.author_id = ba.author_id
    LEFT JOIN Book_Genre AS bg ON bg.book_id = b.book_id
    LEFT JOIN Genre AS g ON g.genre_id = bg.genre_id
    LEFT JOIN Copy AS c ON c.book_id = b.book_id
    WHERE
        (p_keyword IS NULL OR (
            b.title LIKE CONCAT('%', p_keyword, '%') OR
            a.author_name LIKE CONCAT('%', p_keyword, '%') OR
            b.isbn LIKE CONCAT('%', p_keyword, '%')
        ))
        AND (p_title        IS NULL OR b.title       LIKE CONCAT('%', p_title, '%'))
        AND (p_author   IS NULL OR a.author_name LIKE CONCAT('%', p_author, '%'))
        AND (p_isbn     IS NULL OR b.isbn        = p_isbn)
        AND (p_genre    IS NULL OR g.genre_name  = p_genre)
        AND (p_language IS NULL OR b.language    = p_language)
        
        AND (p_availability IS NULL OR EXISTS (
            SELECT 1 FROM Copy c2
            WHERE c2.book_id = b.book_id
              AND c2.status = p_availability
              AND c2.acquisition_type != 'Exchange'
        ))
        
        AND (p_acquisition IS NULL OR EXISTS (
            SELECT 1 FROM Copy c3
            WHERE c3.book_id = b.book_id
              AND c3.acquisition_type = p_acquisition
              AND c3.acquisition_type != 'Exchange' 
        ))
        
        AND (p_min_avg_rating IS NULL OR b.average_rating >= p_min_avg_rating)
        
    GROUP BY 
        b.book_id, b.title, b.isbn, b.publisher, b.publication_date, b.language, b.average_rating
    
    HAVING total_library_copies > 0
    
    ORDER BY b.average_rating DESC, b.title ASC
    LIMIT p_limit OFFSET p_offset;
END //

DELIMITER ;