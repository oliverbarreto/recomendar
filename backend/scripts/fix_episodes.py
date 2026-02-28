#!/usr/bin/env python3
"""
Quick script to fix episodes that have media files but are stuck in processing status
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Database configuration
DATABASE_URL = "sqlite+aiosqlite:///./data/labcastarr.db"

async def fix_episodes():
    """Fix episodes that have media files but wrong status"""

    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Media directory
    media_dir = Path("./media/channel_1")

    print(f"Checking media directory: {media_dir}")
    print(f"Media files found: {list(media_dir.glob('*.mp3'))}")

    async with AsyncSessionLocal() as session:
        try:
            # Get episodes that are stuck in processing but have media files
            result = await session.execute(
                text("SELECT id, video_id, title, status, audio_file_path FROM episodes WHERE status = 'processing'")
            )
            episodes = result.fetchall()

            print(f"Found {len(episodes)} episodes in processing status")

            fixed_count = 0
            for episode in episodes:
                episode_id, video_id, title, status, audio_file_path = episode

                # Check if media file exists
                media_file = media_dir / f"{video_id}.mp3"
                if media_file.exists():
                    print(f"Episode {episode_id} ({video_id}): {title}")
                    print(f"  - Current status: {status}")
                    print(f"  - Current path: {audio_file_path}")
                    print(f"  - Media file exists: {media_file}")

                    # Update episode to completed status with correct path
                    await session.execute(
                        text("""
                            UPDATE episodes
                            SET status = 'completed',
                                audio_file_path = :audio_path,
                                download_date = datetime('now')
                            WHERE id = :episode_id
                        """),
                        {
                            "audio_path": f"channel_1/{video_id}.mp3",
                            "episode_id": episode_id
                        }
                    )

                    print(f"  ✅ Fixed episode {episode_id}")
                    fixed_count += 1

                    # Only fix first 2 episodes as requested
                    if fixed_count >= 2:
                        break
                else:
                    print(f"Episode {episode_id} ({video_id}): Media file missing - {media_file}")

            # Commit changes
            await session.commit()
            print(f"\n🎉 Successfully fixed {fixed_count} episodes")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    # Change to backend directory
    os.chdir("/Users/oliver/Library/Mobile Documents/com~apple~CloudDocs/dev/webaps/labcastarr/backend")
    asyncio.run(fix_episodes())