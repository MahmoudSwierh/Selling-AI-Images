import anthropic
import base64
from PIL import Image
import os
import io
import csv
import re
import time
from pathlib import Path

script_dir = Path(__file__).resolve().parent
base_dir = script_dir.parent

images_folder = base_dir / "To Upload"
output_csv1 = base_dir / "adobe.csv"
output_csv2 = base_dir / "freepik.csv"


categories = ["Animals", "Buildings and Architecture", "Business", "Drinks", "The Environment", "States of Mind", "Food", "Graphic Resources", "Hobbies and Leisure", "Industry", "Landscapes", "Lifestyle", "People", "Plants and Flowers", "Culture and Religion", "Science", "Social Issues", "Sports", "Technology", "Transport", "Travel"]

client = anthropic.Anthropic(
    api_key = os.environ.get("ANTHROPIC_API_KEY"),
)

def analyze_image_with_claude(image_path):
    with Image.open(image_path) as img:
        original_width, original_height = img.size

        new_width = original_width // 6
        new_height = original_height // 6

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)

    buffer = io.BytesIO()
    resized_img.save(buffer, format="JPEG", quality=100, optimize=True)
    buffer.seek(0)

    image_data = base64.standard_b64encode(buffer.read()).decode("utf-8")
    message = client.messages.create( #claude-3-haiku-20240307 #claude-3-5-haiku-20241022
        model="claude-3-5-haiku-20241022",
        max_tokens=2000,
        temperature=0,
        system="You're an expert Adobe Stock contributer.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze the provided stock image carefully. Then, create a descriptive title of 70 characters or fewer.\nThen, select the single most relevant category from the following list and specify its order number: Animals, Buildings and Architecture, Business, Drinks, The Environment, States of Mind, Food, Graphic Resources, Hobbies and Leisure, Industry, Landscapes, Lifestyle, People, Plants and Flowers, Culture and Religion, Science, Social Issues, Sports, Technology, Transport, Travel.\nPrioritize precision in choosing the category by considering the image's primary focus\nFinally, generate a list of 45 keywords which should include every aspect of the following list: {visible elements (e.g., mountains, buildings, clouds, people, vehicles, animals), objects (e.g., smartphone, bicycle, cup of coffee, lantern, suitcase), colors (e.g., red, blue, monochrome, gradient, gold), numbers (e.g., nobody, one, two, dozen, hundreds, crowd), actions (e.g., running, cooking, laughing, meditating, jumping), styles (e.g., minimalism, vintage, surreal, abstract, flat design), settings (e.g., office, beach, forest, kitchen, urban street), seasons (e.g., spring, summer, autumn, winter), cultural or symbolic meanings (e.g., balance, luck, agreement), visual composition (e.g., symmetry, rule of thirds, negative space, centered), perspectives (e.g., bird’s-eye, worm’s-eye, eye level, top-down, side profile), locations (e.g., New York City skyline, Sahara desert, Tokyo street, Alpine mountains), lighting conditions (e.g., golden hour, harsh sunlight, soft diffused light, silhouette, backlighting), artistic techniques (e.g., watercolor effect, double exposure, bokeh, motion blur, pencil sketch), photographic or rendering styles (e.g., HDR, black and white, cinematic, 3D render, isometric, film grain)}\nPut the keywords in one line, with numbering and separated by comma.\nHere is a response example:\nTitle: A young girl with striking eyes and freckles stares intensely at the camera\nCategory: 13. People\nKeywords: 1.look, 2.background, 3.beautiful, 4.face, 5.natural, 6.art, 7.dark, 8.style, 9.pretty, 10.model, 11.human, 12.indoor, 13.young, 14.beauty, 15.artistic, 16.portrait, 17.person, 18.closeup, 19.studio, 20.cute, 21.expression, 22.female, 23.head, 24.innocent, 25.kid, 26.child, 27.youth, 28.eyes, 29.girl, 30.serious, 31.sweet, 32.little, 33.skin, 34.hair, 35.stare, 36.innocence, 37.adorable, 38.artful, 39.youngster, 40.teen, 41.portraiture, 42.freckles, 43.one, 44.artistic portrait, 45.artful portrait"
                    }
                ]
            }
        ]
    )
    print(message.content[0].text)
    print(message.usage)
    return message.content[0].text

# Open the CSV file and write headers before processing images

def file_exists_in_csv(csv_path, filename, delimiter=','):
    try:
        with open(csv_path, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            for row in reader:
                if row["Filename"] == filename:
                    return True
    except FileNotFoundError:
        print("File not found!!")
        pass  # If the file doesn't exist, proceed
    return False

# Open the CSV files and write headers if they don't exist
if not os.path.exists(output_csv1):
    with open(output_csv1, mode="w", newline="", encoding="utf-8") as csv_file1:
        writer1 = csv.DictWriter(csv_file1, fieldnames=["Filename", "Title", "Keywords", "Category"])
        writer1.writeheader()

if not os.path.exists(output_csv2):
    with open(output_csv2, mode="w", newline="", encoding="utf-8") as csv_file2:
        writer2 = csv.DictWriter(csv_file2, fieldnames=["Filename", "Title", "Keywords"], delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer2.writeheader()

for filename in os.listdir(images_folder):
    if filename.lower().endswith((".jpg", ".jpeg")):
        with open(output_csv1, mode="a", newline="", encoding="utf-8") as csv_file1, \
            open(output_csv2, mode="a", newline="", encoding="utf-8") as csv_file2:
            
            writer1 = csv.DictWriter(csv_file1, fieldnames=["Filename", "Title", "Keywords", "Category"])
            writer2 = csv.DictWriter(csv_file2, fieldnames=["Filename", "Title", "Keywords"], delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            image_path = os.path.join(images_folder, filename)

            if ("test" not in images_folder) and file_exists_in_csv(output_csv1, filename) and file_exists_in_csv(output_csv2, filename, delimiter=';'):
                print(f"Skipping {filename}: Already exists in the CSV files.")
                continue

            try:
                response = analyze_image_with_claude(image_path)

                title_match = re.search(r"Title:\s*(.*?)\s*(?:\n|$)", response, re.IGNORECASE)
                title = title_match.group(1).strip()

                # Pattern to extract keywords
                keywords_match = re.search(r"Keywords:\s*(.*?)\s*(?:\n|$)", response, re.IGNORECASE)
                if keywords_match:
                    keywords_raw = keywords_match.group(1)
                    # Remove numbering if present and split keywords
                    keywords = re.sub(r"\d+\.\s*", "", keywords_raw).replace(",", " ").split()
                    keywords = ", ".join(keywords)

                # Pattern to extract category
                category_match = re.search(r"Category:\s*\d*\.\s*(.*?)\s*(?:\n|$)", response, re.IGNORECASE)

                category = category_match.group(1).strip()
                category_num = categories.index(category) + 1
                # print(filename)
                # print(title)
                # print(keywords)
                # print(category_num)

                writer1.writerow({
                    "Filename": filename,
                    "Title": title,
                    "Keywords": keywords,
                    "Category": category_num
                })

                writer2.writerow({
                    "Filename": filename,
                    "Title": title,
                    "Keywords": keywords
                })
                time.sleep(0.5)

                print(f"\nProcessed {filename}: Metadata added.")

            except Exception as e:
                print(f"Error processing {filename}: {e}")
                break
        time.sleep(0.5)