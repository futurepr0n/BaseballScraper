import requests
from bs4 import BeautifulSoup
import json

# Fetch the webpage with a User-Agent header
url = "https://www.espn.com/mlb/injuries"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.espn.com/',
    'Connection': 'keep-alive'
}
response = requests.get(url, headers=headers)
html_content = response.text

# Parse the HTML
soup = BeautifulSoup(html_content, 'html.parser')

# Extract data from each team's table
data = []

# Find all team injury sections
team_sections = soup.find_all('div', class_='ResponsiveTable Table__league-injuries')

for section in team_sections:
    # Get the team name from the span with class "injuries__teamName"
    team_name_element = section.find('span', class_='injuries__teamName ml2')
    
    if team_name_element:
        team_name = team_name_element.text.strip()
        
        # Find the table in this section
        table = section.find('table')
        if table:
            # Find all rows in the table (skip the header row)
            rows = table.find_all('tr', class_='Table__TR Table__TR--sm Table__even')
            
            for row in rows:
                # Find cells by their class names to ensure correct data extraction
                name_cell = row.find('td', class_='col-name Table__TD')
                pos_cell = row.find('td', class_='col-pos Table__TD')
                date_cell = row.find('td', class_='col-date Table__TD')
                status_cell = row.find('td', class_='col-stat Table__TD')
                comment_cell = row.find('td', class_='col-desc Table__TD')
                
                if name_cell and pos_cell and date_cell and status_cell and comment_cell:
                    # Extract the name (removing the link structure)
                    name_link = name_cell.find('a')
                    name = name_link.text.strip() if name_link else name_cell.text.strip()
                    
                    # Extract status text (removing the span structure)
                    status_span = status_cell.find('span')
                    status = status_span.text.strip() if status_span else status_cell.text.strip()
                    
                    # Create a dictionary for the player
                    player_data = {
                        "TEAM NAME": team_name,
                        "NAME": name,
                        "POS": pos_cell.text.strip(),
                        "EST. RETURN DATE": date_cell.text.strip(),
                        "STATUS": status,
                        "COMMENT": comment_cell.text.strip()
                    }
                    
                    # Add to the data list
                    data.append(player_data)

# Save as JSON
with open('mlb_injuries.json', 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=4)

print(f"Data has been scraped and saved as 'mlb_injuries.json' with {len(data)} entries")