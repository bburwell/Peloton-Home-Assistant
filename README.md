# Peloton-Home-Assistant

I own a Peloton Bike and Treadmill.  Love the bike and the competition.  I also use Home Assistant.  I am now beginning to add the Peloton Data to my Home Assistant config.

I will post what I am doing here and will also add a community page on Home Assistant.

This is a work in-progress and I will only update this site when I can.

Here is how I am Using Home Assistant to keep track of Peloton Workouts:
-- I am following for the most part what I mostly use for my sports score tracking.  I have a repository that I go into more detail of what I am doing here if you are interested: https://github.com/bburwell/HA-Sports-Scores

* My Peloton tracking is made up of a:
   1. A Python File that grabs my peloton rides/runs/mediation/etc. and sticks it into a json file (code is in python directory)
   2. A line added to the configuration.yaml so I can call the python file ( get_peloton_rides: 'python /config/www/peloton-ridesv2.py' )
   3. An addition to the sensors.yaml file so my peloton sensor is updated with the data that is in the json file (Code is in sensors directory)
   4. A Peloton Dashboard (code is in the dashboards directory)
      
* Some additonal notes:
  * Python file that uses pylotoncycle - https://github.com/justmedude/pylotoncycle/
  * You will need to enter your own username and password.
  * When I first run the python file I change the code to 500 workouts -
  *       workouts_to_get = 500
  * and change this path output_file = "/config/www/peloton_workouts.json" so I can run it in the /config/www directory manually without it barking ->>
  *      output_file = "peloton_workouts.json"
  * After the first run I change
  *       workouts_to_get = 5 
  *       output_file = "/config/www/peloton_workouts.json"
  * I do this so when the automation runs it updates the json file in the /config/www directory
 
