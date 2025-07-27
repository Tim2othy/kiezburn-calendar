import re

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
    raw_text = (
        """


        """

    )
    events = parse_events(raw_text)
    for e in events:
        print(e)
