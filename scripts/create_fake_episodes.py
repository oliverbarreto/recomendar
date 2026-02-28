#!/usr/bin/env python3
"""
Script to create 20 fake episodes for testing pagination
"""

import asyncio
import random
import string
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

# Now import the app modules
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.repositories.episode_repository import EpisodeRepositoryImpl
from app.domain.entities.episode import Episode, EpisodeStatus
from app.domain.value_objects.video_id import VideoId
from app.domain.value_objects.duration import Duration

async def create_fake_episodes():
    """Create 20 fake episodes for testing pagination"""
    session = get_db_session()
    repo = EpisodeRepositoryImpl(session)

    # Use an existing thumbnail URL from one of the real episodes
    existing_thumbnail = "https://i.ytimg.com/vi_webp/3JIf2f0hEfw/maxresdefault.webp"

    # Generate random titles
    titles = [
        "Introduction to Machine Learning",
        "Advanced Python Programming",
        "Web Development with React",
        "Database Design Fundamentals",
        "Cloud Computing Essentials",
        "Cybersecurity Best Practices",
        "Mobile App Development",
        "Data Science with Python",
        "DevOps Fundamentals",
        "API Design Principles",
        "Software Testing Strategies",
        "Agile Development Methods",
        "Microservices Architecture",
        "Docker Containerization",
        "Kubernetes Orchestration",
        "Frontend Performance Optimization",
        "Backend System Design",
        "Full Stack Development",
        "Code Review Techniques",
        "Team Collaboration Tools"
    ]

    # Create 20 fake episodes
    for i in range(20):
        # Generate random video ID
        video_id = ''.join(random.choices(string.ascii_letters + string.digits, k=11))

        # Create episode entity
        episode = Episode(
            id=None,  # Will be auto-generated
            channel_id=1,
            video_id=VideoId(video_id),
            title=titles[i % len(titles)],  # Cycle through titles
            description=f"This is a test episode #{i+1} created for pagination testing. It contains sample content to demonstrate the pagination feature.",
            publication_date=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            audio_file_path=f"channel_1/{video_id}_fake.mp3",  # Fake audio path
            video_url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=existing_thumbnail,
            duration=Duration(random.randint(300, 3600)),  # 5 minutes to 1 hour
            keywords=["test", "pagination", "fake", "episode"],
            tags=[],
            status=EpisodeStatus.COMPLETED,  # Set as completed to avoid processing
            retry_count=0,
            download_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            youtube_channel="Test Channel",
            youtube_channel_id="UC" + ''.join(random.choices(string.ascii_letters + string.digits, k=22)),
            youtube_channel_url=f"https://www.youtube.com/channel/UC{''.join(random.choices(string.ascii_letters + string.digits, k=22))}",
            is_favorited=random.choice([True, False])
        )

        try:
            # Create the episode
            created_episode = await repo.create(episode)
            print(f"Created episode {i+1}: {created_episode.title} (ID: {created_episode.id})")

            # Commit the transaction
            await session.commit()

        except Exception as e:
            print(f"Error creating episode {i+1}: {e}")
            await session.rollback()

    print("Finished creating 20 fake episodes!")

if __name__ == "__main__":
    asyncio.run(create_fake_episodes())
