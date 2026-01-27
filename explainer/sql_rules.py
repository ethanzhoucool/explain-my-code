# Explanation templates for SQL
TEMPLATES = {
    # Basic Queries
    "select": {
        "eli5": "This picks which columns you want to see, like choosing which toys to play with.",
        "beginner": "SELECT retrieves specific columns from a table.",
        "developer": "SELECT clause specifying projection of columns in the result set.",
        "color": "#61afef"  # Blue
    },
    "select_all": {
        "eli5": "This gets everything from a table, like dumping out all your toys.",
        "beginner": "SELECT * retrieves all columns from a table.",
        "developer": "Wildcard projection selecting all columns (avoid in production for performance).",
        "color": "#61afef"  # Blue
    },
    "from": {
        "eli5": "This says which table to look in, like which toy box to open.",
        "beginner": "FROM specifies which table to query data from.",
        "developer": "FROM clause defining the source table(s) for the query.",
        "color": "#61afef"  # Blue
    },
    "where": {
        "eli5": "This filters to only get what you want, like finding only red toys.",
        "beginner": "WHERE filters rows based on a condition.",
        "developer": "WHERE clause for row-level filtering using predicates.",
        "color": "#c678dd"  # Purple
    },
    "and": {
        "eli5": "This means BOTH conditions must be true.",
        "beginner": "AND requires both conditions to be true.",
        "developer": "Logical AND operator for conjunctive predicates.",
        "color": "#c678dd"  # Purple
    },
    "or": {
        "eli5": "This means EITHER condition can be true.",
        "beginner": "OR requires at least one condition to be true.",
        "developer": "Logical OR operator for disjunctive predicates.",
        "color": "#c678dd"  # Purple
    },
    "not": {
        "eli5": "This means the opposite - if it was true, now it's false.",
        "beginner": "NOT reverses the condition.",
        "developer": "Logical NOT operator for negating predicates.",
        "color": "#c678dd"  # Purple
    },
    "in": {
        "eli5": "This checks if something is in a list of options.",
        "beginner": "IN checks if a value matches any value in a list.",
        "developer": "IN operator for set membership testing.",
        "color": "#c678dd"  # Purple
    },
    "between": {
        "eli5": "This checks if a number is within a range.",
        "beginner": "BETWEEN checks if a value is within a range (inclusive).",
        "developer": "BETWEEN operator for inclusive range predicates.",
        "color": "#c678dd"  # Purple
    },
    "like": {
        "eli5": "This finds things that match a pattern, like finding names starting with 'A'.",
        "beginner": "LIKE searches for a pattern using wildcards (% and _).",
        "developer": "LIKE operator for pattern matching with wildcards.",
        "color": "#c678dd"  # Purple
    },
    "is_null": {
        "eli5": "This checks if something is empty or missing.",
        "beginner": "IS NULL checks if a value is missing/empty.",
        "developer": "NULL predicate for testing undefined/missing values.",
        "color": "#c678dd"  # Purple
    },
    "is_not_null": {
        "eli5": "This checks if something has a value (not empty).",
        "beginner": "IS NOT NULL checks if a value exists.",
        "developer": "NOT NULL predicate for testing defined values.",
        "color": "#c678dd"  # Purple
    },
    
    # Sorting and Limiting
    "order_by": {
        "eli5": "This sorts the results, like arranging toys by size.",
        "beginner": "ORDER BY sorts the results by one or more columns.",
        "developer": "ORDER BY clause for result set sorting.",
        "color": "#e5c07b"  # Yellow
    },
    "asc": {
        "eli5": "This sorts from smallest to biggest (A to Z, 1 to 10).",
        "beginner": "ASC sorts in ascending order (default).",
        "developer": "Ascending sort order specification.",
        "color": "#e5c07b"  # Yellow
    },
    "desc": {
        "eli5": "This sorts from biggest to smallest (Z to A, 10 to 1).",
        "beginner": "DESC sorts in descending order.",
        "developer": "Descending sort order specification.",
        "color": "#e5c07b"  # Yellow
    },
    "limit": {
        "eli5": "This only shows a certain number of results.",
        "beginner": "LIMIT restricts the number of rows returned.",
        "developer": "LIMIT clause for result set size restriction (MySQL/PostgreSQL).",
        "color": "#e5c07b"  # Yellow
    },
    "top": {
        "eli5": "This only shows the first few results (SQL Server style).",
        "beginner": "TOP restricts the number of rows returned.",
        "developer": "TOP clause for result set size restriction (SQL Server/MS Access).",
        "color": "#e5c07b"  # Yellow
    },
    "offset": {
        "eli5": "This skips a number of results before showing the rest.",
        "beginner": "OFFSET skips a number of rows before returning results.",
        "developer": "OFFSET clause for pagination, skipping initial rows.",
        "color": "#e5c07b"  # Yellow
    },
    "fetch": {
        "eli5": "This gets a specific number of rows (used with OFFSET).",
        "beginner": "FETCH retrieves a specific number of rows.",
        "developer": "FETCH clause for row limiting (SQL standard with OFFSET).",
        "color": "#e5c07b"  # Yellow
    },
    
    # Grouping and Aggregates
    "group_by": {
        "eli5": "This puts similar things together, like sorting toys by color.",
        "beginner": "GROUP BY groups rows with the same values together.",
        "developer": "GROUP BY clause for aggregation grouping.",
        "color": "#56b6c2"  # Cyan
    },
    "having": {
        "eli5": "This filters groups after they're made (like WHERE but for groups).",
        "beginner": "HAVING filters groups based on aggregate conditions.",
        "developer": "HAVING clause for filtering grouped/aggregated results.",
        "color": "#56b6c2"  # Cyan
    },
    "count": {
        "eli5": "This counts how many things there are.",
        "beginner": "COUNT() counts the number of rows.",
        "developer": "COUNT aggregate function for row counting.",
        "color": "#56b6c2"  # Cyan
    },
    "sum": {
        "eli5": "This adds up all the numbers.",
        "beginner": "SUM() adds up all values in a column.",
        "developer": "SUM aggregate function for numeric summation.",
        "color": "#56b6c2"  # Cyan
    },
    "avg": {
        "eli5": "This finds the middle/average number.",
        "beginner": "AVG() calculates the average of values.",
        "developer": "AVG aggregate function for arithmetic mean.",
        "color": "#56b6c2"  # Cyan
    },
    "min": {
        "eli5": "This finds the smallest value.",
        "beginner": "MIN() finds the smallest value in a column.",
        "developer": "MIN aggregate function for minimum value.",
        "color": "#56b6c2"  # Cyan
    },
    "max": {
        "eli5": "This finds the biggest value.",
        "beginner": "MAX() finds the largest value in a column.",
        "developer": "MAX aggregate function for maximum value.",
        "color": "#56b6c2"  # Cyan
    },
    
    # Joins
    "join": {
        "eli5": "This combines two tables together based on matching values.",
        "beginner": "JOIN combines rows from two tables based on a related column.",
        "developer": "JOIN clause for combining tables via relational predicates.",
        "color": "#e06c75"  # Red
    },
    "inner_join": {
        "eli5": "This only keeps rows that match in BOTH tables.",
        "beginner": "INNER JOIN returns only matching rows from both tables.",
        "developer": "INNER JOIN returning intersection of matching rows.",
        "color": "#e06c75"  # Red
    },
    "left_join": {
        "eli5": "This keeps ALL rows from the left table, even without matches.",
        "beginner": "LEFT JOIN returns all rows from the left table, with matches from the right.",
        "developer": "LEFT OUTER JOIN preserving all left table rows.",
        "color": "#e06c75"  # Red
    },
    "right_join": {
        "eli5": "This keeps ALL rows from the right table, even without matches.",
        "beginner": "RIGHT JOIN returns all rows from the right table, with matches from the left.",
        "developer": "RIGHT OUTER JOIN preserving all right table rows.",
        "color": "#e06c75"  # Red
    },
    "full_join": {
        "eli5": "This keeps ALL rows from BOTH tables.",
        "beginner": "FULL JOIN returns all rows from both tables.",
        "developer": "FULL OUTER JOIN returning union of both tables.",
        "color": "#e06c75"  # Red
    },
    "cross_join": {
        "eli5": "This pairs every row with every other row (can be huge!).",
        "beginner": "CROSS JOIN returns all possible combinations of rows.",
        "developer": "CROSS JOIN producing Cartesian product of tables.",
        "color": "#e06c75"  # Red
    },
    "self_join": {
        "eli5": "This joins a table with itself.",
        "beginner": "A self-join joins a table with itself using aliases.",
        "developer": "Self-referential join for hierarchical or comparative queries.",
        "color": "#e06c75"  # Red
    },
    "on": {
        "eli5": "This says how to match rows between tables.",
        "beginner": "ON specifies the condition for joining tables.",
        "developer": "ON clause defining join predicate conditions.",
        "color": "#e06c75"  # Red
    },
    "using": {
        "eli5": "This joins on columns with the same name.",
        "beginner": "USING joins tables on columns with identical names.",
        "developer": "USING clause for natural join on named columns.",
        "color": "#e06c75"  # Red
    },
    
    # Subqueries
    "subquery": {
        "eli5": "This is a query inside another query.",
        "beginner": "A subquery is a query nested inside another query.",
        "developer": "Subquery (nested SELECT) for complex data retrieval.",
        "color": "#d19a66"  # Orange
    },
    "exists": {
        "eli5": "This checks if a subquery returns any results.",
        "beginner": "EXISTS returns true if the subquery returns any rows.",
        "developer": "EXISTS predicate for correlated subquery existence testing.",
        "color": "#d19a66"  # Orange
    },
    "any": {
        "eli5": "This compares to ANY value from a subquery.",
        "beginner": "ANY returns true if the comparison is true for any subquery value.",
        "developer": "ANY/SOME operator for subquery value comparison.",
        "color": "#d19a66"  # Orange
    },
    "all": {
        "eli5": "This compares to ALL values from a subquery.",
        "beginner": "ALL returns true if the comparison is true for all subquery values.",
        "developer": "ALL operator requiring condition true for entire subquery result.",
        "color": "#d19a66"  # Orange
    },
    
    # Set Operations
    "union": {
        "eli5": "This combines results from two queries (no duplicates).",
        "beginner": "UNION combines results from two queries, removing duplicates.",
        "developer": "UNION set operator for distinct row combination.",
        "color": "#98c379"  # Green
    },
    "union_all": {
        "eli5": "This combines results from two queries (keeps duplicates).",
        "beginner": "UNION ALL combines results keeping all rows including duplicates.",
        "developer": "UNION ALL for multiset combination without deduplication.",
        "color": "#98c379"  # Green
    },
    "intersect": {
        "eli5": "This only keeps rows that appear in BOTH queries.",
        "beginner": "INTERSECT returns only rows that appear in both queries.",
        "developer": "INTERSECT set operator for result set intersection.",
        "color": "#98c379"  # Green
    },
    "except": {
        "eli5": "This keeps rows from the first query that aren't in the second.",
        "beginner": "EXCEPT returns rows from the first query not in the second.",
        "developer": "EXCEPT/MINUS set operator for result set difference.",
        "color": "#98c379"  # Green
    },
    
    # Data Modification
    "insert": {
        "eli5": "This adds new rows to a table.",
        "beginner": "INSERT adds new rows of data to a table.",
        "developer": "INSERT statement for row creation.",
        "color": "#98c379"  # Green
    },
    "values": {
        "eli5": "This specifies the actual data to insert.",
        "beginner": "VALUES specifies the data for each new row.",
        "developer": "VALUES clause providing literal row data.",
        "color": "#98c379"  # Green
    },
    "update": {
        "eli5": "This changes existing data in a table.",
        "beginner": "UPDATE modifies existing rows in a table.",
        "developer": "UPDATE statement for row modification.",
        "color": "#e5c07b"  # Yellow
    },
    "set": {
        "eli5": "This says which columns to change and to what values.",
        "beginner": "SET specifies which columns to update and their new values.",
        "developer": "SET clause for column assignment in UPDATE.",
        "color": "#e5c07b"  # Yellow
    },
    "delete": {
        "eli5": "This removes rows from a table.",
        "beginner": "DELETE removes rows from a table.",
        "developer": "DELETE statement for row removal.",
        "color": "#e06c75"  # Red
    },
    "truncate": {
        "eli5": "This removes ALL rows from a table very quickly.",
        "beginner": "TRUNCATE removes all rows from a table (faster than DELETE).",
        "developer": "TRUNCATE DDL for fast table emptying without logging individual rows.",
        "color": "#e06c75"  # Red
    },
    "merge": {
        "eli5": "This updates if a row exists, inserts if it doesn't.",
        "beginner": "MERGE performs insert, update, or delete in one statement.",
        "developer": "MERGE (UPSERT) statement for conditional DML operations.",
        "color": "#e5c07b"  # Yellow
    },
    
    # Table Definition
    "create_table": {
        "eli5": "This makes a new table to store data.",
        "beginner": "CREATE TABLE creates a new table with specified columns.",
        "developer": "CREATE TABLE DDL for table schema definition.",
        "color": "#61afef"  # Blue
    },
    "alter_table": {
        "eli5": "This changes an existing table's structure.",
        "beginner": "ALTER TABLE modifies an existing table's structure.",
        "developer": "ALTER TABLE DDL for schema modification.",
        "color": "#61afef"  # Blue
    },
    "drop_table": {
        "eli5": "This permanently deletes a table and all its data.",
        "beginner": "DROP TABLE permanently removes a table.",
        "developer": "DROP TABLE DDL for table removal.",
        "color": "#e06c75"  # Red
    },
    "add_column": {
        "eli5": "This adds a new column to a table.",
        "beginner": "ADD adds a new column to an existing table.",
        "developer": "ADD clause for column addition in ALTER TABLE.",
        "color": "#61afef"  # Blue
    },
    "drop_column": {
        "eli5": "This removes a column from a table.",
        "beginner": "DROP COLUMN removes a column from a table.",
        "developer": "DROP COLUMN clause for column removal.",
        "color": "#e06c75"  # Red
    },
    "modify_column": {
        "eli5": "This changes a column's properties.",
        "beginner": "MODIFY/ALTER COLUMN changes a column's data type or constraints.",
        "developer": "MODIFY/ALTER COLUMN for column definition changes.",
        "color": "#e5c07b"  # Yellow
    },
    "rename": {
        "eli5": "This gives a table or column a new name.",
        "beginner": "RENAME changes the name of a table or column.",
        "developer": "RENAME clause for object renaming.",
        "color": "#e5c07b"  # Yellow
    },
    
    # Data Types
    "int_type": {
        "eli5": "This stores whole numbers like 1, 2, 3.",
        "beginner": "INT stores whole numbers (integers).",
        "developer": "INTEGER data type for whole number storage.",
        "color": "#d19a66"  # Orange
    },
    "varchar": {
        "eli5": "This stores text that can vary in length.",
        "beginner": "VARCHAR stores variable-length text.",
        "developer": "VARCHAR for variable-length character strings.",
        "color": "#d19a66"  # Orange
    },
    "char_type": {
        "eli5": "This stores text with a fixed length.",
        "beginner": "CHAR stores fixed-length text.",
        "developer": "CHAR for fixed-length character strings.",
        "color": "#d19a66"  # Orange
    },
    "text_type": {
        "eli5": "This stores very long text.",
        "beginner": "TEXT stores large amounts of text.",
        "developer": "TEXT data type for large character data.",
        "color": "#d19a66"  # Orange
    },
    "decimal_type": {
        "eli5": "This stores exact decimal numbers (good for money).",
        "beginner": "DECIMAL stores exact decimal numbers.",
        "developer": "DECIMAL/NUMERIC for exact fixed-point arithmetic.",
        "color": "#d19a66"  # Orange
    },
    "float_type": {
        "eli5": "This stores decimal numbers (approximate).",
        "beginner": "FLOAT stores approximate decimal numbers.",
        "developer": "FLOAT/REAL for approximate floating-point numbers.",
        "color": "#d19a66"  # Orange
    },
    "date_type": {
        "eli5": "This stores a date like 2024-01-15.",
        "beginner": "DATE stores a date (year, month, day).",
        "developer": "DATE data type for calendar dates.",
        "color": "#d19a66"  # Orange
    },
    "datetime_type": {
        "eli5": "This stores both a date and time.",
        "beginner": "DATETIME stores both date and time.",
        "developer": "DATETIME/TIMESTAMP for date-time values.",
        "color": "#d19a66"  # Orange
    },
    "boolean_type": {
        "eli5": "This stores true or false.",
        "beginner": "BOOLEAN stores true or false values.",
        "developer": "BOOLEAN/BIT for logical true/false storage.",
        "color": "#d19a66"  # Orange
    },
    "blob_type": {
        "eli5": "This stores binary data like images.",
        "beginner": "BLOB stores binary data (images, files).",
        "developer": "BLOB for binary large object storage.",
        "color": "#d19a66"  # Orange
    },
    
    # Constraints
    "primary_key": {
        "eli5": "This uniquely identifies each row, like a student ID.",
        "beginner": "PRIMARY KEY uniquely identifies each row in a table.",
        "developer": "PRIMARY KEY constraint for unique row identification.",
        "color": "#c678dd"  # Purple
    },
    "foreign_key": {
        "eli5": "This links to a primary key in another table.",
        "beginner": "FOREIGN KEY creates a link between two tables.",
        "developer": "FOREIGN KEY constraint for referential integrity.",
        "color": "#c678dd"  # Purple
    },
    "references": {
        "eli5": "This says which table and column a foreign key points to.",
        "beginner": "REFERENCES specifies the table a foreign key links to.",
        "developer": "REFERENCES clause defining foreign key target.",
        "color": "#c678dd"  # Purple
    },
    "unique": {
        "eli5": "This makes sure no duplicate values are allowed.",
        "beginner": "UNIQUE ensures all values in a column are different.",
        "developer": "UNIQUE constraint preventing duplicate values.",
        "color": "#c678dd"  # Purple
    },
    "not_null": {
        "eli5": "This means the column must have a value (can't be empty).",
        "beginner": "NOT NULL requires the column to always have a value.",
        "developer": "NOT NULL constraint preventing null values.",
        "color": "#c678dd"  # Purple
    },
    "default": {
        "eli5": "This sets a value if none is provided.",
        "beginner": "DEFAULT sets a value when none is specified.",
        "developer": "DEFAULT constraint for automatic value assignment.",
        "color": "#c678dd"  # Purple
    },
    "check": {
        "eli5": "This makes sure values follow a rule.",
        "beginner": "CHECK ensures values meet a specific condition.",
        "developer": "CHECK constraint for domain validation.",
        "color": "#c678dd"  # Purple
    },
    "auto_increment": {
        "eli5": "This automatically gives each new row the next number.",
        "beginner": "AUTO_INCREMENT automatically generates unique numbers.",
        "developer": "AUTO_INCREMENT/IDENTITY for automatic sequential values.",
        "color": "#c678dd"  # Purple
    },
    "constraint": {
        "eli5": "This is a rule that data must follow.",
        "beginner": "CONSTRAINT defines a rule for data in the table.",
        "developer": "Named constraint definition for table rules.",
        "color": "#c678dd"  # Purple
    },
    "cascade": {
        "eli5": "This automatically updates or deletes related rows.",
        "beginner": "CASCADE automatically updates/deletes related rows.",
        "developer": "CASCADE referential action for automatic propagation.",
        "color": "#c678dd"  # Purple
    },
    
    # Indexes
    "create_index": {
        "eli5": "This makes searching faster, like an index in a book.",
        "beginner": "CREATE INDEX creates an index to speed up queries.",
        "developer": "CREATE INDEX for query performance optimization.",
        "color": "#56b6c2"  # Cyan
    },
    "drop_index": {
        "eli5": "This removes an index.",
        "beginner": "DROP INDEX removes an existing index.",
        "developer": "DROP INDEX for index removal.",
        "color": "#e06c75"  # Red
    },
    "unique_index": {
        "eli5": "This creates an index that also prevents duplicates.",
        "beginner": "UNIQUE INDEX speeds up queries and prevents duplicates.",
        "developer": "UNIQUE INDEX combining performance and uniqueness constraint.",
        "color": "#56b6c2"  # Cyan
    },
    
    # Views
    "create_view": {
        "eli5": "This saves a query so you can use it like a table.",
        "beginner": "CREATE VIEW creates a virtual table from a query.",
        "developer": "CREATE VIEW for virtual table definition.",
        "color": "#61afef"  # Blue
    },
    "drop_view": {
        "eli5": "This removes a saved view.",
        "beginner": "DROP VIEW removes an existing view.",
        "developer": "DROP VIEW for view removal.",
        "color": "#e06c75"  # Red
    },
    "with_clause": {
        "eli5": "This creates a temporary named result you can use in your query.",
        "beginner": "WITH creates a temporary named result set (CTE).",
        "developer": "WITH clause for Common Table Expression (CTE) definition.",
        "color": "#61afef"  # Blue
    },
    
    # Transactions
    "begin_transaction": {
        "eli5": "This starts a group of changes that should happen together.",
        "beginner": "BEGIN TRANSACTION starts a group of operations.",
        "developer": "BEGIN TRANSACTION for explicit transaction demarcation.",
        "color": "#e5c07b"  # Yellow
    },
    "commit": {
        "eli5": "This saves all the changes you made.",
        "beginner": "COMMIT saves all changes made in the transaction.",
        "developer": "COMMIT for transaction persistence.",
        "color": "#98c379"  # Green
    },
    "rollback": {
        "eli5": "This undoes all the changes since the last save point.",
        "beginner": "ROLLBACK undoes all changes in the transaction.",
        "developer": "ROLLBACK for transaction reversal.",
        "color": "#e06c75"  # Red
    },
    "savepoint": {
        "eli5": "This creates a checkpoint you can roll back to.",
        "beginner": "SAVEPOINT creates a point you can rollback to.",
        "developer": "SAVEPOINT for partial transaction rollback points.",
        "color": "#e5c07b"  # Yellow
    },
    
    # Functions
    "coalesce": {
        "eli5": "This returns the first non-empty value.",
        "beginner": "COALESCE returns the first non-null value in a list.",
        "developer": "COALESCE function for null-safe value selection.",
        "color": "#56b6c2"  # Cyan
    },
    "nullif": {
        "eli5": "This returns null if two values are equal.",
        "beginner": "NULLIF returns null if two values are equal.",
        "developer": "NULLIF function for conditional null generation.",
        "color": "#56b6c2"  # Cyan
    },
    "case_when": {
        "eli5": "This checks conditions and returns different values.",
        "beginner": "CASE WHEN provides if-then-else logic in queries.",
        "developer": "CASE expression for conditional value selection.",
        "color": "#c678dd"  # Purple
    },
    "cast": {
        "eli5": "This converts a value to a different type.",
        "beginner": "CAST converts a value to a different data type.",
        "developer": "CAST for explicit type conversion.",
        "color": "#56b6c2"  # Cyan
    },
    "convert": {
        "eli5": "This converts a value to a different type (SQL Server style).",
        "beginner": "CONVERT changes a value to a different data type.",
        "developer": "CONVERT function for type conversion (SQL Server).",
        "color": "#56b6c2"  # Cyan
    },
    "concat": {
        "eli5": "This joins text together.",
        "beginner": "CONCAT joins strings together.",
        "developer": "CONCAT function for string concatenation.",
        "color": "#56b6c2"  # Cyan
    },
    "substring": {
        "eli5": "This gets part of a text string.",
        "beginner": "SUBSTRING extracts part of a string.",
        "developer": "SUBSTRING/SUBSTR for string extraction.",
        "color": "#56b6c2"  # Cyan
    },
    "length": {
        "eli5": "This counts how many characters are in text.",
        "beginner": "LENGTH returns the number of characters in a string.",
        "developer": "LENGTH/LEN function for string length.",
        "color": "#56b6c2"  # Cyan
    },
    "upper": {
        "eli5": "This makes text ALL UPPERCASE.",
        "beginner": "UPPER converts text to uppercase.",
        "developer": "UPPER function for uppercase conversion.",
        "color": "#56b6c2"  # Cyan
    },
    "lower": {
        "eli5": "This makes text all lowercase.",
        "beginner": "LOWER converts text to lowercase.",
        "developer": "LOWER function for lowercase conversion.",
        "color": "#56b6c2"  # Cyan
    },
    "trim": {
        "eli5": "This removes extra spaces from the beginning and end.",
        "beginner": "TRIM removes leading and trailing spaces.",
        "developer": "TRIM function for whitespace removal.",
        "color": "#56b6c2"  # Cyan
    },
    "replace": {
        "eli5": "This swaps one text for another.",
        "beginner": "REPLACE substitutes text within a string.",
        "developer": "REPLACE function for string substitution.",
        "color": "#56b6c2"  # Cyan
    },
    "round": {
        "eli5": "This rounds a number to fewer decimal places.",
        "beginner": "ROUND rounds a number to specified decimal places.",
        "developer": "ROUND function for numeric rounding.",
        "color": "#56b6c2"  # Cyan
    },
    "abs": {
        "eli5": "This makes negative numbers positive.",
        "beginner": "ABS returns the absolute value of a number.",
        "developer": "ABS function for absolute value.",
        "color": "#56b6c2"  # Cyan
    },
    "now": {
        "eli5": "This gets the current date and time.",
        "beginner": "NOW() returns the current date and time.",
        "developer": "NOW/GETDATE/CURRENT_TIMESTAMP for current datetime.",
        "color": "#56b6c2"  # Cyan
    },
    "datepart": {
        "eli5": "This extracts part of a date (like the year or month).",
        "beginner": "DATEPART extracts a part of a date (year, month, day).",
        "developer": "DATEPART/EXTRACT for date component extraction.",
        "color": "#56b6c2"  # Cyan
    },
    "datediff": {
        "eli5": "This calculates the difference between two dates.",
        "beginner": "DATEDIFF calculates the difference between two dates.",
        "developer": "DATEDIFF for date interval calculation.",
        "color": "#56b6c2"  # Cyan
    },
    "dateadd": {
        "eli5": "This adds time to a date.",
        "beginner": "DATEADD adds a time interval to a date.",
        "developer": "DATEADD for date arithmetic.",
        "color": "#56b6c2"  # Cyan
    },
    "isnull_func": {
        "eli5": "This replaces null with a default value.",
        "beginner": "ISNULL replaces null values with a specified value.",
        "developer": "ISNULL/IFNULL/NVL for null replacement.",
        "color": "#56b6c2"  # Cyan
    },
    
    # Window Functions
    "over": {
        "eli5": "This defines a window of rows for calculations.",
        "beginner": "OVER defines the window for window functions.",
        "developer": "OVER clause for window function specification.",
        "color": "#61afef"  # Blue
    },
    "partition_by": {
        "eli5": "This divides rows into groups for window calculations.",
        "beginner": "PARTITION BY divides rows into groups for window functions.",
        "developer": "PARTITION BY for window partitioning.",
        "color": "#61afef"  # Blue
    },
    "row_number": {
        "eli5": "This gives each row a unique number.",
        "beginner": "ROW_NUMBER assigns a unique number to each row.",
        "developer": "ROW_NUMBER() window function for sequential numbering.",
        "color": "#61afef"  # Blue
    },
    "rank": {
        "eli5": "This ranks rows with gaps for ties.",
        "beginner": "RANK assigns a rank with gaps for ties.",
        "developer": "RANK() window function with gap ranking.",
        "color": "#61afef"  # Blue
    },
    "dense_rank": {
        "eli5": "This ranks rows without gaps for ties.",
        "beginner": "DENSE_RANK assigns a rank without gaps for ties.",
        "developer": "DENSE_RANK() window function with continuous ranking.",
        "color": "#61afef"  # Blue
    },
    "lead": {
        "eli5": "This looks at the next row's value.",
        "beginner": "LEAD accesses a value from a following row.",
        "developer": "LEAD() window function for forward row access.",
        "color": "#61afef"  # Blue
    },
    "lag": {
        "eli5": "This looks at the previous row's value.",
        "beginner": "LAG accesses a value from a preceding row.",
        "developer": "LAG() window function for backward row access.",
        "color": "#61afef"  # Blue
    },
    "first_value": {
        "eli5": "This gets the first value in the window.",
        "beginner": "FIRST_VALUE returns the first value in the window.",
        "developer": "FIRST_VALUE() window function for initial value.",
        "color": "#61afef"  # Blue
    },
    "last_value": {
        "eli5": "This gets the last value in the window.",
        "beginner": "LAST_VALUE returns the last value in the window.",
        "developer": "LAST_VALUE() window function for terminal value.",
        "color": "#61afef"  # Blue
    },
    "ntile": {
        "eli5": "This divides rows into a specified number of groups.",
        "beginner": "NTILE divides rows into a specified number of buckets.",
        "developer": "NTILE() window function for bucket distribution.",
        "color": "#61afef"  # Blue
    },
    
    # Aliases
    "as_alias": {
        "eli5": "This gives something a nickname.",
        "beginner": "AS gives a column or table a temporary name (alias).",
        "developer": "AS keyword for column/table aliasing.",
        "color": "#98c379"  # Green
    },
    
    # Distinct
    "distinct": {
        "eli5": "This removes duplicate rows from results.",
        "beginner": "DISTINCT removes duplicate rows from results.",
        "developer": "DISTINCT keyword for duplicate elimination.",
        "color": "#c678dd"  # Purple
    },
    
    # Comments
    "comment": {
        "eli5": "This is a note that the database ignores.",
        "beginner": "A comment explains the code but doesn't run.",
        "developer": "SQL comment for documentation.",
        "color": "#5c6370"  # Gray
    },
    
    # Stored Procedures & Functions
    "create_procedure": {
        "eli5": "This creates a saved set of SQL commands.",
        "beginner": "CREATE PROCEDURE creates a reusable stored procedure.",
        "developer": "CREATE PROCEDURE for stored procedure definition.",
        "color": "#61afef"  # Blue
    },
    "create_function": {
        "eli5": "This creates a custom function you can use in queries.",
        "beginner": "CREATE FUNCTION creates a reusable function.",
        "developer": "CREATE FUNCTION for user-defined function definition.",
        "color": "#61afef"  # Blue
    },
    "execute": {
        "eli5": "This runs a stored procedure.",
        "beginner": "EXECUTE/EXEC runs a stored procedure.",
        "developer": "EXECUTE for stored procedure invocation.",
        "color": "#98c379"  # Green
    },
    "declare": {
        "eli5": "This creates a variable to store a value.",
        "beginner": "DECLARE creates a variable.",
        "developer": "DECLARE for variable declaration.",
        "color": "#d19a66"  # Orange
    },
    "set_var": {
        "eli5": "This gives a variable a value.",
        "beginner": "SET assigns a value to a variable.",
        "developer": "SET for variable assignment.",
        "color": "#d19a66"  # Orange
    },
    "if_statement": {
        "eli5": "This runs code only if a condition is true.",
        "beginner": "IF runs code conditionally.",
        "developer": "IF statement for conditional execution in procedures.",
        "color": "#c678dd"  # Purple
    },
    "while_loop": {
        "eli5": "This repeats code while a condition is true.",
        "beginner": "WHILE loops until a condition becomes false.",
        "developer": "WHILE loop for iterative execution in procedures.",
        "color": "#e06c75"  # Red
    },
    "return": {
        "eli5": "This exits and optionally returns a value.",
        "beginner": "RETURN exits and optionally returns a value.",
        "developer": "RETURN for procedure/function exit with optional value.",
        "color": "#c678dd"  # Purple
    },
    
    # Permissions
    "grant": {
        "eli5": "This gives someone permission to do something.",
        "beginner": "GRANT gives users permission to access objects.",
        "developer": "GRANT for privilege assignment.",
        "color": "#98c379"  # Green
    },
    "revoke": {
        "eli5": "This takes away someone's permission.",
        "beginner": "REVOKE removes user permissions.",
        "developer": "REVOKE for privilege removal.",
        "color": "#e06c75"  # Red
    },
}


