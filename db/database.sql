CREATE TABLE IF NOT EXISTS "issues"(
  "issue_id" integer NOT NULL PRIMARY KEY,
  "issue_number" integer NOT NULL,
  "repo" varchar(256) NOT NULL,
  "owner" varchar(256) NOT NULL,
  "title" varchar(256) NOT NULL,
  "author" varchar(256) NOT NULL,
  "body" text,
  "status" varchar(16),
  "created_at" timestamp,
  "updated_at" timestamp,
  "deleted_at" timestamp
);

CREATE TABLE IF NOT EXISTS "assigned"(
  "id" SERIAL PRIMARY KEY,
  "issue_id" integer NOT NULL,
  "user" varchar(256) NOT NULL,
  "created_at" timestamp,
  "deleted_at" timestamp,
  CONSTRAINT fk_issue FOREIGN KEY(issue_id) REFERENCES issues(issue_id)
);