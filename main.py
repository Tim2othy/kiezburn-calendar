import re
import json
from datetime import datetime, timedelta

def parse_events_by_date(raw_text):
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]

    # Manual mapping for the dates mentioned in the data
    date_mapping = {
        "Tuesday 29th": "2025-07-29",
        "Wednesday 30th": "2025-07-30",
        "Thursday 31st": "2025-07-31",
        "Friday 1st": "2025-08-01",
        "Saturday 2nd": "2025-08-02",
        "Sunday 3rd": "2025-08-03",
        "Monday 4th": "2025-08-04"
    }

    result = {}
    current_date = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line is a date header
        if line in date_mapping:
            current_date = date_mapping[line]
            if current_date not in result:
                result[current_date] = []
            i += 1
            continue

        # Match time using a pattern like "10am", "2:30pm", etc.
        if re.match(r'\d{1,2}(:\d{2})?(am|pm)', line.lower()) and current_date:
            time_str = line.lower()
            # Convert to 24-hour format with zero padding
            match = re.match(r'(\d{1,2})(:(\d{2}))?(am|pm)', time_str)
            hour = int(match.group(1))
            minute = int(match.group(3)) if match.group(3) else 0
            if match.group(4) == 'pm' and hour != 12:
                hour += 12
            if match.group(4) == 'am' and hour == 12:
                hour = 0
            formatted_time = f"{hour:02}:{minute:02}"

            # Next two lines should be location and event name
            if i + 2 < len(lines):
                location = lines[i+1]
                event = lines[i+2]
                i += 3

                # Merge additional lines if the event description continues
                while i < len(lines) and not re.match(r'\d{1,2}(:\d{2})?(am|pm)', lines[i].lower()) and lines[i] not in date_mapping:
                    event += " " + lines[i]
                    i += 1

                result[current_date].append({
                    "time": formatted_time,
                    "event": event.strip(),
                    "location": location.strip()
                })
            else:
                i += 1
        else:
            i += 1

    return result

def generate_ics_file(events_by_date, filename='events.ics'):
    """Generate an ICS file from the events data"""
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kiezburn Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for date_str, events in events_by_date.items():
        for event in events:
            # Parse the date and time
            year, month, day = map(int, date_str.split('-'))
            hour, minute = map(int, event['time'].split(':'))

            # Create datetime objects
            start_dt = datetime(year, month, day, hour, minute)
            # Assume 1 hour duration for each event
            end_dt = start_dt + timedelta(hours=1)

            # Format for ICS (UTC format)
            start_str = start_dt.strftime('%Y%m%dT%H%M%S')
            end_str = end_dt.strftime('%Y%m%dT%H%M%S')

            # Create unique ID for the event
            uid = f"{start_str}-{abs(hash(event['event'] + event['location']))}@kiezburn.local"

            # Escape special characters in text fields
            summary = event['event'].replace(',', '\\,').replace(';', '\\;').replace('\\', '\\\\')
            location = event['location'].replace(',', '\\,').replace(';', '\\;').replace('\\', '\\\\')

            # Add event to ICS
            ics_content.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{summary}",
                f"LOCATION:{location}",
                f"DESCRIPTION:Kiezburn event at {location}",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE",
                "END:VEVENT"
            ])

    ics_content.append("END:VCALENDAR")

    # Write to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ics_content))

    return filename

def parse_events(raw_text):
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]

    result = []
    i = 0
    while i < len(lines):
        # Match time using a pattern like "10am", "2:30pm", etc.
        if re.match(r'\d{1,2}(:\d{2})?(am|pm)', lines[i].lower()):
            time_str = lines[i].lower()
            # Convert to 24-hour format with zero padding
            match = re.match(r'(\d{1,2})(:(\d{2}))?(am|pm)', time_str)
            hour = int(match.group(1))
            minute = int(match.group(3)) if match.group(3) else 0
            if match.group(4) == 'pm' and hour != 12:
                hour += 12
            if match.group(4) == 'am' and hour == 12:
                hour = 0
            formatted_time = f"{hour:02}:{minute:02}"

            # Next two lines should be location and event name
            location = lines[i+1]
            event = lines[i+2]
            i += 3

            # Merge additional lines if the event description continues
            while i < len(lines) and not re.match(r'\d{1,2}(:\d{2})?(am|pm)', lines[i].lower()):
                event += " " + lines[i]
                i += 1

            result.append((formatted_time, f"{event.strip()} - {location.strip()}"))
        else:
            i += 1  # Safety skip in case format is off

    return result


# Example usage
if __name__ == "__main__":
    # Read the text file
    try:
        with open('input.txt', 'r', encoding='utf-8') as file:
            raw_text = file.read()

        # Parse the events by date
        events_by_date = parse_events_by_date(raw_text)

        # Save the transformed data to output.txt in JSON format
        with open('output.txt', 'w', encoding='utf-8') as output_file:
            json.dump(events_by_date, output_file, indent=2, ensure_ascii=False)

        # Generate ICS file for Google Calendar import
        ics_filename = generate_ics_file(events_by_date, 'kiezburn_events.ics')

        print(f"Successfully processed events for {len(events_by_date)} dates")
        print(f"- JSON output saved to: output.txt")
        print(f"- ICS calendar file saved to: {ics_filename}")

        # Count total events
        total_events = sum(len(events) for events in events_by_date.values())
        print(f"- Total events: {total_events}")

        # Print a preview of the data structure
        print("\nDates found:")
        for date in sorted(events_by_date.keys()):
            print(f"  {date}: {len(events_by_date[date])} events")

        # Show first few events from the first date
        if events_by_date:
            first_date = sorted(events_by_date.keys())[0]
            print(f"\nFirst 3 events for {first_date}:")
            for event in events_by_date[first_date][:3]:
                print(f"  {event['time']} - {event['event']} @ {event['location']}")

        print(f"\nTo import into Google Calendar:")
        print(f"1. Open Google Calendar")
        print(f"2. Click the '+' next to 'Other calendars'")
        print(f"3. Select 'Import'")
        print(f"4. Choose the file: {ics_filename}")
        print(f"5. Select which calendar to add events to")
        print(f"6. Click 'Import'")

    except FileNotFoundError:
        print("Error: input.txt file not found")
    except Exception as e:
        print(f"Error: {e}")