def detect_features_in_line(line):
    """
    Detect SQL features in a single line of code.
    """
    features = []
    line_upper = line.upper()
    line_lower = line.lower()
    
    patterns = [
        # Basic Queries
        ('SELECT *', 'select_all'),
        ('SELECT ', 'select'),
        (' FROM ', 'from'),
        ('FROM ', 'from'),
        (' WHERE ', 'where'),
        ('WHERE ', 'where'),
        (' AND ', 'and'),
        (' OR ', 'or'),
        (' NOT ', 'not'),
        (' IN ', 'in'),
        (' IN(', 'in'),
        (' BETWEEN ', 'between'),
        (' LIKE ', 'like'),
        (' IS NULL', 'is_null'),
        (' IS NOT NULL', 'is_not_null'),
        
        # Sorting and Limiting
        ('ORDER BY ', 'order_by'),
        (' ASC', 'asc'),
        (' DESC', 'desc'),
        (' LIMIT ', 'limit'),
        ('LIMIT ', 'limit'),
        ('TOP ', 'top'),
        (' OFFSET ', 'offset'),
        ('OFFSET ', 'offset'),
        ('FETCH ', 'fetch'),
        
        # Grouping and Aggregates
        ('GROUP BY ', 'group_by'),
        (' HAVING ', 'having'),
        ('HAVING ', 'having'),
        ('COUNT(', 'count'),
        ('COUNT (', 'count'),
        ('SUM(', 'sum'),
        ('SUM (', 'sum'),
        ('AVG(', 'avg'),
        ('AVG (', 'avg'),
        ('MIN(', 'min'),
        ('MIN (', 'min'),
        ('MAX(', 'max'),
        ('MAX (', 'max'),
        
        # Joins
        ('INNER JOIN ', 'inner_join'),
        ('LEFT JOIN ', 'left_join'),
        ('LEFT OUTER JOIN ', 'left_join'),
        ('RIGHT JOIN ', 'right_join'),
        ('RIGHT OUTER JOIN ', 'right_join'),
        ('FULL JOIN ', 'full_join'),
        ('FULL OUTER JOIN ', 'full_join'),
        ('CROSS JOIN ', 'cross_join'),
        (' JOIN ', 'join'),
        ('JOIN ', 'join'),
        (' ON ', 'on'),
        (' USING ', 'using'),
        (' USING(', 'using'),
        
        # Set Operations
        ('UNION ALL', 'union_all'),
        (' UNION ', 'union'),
        ('UNION ', 'union'),
        ('INTERSECT ', 'intersect'),
        (' INTERSECT', 'intersect'),
        ('EXCEPT ', 'except'),
        (' EXCEPT', 'except'),
        ('MINUS ', 'except'),
        
        # Subqueries
        (' EXISTS ', 'exists'),
        (' EXISTS(', 'exists'),
        ('EXISTS(', 'exists'),
        (' ANY ', 'any'),
        (' ANY(', 'any'),
        (' ALL ', 'all'),
        (' ALL(', 'all'),
        
        # Data Modification
        ('INSERT INTO ', 'insert'),
        ('INSERT ', 'insert'),
        (' VALUES ', 'values'),
        ('VALUES ', 'values'),
        ('VALUES(', 'values'),
        ('UPDATE ', 'update'),
        (' SET ', 'set'),
        ('DELETE FROM ', 'delete'),
        ('DELETE ', 'delete'),
        ('TRUNCATE ', 'truncate'),
        ('MERGE ', 'merge'),
        
        # Table Definition
        ('CREATE TABLE ', 'create_table'),
        ('ALTER TABLE ', 'alter_table'),
        ('DROP TABLE ', 'drop_table'),
        (' ADD COLUMN ', 'add_column'),
        (' ADD ', 'add_column'),
        ('DROP COLUMN ', 'drop_column'),
        ('MODIFY COLUMN ', 'modify_column'),
        ('ALTER COLUMN ', 'modify_column'),
        ('RENAME ', 'rename'),
        
        # Data Types
        ('INT ', 'int_type'),
        ('INT,', 'int_type'),
        ('INT)', 'int_type'),
        ('INTEGER ', 'int_type'),
        ('INTEGER,', 'int_type'),
        ('VARCHAR', 'varchar'),
        ('CHAR(', 'char_type'),
        ('TEXT ', 'text_type'),
        ('TEXT,', 'text_type'),
        ('TEXT)', 'text_type'),
        ('DECIMAL', 'decimal_type'),
        ('NUMERIC', 'decimal_type'),
        ('FLOAT', 'float_type'),
        ('REAL', 'float_type'),
        ('DOUBLE', 'float_type'),
        (' DATE ', 'date_type'),
        (' DATE,', 'date_type'),
        (' DATE)', 'date_type'),
        ('DATETIME', 'datetime_type'),
        ('TIMESTAMP', 'datetime_type'),
        ('BOOLEAN', 'boolean_type'),
        (' BIT ', 'boolean_type'),
        ('BLOB', 'blob_type'),
        
        # Constraints
        ('PRIMARY KEY', 'primary_key'),
        ('FOREIGN KEY', 'foreign_key'),
        ('REFERENCES ', 'references'),
        (' UNIQUE', 'unique'),
        ('NOT NULL', 'not_null'),
        (' DEFAULT ', 'default'),
        ('DEFAULT ', 'default'),
        (' CHECK ', 'check'),
        (' CHECK(', 'check'),
        ('AUTO_INCREMENT', 'auto_increment'),
        ('IDENTITY', 'auto_increment'),
        ('SERIAL', 'auto_increment'),
        ('CONSTRAINT ', 'constraint'),
        (' CASCADE', 'cascade'),
        
        # Indexes
        ('CREATE INDEX ', 'create_index'),
        ('CREATE UNIQUE INDEX ', 'unique_index'),
        ('DROP INDEX ', 'drop_index'),
        
        # Views
        ('CREATE VIEW ', 'create_view'),
        ('CREATE OR REPLACE VIEW ', 'create_view'),
        ('DROP VIEW ', 'drop_view'),
        ('WITH ', 'with_clause'),
        
        # Transactions
        ('BEGIN TRANSACTION', 'begin_transaction'),
        ('BEGIN TRAN', 'begin_transaction'),
        ('START TRANSACTION', 'begin_transaction'),
        ('BEGIN;', 'begin_transaction'),
        ('COMMIT', 'commit'),
        ('ROLLBACK', 'rollback'),
        ('SAVEPOINT ', 'savepoint'),
        
        # Functions
        ('COALESCE(', 'coalesce'),
        ('NULLIF(', 'nullif'),
        ('CASE ', 'case_when'),
        (' WHEN ', 'case_when'),
        (' THEN ', 'case_when'),
        (' ELSE ', 'case_when'),
        (' END', 'case_when'),
        ('CAST(', 'cast'),
        ('CONVERT(', 'convert'),
        ('CONCAT(', 'concat'),
        ('SUBSTRING(', 'substring'),
        ('SUBSTR(', 'substring'),
        ('LENGTH(', 'length'),
        ('LEN(', 'length'),
        ('UPPER(', 'upper'),
        ('LOWER(', 'lower'),
        ('TRIM(', 'trim'),
        ('LTRIM(', 'trim'),
        ('RTRIM(', 'trim'),
        ('REPLACE(', 'replace'),
        ('ROUND(', 'round'),
        ('ABS(', 'abs'),
        ('NOW(', 'now'),
        ('GETDATE(', 'now'),
        ('CURRENT_TIMESTAMP', 'now'),
        ('DATEPART(', 'datepart'),
        ('EXTRACT(', 'datepart'),
        ('YEAR(', 'datepart'),
        ('MONTH(', 'datepart'),
        ('DAY(', 'datepart'),
        ('DATEDIFF(', 'datediff'),
        ('DATEADD(', 'dateadd'),
        ('ISNULL(', 'isnull_func'),
        ('IFNULL(', 'isnull_func'),
        ('NVL(', 'isnull_func'),
        
        # Window Functions
        (' OVER ', 'over'),
        (' OVER(', 'over'),
        ('PARTITION BY ', 'partition_by'),
        ('ROW_NUMBER(', 'row_number'),
        ('RANK(', 'rank'),
        ('DENSE_RANK(', 'dense_rank'),
        ('LEAD(', 'lead'),
        ('LAG(', 'lag'),
        ('FIRST_VALUE(', 'first_value'),
        ('LAST_VALUE(', 'last_value'),
        ('NTILE(', 'ntile'),
        
        # Aliases
        (' AS ', 'as_alias'),
        
        # Distinct
        ('DISTINCT ', 'distinct'),
        ('SELECT DISTINCT', 'distinct'),
        
        # Stored Procedures
        ('CREATE PROCEDURE ', 'create_procedure'),
        ('CREATE PROC ', 'create_procedure'),
        ('CREATE FUNCTION ', 'create_function'),
        ('EXECUTE ', 'execute'),
        ('EXEC ', 'execute'),
        ('DECLARE ', 'declare'),
        ('DECLARE @', 'declare'),
        ('@', 'set_var'),
        (' IF ', 'if_statement'),
        ('IF ', 'if_statement'),
        (' WHILE ', 'while_loop'),
        ('WHILE ', 'while_loop'),
        ('RETURN ', 'return'),
        ('RETURN;', 'return'),
        
        # Permissions
        ('GRANT ', 'grant'),
        ('REVOKE ', 'revoke'),
        
        # Comments
        ('--', 'comment'),
        ('/*', 'comment'),
    ]
    
    # Find all pattern matches
    for pattern, feature_type in patterns:
        start = 0
        while True:
            pos = line_upper.find(pattern, start)
            if pos == -1:
                break
            
            keyword = line[pos:pos + len(pattern)]
            features.append({
                'keyword': keyword.strip(),
                'start': pos,
                'end': pos + len(pattern),
                'type': feature_type
            })
            start = pos + 1
    
    # Sort by position and remove duplicates at same position
    features.sort(key=lambda x: (x['start'], -len(x['keyword'])))
    
    # Remove overlapping matches (keep longest)
    filtered = []
    last_end = -1
    for f in features:
        if f['start'] >= last_end:
            filtered.append(f)
            last_end = f['end']
    
    return filtered


