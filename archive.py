import praw
import textwrap
import configparser
from datetime import datetime, timezone

config = configparser.ConfigParser()
config.read("config.ini")

reddit = praw.Reddit(
    client_id=config["reddit"]["client_id"],
    client_secret=config["reddit"]["client_secret"],
    user_agent=config["reddit"]["user_agent"],
    username=config["reddit"]["username"],
    password=config["reddit"]["password"],
)

post_url = ""
submission = reddit.submission(url=post_url)

# Expand all comments
submission.comments.replace_more(limit=None)

with open("FILE_NAME.txt", "w", encoding="utf-8") as f:
    wrapper = textwrap.TextWrapper(width=80)

    post_date = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    media_urls = []
    # Check for gallery posts
    gallery_data = getattr(submission, 'gallery_data', None)
    if gallery_data:
        for item in submission.gallery_data['items']:
            media_id = item['media_id']
            if media_id in submission.media_metadata:
                media_url = submission.media_metadata[media_id]['s']['u'].replace('&amp;', '&')
                media_urls.append(media_url)
    # Check for single media (e.g., images/videos directly in the post)
    elif submission.is_reddit_media_domain and not gallery_data:
        media_urls.append(submission.url)

    if media_urls:
        f.write("Media:\n")
        for i, media_url in enumerate(media_urls, start=1):
            f.write(f"  Media {i}: {media_url}\n")
        f.write("\n")

    total_views = getattr(submission, "view_count", "Unavailable")
    upvote_ratio = getattr(submission, "upvote_ratio", "Unavailable")
    f.write(f"Subreddit: {submission.subreddit}\n")
    f.write(f"Title: {submission.title}\n")
    f.write(f"Author: {submission.author}\n")
    f.write(f"Upvotes: {submission.score}\n")
    f.write(f"Upvote Rate: {"Unavailable" if upvote_ratio is None else upvote_ratio}\n")
    f.write(f"Total Views: {"Unavailable" if total_views is None else total_views}\n")
    f.write(f"Total Comments: {submission.num_comments}\n")
    f.write(f"Content:\n{wrapper.fill(submission.selftext)}\n")
    f.write(f"URL: {submission.url}\n\n")
    f.write("Comments:\n")

    # Recursive function to save, format, and add metadata for comments
    def save_comment(comment, depth=0):
        indent = "    " * depth
        f.write(f"{indent}- Author: {comment.author}\n")
        f.write(f"{indent}  Upvotes: {comment.score}\n")
        formatted_comment = wrapper.fill(comment.body)
        indented_comment = "\n".join(indent + "  " + line for line in formatted_comment.splitlines())
        f.write(f"{indented_comment}\n\n")
        for reply in comment.replies:
            save_comment(reply, depth + 1)

    # Save all top-level comments and their replies
    for top_level_comment in submission.comments:
        save_comment(top_level_comment)