* I know some are looking at trying to add automation for lights and music and BPM's.  I haven't gone down that path but I will give a couple of commnents:
  * First I do not know how many API calls are allowed daily for the Peloton API.  If it is unlimited then this could be easlity created.  If it is limited, which I expect it to be, you could then possibly use something like a motion detector to run the python file more frequently.
  * What you would want to key off of is the status key - "status": "IN_PROGRESS" is going on right now vs "status": "COMPLETE"
  * Here is an example of whats in the json file for each workout:
    ```
    {
      "workout_id": "15719b81",
      "workout_date": "2025-07-07",
      "created_at": "2025-07-07T09:52:50",
      "fitness_discipline": "meditation",
      "title": "5 min Happiness Meditation",
      "instructor_name": "Anna Greenberg",
      "duration": 300,
      "metrics": {
        "avg_cadence": 0,
        "avg_power": 0,
        "calories": 0,
        "distance": 0
      },
      "summary": {
        "created_at": 1751907170,
        "device_type": "web",
        "end_time": null,
        "fitness_discipline": "meditation",
        "has_pedaling_metrics": false,
        "has_leaderboard_metrics": false,
        "id": "15719b8fe6d5471f9b88cff125ad2851",
        "is_total_work_personal_record": false,
        "is_outdoor": false,
        "metrics_type": null,
        "name": "Meditation Workout",
        "peloton_id": "f87443",
        "platform": "web",
        "start_time": 1751907169,
        "status": "IN_PROGRESS",
        "timezone": "America/Los_Angeles",
        "title": null,
        "total_work": 0.0,
        "user_id": "6af68",
        "workout_type": "class",
        "total_video_watch_time_seconds": 0,
        "total_video_buffering_seconds": 0,
        "v2_total_video_watch_time_seconds": null,
        "v2_total_video_buffering_seconds": null,
        "total_music_audio_play_seconds": null,
        "total_music_audio_buffer_seconds": null,
        "service_id": null,
        "created": 1751907170,
        "device_time_created_at": 1751881969,
        "strava_id": null,
        "fitbit_id": null,
        "is_skip_intro_available": false,
        "pause_time_remaining": null,
        "pause_time_elapsed": null,
        "is_paused": false,
        "has_paused": false,
        "is_pause_available": false,
        "ride": {
          "content_availability": "digital_and_above",
          "content_availability_level": "digital_and_above",
          "free_for_limited_time": false,
          "is_limited_ride": false,
          "availability": {
            "is_available": true,
            "reason": null
          },
          "class_type_ids": [
            "f4cf26e6059943a0a8e3a6533bb76239"
          ],
          "content_provider": "peloton",
          "content_format": "video",
          "description": "A guided meditation that focuses on cultivating happiness and a more playful attitude towards life.",
          "difficulty_estimate": 3.541198501872659,
          "overall_estimate": 0.996382768826044,
          "difficulty_rating_avg": 3.541198501872659,
          "difficulty_rating_count": 534,
          "difficulty_level": null,
          "duration": 300,
          "equipment_ids": [],
          "equipment_tags": [],
          "explicit_rating": 0,
          "extra_images": [],
          "fitness_discipline": "meditation",
          "fitness_discipline_display_name": "Meditation",
          "has_closed_captions": true,
          "has_pedaling_metrics": false,
          "home_peloton_id": "f622a2",
          "id": "3cdcfb4e40fda8bf",
          "image_url": "https://s3.amazonaws.com/peloton-ride-images/c0c10043ca2b7a81c80b9029da2c41a0912df5de/img_1741981343_9a3163ff4a954bda834aa82c61eccca6.png",
          "instructor_id": "a8c56f162c964e9392568bc13828a3fb",
          "individual_instructor_ids": [],
          "is_archived": true,
          "is_closed_caption_shown": true,
          "is_explicit": false,
          "has_free_mode": false,
          "is_live_in_studio_only": true,
          "language": "english",
          "origin_locale": "en-US",
          "length": 343,
          "live_stream_id": "3cdcf51307ff424399fb3b4e40fda8bf-live",
          "live_stream_url": null,
          "location": "psny-studio-2",
          "metrics": [
            "heart_rate"
          ],
          "original_air_time": 1748404800,
          "overall_rating_avg": 0.996382768826044,
          "overall_rating_count": 3041,
          "pedaling_start_offset": 1,
          "pedaling_end_offset": 301,
          "pedaling_duration": 300,
          "rating": 0,
          "ride_type_id": "f4cf26e6059943a0a8e3a6533bb76239",
          "ride_type_ids": [
            "f4cf26e6059943a0a8e3a6533bb76239"
          ],
          "sample_vod_stream_url": null,
          "sample_preview_stream_url": null,
          "scheduled_start_time": 1748404800,
          "series_id": "b2e8dc24d30f42e096eb5bf0b61386cb",
          "sold_out": false,
          "studio_peloton_id": "7866db3ff4f04574be21abde85b3433c",
          "title": "5 min Happiness Meditation",
          "total_ratings": 6357,
          "total_in_progress_workouts": 4,
          "total_workouts": 100000,
          "vod_stream_url": null,
          "vod_stream_id": "3cdcf51307ff424399fb3b4e40fda8bf-vod",
          "captions": [
            "en-US",
            "es-ES"
          ],
          "user_caption_locales": [],
          "join_tokens": {
            "on_demand": "eyJob21lX3BlbG90b25faWQiOiBudWxsLCAicmlkZV9pZCI6ICIzY2RjZjUxMzA3ZmY0MjQzOTlmYjNiNGU0MGZkYThiZiIsICJzdHVkaW9fcGVsb3Rvbl9pZCI6IG51bGwsICJ0eXBlIjogIm9uX2RlbWFuZCJ9"
          },
          "flags": [],
          "is_dynamic_video_eligible": false,
          "is_fixed_distance": false,
          "dynamic_video_recorded_speed_in_mph": null,
          "thumbnail_title": null,
          "thumbnail_location": null,
          "distance": null,
          "distance_unit": null,
          "distance_display_value": null,
          "is_outdoor": false,
          "has_tread_pace_target": false,
          "excluded_platforms": [],
          "class_avg_follow_along_score": 0.0,
          "muscle_group_score": []
        },
        "total_heart_rate_zone_durations": null,
        "average_effort_score": null,
        "achievement_templates": [],
        "leaderboard_rank": null,
        "total_leaderboard_users": 0,
        "leaderboard_distance_rank": null,
        "total_leaderboard_distance_users": 0,
        "ftp_info": {
          "ftp": 0,
          "ftp_source": null,
          "ftp_workout_id": null
        },
        "device_type_display_name": "App",
        "metadata": {
          "playlist_type": "synced"
        },
        "is_3p_digital_workout": false
      }
    }
  ]
}
  ```

![image](https://github.com/user-attachments/assets/750159cc-f05a-4b9c-b837-363837576b8a)




