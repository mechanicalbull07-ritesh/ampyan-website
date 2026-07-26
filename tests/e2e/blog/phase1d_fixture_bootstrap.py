"""Atomic, disposable-only Phase 1D PostgreSQL fixture bootstrap."""
import argparse
import json
import os
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import Json


REQUIRED_SLUGS = {
    "phase1d-published", "phase1d-draft", "phase1d-pending",
    "phase1d-rejected", "phase1d-rich",
}


def guarded_url():
    value = os.environ.get("PHASE1D_FIXTURE_DATABASE_URL", "")
    parsed = urlparse(value)
    if (
        parsed.hostname not in {"127.0.0.1", "localhost"}
        or not (parsed.path or "").lstrip("/").startswith("ampyan_blog_phase1d")
        or os.environ.get("ENV", "").lower() == "production"
        or os.environ.get("RENDER", "").lower() == "true"
    ):
        raise RuntimeError("Phase 1D fixtures require an explicit disposable localhost database.")
    return value


def insert_blog(cursor, fixture, *, category_id=None):
    cursor.execute(
        """
        INSERT INTO blogs(
          slug,author_id,title,subtitle,excerpt,status,category_id,
          reading_time_minutes,published_at,submitted_at,version
        ) VALUES(
          %(slug)s,%(author_id)s,%(title)s,%(subtitle)s,%(excerpt)s,%(status)s,
          %(category_id)s,%(reading_time)s,
          CASE WHEN %(status)s='published' THEN CURRENT_TIMESTAMP END,
          CASE WHEN %(status)s='pending_review' THEN CURRENT_TIMESTAMP END,1
        ) RETURNING id
        """,
        {
            **fixture,
            "category_id": category_id,
            "subtitle": fixture.get("subtitle"),
            "excerpt": fixture.get("excerpt", fixture["title"]),
            "reading_time": fixture.get("reading_time", 1),
        },
    )
    return cursor.fetchone()[0]


