#!/bin/bash

# Script to create 20 fake episodes for testing pagination

API_BASE="http://localhost:8000/v1"

# Array of real YouTube video URLs that exist
VIDEO_URLS=(
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    "https://www.youtube.com/watch?v=9bZkp7q19f0"
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk"
    "https://www.youtube.com/watch?v=y6120QOlsfU"
    "https://www.youtube.com/watch?v=ZZ5LpwO-An4"
    "https://www.youtube.com/watch?v=hTWKbfoikeg"
    "https://www.youtube.com/watch?v=2xx_2XNxxfA"
    "https://www.youtube.com/watch?v=uelHwf8o7_U"
    "https://www.youtube.com/watch?v=1La4QzGeaaQ"
    "https://www.youtube.com/watch?v=5yx6BWlEVcY"
    "https://www.youtube.com/watch?v=DLzxrzFCyOs"
    "https://www.youtube.com/watch?v=ktvTqknDobU"
    "https://www.youtube.com/watch?v=JGwWNGJdvx8"
    "https://www.youtube.com/watch?v=hFZFjoX2cGg"
    "https://www.youtube.com/watch?v=0SBS4tBHKLU"
    "https://www.youtube.com/watch?v=9UZbGgXvCCA"
    "https://www.youtube.com/watch?v=2g811Eo7K8U"
    "https://www.youtube.com/watch?v=fmI_Ndrxy14"
    "https://www.youtube.com/watch?v=SSbBvKaM6sk"
    "https://www.youtube.com/watch?v=OPf0YbXqDm0"
)

# Array of fake titles for our episodes
TITLES=(
    "Introduction to Machine Learning"
    "Advanced Python Programming"
    "Web Development with React"
    "Database Design Fundamentals"
    "Cloud Computing Essentials"
    "Cybersecurity Best Practices"
    "Mobile App Development"
    "Data Science with Python"
    "DevOps Fundamentals"
    "API Design Principles"
    "Software Testing Strategies"
    "Agile Development Methods"
    "Microservices Architecture"
    "Docker Containerization"
    "Kubernetes Orchestration"
    "Frontend Performance Optimization"
    "Backend System Design"
    "Full Stack Development"
    "Code Review Techniques"
    "Team Collaboration Tools"
)

echo "Creating 20 fake episodes for pagination testing..."

for i in {1..20}; do
    # Get video URL and title
    VIDEO_URL_INDEX=$((i % ${#VIDEO_URLS[@]}))
    VIDEO_URL="${VIDEO_URLS[$VIDEO_URL_INDEX]}"
    TITLE_INDEX=$((i % ${#TITLES[@]}))
    TITLE="${TITLES[$TITLE_INDEX]} - Episode $i"

    # Get metadata from the analyze endpoint
    echo "Getting metadata for episode $i: $TITLE"
    METADATA=$(curl -s "${API_BASE}/episodes/analyze" \
        -H "Content-Type: application/json" \
        -d "{\"video_url\": \"${VIDEO_URL}\"}" 2>/dev/null)

    if [[ $? -ne 0 || -z "$METADATA" ]]; then
        echo "✗ Failed to get metadata for episode $i"
        continue
    fi

    # Extract video_id from metadata (simplified extraction)
    VIDEO_ID=$(echo "$METADATA" | grep -o '"video_id":"[^"]*"' | cut -d'"' -f4)

    # Generate description
    DESCRIPTION="This is a test episode #$i created for pagination testing. It contains sample content to demonstrate the pagination feature working correctly. Original video: $(echo "$METADATA" | grep -o '"title":"[^"]*"' | head -1 | cut -d'"' -f4)"

    # Create episode with metadata
    JSON_PAYLOAD=$(cat << EOF
{
    "channel_id": 1,
    "video_url": "${VIDEO_URL}",
    "title": "${TITLE}",
    "description": "${DESCRIPTION}",
    "duration_seconds": $(echo "$METADATA" | grep -o '"duration_seconds":[0-9]*' | grep -o '[0-9]*'),
    "thumbnail_url": "$(echo "$METADATA" | grep -o '"thumbnail_url":"[^"]*"' | cut -d'"' -f4)",
    "is_favorited": $(shuf -i 0-1 -n 1)
}
EOF
    )

    echo "Creating episode $i with video ID: $VIDEO_ID"

    # Make API call to create episode
    RESPONSE=$(curl -s -X POST "${API_BASE}/episodes/" \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD" 2>/dev/null)

    if [[ $? -eq 0 ]]; then
        echo "✓ Episode $i created successfully"
    else
        echo "✗ Failed to create episode $i"
        echo "Response: $RESPONSE"
    fi

    # Small delay to avoid overwhelming the server
    sleep 0.5
done

echo "Finished creating fake episodes!"
