import streamlit as st
import requests
from datetime import datetime, timedelta

# --- IMPORTANT ---
# Enter your YouTube Data API Key here.
# Go to https://console.cloud.google.com/apis/dashboard to create one.
API_KEY = "AIzaSyCnwJrd2TIqF7loNiSjFlwOh9s6AZ2hm5g"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("MrBeast Viral Video Finder")

# Input Fields
days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)

# List of keywords focused on MrBeast viral videos
keywords = [
    "MrBeast viral video",
    "MrBeast trending",
    "MrBeast most viewed video",
    "MrBeast new video",
    "MrBeast challenge",
    "MrBeast gives away money",
    "MrBeast last to leave",
    "MrBeast 100 million",
    "MrBeast Squid Game",
    "MrBeast versus",
    "MrBeast survival challenge",
    "I spent 7 days MrBeast",
    "world's most dangerous MrBeast",
    "Feastables",
    "MrBeast Burger",
    "MrBeast philanthropy",
    "MrBeast $1 vs $1,000,000"
]


# Fetch Data Button
if st.button("Fetch Data"):
    if API_KEY == "Enter your API Key here":
        st.error("Please enter your YouTube API Key in the script to run the tool.")
    else:
        try:
            # Calculate date range
            start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
            all_results = []

            # Iterate over the list of keywords
            progress_bar = st.progress(0)
            for i, keyword in enumerate(keywords):
                st.write(f"Searching for keyword: {keyword}")

                # Define search parameters
                search_params = {
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "order": "viewCount",
                    "publishedAfter": start_date,
                    "maxResults": 5,  # Fetch 5 results per keyword
                    "key": API_KEY,
                }

                # Fetch video data
                response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                data = response.json()

                # Check if "items" key exists
                if "items" not in data or not data["items"]:
                    st.warning(f"No videos found for keyword: {keyword}")
                    continue

                videos = data["items"]
                video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
                channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

                if not video_ids or not channel_ids:
                    st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                    continue

                # --- Fetch video statistics ---
                stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
                stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                stats_data = stats_response.json()

                if "items" not in stats_data:
                    st.warning(f"Failed to fetch video statistics for keyword: {keyword} (Items key missing)")
                    continue
                
                # Create a dictionary for video stats for easy lookup
                video_stats_dict = {item['id']: item['statistics'] for item in stats_data.get("items", [])}


                # --- Fetch channel statistics ---
                # Get unique channel IDs to avoid duplicate API calls
                unique_channel_ids = list(set(channel_ids))
                channel_params = {"part": "statistics", "id": ",".join(unique_channel_ids), "key": API_KEY}
                channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                channel_data = channel_response.json()

                if "items" not in channel_data:
                    st.warning(f"Failed to fetch channel statistics for keyword: {keyword} (Items key missing)")
                    continue
                
                # Create a dictionary for channel stats for easy lookup
                channel_stats_dict = {item['id']: item['statistics'] for item in channel_data.get("items", [])}

                # Collect results
                for video in videos:
                    video_id = video["id"]["videoId"]
                    channel_id = video["snippet"]["channelId"]

                    # Get stats from our dictionaries
                    stat = video_stats_dict.get(video_id)
                    channel_stat = channel_stats_dict.get(channel_id)

                    # Ensure we have stats for both video and channel
                    if not stat or not channel_stat:
                        st.warning(f"Skipping video {video_id} - missing stats.")
                        continue

                    subs = int(channel_stat.get("subscriberCount", 0))

                    # Only include smaller channels
                    if subs < 3000:
                        title = video["snippet"].get("title", "N/A")
                        description = video["snippet"].get("description", "")[:200]
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        views = int(stat.get("viewCount", 0))
                        
                        all_results.append({
                            "Title": title,
                            "Description": description,
                            "URL": video_url,
                            "Views": views,
                            "Subscribers": subs,
                            "Keyword": keyword
                        })
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(keywords))

            # Display results
            if all_results:
                st.success(f"Found {len(all_results)} results across all keywords!")
                
                # Sort by views descending
                sorted_results = sorted(all_results, key=lambda x: x['Views'], reverse=True)
                
                for result in sorted_results:
                    st.markdown(
                        f"**Title:** {result['Title']}  \n"
                        f"**Description:** {result['Description']}...  \n"
                        f"**URL:** [Watch Video]({result['URL']})  \n"
                        f"**Views:** {result['Views']} | **Subscribers:** {result['Subscribers']}  \n"
                        f"**Found with keyword:** '{result['Keyword']}'"
                    )
                    st.write("---")
            else:
                st.warning("No results found for channels with fewer than 3,000 subscribers.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

