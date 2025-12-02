import math
from datetime import datetime, timedelta

# 1 mile ≈ 1.60934 km
MILES_TO_METERS = 1609.34
HOURS_TO_SECONDS = 3600

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def get_coordinate_at_distance(geometry, target_distance_meters):
    """
    Finds the coordinate along the path at the specified distance.
    geometry: List of [lng, lat]
    """
    if not geometry:
        return None
    
    current_dist = 0
    for i in range(len(geometry) - 1):
        p1 = geometry[i]
        p2 = geometry[i+1]
        
        # geometry is [lng, lat]
        dist_segment = haversine_distance(p1[1], p1[0], p2[1], p2[0])
        
        if current_dist + dist_segment >= target_distance_meters:
            # Interpolate or just return p2 (simple approach)
            # For better precision, we could interpolate, but p2 is close enough for map markers usually
            return {"lat": p2[1], "lng": p2[0]}
        
        current_dist += dist_segment
        
    # If we run out of geometry, return the last point
    last = geometry[-1]
    return {"lat": last[1], "lng": last[0]}

def generate_daily_logs(route_distance_meters, route_duration_seconds, cycle_used_hours):
    # Deprecated in favor of generate_eld_sheets
    return generate_eld_sheets(route_distance_meters, route_duration_seconds, cycle_used_hours)


