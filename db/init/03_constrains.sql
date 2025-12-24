ALTER TABLE User
  ADD CONSTRAINT chk_user_password_len
  CHECK (CHAR_LENGTH(user_password) >= 8);
