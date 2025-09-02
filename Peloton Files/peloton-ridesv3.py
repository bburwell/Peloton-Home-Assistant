import json
import os
from collections import defaultdict
from datetime import datetime
import pylotoncycle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Peloton credentials from environment variables
username = "xxx@xxx.com"
password = "xxx"

if not username or not password:
    print("Peloton username and/or password not found in environment variables!")
    exit(1)

# File paths
output_workouts_file = "/config/www/peloton_workouts.json"
in_progress_file = "/config/www/peloton_workouts_in_progress.json"
output_averages_file = "/config/www/peloton_averages.json"
workouts_to_get = 10  # Number of recent workouts to fetch

# Initialize Peloton connection
try:
    conn = pylotoncycle.PylotonCycle(username, password)
except Exception as e:
    print(f"Failed to connect to Peloton API: {e}")
    exit(1)

# Load existing JSON data for workouts
existing_workouts_data = {"peloton": "all workouts", "peloton_workouts": []}
if os.path.exists(output_workouts_file):
    try:
        with open(output_workouts_file, "r") as f:
            existing_workouts_data = json.load(f)
            if not isinstance(existing_workouts_data, dict) or "peloton_workouts" not in existing_workouts_data:
                existing_workouts_data = {"peloton": "all workouts", "peloton_workouts": []}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in existing workouts file: {e}, resetting to empty")
    except Exception as e:
        print(f"Failed to load existing workouts JSON file: {e}")

in_progress_data = {"peloton": "in progress or last completed workout", "peloton_workouts": []}
if os.path.exists(in_progress_file):
    try:
        with open(in_progress_file, "r") as f:
            in_progress_data = json.load(f)
            if not isinstance(in_progress_data, dict) or "peloton_workouts" not in in_progress_data:
                in_progress_data = {"peloton": "in progress or last completed workout", "peloton_workouts": []}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in in-progress file: {e}, resetting to empty")
    except Exception as e:
        print(f"Failed to load in-progress JSON file: {e}")

# Gather all existing workout IDs
existing_workout_ids = set(w["workout_id"] for w in existing_workouts_data.get("peloton_workouts", []))

# Fetch recent workouts
try:
    workouts = conn.GetRecentWorkouts(workouts_to_get)
except Exception as e:
    print(f"Failed to fetch workouts: {e}")
    exit(1)

