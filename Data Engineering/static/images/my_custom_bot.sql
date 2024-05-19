CREATE DATABASE MY_CUSTOM_BOT;
commit;
USE MY_CUSTOM_BOT;
SELECT User FROM mysql.user;
DESCRIBE searchresults;

SET SQL_SAFE_UPDATES = 0;
DELETE FROM searchresults;
SET SQL_SAFE_UPDATES = 1;  -- Re-enable safe updates


commit;
select * from SearchTerms;

ALTER TABLE searchresults
ADD COLUMN SearchTerm VARCHAR(255);

















USE MY_CUSTOM_BOT;

-- Table used for the project
select * from searchresults order by Frequency DESC;