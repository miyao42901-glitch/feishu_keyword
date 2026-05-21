USE mysql;
UPDATE user SET plugin='mysql_native_password', authentication_string='' WHERE User='root';
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'lUgKNXSuJrtIcoO';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'lUgKNXSuJrtIcoO';
FLUSH PRIVILEGES;