def bootstrap(force_error=False):
    database_url = guarded_url()
    fixture_ids = {}
    with psycopg2.connect(database_url) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE "user" SET name='Author One',username='author1',
                       email='author1@test.invalid' WHERE id=1"""
                )
                cursor.execute(
                    """UPDATE "user" SET name='Reader Two',username='reader2',
                       email='reader2@test.invalid' WHERE id=2"""
                )
                for user_id, username in (
                    (3, "moderator"), (4, "admin"), (5, "blocked"), (6, "banned")
                ):
                    cursor.execute(
                        'UPDATE "user" SET username=%s WHERE id=%s',
                        (username, user_id),
                    )
                cursor.execute(
                    """INSERT INTO "user"(name,username,email,password,phone,role)
                       VALUES('Empty Author','author2','author2@test.invalid',
                              'hash','','user') RETURNING id"""
                )
                fixture_ids["empty_author"] = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO blog_categories(name,slug)
                       VALUES('Maintenance','maintenance') RETURNING id"""
                )
                category_id = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO blog_tags(name,slug)
                       VALUES('Safety','safety') RETURNING id"""
                )
                fixture_ids["tag"] = cursor.fetchone()[0]
                if force_error:
                    raise RuntimeError("forced atomic bootstrap rollback")

                fixtures = (
                    ("published", "phase1d-published", "Phase 1D Published", "published"),
                    ("draft", "phase1d-draft", "Phase 1D Draft", "draft"),
                    ("submitted", "phase1d-pending", "Phase 1D Submitted", "pending_review"),
                    ("rejected", "phase1d-rejected", "Phase 1D Rejected", "rejected"),
                    ("rich", "phase1d-rich", "Phase 1D Long Rich Article", "published"),
                )
                for key, slug, title, status in fixtures:
                    fixture_ids[key] = insert_blog(cursor, {
                        "slug": slug, "author_id": 1, "title": title,
                        "subtitle": f"{key.title()} state", "status": status,
                        "reading_time": 12 if key == "rich" else 2,
                    }, category_id=category_id)
                for index in range(1, 16):
                    fixture_ids[f"page_{index}"] = insert_blog(cursor, {
                        "slug": f"phase1d-page-{index}", "author_id": 1,
                        "title": f"Pagination Blog {index}",
                        "subtitle": "Pagination fixture", "status": "published",
                    }, category_id=category_id)

                blocks = {
                    "published": [("paragraph", {"text": "Published हिन्दी 🚗"})],
                    "draft": [("paragraph", {"text": "Draft content"})],
                    "submitted": [("paragraph", {"text": "Submitted content"})],
                    "rejected": [("paragraph", {"text": "Rejected content"})],
                    "rich": [
                        ("heading", {"text": "All blocks heading", "level": 2}),
                        ("paragraph", {"text": "Long हिन्दी paragraph 🙂 " * 500}),
                        ("quote", {"text": "Quote", "citation": "AMPYAN"}),
                        ("bullet_list", {"items": ["One", "Two"]}),
                        ("numbered_list", {"items": ["First", "Second"]}),
                        ("table", {"rows": [["Part", "State"], ["Brake", "Good"]]}),
                        ("callout", {"text": "Callout"}),
                        ("divider", {}),
                        ("image", {"url": "https://media.invalid/phase1d/static.webp",
                                   "caption": "Caption", "alt_text": "Alt"}),
                        ("gallery", {"items": [{"url": "https://media.invalid/phase1d/a.webp",
                                               "caption": "Gallery"}]}),
                        ("youtube", {"url": "https://youtube.com/watch?v=test"}),
                        ("instagram", {"url": "https://instagram.com/p/test"}),
                        ("link_preview", {"url": "https://example.com", "title": "Link"}),
                    ],
                }
                for key, values in blocks.items():
                    for position, (kind, data) in enumerate(values):
                        cursor.execute(
                            """INSERT INTO blog_content_blocks(
                                 blog_id,stable_block_id,block_type,position,data
                               ) VALUES(%s,%s,%s,%s,%s)""",
                            (fixture_ids[key], f"{key}-{position}", kind, position, Json(data)),
                        )
                cursor.execute(
                    """INSERT INTO blog_comments(blog_id,user_id,body,status)
                       VALUES(%s,2,'Visible comment','visible') RETURNING id""",
                    (fixture_ids["published"],),
                )
                fixture_ids["comment"] = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO blog_comments(blog_id,user_id,body,status)
                       VALUES(%s,2,'Deleted parent','deleted') RETURNING id""",
                    (fixture_ids["published"],),
                )
                parent_id = cursor.fetchone()[0]
                cursor.execute(
                    """INSERT INTO blog_comments(
                         blog_id,user_id,parent_comment_id,body,status
                       ) VALUES(%s,1,%s,'Visible reply','visible')""",
                    (fixture_ids["published"], parent_id),
                )
                cursor.execute(
                    "UPDATE blogs SET comment_count=3 WHERE id=%s",
                    (fixture_ids["published"],),
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_get_serial_sequence('blogs','id')")
            sequence_name = cursor.fetchone()[0]
            cursor.execute("SELECT count(*),min(id),max(id) FROM blogs")
            blog_count, minimum_id, maximum_id = cursor.fetchone()
            cursor.execute(
                """INSERT INTO blogs(
                     slug,author_id,title,status,reading_time_minutes,version
                   ) VALUES('phase1d-sequence-probe',1,'Sequence Probe','draft',0,1)
                   RETURNING id"""
            )
            probe_id = cursor.fetchone()[0]
            if probe_id <= maximum_id:
                raise AssertionError((sequence_name, maximum_id, probe_id))
            connection.rollback()
            cursor.execute("SELECT count(*) FROM blog_categories")
            category_count = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM blog_comments")
            comment_count = cursor.fetchone()[0]
            cursor.execute('SELECT count(*) FROM "user"')
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT slug FROM blogs")
            slugs = {row[0] for row in cursor.fetchall()}
            if not REQUIRED_SLUGS.issubset(slugs):
                raise AssertionError(REQUIRED_SLUGS - slugs)
            cursor.execute(
                "SELECT last_value FROM pg_sequences WHERE schemaname=current_schema() "
                "AND sequencename=%s",
                (sequence_name.rsplit(".", 1)[-1],),
            )
            sequence_state = {"last_value": cursor.fetchone()[0]}
    return {
        "database": urlparse(database_url).path.lstrip("/"),
        "sequence_name": sequence_name,
        "sequence_state": sequence_state,
        "blog_count": blog_count,
        "min_blog_id": minimum_id,
        "max_blog_id": maximum_id,
        "probe_blog_id": probe_id,
        "category_count": category_count,
        "comment_count": comment_count,
        "user_count": user_count,
        "moderation_fixture_count": 1,
        "required_slugs": sorted(REQUIRED_SLUGS),
        "fixture_ids": fixture_ids,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-error", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(bootstrap(arguments.force_error), indent=2))