# Process workouts
updated_in_progress = []
updated_workouts = []
seen_workout_ids = set()  # Track processed workout IDs to avoid duplicates
for workout in workouts:  # Process only new API-fetched workouts first
    workout_id = workout["id"]
    if workout_id in seen_workout_ids:
        continue
    seen_workout_ids.add(workout_id)
    try:
        metrics = conn.GetWorkoutMetricsById(workout_id)
        summary = conn.GetWorkoutSummaryById(workout_id)
        status = summary.get("status", "unknown").upper()
        # Handle created_at consistently
        created_at_value = workout.get("created_at")
        if isinstance(created_at_value, (int, float)):  # New API data (timestamp)
            created_at = datetime.fromtimestamp(created_at_value).isoformat()
        elif isinstance(created_at_value, str):  # Existing JSON data (ISO string)
            try:
                created_at = datetime.fromisoformat(created_at_value).isoformat()
            except ValueError:
                created_at = datetime.now().isoformat()  # Fallback if invalid
        else:
            created_at = datetime.now().isoformat()  # Default fallback
        workout_date = datetime.fromisoformat(created_at).strftime("%Y-%m-%d")  # Consistent date from created_at
        title = workout.get("title") or workout.get("ride", {}).get("title", "Unknown")
        instructor_name = workout.get("instructor_name") or workout.get("ride", {}).get("instructor_name", "Unknown")

        avg_metrics = {m["display_name"]: m["value"] for m in metrics.get("average_summaries", []) if isinstance(metrics, dict)} or {}
        sum_metrics = {m["display_name"]: m["value"] for m in metrics.get("summaries", []) if isinstance(metrics, dict)} or {}

        # Source distance in miles directly from API, log the source
        distance_miles_sources = {
            "metrics_distance": metrics.get("distance"),
            "sum_metrics_distance": sum_metrics.get("Distance"),
            "ride_distance": summary.get("ride", {}).get("distance")
        }
        distance_miles = next((v for v in distance_miles_sources.values() if v is not None and v > 0), None)
        distance_source = next((k for k, v in distance_miles_sources.items() if v is not None and v > 0), "none")
        print(f"Workout {workout_id}: Distance ({distance_miles} miles) sourced from {distance_source}")

        # Fallback estimation if distance is None or 0 (based on power and duration)
        if distance_miles is None or distance_miles == 0:
            avg_power = avg_metrics.get("Avg Output", 0)
            duration_hours = duration / 3600 if duration > 0 else 1  # Avoid division by zero
            if avg_power > 0:
                estimated_distance_miles = (avg_power * duration_hours * 0.386) / 1000  # Rough estimate
                distance_miles = estimated_distance_miles if estimated_distance_miles > 0 else 0
                print(f"Workout {workout_id}: Using estimated distance {distance_miles} miles based on power")
            else:
                distance_miles = 0
                print(f"Workout {workout_id}: No distance data and no power for estimation")

        # Calculate average speed in mph
        duration = workout["ride"].get("duration", 0) if "ride" in workout else workout.get("duration", 0)
        duration_hours = duration / 3600
        average_speed_mph = (distance_miles / duration_hours) if duration_hours > 0 and distance_miles > 0 else 0

        # Convert total_work from joules to kilojoules
        total_work = summary.get("total_work", metrics.get("total_output", 0))
        total_output = total_work / 1000 if total_work is not None else 0

        # Extract heart rate metrics
        heart_rate_data = next((m for m in metrics.get("metrics", []) if m["display_name"] == "Heart Rate"), {})
        heart_rate_avg = heart_rate_data.get("average_value", 0)
        heart_rate_max = heart_rate_data.get("max_value", 0)

        # Extract cadence and resistance metrics
        cadence_data = next((m for m in metrics.get("metrics", []) if m["display_name"] == "Cadence"), {})
        cadence_max = cadence_data.get("max_value", 0)
        resistance_data = next((m for m in metrics.get("metrics", []) if m["display_name"] == "Resistance"), {})
        resistance_max = resistance_data.get("max_value", 0)

        # Extract additional metrics
        leaderboard_rank = summary.get("leaderboard_rank", 0)
        total_leaderboard_users = summary.get("total_leaderboard_users", 0)
        ftp = summary.get("ftp_info", {}).get("ftp", 0)
        muscle_group_scores = summary.get("ride", {}).get("muscle_group_score", []) or metrics.get("muscle_group_score", [])

        # Extract detailed metrics for graphing
        detailed_metrics = {}
        for metric in metrics.get("metrics", []):
            if metric.get("values"):
                detailed_metrics[metric["display_name"]] = {
                    "values": metric["values"],
                    "max_value": metric["max_value"],
                    "average_value": metric["average_value"],
                    "display_unit": metric["display_unit"]
                }

        workout_details = {
            "workout_id": workout_id,
            "workout_date": workout_date,
            "created_at": created_at,
            "fitness_discipline": workout["fitness_discipline"] if "fitness_discipline" in workout else workout.get("fitness_discipline"),
            "title": title,
            "instructor_name": instructor_name,
            "duration": duration,
            "metrics": {
                "avg_cadence": avg_metrics.get("Avg Cadence", metrics.get("avg_cadence", 0)),
                "avg_power": avg_metrics.get("Avg Output", metrics.get("avg_power", 0)),
                "avg_resistance": avg_metrics.get("Avg Resistance", metrics.get("avg_resistance", 0)),
                "calories": sum_metrics.get("Calories", metrics.get("calories", 0)),
                "distance_miles": round(distance_miles, 2) if distance_miles > 0 else 0,
                "total_output": total_output,
                "average_speed_mph": round(average_speed_mph, 2) if average_speed_mph > 0 else 0,
                "heart_rate_avg": heart_rate_avg,
                "heart_rate_max": heart_rate_max,
                "cadence_max": cadence_max,
                "resistance_max": resistance_max,
                "leaderboard_rank": leaderboard_rank,
                "total_leaderboard_users": total_leaderboard_users,
                "ftp": ftp
            },
            "muscle_group_scores": {mg["display_name"]: mg["score"] for mg in muscle_group_scores},
            "detailed_metrics": detailed_metrics,
            "summary": summary
        }
        if status == "IN_PROGRESS":
            updated_in_progress = [workout_details]
            print(f"Updating IN_PROGRESS workout: {workout_id} | {created_at} | {title} | {instructor_name}")
        elif status == "COMPLETE":
            updated_workouts.append(workout_details)
            print(f"Processing COMPLETED workout: {workout_id} | {created_at} | {title} | {instructor_name}")
        else:
            print(f"Skipping workout {workout_id} with status '{status}'")
    except Exception as e:
        print(f"Failed to process workout {workout_id}: {e}")
        continue