def generate_eld_sheets(route_distance_meters, route_duration_seconds, cycle_used_hours, start_time=None, route_geometry=None):
    """
    Generate ELD-style log sheets for the trip.
    Returns a list of daily logs, each containing:
    - date
    - grid_events: list of {status, start, end, duration} (clamped to 24h day)
    - summary: {distance, drive_hours, on_duty_hours, ...}
    - stops: list of {type, location, time}
    """
    if start_time is None:
        start_time = datetime.now()

    # Constants
    HOURS_TO_SECONDS = 3600
    MILES_TO_METERS = 1609.34
    MAX_DRIVE_HOURS = 11
    MAX_ON_DUTY_HOURS = 14
    CYCLE_LIMIT_HOURS = 70
    FUEL_RANGE_METERS = 1000 * MILES_TO_METERS
    
    # --- STEP 1: Generate Continuous Stream of Events ---
    # We simulate the trip event-by-event without worrying about day boundaries yet.
    
    raw_events = [] # {status, start, end, duration, start_dist, end_dist}
    stops_data = [] # {type, time, dist}
    
    current_time = start_time
    remaining_distance = route_distance_meters
    avg_speed_mps = route_distance_meters / route_duration_seconds if route_duration_seconds > 0 else 0
    
    cycle_used_seconds = cycle_used_hours * HOURS_TO_SECONDS
    cycle_limit_seconds = CYCLE_LIMIT_HOURS * HOURS_TO_SECONDS
    
    cumulative_distance = 0
    distance_since_fuel = 0
    
    # Shift State
    shift_start_time = current_time
    shift_drive_seconds = 0
    shift_on_duty_seconds = 0
    time_since_last_break = 0
    
    trip_complete = False
    
    # Initial Pickup (1 hour On Duty)
    duration = 3600
    raw_events.append({
        "status": "ON_DUTY",
        "start": current_time,
        "end": current_time + timedelta(seconds=duration),
        "duration": duration,
        "start_dist": cumulative_distance,
        "end_dist": cumulative_distance
    })
    stops_data.append({
        "type": "Pickup",
        "time": current_time,
        "dist": cumulative_distance
    })
    current_time += timedelta(seconds=duration)
    shift_on_duty_seconds += duration
    cycle_used_seconds += duration
    
    while not trip_complete:
        # Determine constraints
        
        # 1. Fuel
        dist_to_fuel = FUEL_RANGE_METERS - distance_since_fuel
        time_to_fuel = dist_to_fuel / avg_speed_mps if avg_speed_mps > 0 else 999999
        
        # 2. Destination
        time_to_dest = remaining_distance / avg_speed_mps if avg_speed_mps > 0 else 0
        
        # 3. Shift Limits (11h drive, 14h duty)
        time_left_drive = (11 * HOURS_TO_SECONDS) - shift_drive_seconds
        time_left_duty = (14 * HOURS_TO_SECONDS) - shift_on_duty_seconds
        
        # 4. Cycle Limit
        time_left_cycle = cycle_limit_seconds - cycle_used_seconds
        
        # 5. 8h Break Rule (Must take 30m break if driving > 8h since last break)
        # Simplified: If we have driven 8h in this shift without a break, we need one.
        # We track continuous drive time? Or just cumulative in shift? 
        # DOT: "May drive only if 8 hours or less have passed since end of driver's last off-duty/sleeper period of at least 30 minutes."
        # Actually it's: Drive limit is 11h. But you must stop for 30m before driving beyond the 8th hour of COMING ON DUTY? No, since last break.
        # Let's use a simplified counter: time_since_last_break (counts driving time only? No, counts all time since break).
        # Actually, let's just enforce: After 8h of DRIVING in a shift, force a 30m break.
        time_to_8h_break = (8 * HOURS_TO_SECONDS) - shift_drive_seconds 
        # If we already took a break, this logic might be too strict, but it's safe.
        # Better: reset shift_drive_seconds only on 10h break. 
        # We need a separate counter for 8h rule if we want to be precise, but for this app, 
        # let's assume we take a break at 8h of driving.
        
        # DECISION LOGIC
        
        # Check if we need to stop for Shift/Cycle reasons
        if time_left_drive <= 0 or time_left_duty <= 0:
            # Must take 10h break (Sleeper)
            duration = 10 * HOURS_TO_SECONDS
            raw_events.append({
                "status": "SLEEPER",
                "start": current_time,
                "end": current_time + timedelta(seconds=duration),
                "duration": duration,
                "start_dist": cumulative_distance,
                "end_dist": cumulative_distance
            })
            stops_data.append({
                "type": "Rest (10h)",
                "time": current_time,
                "dist": cumulative_distance
            })
            current_time += timedelta(seconds=duration)
            # Reset Shift
            shift_drive_seconds = 0
            shift_on_duty_seconds = 0
            continue # Loop again to decide next action
            
        if time_left_cycle <= 0:
            # Must take 34h restart
            duration = 34 * HOURS_TO_SECONDS
            raw_events.append({
                "status": "OFF_DUTY",
                "start": current_time,
                "end": current_time + timedelta(seconds=duration),
                "duration": duration,
                "start_dist": cumulative_distance,
                "end_dist": cumulative_distance
            })
            stops_data.append({
                "type": "Cycle Restart (34h)",
                "time": current_time,
                "dist": cumulative_distance
            })
            current_time += timedelta(seconds=duration)
            cycle_used_seconds = 0
            shift_drive_seconds = 0
            shift_on_duty_seconds = 0
            continue

        # We can drive. How long?
        # Candidates:
        next_event_time = min(time_to_fuel, time_to_dest, time_left_drive, time_left_duty, time_left_cycle)
        
        # Check 8h break
        if shift_drive_seconds < 8 * HOURS_TO_SECONDS and (shift_drive_seconds + next_event_time) > 8 * HOURS_TO_SECONDS:
            # Cap drive at 8h mark
            time_to_cap = (8 * HOURS_TO_SECONDS) - shift_drive_seconds
            if time_to_cap < next_event_time:
                next_event_time = time_to_cap
                # We will stop here, and next loop will see we are at 8h and force break?
                # No, we need to explicitly force break if we are AT 8h.
        
        # If we are AT 8h drive (approx), take break
        if abs(shift_drive_seconds - 8 * HOURS_TO_SECONDS) < 60: # Tolerance
             duration = 1800 # 30 mins
             raw_events.append({
                "status": "OFF_DUTY",
                "start": current_time,
                "end": current_time + timedelta(seconds=duration),
                "duration": duration,
                "start_dist": cumulative_distance,
                "end_dist": cumulative_distance
            })
             stops_data.append({
                "type": "Rest (30m)",
                "time": current_time,
                "dist": cumulative_distance
            })
             current_time += timedelta(seconds=duration)
             # Break extends shift time but doesn't count as drive
             shift_on_duty_seconds += duration 
             # Actually 30m break is Off Duty, so it does NOT count to 14h window? 
             # DOT: "The 14-hour driving window... consecutive hours." Off duty does NOT pause the 14h clock.
             # So yes, it counts towards shift elapsed time.
             
             # But it allows driving to continue.
             # Hack: reduce shift_drive_seconds to allow more driving? 
             # No, 8h rule is "since last break". 
             # So we need to track "drive_since_break".
             # For simplicity: We just took a break, so we can drive another 3h (until 11h limit).
             # We don't need to reset shift_drive_seconds (that's 11h limit).
             # We just pass the 8h check.
             # To avoid infinite loop of taking breaks, we need to know we JUST took one.
             # Let's just nudge shift_drive_seconds by 1 sec to pass the equality check? 
             # Or better, logic: if we just drove, and we are at 8h, take break.
             # If we just took a break, we drive.
             # Let's rely on the loop. Next iteration: shift_drive is 8h. 
             # We need to ensure we don't trigger "If AT 8h" again.
             # We can check if last event was OFF_DUTY.
             if raw_events[-1]["status"] == "OFF_DUTY":
                 pass # Don't take another break
             else:
                 continue # Go take the break
        
        # DRIVE
        if next_event_time > 0:
            raw_events.append({
                "status": "DRIVING",
                "start": current_time,
                "end": current_time + timedelta(seconds=next_event_time),
                "duration": next_event_time,
                "start_dist": cumulative_distance,
                "end_dist": cumulative_distance + (next_event_time * avg_speed_mps)
            })
            
            dist_covered = next_event_time * avg_speed_mps
            remaining_distance -= dist_covered
            cumulative_distance += dist_covered
            distance_since_fuel += dist_covered
            
            current_time += timedelta(seconds=next_event_time)
            shift_drive_seconds += next_event_time
            shift_on_duty_seconds += next_event_time
            cycle_used_seconds += next_event_time
            
            # Check what stopped us
            if remaining_distance <= 100:
                trip_complete = True
                # Dropoff
                duration = 3600
                raw_events.append({
                    "status": "ON_DUTY",
                    "start": current_time,
                    "end": current_time + timedelta(seconds=duration),
                    "duration": duration,
                    "start_dist": cumulative_distance,
                    "end_dist": cumulative_distance
                })
                stops_data.append({
                    "type": "Dropoff",
                    "time": current_time,
                    "dist": cumulative_distance
                })
                current_time += timedelta(seconds=duration)
                
            elif distance_since_fuel >= FUEL_RANGE_METERS - 100:
                # Fuel
                duration = 1800
                raw_events.append({
                    "status": "ON_DUTY",
                    "start": current_time,
                    "end": current_time + timedelta(seconds=duration),
                    "duration": duration,
                    "start_dist": cumulative_distance,
                    "end_dist": cumulative_distance
                })
                stops_data.append({
                    "type": "Fuel",
                    "time": current_time,
                    "dist": cumulative_distance
                })
                current_time += timedelta(seconds=duration)
                distance_since_fuel = 0
                shift_on_duty_seconds += duration
                cycle_used_seconds += duration

    # --- STEP 2: Bucket into Calendar Days (Midnight to Midnight) ---
    
    daily_logs = []
    
    # Helper to get midnight of a datetime
    def get_midnight(dt):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    trip_start = raw_events[0]["start"]
    trip_end = raw_events[-1]["end"]
    
    current_day_start = get_midnight(trip_start)
    
    while current_day_start < trip_end:
        current_day_end = current_day_start + timedelta(days=1)
        
        day_log = {
            "day_no": len(daily_logs) + 1,
            "date": current_day_start.strftime("%Y-%m-%d"),
            "grid_events": [],
            "stops": [],
            "summary": {
                "drive_hours": 0,
                "on_duty_hours": 0,
                "distance_miles": 0
            }
        }
        
        # Find events that overlap with this day
        for event in raw_events:
            # Event interval: [e_start, e_end]
            # Day interval: [d_start, d_end]
            
            e_start = event["start"]
            e_end = event["end"]
            
            # Overlap logic
            overlap_start = max(e_start, current_day_start)
            overlap_end = min(e_end, current_day_end)
            
            if overlap_start < overlap_end:
                # There is an overlap
                duration = (overlap_end - overlap_start).total_seconds()
                
                day_log["grid_events"].append({
                    "status": event["status"],
                    "start": overlap_start.isoformat(),
                    "end": overlap_end.isoformat(),
                    "duration": duration
                })
                
                # Update summary
                if event["status"] == "DRIVING":
                    day_log["summary"]["drive_hours"] += duration
                    # Pro-rate distance
                    total_event_dist = event["end_dist"] - event["start_dist"]
                    total_event_dur = event["duration"]
                    if total_event_dur > 0:
                        dist_fraction = duration / total_event_dur
                        day_log["summary"]["distance_miles"] += (total_event_dist * dist_fraction / MILES_TO_METERS)
                
                if event["status"] in ["DRIVING", "ON_DUTY"]:
                    day_log["summary"]["on_duty_hours"] += duration
                    
        # Find stops in this day
        for stop in stops_data:
            if current_day_start <= stop["time"] < current_day_end:
                # Get coord
                coord = None
                if route_geometry:
                    coord = get_coordinate_at_distance(route_geometry, stop["dist"])
                
                day_log["stops"].append({
                    "type": stop["type"],
                    "time": stop["time"].strftime("%H:%M"),
                    "coord": coord
                })
        
        # Round summary
        day_log["summary"]["drive_hours"] = round(day_log["summary"]["drive_hours"] / 3600, 2)
        day_log["summary"]["on_duty_hours"] = round(day_log["summary"]["on_duty_hours"] / 3600, 2)
        day_log["summary"]["distance_miles"] = round(day_log["summary"]["distance_miles"], 2)
        
        daily_logs.append(day_log)
        current_day_start = current_day_end

    return daily_logs