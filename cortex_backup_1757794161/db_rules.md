# Database Schema Change Rules

- All database schema changes MUST be done through Alembic migrations.
- Direct `ALTER TABLE` or other DDL commands are strictly prohibited on the production database.