# Append existing workouts that weren’t fetched by the API
for workout in existing_workouts_data["peloton_workouts"]:
    workout_id = workout.get("workout_id")
    if workout_id not in seen_workout_ids:
        updated_workouts.append(workout)
        print(f"Reusing existing workout: {workout_id} | {workout.get('created_at', 'Unknown')} | {workout.get('title', 'Unknown')}")

# Update in-progress if no new match, keep the last one
if not updated_in_progress and in_progress_data["peloton_workouts"]:
    updated_in_progress = in_progress_data["peloton_workouts"]

# Save workouts and in-progress data
try:
    with open(in_progress_file, "w", encoding="utf-8") as f:
        json.dump({"peloton": "in progress or last completed workout", "peloton_workouts": updated_in_progress}, f, indent=2, ensure_ascii=False)
    print(f"In-progress workout data saved to {in_progress_file}")
except Exception as e:
    print(f"Failed to save in-progress JSON file: {e}")

try:
    with open(output_workouts_file, "w", encoding="utf-8") as f:
        json.dump({"peloton": "all workouts", "peloton_workouts": updated_workouts}, f, indent=2, ensure_ascii=False)
    print(f"Workout data saved to {output_workouts_file}")
except Exception as e:
    print(f"Failed to save workouts JSON file: {e}")

# --- Begin Averages Calculation ---
print(f"Starting averages calculation with {len(updated_workouts)} completed workouts")

# Group workouts by discipline and duration
duration_groups = defaultdict(lambda: defaultdict(list))
tolerance = 60  # Allow ±1 minute variation for grouping

for workout in updated_workouts:
    duration = workout.get("duration", 0)
    status = workout.get("summary", {}).get("status", "unknown").upper()
    discipline = workout.get("fitness_discipline", "").lower()
    print(f"Processing workout: {workout.get('title', 'Unknown')} | Duration: {duration} | Status: {status}")
    if status != "COMPLETE":
        print(f"Skipping {workout.get('title', 'Unknown')} due to status {status}")
        continue
    rounded_duration = round(duration / 60) * 60
    if 300 <= rounded_duration <= 3600:  # Limit to 5-60 minutes
        duration_groups[discipline][rounded_duration].append(workout)
    else:
        print(f"Skipping {workout.get('title', 'Unknown')} due to duration {rounded_duration} outside 5-60 min range")

