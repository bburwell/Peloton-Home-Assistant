import json
import os
from datetime import datetime
import pylotoncycle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Peloton credentials from environment variables
username = "yourname@youremail.com"
password = "yourpassword"

if not username or not password:
    print("Peloton username and/or password not found in environment variables!")
    exit(1)

output_file = "/config/www/peloton_workouts.json"
workouts_to_get = 5  # Adjust as needed

# Initialize Peloton connection
try:
    conn = pylotoncycle.PylotonCycle(username, password)
except Exception as e:
    print(f"Failed to connect to Peloton API: {e}")
    exit(1)

# Fetch recent workouts
try:
    workouts = conn.GetRecentWorkouts(workouts_to_get)
except Exception as e:
    print(f"Failed to fetch workouts: {e}")
    exit(1)

# Load existing JSON data (flat array under peloton_workouts)
existing_data = {"peloton": "all workouts", "peloton_workouts": []}
if os.path.exists(output_file):
    try:
        with open(output_file, "r") as f:
            existing_data = json.load(f)
            if not isinstance(existing_data, dict) or "peloton_workouts" not in existing_data:
                existing_data = {"peloton": "all workouts", "peloton_workouts": []}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in existing file: {e}, resetting to empty")
    except Exception as e:
        print(f"Failed to load existing JSON file: {e}")

# Gather all existing workout IDs for deduplication
existing_workout_ids = set(w["workout_id"] for w in existing_data.get("peloton_workouts", []))

# Prepare new workout data
today = datetime.now().strftime("%Y-%m-%d")
new_workouts = []
for workout in workouts:
    workout_id = workout["id"]
    created_at = datetime.fromtimestamp(workout["created_at"]).isoformat()
    workout_date = datetime.fromtimestamp(workout["created_at"]).strftime("%Y-%m-%d")
    title = workout.get("title") or workout.get("ride", {}).get("title", "Unknown")
    instructor_name = workout.get("instructor_name") or workout.get("ride", {}).get("instructor_name", "Unknown")
    if workout_id in existing_workout_ids:
        print(f"Skipping existing workout: {workout_id} | {created_at} | {title} | {instructor_name}")
        continue
    try:
        metrics = conn.GetWorkoutMetricsById(workout_id)
        summary = conn.GetWorkoutSummaryById(workout_id)
        average_summaries = metrics.get("average_summaries", [{}])
        summaries = metrics.get("summaries", [{}])
        workout_details = {
            "workout_id": workout_id,
            "workout_date": workout_date,
            "created_at": created_at,
            "fitness_discipline": workout["fitness_discipline"],
            "title": title,
            "instructor_name": instructor_name,
            "duration": workout["ride"].get("duration", 0),
            "metrics": {
                "avg_cadence": average_summaries[0].get("value", 0) if len(average_summaries) > 0 else 0,
                "avg_power": average_summaries[1].get("value", 0) if len(average_summaries) > 1 else 0,
                "calories": summaries[0].get("value", 0) if len(summaries) > 0 else 0,
                "distance": summaries[1].get("value", 0) if len(summaries) > 1 else 0
            },
            "summary": summary
        }
        new_workouts.append(workout_details)
        print(f"Adding NEW workout: {workout_id} | {created_at} | {title} | {instructor_name}")
    except Exception as e:
        print(f"Failed to fetch metrics for workout {workout_id}: {e}")
        continue

if new_workouts:
    # Combine existing and new workouts, avoiding duplicates
    updated_workouts = existing_data["peloton_workouts"] + [w for w in new_workouts if w["workout_id"] not in existing_workout_ids]
    # Save with peloton and peloton_workouts keys
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"peloton": "all workouts", "peloton_workouts": updated_workouts}, f, indent=2, ensure_ascii=False)
        print(f"Workout data saved to {output_file}")
        print(f"Total new workouts added: {len(new_workouts)}")
    except Exception as e:
        print(f"Failed to save JSON file: {e}")
else:
    print("No new workouts to add.")
