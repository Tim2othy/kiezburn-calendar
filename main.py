"""Kiezburn Calendar Parser"""
import re
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

def parse_events_by_date(raw_text):
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]

    # Manually mapping the dates
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

def generate_ics_file(events_by_date, filename='kiezburn_events.ics'):
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kiezburn Calendar Parser//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Kiezburn Events",
        "X-WR-CALDESC:Kiezburn event schedule"
    ]

    event_count = 0
    for date_str, events in sorted(events_by_date.items()):
        for event in events:
            try:
                # Parse the date and time
                year, month, day = map(int, date_str.split('-'))
                hour, minute = map(int, event['time'].split(':'))

                # Create datetime objects
                start_dt = datetime(year, month, day, hour, minute)
                # Assume 1 hour duration for each event
                end_dt = start_dt + timedelta(hours=1)

                # Format for ICS (local time format)
                start_str = start_dt.strftime('%Y%m%dT%H%M%S')
                end_str = end_dt.strftime('%Y%m%dT%H%M%S')

                # Create unique ID for the event
                uid = f"{start_str}-{abs(hash(event['event'] + event['location']))}@kiezburn.local"

                # Escape special characters in text fields according to RFC 5545
                summary = event['event'].replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')
                location = event['location'].replace('\\', '\\\\').replace(',', '\\,').replace(';', '\\;').replace('\n', '\\n')

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
                    f"CREATED:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                    "END:VEVENT"
                ])
                event_count += 1

            except (ValueError, KeyError) as e:
                print(f"Warning: Skipped invalid event: {event} - {e}")
                continue

    ics_content.append("END:VCALENDAR")

    # Write to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ics_content))
        print(f"✓ Generated ICS file")
    except IOError as e:
        print(f"Error writing ICS file: {e}")
        return None

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


def main():
    """Main function to process event data and generate output files."""
    input_file = 'input.txt'
    json_file = 'events.json'
    ics_file = 'kiezburn_events.ics'

    print("🎪 Kiezburn Calendar Parser")
    print("=" * 40)

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: {input_file} not found!")
        print(f"Please create {input_file} with your event schedule.")
        sys.exit(1)

    try:
        # Read the input file
        print(f"📖 Reading {input_file}")
        with open(input_file, 'r', encoding='utf-8') as file:
            raw_text = file.read()

        if not raw_text.strip():
            print(f"❌ Error: {input_file} is empty!")
            sys.exit(1)

        # Parse the events by date
        events_by_date = parse_events_by_date(raw_text)

        if not events_by_date:
            print("❌ No events found! Check your input format.")
            sys.exit(1)

        # Save the structured data as JSON
        print(f"💾 Saving data to {json_file}")
        try:
            with open(json_file, 'w', encoding='utf-8') as output_file:
                json.dump(events_by_date, output_file, indent=2, ensure_ascii=False)
            print(f"✓ JSON data saved successfully")
        except IOError as e:
            print(f"❌ Error saving JSON file: {e}")
            sys.exit(1)

        # Generate ICS calendar file
        print(f"📅 Generating calendar file {ics_file}")
        ics_filename = generate_ics_file(events_by_date, ics_file)

        if not ics_filename:
            print("❌ Failed to generate ICS file")
            sys.exit(1)

        # Summary statistics
        total_events = sum(len(events) for events in events_by_date.values())
        print("")
        print("📊 SUMMARY")
        print(f"✓ Processed {len(events_by_date)} dates")
        print(f"✓ Total events: {total_events}")
        print(f"✓ JSON file: {json_file}")
        print(f"✓ Calendar file: {ics_filename}")

        # Events per day breakdown
        print(f"\n📅 Events per day:")
        for date in sorted(events_by_date.keys()):
            # Convert date to more readable format
            dt = datetime.strptime(date, '%Y-%m-%d')
            day_name = dt.strftime('%A, %B %d')
            print(f"  {day_name}: {len(events_by_date[date])} events")

    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found!")
        print("Please make sure the input file exists.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