# Calculate averages, best, worst, and personal record details
averages_data = {}
for discipline, durations in duration_groups.items():
    print(f"Processing discipline: {discipline}")
    averages_data[discipline.capitalize()] = {}
    for duration, workouts_list in durations.items():
        print(f"Processing duration: {duration} seconds ({duration // 60} minutes) with {len(workouts_list)} workouts")
        if not workouts_list:
            print(f"No workouts for {duration} seconds, skipping")
            continue
        if discipline == "cycling":
            # Extract metrics with debug prints
            powers = [w["metrics"]["avg_power"] for w in workouts_list if w["metrics"].get("avg_power") is not None]
            print(f"Power values for {duration} sec: {powers}")
            cadences = [w["metrics"]["avg_cadence"] for w in workouts_list if w["metrics"].get("avg_cadence") is not None]
            print(f"Cadence values for {duration} sec: {cadences}")
            calories = [w["metrics"]["calories"] for w in workouts_list if w["metrics"].get("calories") is not None]
            print(f"Calorie values for {duration} sec: {calories}")
            distances_miles = [w["metrics"]["distance_miles"] for w in workouts_list if w["metrics"].get("distance_miles") is not None]
            print(f"Distance values for {duration} sec: {distances_miles}")
            total_outputs = [w["metrics"].get("total_output", 0) for w in workouts_list]  # Allow zero as fallback
            print(f"Total output values for {duration} sec: {total_outputs}")
            average_speeds = [w["metrics"]["average_speed_mph"] for w in workouts_list if w["metrics"].get("average_speed_mph") is not None]
            print(f"Speed values for {duration} sec: {average_speeds}")
            heart_rates_avg = [w["metrics"]["heart_rate_avg"] for w in workouts_list if w["metrics"].get("heart_rate_avg") is not None]
            print(f"Heart rate avg values for {duration} sec: {heart_rates_avg}")
            heart_rates_max = [w["metrics"]["heart_rate_max"] for w in workouts_list if w["metrics"].get("heart_rate_max") is not None]
            print(f"Heart rate max values for {duration} sec: {heart_rates_max}")
            cadence_maxes = [w["metrics"]["cadence_max"] for w in workouts_list if w["metrics"].get("cadence_max") is not None]
            print(f"Cadence max values for {duration} sec: {cadence_maxes}")
            resistance_maxes = [w["metrics"]["resistance_max"] for w in workouts_list if w["metrics"].get("resistance_max") is not None]
            print(f"Resistance max values for {duration} sec: {resistance_maxes}")
            leaderboard_ranks = [w["metrics"]["leaderboard_rank"] for w in workouts_list if w["metrics"].get("leaderboard_rank") is not None]
            print(f"Leaderboard rank values for {duration} sec: {leaderboard_ranks}")
            total_leaderboard_users_list = [w["metrics"]["total_leaderboard_users"] for w in workouts_list if w["metrics"].get("total_leaderboard_users") is not None]
            print(f"Total leaderboard users values for {duration} sec: {total_leaderboard_users_list}")
            ftps = [w["metrics"]["ftp"] for w in workouts_list if w["metrics"].get("ftp") is not None]
            print(f"FTP values for {duration} sec: {ftps}")

            personal_records = [(w["workout_date"], w["instructor_name"], w["title"], w["summary"]["ride"].get("description", "No description"), w["summary"]["ride"].get("image_url", "No image"), w["metrics"], w["summary"].get("is_total_work_personal_record", False)) 
                              for w in workouts_list if w["summary"].get("is_total_work_personal_record", False)]
            latest_pr = max(personal_records, default=None, key=lambda x: datetime.fromisoformat(x[0])) if personal_records else None
            if latest_pr:
                pr_metrics = latest_pr[5].copy()
                matching_workout = next((w for w in workouts_list if w["workout_date"] == latest_pr[0]), None)
                pr_duration = matching_workout["duration"] / 3600 if matching_workout else latest_pr[5].get("duration", 300) / 3600
                pr_distance_miles = pr_metrics.get("distance_miles", 0)
                pr_metrics["total_output"] = pr_metrics.get("total_output", 0)
                pr_metrics["average_speed_mph"] = round(pr_distance_miles / pr_duration, 2) if pr_duration > 0 and pr_distance_miles > 0 else 0
                latest_pr = (latest_pr[0], latest_pr[1], latest_pr[2], latest_pr[3], latest_pr[4], pr_metrics, latest_pr[6])
            personal_record_details = {
                "percentage": (sum(1 for pr in personal_records if pr[6]) / len(workouts_list) * 100) if personal_records and workouts_list else 0,
                "latest": {
                    "workout_date": latest_pr[0] if latest_pr else None,
                    "instructor_name": latest_pr[1] if latest_pr else None,
                    "title": latest_pr[2] if latest_pr else None,
                    "description": latest_pr[3] if latest_pr else None,
                    "image_url": latest_pr[4] if latest_pr else None,
                    "metrics": latest_pr[5] if latest_pr else None
                } if latest_pr else None
            }
            key = f"{duration // 60}_Minute_Ride".replace(" ", "_")
            averages_data[discipline.capitalize()][key] = {
                "average_power": round(sum(powers) / len(powers), 2) if powers else 0,
                "average_cadence": round(sum(cadences) / len(cadences), 2) if cadences else 0,
                "average_calories": round(sum(calories) / len(calories), 2) if calories else 0,
                "average_distance_miles": round(sum(distances_miles) / len(distances_miles), 2) if distances_miles else 0,
                "average_speed_mph": round(sum(average_speeds) / len(average_speeds), 2) if average_speeds else 0,
                "average_heart_rate": round(sum(heart_rates_avg) / len(heart_rates_avg), 2) if heart_rates_avg else 0,
                "average_heart_rate_max": round(sum(heart_rates_max) / len(heart_rates_max), 2) if heart_rates_max else 0,
                "average_cadence_max": round(sum(cadence_maxes) / len(cadence_maxes), 2) if cadence_maxes else 0,
                "average_resistance_max": round(sum(resistance_maxes) / len(resistance_maxes), 2) if resistance_maxes else 0,
                "average_leaderboard_rank": round(sum(leaderboard_ranks) / len(leaderboard_ranks), 2) if leaderboard_ranks else 0,
                "average_total_leaderboard_users": round(sum(total_leaderboard_users_list) / len(total_leaderboard_users_list), 2) if total_leaderboard_users_list else 0,
                "average_ftp": round(sum(ftps) / len(ftps), 2) if ftps else 0,
                "best_power": max(powers) if powers else 0,
                "best_cadence": max(cadences) if cadences else 0,
                "best_calories": max(calories) if calories else 0,
                "best_distance_miles": max(distances_miles) if distances_miles else 0,
                "best_speed_mph": max(average_speeds) if average_speeds else 0,
                "best_heart_rate": max(heart_rates_avg) if heart_rates_avg else 0,
                "best_heart_rate_max": max(heart_rates_max) if heart_rates_max else 0,
                "best_cadence_max": max(cadence_maxes) if cadence_maxes else 0,
                "best_resistance_max": max(resistance_maxes) if resistance_maxes else 0,
                "best_leaderboard_rank": min(leaderboard_ranks) if leaderboard_ranks else 0,
                "best_total_leaderboard_users": max(total_leaderboard_users_list) if total_leaderboard_users_list else 0,
                "best_ftp": max(ftps) if ftps else 0,
                "worst_power": min(powers) if powers else 0,
                "worst_cadence": min(cadences) if cadences else 0,
                "worst_calories": min(calories) if calories else 0,
                "worst_distance_miles": min(distances_miles) if distances_miles else 0,
                "worst_speed_mph": min(average_speeds) if average_speeds else 0,
                "worst_heart_rate": min(heart_rates_avg) if heart_rates_avg else 0,
                "worst_heart_rate_max": min(heart_rates_max) if heart_rates_max else 0,
                "worst_cadence_max": min(cadence_maxes) if cadence_maxes else 0,
                "worst_resistance_max": min(resistance_maxes) if resistance_maxes else 0,
                "worst_leaderboard_rank": max(leaderboard_ranks) if leaderboard_ranks else 0,
                "worst_total_leaderboard_users": min(total_leaderboard_users_list) if total_leaderboard_users_list else 0,
                "worst_ftp": min(ftps) if ftps else 0,
                "total_output": round(sum(total_outputs) / len(total_outputs), 2) if total_outputs else 0,
                "best_total_output": max(total_outputs) if total_outputs else 0,
                "worst_total_output": min(total_outputs) if total_outputs else 0,
                "personal_record": personal_record_details
            }
            # Calculate muscle group averages
            muscle_group_averages = {}
            unique_mg_names = set()
            for w in workouts_list:
                mg_scores = w.get("muscle_group_scores", [])
                if isinstance(mg_scores, str):
                    try:
                        import ast
                        mg_scores = ast.literal_eval(mg_scores) if mg_scores else []
                    except (ValueError, SyntaxError):
                        mg_scores = []
                if isinstance(mg_scores, list):
                    for mg in mg_scores:
                        if isinstance(mg, dict) and "display_name" in mg:
                            unique_mg_names.add(mg["display_name"])
                else:
                    print(f"Unexpected muscle_group_scores type for workout {w.get('workout_id', 'Unknown')}: {type(mg_scores)}")

            for mg_name in unique_mg_names:
                mg_scores = [w["muscle_group_scores"].get(mg_name, 0) for w in workouts_list if isinstance(w.get("muscle_group_scores"), list) and mg_name in [mg.get("display_name") for mg in w.get("muscle_group_scores", [])]]
                if mg_scores and any(s > 0 for s in mg_scores):
                    muscle_group_averages[mg_name] = round(sum(mg_scores) / len(mg_scores), 2)

            if muscle_group_averages:
                averages_data[discipline.capitalize()][key]["muscle_group_averages"] = muscle_group_averages
        else:
            print(f"Skipping non-cycling discipline: {discipline}")

# Sort durations for consistent output
for discipline in averages_data:
    averages_data[discipline] = dict(sorted(averages_data[discipline].items(), key=lambda x: int(x[0].split('_')[0])))

# Save averages data
try:
    print(f"Attempting to save averages to {output_averages_file} with data: {averages_data}")
    with open(output_averages_file, "w", encoding="utf-8") as f:
        json.dump({"peloton_workout_averages": "cycling workout averages", "peloton_averages": averages_data}, f, indent=2, ensure_ascii=False)
    print(f"Averages data saved to {output_averages_file}")
except Exception as e:
    print(f"Failed to save averages JSON file: {e}")