def build_highlighted_line(line, level):
    """
    Builds HTML with highlighted keywords and tooltips.
    """
    # Skip lines that are comments
    stripped = line.strip()
    if stripped.startswith('--') or stripped.startswith('/*') or stripped.startswith('*'):
        return line, False
    
    features = detect_features_in_line(line)
    
    if not features:
        return line, False
    
    result = []
    last_pos = 0
    
    for feature in features:
        if feature['start'] < last_pos:
            continue
            
        # Add text before the keyword
        result.append(line[last_pos:feature['start']])
        
        # Add highlighted keyword with tooltip
        keyword = feature['keyword']
        feature_type = feature['type']
        explanation = TEMPLATES.get(feature_type, {}).get(level, '')
        color = TEMPLATES.get(feature_type, {}).get('color', '#666')
        
        if explanation:
            result.append(
                f'<span class="highlight" style="background-color: {color}; color: white;" '
                f'data-tooltip="{explanation}">{keyword}</span>'
            )
        else:
            result.append(keyword)
        
        last_pos = feature['end']
    
    result.append(line[last_pos:])
    
    return ''.join(result), True


def generate_annotated_code(code, level):
    """
    Generates code with line-by-line highlighting.
    """
    lines = code.split('\n')
    annotated = []
    
    for i, line in enumerate(lines, 1):
        highlighted_line, has_highlights = build_highlighted_line(line, level)
        annotated.append({
            'number': i,
            'code': line,
            'highlighted': highlighted_line,
            'has_highlights': has_highlights
        })
    
    return annotated
